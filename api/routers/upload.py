import io
import uuid
import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException
from dependencies import storage

router = APIRouter(tags=["Upload"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, f"Expected an image, got: {file.content_type}")

    contents = await file.read()
    nparr    = np.frombuffer(contents, np.uint8)
    image    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(422, "Could not decode image")

    run_id      = str(uuid.uuid4())[:8]
    object_name = f"uploads/{run_id}_{file.filename}"
    storage.upload_image(image, object_name, metadata={"original_name": file.filename})
    presigned = storage.presigned_url(object_name, expires_hours=24)

    return {
        "run_id":       run_id,
        "object_name":  object_name,
        "size_bytes":   len(contents),
        "presigned_url": presigned,
        "expires_in":   "24h",
    }


'''@router.post("/upload/raw")
async def upload_raw(file: UploadFile = File(...)):
    contents    = await file.read()
    run_id      = str(uuid.uuid4())[:8]
    object_name = f"raw/{run_id}_{file.filename}"

    storage.client.put_object(
        storage.bucket_name,
        object_name,
        io.BytesIO(contents),
        len(contents),
        content_type=file.content_type,
    )
    presigned = storage.presigned_url(object_name, expires_hours=24)

    return {
        "run_id":        run_id,
        "object_name":   object_name,
        "content_type":  file.content_type,
        "size_bytes":    len(contents),
        "presigned_url": presigned,
    }'''