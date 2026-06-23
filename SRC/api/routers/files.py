from fastapi import APIRouter, HTTPException
from SRC.core.dependencies import storage

router = APIRouter(tags=["Files"])


@router.get("/files")
def list_files(prefix: str = "", limit: int = 50):
    if not storage.is_connected:
        raise HTTPException(503, "MinIO not connected")

    objects = storage.list_objects(prefix=prefix)
    files   = []
    for obj in objects:
        files.append({
            "name":          obj.object_name,
            "size_bytes":    obj.size,
            "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
        })
        if len(files) >= limit:
            break

    return {"total": len(files), "files": files}


@router.get("/files/{object_name:path}")
def get_file_url(object_name: str, expires_hours: int = 24):
    if not storage.is_connected:
        raise HTTPException(503, "MinIO not connected")
    try:
        url = storage.presigned_url(object_name, expires_hours)
        return {
            "object_name":   object_name,
            "presigned_url": url,
            "expires_in":    f"{expires_hours}h",
        }
    except Exception as e:
        raise HTTPException(404, f"Not found: {e}")


@router.delete("/files/{object_name:path}")
def delete_file(object_name: str):
    if not storage.is_connected:
        raise HTTPException(503, "MinIO not connected")
    try:
        storage.delete_object(object_name)
        return {"deleted": object_name}
    except Exception as e:
        raise HTTPException(404, f"Could not delete: {e}")