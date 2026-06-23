import cv2
import numpy as np


def validate_image(image: np.ndarray, file_size_bytes: int) -> dict:
    h, w = image.shape[:2]

    # Check 1 — resolution
    if h < 100 or w < 100:
        return {
            "passed": False,
            "reason": f"Image too small ({w}x{h}). Minimum 100x100 required."
        }

    # Check 2 — file size
    if file_size_bytes < 5000:
        return {
            "passed": False,
            "reason": f"File too small ({file_size_bytes} bytes). Likely corrupt."
        }

    # Compute metrics
    gray       = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur       = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = float(gray.mean())

    # Check 3 — blank image
    if brightness > 252:
        return {
            "passed": False,
            "reason": f"Image appears blank (brightness: {brightness:.1f})."
        }

    # Check 4 — too dark
    if brightness < 10:
        return {
            "passed": False,
            "reason": f"Image too dark (brightness: {brightness:.1f})."
        }

    # Check 5 — blur
    if blur < 0.4:
        return {
            "passed": False,
            "reason": f"Image too blurry (blur score: {blur:.1f}). Minimum 0.4 required."
        }

    return {"passed": True, "reason": "Image quality acceptable"}