import io
import os
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.storage.minio_client import MinioStorageClient

load_dotenv()

app = FastAPI(
    title="Signature Verification API",
    description="Upload documents, store in MinIO, retrieve via presigned URL",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = MinioStorageClient()


@app.get("/health")
def health():
    minio = storage.health_check()
    return {
        "status": "ok",
        "minio": minio,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/storage/health")
def storage_health():
    return storage.health_check()


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, f"Expected an image, got: {file.content_type}")

    contents = await file.read()
    run_id = str(uuid.uuid4())[:8]
    object_name = f"uploads/{run_id}_{file.filename}"

    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(422, "Could not decode image")

    storage.upload_image(image, object_name, metadata={"original_name": file.filename})
    presigned = storage.presigned_url(object_name, expires_hours=24)

    return {
        "run_id": run_id,
        "object_name": object_name,
        "size_bytes": len(contents),
        "presigned_url": presigned,
        "expires_in": "24h",
    }


@app.post("/upload/raw")
async def upload_raw(file: UploadFile = File(...)):
    contents = await file.read()
    run_id = str(uuid.uuid4())[:8]
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
        "run_id": run_id,
        "object_name": object_name,
        "content_type": file.content_type,
        "size_bytes": len(contents),
        "presigned_url": presigned,
    }


@app.get("/files")
def list_files(prefix: str = "", limit: int = 50):
    if not storage.is_connected:
        raise HTTPException(503, "MinIO not connected")

    objects = storage.client.list_objects(
        storage.bucket_name, prefix=prefix, recursive=True
    )
    files = []
    for obj in objects:
        files.append({
            "name": obj.object_name,
            "size_bytes": obj.size,
            "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
        })
        if len(files) >= limit:
            break

    return {"total": len(files), "files": files}


@app.get("/files/{object_name:path}")
def get_file_url(object_name: str, expires_hours: int = 24):
    if not storage.is_connected:
        raise HTTPException(503, "MinIO not connected")
    try:
        url = storage.presigned_url(object_name, expires_hours=expires_hours)
        return {
            "object_name": object_name,
            "presigned_url": url,
            "expires_in": f"{expires_hours}h",
        }
    except Exception as e:
        raise HTTPException(404, f"Object not found: {e}")


@app.delete("/files/{object_name:path}")
def delete_file(object_name: str):
    if not storage.is_connected:
        raise HTTPException(503, "MinIO not connected")
    try:
        storage.client.remove_object(storage.bucket_name, object_name)
        return {"deleted": object_name}
    except Exception as e:
        raise HTTPException(404, f"Could not delete: {e}")


@app.get("/runs")
def list_runs():
    if not storage.is_connected:
        return []
    return storage.list_runs()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
        log_level="info",
    )