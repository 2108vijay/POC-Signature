"""
MinIO Storage Client for Signature Detection POC
Handles authentication, bucket management, upload/download, and presigned URLs.
"""

import hashlib
import io
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from loguru import logger

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    logger.warning("minio not installed — install with: pip install minio")


class MinioStorageClient:
    """
    MinIO client for the signature detection POC.
    Stores: raw images, enhanced images, detection results, cropped signatures.
    """

    def __init__(
        self,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        bucket_name: str = None,
        secure: bool = False,
    ):
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = bucket_name or os.getenv("MINIO_BUCKET_NAME", "signature-poc")
        self.secure = secure or os.getenv("MINIO_SECURE", "false").lower() == "true"
        self.client = None
        self._connect()

    def _connect(self):
        """Establish MinIO connection."""
        if not MINIO_AVAILABLE:
            logger.error("minio package not installed")
            return

        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
            self._ensure_bucket()
            logger.info(f"Connected to MinIO at {self.endpoint}, bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"MinIO connection failed: {e}")
            logger.info(
                "To start MinIO locally with Docker:\n"
                "  docker run -p 9000:9000 -p 9001:9001 \\\n"
                "    -e MINIO_ROOT_USER=minioadmin \\\n"
                "    -e MINIO_ROOT_PASSWORD=minioadmin \\\n"
                "    minio/minio server /data --console-address ':9001'"
            )

    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            logger.info(f"Created bucket: {self.bucket_name}")

    @property
    def is_connected(self) -> bool:
        return self.client is not None

    # ─── Upload Methods ───────────────────────────────────────────────────────

    def upload_image(
        self,
        image: np.ndarray,
        object_name: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Encode a numpy BGR image and upload to MinIO. Returns object URL."""
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")

        _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        data = io.BytesIO(buffer.tobytes())
        size = len(buffer.tobytes())

        extra_headers = {}
        if metadata:
            # MinIO metadata keys must be prefixed with x-amz-meta-
            extra_headers = {f"x-amz-meta-{k}": str(v) for k, v in metadata.items()}

        self.client.put_object(
            self.bucket_name,
            object_name,
            data,
            size,
            content_type="image/jpeg",
            metadata=extra_headers or None,
        )
        logger.info(f"Uploaded image: {object_name} ({size / 1024:.1f} KB)")
        return f"{self.endpoint}/{self.bucket_name}/{object_name}"

    def upload_file(self, local_path: str, object_name: str) -> str:
        """Upload a local file to MinIO."""
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")

        self.client.fput_object(self.bucket_name, object_name, str(local_path))
        logger.info(f"Uploaded file: {local_path} → {object_name}")
        return f"{self.endpoint}/{self.bucket_name}/{object_name}"

    def upload_json(self, data: dict, object_name: str) -> str:
        """Upload a JSON payload to MinIO."""
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")

        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.client.put_object(
            self.bucket_name,
            object_name,
            io.BytesIO(json_bytes),
            len(json_bytes),
            content_type="application/json",
        )
        logger.info(f"Uploaded JSON: {object_name}")
        return f"{self.endpoint}/{self.bucket_name}/{object_name}"

    # ─── Download Methods ─────────────────────────────────────────────────────

    def download_image(self, object_name: str) -> np.ndarray:
        """Download an image from MinIO and decode to numpy array."""
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")

        response = self.client.get_object(self.bucket_name, object_name)
        data = np.frombuffer(response.read(), dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)

    def download_file(self, object_name: str, local_path: str):
        """Download an object to a local file."""
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")

        self.client.fget_object(self.bucket_name, object_name, str(local_path))
        logger.info(f"Downloaded: {object_name} → {local_path}")

    # ─── URL Generation ───────────────────────────────────────────────────────

    def presigned_url(self, object_name: str, expires_hours: int = 24) -> str:
        """Generate a presigned URL for temporary access."""
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")

        url = self.client.presigned_get_object(
            self.bucket_name,
            object_name,
            expires=timedelta(hours=expires_hours),
        )
        logger.info(f"Presigned URL ({expires_hours}h): {object_name}")
        return url

    # ─── Full Pipeline Storage ────────────────────────────────────────────────

    def store_detection_result(
        self,
        image: np.ndarray,
        result: dict,
        signature_crops: list = None,
        run_id: str = None,
    ) -> dict:
        """
        Store a full detection result set:
          - Original / enhanced image
          - JSON result report
          - Individual signature crops
        Returns dict of stored object names.
        """
        if run_id is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_hash = hashlib.md5(image.tobytes()).hexdigest()[:8]
            run_id = f"{ts}_{img_hash}"

        stored = {}
        prefix = f"detections/{run_id}"

        # Store source image
        img_obj = f"{prefix}/image.jpg"
        self.upload_image(image, img_obj, metadata={"run_id": run_id})
        stored["image"] = img_obj

        # Store JSON result
        result_obj = f"{prefix}/result.json"
        result_with_id = {"run_id": run_id, **result}
        self.upload_json(result_with_id, result_obj)
        stored["result"] = result_obj

        # Store signature crops
        if signature_crops:
            stored["signatures"] = []
            for i, crop_path in enumerate(signature_crops):
                obj_name = f"{prefix}/signatures/sig_{i:02d}.jpg"
                self.upload_file(str(crop_path), obj_name)
                stored["signatures"].append(obj_name)

        logger.info(f"Detection run stored under prefix: {prefix}")
        return {"run_id": run_id, "objects": stored}

    def list_runs(self, limit: int = 50) -> list:
        """List recent detection runs stored in MinIO."""
        if not self.is_connected:
            return []

        objects = self.client.list_objects(
            self.bucket_name, prefix="detections/", recursive=False
        )
        runs = []
        for obj in objects:
            if obj.is_dir:
                runs.append({
                    "run_id": obj.object_name.split("/")[1],
                    "prefix": obj.object_name,
                })
        return runs[:limit]

    def health_check(self) -> dict:
        """Return MinIO connection health status."""
        if not self.is_connected:
            return {"status": "disconnected", "endpoint": self.endpoint}
        try:
            bucket_exists = self.client.bucket_exists(self.bucket_name)
            objects = list(self.client.list_objects(self.bucket_name, prefix="detections/"))
            return {
                "status": "connected",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name,
                "bucket_exists": bucket_exists,
                "detection_runs": len(objects),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
