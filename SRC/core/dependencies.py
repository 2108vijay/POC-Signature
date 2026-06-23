from pathlib import Path
from SRC.core.config import config
from SRC.storage.minio_client import MinioStorageClient
from SRC.utils.logger import logger

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("ultralytics not installed")


storage = MinioStorageClient()


classifier = None
detector   = None

if YOLO_AVAILABLE:

    BASE_DIR = Path(__file__).resolve().parents[1]
    clf_path = BASE_DIR / config.CLASSIFIER_PATH
    det_path = BASE_DIR / config.DETECTOR_PATH
    #clf_path = Path(config.CLASSIFIER_PATH)
    #det_path = Path(config.DETECTOR_PATH)

    if clf_path.exists():
        classifier = YOLO(str(clf_path))
        logger.info(f"Classifier loaded: {clf_path.name}")
    else:
        logger.warning(f"Classifier not found: {clf_path}")

    if det_path.exists():
        detector = YOLO(str(det_path))
        logger.info(f"Detector loaded: {det_path.name}")
    else:
        logger.warning(f"Detector not found: {det_path}")