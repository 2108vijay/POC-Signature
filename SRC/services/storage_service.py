import uuid
from SRC.storage.minio_client import MinioStorageClient

# Rename store_original to store_accepted and change the path
def store_accepted(storage: MinioStorageClient, image, filename: str) -> str:
    run_id      = str(uuid.uuid4())[:8]
    object_name = f"accepted/{run_id}_{filename}"
    storage.upload_image(image, object_name)
    return object_name


def store_enhanced(storage: MinioStorageClient, image, filename: str) -> str:
    run_id      = str(uuid.uuid4())[:8]
    object_name = f"enhanced/{run_id}_{filename}"
    storage.upload_image(image, object_name)
    return object_name


def store_rejected(
    storage: MinioStorageClient,
    image,
    filename: str,
    reason: str
) -> str:
    run_id      = str(uuid.uuid4())[:8]
    object_name = f"rejected/{run_id}_{filename}"
    storage.upload_image(image, object_name, metadata={"reason": reason})
    return object_name


def store_signature_crop(
    storage: MinioStorageClient,
    crop,
    run_id: str,
    index: int
) -> str:
    object_name = f"signatures/{run_id}_sig_{index}.jpg"
    storage.upload_image(crop, object_name)
    return storage.presigned_url(object_name, expires_hours=24)