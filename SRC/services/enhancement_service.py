import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class QualityReport:
    blur_score:           float
    brightness:           float
    contrast:             float
    noise_score:          float
    resolution:           str
    overall_score:        float
    grade:                str
    enhancements_applied: List[str] = field(default_factory=list)


def assess_quality(image: np.ndarray) -> QualityReport:
    gray       = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    h, w       = gray.shape
    blur       = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast   = float(gray.std())
    noise      = float(cv2.Laplacian(gray, cv2.CV_64F).std())
    res_score  = min((h * w) / (640 * 640), 1.0) * 100

    overall = (
        min(blur / 200.0, 1.0)      * 100 * 0.35 +
        min(contrast / 60.0, 1.0)   * 100 * 0.25 +
        min(noise / 50.0, 1.0)      * 100 * 0.15 +
        (100 - abs(brightness - 128) / 128 * 100) * 0.15 +
        res_score * 0.10
    )

    if overall >= 85:   grade = "A"
    elif overall >= 70: grade = "B"
    elif overall >= 55: grade = "C"
    elif overall >= 40: grade = "D"
    else:               grade = "F"

    return QualityReport(
        blur_score=round(blur, 2),
        brightness=round(brightness, 2),
        contrast=round(contrast, 2),
        noise_score=round(noise, 2),
        resolution=f"{w}x{h}",
        overall_score=round(overall, 2),
        grade=grade,
    )


def enhance_image(
    image: np.ndarray,
    report: QualityReport
) -> Tuple[np.ndarray, List[str]]:
    enhanced = image.copy()
    applied  = []

    # Denoise
    if report.noise_score < 20:
        enhanced = cv2.fastNlMeansDenoisingColored(
            enhanced, None, 8, 8, 7, 21
        )
        applied.append("denoising")

    # Upscale
    h, w = enhanced.shape[:2]
    if h < 300 or w < 300:
        scale    = max(300 / h, 300 / w)
        enhanced = cv2.resize(
            enhanced, None, fx=scale, fy=scale,
            interpolation=cv2.INTER_CUBIC
        )
        applied.append("upscaling")

    # Brightness correction
    if report.brightness < 80 or report.brightness > 200:
        lab     = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l       = cv2.add(l, 40) if report.brightness < 80 else cv2.subtract(l, 40)
        enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
        applied.append("brightness_correction")

    # Contrast
    if report.contrast < 30:
        lab     = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe   = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l       = clahe.apply(l)
        enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
        applied.append("contrast_adjustment")

    # Sharpen
    if report.blur_score < 80:
        blur     = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
        enhanced = cv2.addWeighted(enhanced, 1.6, blur, -0.6, 0)
        applied.append("sharpening")

    return enhanced, applied