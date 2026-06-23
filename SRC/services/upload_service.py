import uuid
import cv2
import numpy as np
from SRC.storage.minio_client import MinioStorageClient
from SRC.utils.logger import logger


def handle_upload(
    image: np.ndarray,
    filename: str,
    contents: bytes,
    storage: MinioStorageClient
) -> dict:
    run_id      = str(uuid.uuid4())[:8]
    object_name = f"uploads/{run_id}_{filename}"

    storage.upload_image(image, object_name, metadata={"original_name": filename})
    presigned = storage.presigned_url(object_name, expires_hours=24)

    logger.info(f"Upload handled: {object_name}")

    return {
        "run_id":        run_id,
        "object_name":   object_name,
        "size_bytes":    len(contents),
        "presigned_url": presigned,
        "expires_in":    "24h",
    }