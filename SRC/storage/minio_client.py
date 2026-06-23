import hashlib
import io
import json
from datetime import datetime, timedelta
from typing import Optional

import cv2
import numpy as np
from minio import Minio
from SRC.core.config import config
from SRC.utils.logger import logger


class MinioStorageClient:

    def __init__(self):
        self.endpoint = config.MINIO_ENDPOINT
        self.bucket   = config.MINIO_BUCKET
        self.client   = None
        self._connect()

    def _connect(self):
        try:
            self.client = Minio(
                self.endpoint,
                access_key=config.MINIO_ACCESS_KEY,
                secret_key=config.MINIO_SECRET_KEY,
                secure=config.MINIO_SECURE,
            )
            self._ensure_bucket()
            logger.info(f"MinIO connected: {self.endpoint} | bucket: {self.bucket}")
        except Exception as e:
            logger.error(f"MinIO connection failed: {e}")
            self.client = None

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info(f"Bucket created: {self.bucket}")

    @property
    def is_connected(self) -> bool:
        return self.client is not None

    # ── Upload ────────────────────────────────────────────────────────────────

    def upload_image(
        self,
        image: np.ndarray,
        object_name: str,
        metadata: Optional[dict] = None
    ) -> str:
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")

        _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        data    = io.BytesIO(buffer.tobytes())
        size    = len(buffer.tobytes())
        headers = {f"x-amz-meta-{k}": str(v) for k, v in (metadata or {}).items()}

        self.client.put_object(
            self.bucket, object_name, data, size,
            content_type="image/jpeg",
            metadata=headers or None,
        )
        logger.info(f"Uploaded image: {object_name} ({size / 1024:.1f} KB)")
        return f"{self.endpoint}/{self.bucket}/{object_name}"

    def upload_file(self, local_path: str, object_name: str) -> str:
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")
        self.client.fput_object(self.bucket, object_name, str(local_path))
        logger.info(f"Uploaded file: {local_path} → {object_name}")
        return f"{self.endpoint}/{self.bucket}/{object_name}"

    def upload_json(self, data: dict, object_name: str) -> str:
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.client.put_object(
            self.bucket, object_name,
            io.BytesIO(json_bytes), len(json_bytes),
            content_type="application/json",
        )
        logger.info(f"Uploaded JSON: {object_name}")
        return f"{self.endpoint}/{self.bucket}/{object_name}"

    # ── Download ──────────────────────────────────────────────────────────────

    def download_image(self, object_name: str) -> np.ndarray:
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")
        response = self.client.get_object(self.bucket, object_name)
        data = np.frombuffer(response.read(), dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)

    def download_file(self, object_name: str, local_path: str):
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")
        self.client.fget_object(self.bucket, object_name, str(local_path))
        logger.info(f"Downloaded: {object_name} → {local_path}")

    # ── URLs ──────────────────────────────────────────────────────────────────

    def presigned_url(self, object_name: str, expires_hours: int = 24) -> str:
        if not self.is_connected:
            raise RuntimeError("MinIO not connected")
        url = self.client.presigned_get_object(
            self.bucket, object_name,
            expires=timedelta(hours=expires_hours),
        )
        logger.info(f"Presigned URL ({expires_hours}h): {object_name}")
        return url

    # ── List / Delete ─────────────────────────────────────────────────────────

    def list_objects(self, prefix: str = "", recursive: bool = True):
        return self.client.list_objects(
            self.bucket, prefix=prefix, recursive=recursive
        )

    def delete_object(self, object_name: str):
        self.client.remove_object(self.bucket, object_name)
        logger.info(f"Deleted: {object_name}")

    def list_runs(self, limit: int = 50) -> list:
        if not self.is_connected:
            return []
        objects = self.client.list_objects(
            self.bucket, prefix="detections/", recursive=False
        )
        runs = []
        for obj in objects:
            if obj.is_dir:
                runs.append({
                    "run_id": obj.object_name.split("/")[1],
                    "prefix": obj.object_name,
                })
        return runs[:limit]

    def store_detection_result(
        self,
        image: np.ndarray,
        result: dict,
        signature_crops: list = None,
        run_id: str = None,
    ) -> dict:
        if run_id is None:
            ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_hash = hashlib.md5(image.tobytes()).hexdigest()[:8]
            run_id   = f"{ts}_{img_hash}"

        prefix = f"detections/{run_id}"
        stored = {}

        img_obj = f"{prefix}/image.jpg"
        self.upload_image(image, img_obj, metadata={"run_id": run_id})
        stored["image"] = img_obj

        result_obj = f"{prefix}/result.json"
        self.upload_json({"run_id": run_id, **result}, result_obj)
        stored["result"] = result_obj

        if signature_crops:
            stored["signatures"] = []
            for i, crop_path in enumerate(signature_crops):
                obj_name = f"{prefix}/signatures/sig_{i:02d}.jpg"
                self.upload_file(str(crop_path), obj_name)
                stored["signatures"].append(obj_name)

        logger.info(f"Detection run stored: {prefix}")
        return {"run_id": run_id, "objects": stored}

    # ── Health ────────────────────────────────────────────────────────────────

    def health_check(self) -> dict:
        if not self.is_connected:
            return {"status": "disconnected", "endpoint": self.endpoint}
        try:
            
            folders = ["uploads", "accepted", "enhanced", "signatures", "rejected"]
            counts  = {f: len(list(self.list_objects(prefix=f"{f}/"))) for f in folders}
            return {
                "status":      "connected",
                "endpoint":    self.endpoint,
                "bucket":      self.bucket,
                "folders":     counts,
                "total_files": sum(counts.values()),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}