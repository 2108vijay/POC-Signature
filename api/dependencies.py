from pathlib import Path
from loguru import logger

from src.storage.minio_client import MinioStorageClient

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# ── Storage ───────────────────────────────────────────────────
storage = MinioStorageClient()

# ── Models ────────────────────────────────────────────────────
MODELS_DIR      = Path(__file__).parent / "models"
classifier_path = MODELS_DIR / "document_classifier.pt"
detector_path   = MODELS_DIR / "signature_yolov8_v2.pt"

classifier = None
detector   = None

if YOLO_AVAILABLE:
    if classifier_path.exists():
        classifier = YOLO(str(classifier_path))
        logger.info(f"Classifier loaded: {classifier_path.name}")
    else:
        logger.warning(f"Classifier not found: {classifier_path}")

    if detector_path.exists():
        detector = YOLO(str(detector_path))
        logger.info(f"Detector loaded: {detector_path.name}")
    else:
        logger.warning(f"Detector not found: {detector_path}")