import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from SRC.auth.oauth2 import verify_user
from SRC.core.dependencies import storage
from SRC.services.validation_service import validate_image
from SRC.services.enhancement_service import assess_quality, enhance_image
from SRC.services.detection_service import classify_document, detect_signatures
from SRC.utils.file_validator import verify_file_format
from SRC.services.storage_service import store_accepted, store_enhanced, store_rejected


from SRC.training.pdf_utils import pdf_to_image 

router = APIRouter(tags=["Detection"])


@router.post("/detect")
async def detect(
    file: UploadFile = File(...),
    username: str = Depends(verify_user),
):
    contents = await file.read()


    fmt = verify_file_format(contents, file.content_type)
    if not fmt["valid"]:
        return JSONResponse(status_code=400, content={
            "error":  "Invalid file format",
            "reason": fmt["reason"],
        })

  
    if fmt["actual"] == "pdf":
        try:
            image = pdf_to_image(contents)
        except Exception as e:
            raise HTTPException(422, f"Could not process PDF: {str(e)}")
    else:
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(422, "Could not decode image")

    # Validation
    validation = validate_image(image, len(contents))
    if not validation["passed"]:
        rejected_path = store_rejected(
            storage, image, file.filename, validation["reason"]
        )
        return JSONResponse(content={
            "document":   file.filename,
            "validation": {
                "passed": False,
                "reason": validation["reason"],
            },
            "stored": {"rejected": rejected_path},
        })


    before = assess_quality(image)


    needs_enhancement = before.overall_score < 65
    enhanced_image    = image
    enhancements      = []

    if needs_enhancement:
        enhanced_image, enhancements = enhance_image(image, before)


    after = assess_quality(enhanced_image)

    doc_info = classify_document(enhanced_image)

   
    detections = detect_signatures(enhanced_image, storage)


    orig_path     = store_accepted(storage, image, file.filename)
    enhanced_path = store_enhanced(storage, enhanced_image, file.filename) \
                    if needs_enhancement else None

    return JSONResponse(content={
        "document":     file.filename,
        "requested_by": username,
        "validation": {
            "passed": True,
            "reason": "Image quality acceptable",
        },
        "quality": {
            "before": {
                "blur_score":    before.blur_score,
                "brightness":    before.brightness,
                "contrast":      before.contrast,
                "overall_score": before.overall_score,
                "grade":         before.grade,
            },
            "after": {
                "blur_score":    after.blur_score,
                "brightness":    after.brightness,
                "contrast":      after.contrast,
                "overall_score": after.overall_score,
                "grade":         after.grade,
            },
            "enhanced":             needs_enhancement,
            "enhancements_applied": enhancements,
        },
        "document_type":       doc_info["document_type"],
        "document_confidence": doc_info["document_confidence"],
        "signature_found":     len(detections) > 0,
        "signature_verified":  any(d["verified"] for d in detections),
        "total_signatures":    len(detections),
        "detections":          detections,
        "stored": {
            "accepted":   orig_path, 
            "enhanced":   enhanced_path,
            "signatures": [d["crop_url"] for d in detections],
        },
    })