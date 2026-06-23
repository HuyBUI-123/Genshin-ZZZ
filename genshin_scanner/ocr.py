"""
Image → OCR text → parsed artifact data.
Uses rapidocr-onnxruntime (pure pip install, no system binaries needed).
"""
import cv2
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

from config import POPUP_REGION
from parser import parse_popup_text

# Single shared engine instance (loads ONNX models once)
_engine = RapidOCR()


def load_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def preprocess(img: Image.Image) -> np.ndarray:
    """
    Upscale 2x + mild sharpening before OCR.
    The popup has cream background / dark text so contrast is already good.
    """
    arr = np.array(img)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    up = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(up, (0, 0), 3)
    sharp = cv2.addWeighted(up, 1.5, blur, -0.5, 0)
    # RapidOCR accepts BGR numpy array
    return cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)


def run_ocr(img: Image.Image) -> str:
    """
    Run RapidOCR on the image.
    Returns lines sorted top-to-bottom, joined by newlines.
    """
    arr = preprocess(img)
    result, _ = _engine(arr)
    if not result:
        return ""

    # result is a list of [box, text, confidence]
    # Sort entries by the top-left y coordinate so we read top-to-bottom
    result_sorted = sorted(result, key=lambda r: r[0][0][1])
    lines = [entry[1] for entry in result_sorted]
    return "\n".join(lines)


def extract_from_image(img: Image.Image) -> tuple[dict, str]:
    """Return (parsed_data, raw_ocr_text)."""
    raw = run_ocr(img)
    data = parse_popup_text(raw)
    return data, raw


def capture_popup() -> Image.Image:
    """Grab the popup region directly from the screen."""
    import mss
    with mss.mss() as sct:
        shot = sct.grab(POPUP_REGION)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def extract_from_screen() -> tuple[dict, str]:
    """Capture popup from live game screen and extract data."""
    img = capture_popup()
    return extract_from_image(img)
