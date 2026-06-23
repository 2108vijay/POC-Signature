import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException
from SRC.core.dependencies import storage
from SRC.services.upload_service import handle_upload
from SRC.utils.file_validator import verify_file_format

router = APIRouter(tags=["Upload"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, f"Expected image, got: {file.content_type}")

    contents = await file.read()


    fmt = verify_file_format(contents, file.content_type)
    if not fmt["valid"]:
        raise HTTPException(400, fmt["reason"])

    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(422, "Could not decode image")

    return handle_upload(image, file.filename, contents, storage)