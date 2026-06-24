"""
Detects 5-star artifact thumbnails in the strongbox "Obtained" frame.

Layout-independent: finds the gold/orange thumbnail backgrounds by color,
filters by size/shape, and returns their click positions sorted in reading
order (left-to-right, top-to-bottom).
"""
import cv2
import numpy as np
from PIL import Image

import config


def _search_offset() -> tuple[int, int]:
    """Top-left offset of the search region, for converting back to screen coords."""
    if config.OBTAINED_REGION:
        return config.OBTAINED_REGION["left"], config.OBTAINED_REGION["top"]
    return 0, 0


def _crop_to_region(arr: np.ndarray) -> np.ndarray:
    if config.OBTAINED_REGION:
        r = config.OBTAINED_REGION
        return arr[r["top"]: r["top"] + r["height"], r["left"]: r["left"] + r["width"]]
    return arr


def detect_thumbnails(img: Image.Image) -> list[dict]:
    """
    Find artifact thumbnails in the given image (full screen or screenshot).

    Returns a list of dicts in reading order:
        { "x": center_x, "y": center_y, "box": (x, y, w, h) }
    Coordinates are absolute (screen-space, accounting for OBTAINED_REGION).
    """
    arr = np.array(img.convert("RGB"))
    arr_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    region = _crop_to_region(arr_bgr)
    off_x, off_y = _search_offset()

    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        np.array(config.THUMB_HSV_LOWER),
        np.array(config.THUMB_HSV_UPPER),
    )

    # Close small gaps so each thumbnail is one solid blob
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    found = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        bbox_area = w * h
        aspect = w / h if h else 0
        if bbox_area < config.THUMB_MIN_AREA or bbox_area > config.THUMB_MAX_AREA:
            continue
        if aspect < config.THUMB_MIN_ASPECT or aspect > config.THUMB_MAX_ASPECT:
            continue
        # Reject round gold icons (Mora, etc.): a solid rectangular artifact
        # background fills its bounding box; a circle only fills ~78% of it.
        extent = cv2.contourArea(c) / bbox_area if bbox_area else 0
        if extent < config.THUMB_MIN_EXTENT:
            continue
        found.append({
            "x": off_x + x + w // 2,
            "y": off_y + y + h // 2,
            "box": (off_x + x, off_y + y, w, h),
        })

    return _sort_reading_order(found)


def _sort_reading_order(items: list[dict]) -> list[dict]:
    """Sort top-to-bottom by row, then left-to-right within each row."""
    if not items:
        return []
    tol = config.THUMB_ROW_TOLERANCE
    items = sorted(items, key=lambda i: i["y"])
    rows: list[list[dict]] = []
    for it in items:
        placed = False
        for row in rows:
            if abs(row[0]["y"] - it["y"]) <= tol:
                row.append(it)
                placed = True
                break
        if not placed:
            rows.append([it])
    ordered = []
    for row in rows:
        ordered.extend(sorted(row, key=lambda i: i["x"]))
    return ordered
