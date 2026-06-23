import uuid
import cv2
import numpy as np
from SRC.core.dependencies import classifier, detector
from SRC.services.storage_service import store_signature_crop
from SRC.storage.minio_client import MinioStorageClient


def classify_document(image: np.ndarray) -> dict:
    if classifier is None:
        return {"document_type": "unknown", "document_confidence": 0.0}

    result    = classifier.predict(image, verbose=False)
    probs     = result[0].probs
    top1_idx  = int(probs.top1)
    top1_conf = float(probs.top1conf)
    names     = result[0].names
    doc_type  = names[top1_idx] if top1_conf >= 0.5 else "others"

    return {
        "document_type":       doc_type,
        "document_confidence": round(top1_conf, 4),
    }


def detect_signatures(
    image: np.ndarray,
    storage: MinioStorageClient
) -> list:
    if detector is None:
        return []

    h, w       = image.shape[:2]
    result     = detector.predict(image, conf=0.3, verbose=False)
    detections = []
    run_id     = str(uuid.uuid4())[:8]

    for i, box in enumerate(result[0].boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        conf            = float(box.conf[0])

        pad  = 10
        cx1  = max(0, x1 - pad)
        cy1  = max(0, y1 - pad)
        cx2  = min(w, x2 + pad)
        cy2  = min(h, y2 + pad)
        crop = image[cy1:cy2, cx1:cx2]

        crop_url = store_signature_crop(storage, crop, run_id, i)

        detections.append({
            "signature_id": i + 1,
            "confidence":   round(conf, 4),
            "verified":     conf >= 0.5,
            "bounding_box": {
                "x1": x1, "y1": y1,
                "x2": x2, "y2": y2,
                "width":  x2 - x1,
                "height": y2 - y1,
            },
            "crop_url": crop_url,
        })

    return detections