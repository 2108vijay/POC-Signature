from datetime import datetime
from fastapi import APIRouter
from dependencies import storage

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "minio": storage.health_check(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/storage/health")
def storage_health():
    return storage.health_check()