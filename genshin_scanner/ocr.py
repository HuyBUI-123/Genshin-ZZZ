"""
Image → OCR text → parsed artifact data.

Uses RapidOCR (ONNX): fast on CPU, small to package. The engine returns
[box, text, score] entries which we sort top-to-bottom and join into lines
for the parser.
"""
import cv2
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

import config
from parser import parse_popup_text

# Single shared engine instance (loads ONNX models once at import).
_engine = RapidOCR()


# ---------- pipeline ----------

def load_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def preprocess(img: Image.Image) -> np.ndarray:
    """
    Return a BGR ndarray for the OCR engine. When OCR_PREPROCESS is on, upscale
    2x + unsharp (helps small/soft text); when off, pass the crop through as-is.
    """
    arr = np.array(img.convert("RGB"))
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    if not config.OCR_PREPROCESS:
        return bgr

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    up = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(up, (0, 0), 3)
    sharp = cv2.addWeighted(up, 1.5, blur, -0.5, 0)
    return cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)


def _top_y(box) -> float:
    try:
        return min(p[1] for p in box)
    except (TypeError, IndexError):
        return 0.0


def run_ocr(img: Image.Image) -> str:
    """Run RapidOCR; return recognized lines sorted top-to-bottom."""
    arr = preprocess(img)
    result, _ = _engine(arr)  # entries: [box, text, score]
    if not result:
        return ""
    result_sorted = sorted(result, key=lambda r: _top_y(r[0]))
    return "\n".join(r[1] for r in result_sorted)


def extract_from_image(img: Image.Image) -> tuple[dict, str]:
    """Return (parsed_data, raw_ocr_text)."""
    raw = run_ocr(img)
    data = parse_popup_text(raw)
    return data, raw


def capture_popup() -> Image.Image:
    """Grab the popup region directly from the screen."""
    import mss
    with mss.mss() as sct:
        shot = sct.grab(config.POPUP_REGION)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def extract_from_screen() -> tuple[dict, str]:
    """Capture popup from live game screen and extract data."""
    img = capture_popup()
    return extract_from_image(img)
