"""
Click automation: drives the mouse through the detected thumbnails,
OCRs each detail popup, and returns the parsed artifacts.

Flow per artifact (popup overlaps center thumbnails, so we must dismiss
between each one before the next click lands on a thumbnail):
    click thumbnail -> wait -> capture+OCR popup -> dismiss popup -> next
"""
import time
import threading
import mss
import pyautogui
import keyboard
from PIL import Image

import config
from detector import detect_thumbnails
from ocr import extract_from_image, capture_popup

# Abort via a global key instead
pyautogui.FAILSAFE = False

# Set when the user presses the abort key during a scan.
_abort_event = threading.Event()


def _arm_abort() -> None:
    _abort_event.clear()
    try:
        keyboard.add_hotkey(config.ABORT_KEY, _abort_event.set)
    except Exception as e:  # noqa: BLE001 — keep scanning even if the bind fails
        print(f"[scan] could not bind abort key '{config.ABORT_KEY}': {e}", flush=True)


def _disarm_abort() -> None:
    try:
        keyboard.remove_hotkey(config.ABORT_KEY)
    except (KeyError, ValueError):
        pass


def _primary_monitor(sct) -> dict:
    """
    The Windows primary monitor — its top-left is always at virtual (0,0).
    We find it by coordinates rather than by mss's monitor INDEX, because the
    index order changes when display ports/cables are swapped. POPUP_REGION and
    pyautogui clicks are all calibrated relative to this (0,0) origin.
    """
    for mon in sct.monitors[1:]:
        if mon["left"] == 0 and mon["top"] == 0:
            return mon
    # Fallback: first real monitor, or the virtual bounding box.
    return sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]


def capture_full_screen() -> Image.Image:
    """Grab the entire primary monitor (the one at virtual origin)."""
    with mss.mss() as sct:
        mon = _primary_monitor(sct)
        shot = sct.grab(mon)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def _dismiss_popup() -> None:
    x, y = config.POPUP_DISMISS_POINT
    pyautogui.moveTo(x, y, duration=config.MOUSE_MOVE_DURATION)
    pyautogui.click()
    time.sleep(config.DISMISS_WAIT)


def scan_all(progress_cb=None) -> list[dict]:
    """
    Detect every 5-star thumbnail, click through each, OCR its popup.

    progress_cb(done, total, data) is called after each artifact, if given.
    Returns a list of parsed-artifact dicts (with debug fields).
    """
    # Trace what the scan is doing
    print("\n[scan] capturing screen...", flush=True)
    screen = capture_full_screen()
    print("[scan] detecting thumbnails...", flush=True)
    thumbs = detect_thumbnails(screen)

    results: list[dict] = []
    total = len(thumbs)

    # Always report the count so a 0-detection scan isn't a silent no-op.
    print(f"[scan] detected {total} thumbnail(s) in the Obtained frame.", flush=True)
    if total == 0:
        print("Nothing to scan")

    _arm_abort()
    print(f"[scan] press '{config.ABORT_KEY}' to abort.", flush=True)
    try:
        for i, t in enumerate(thumbs):
            if _abort_event.is_set():
                print(f"[scan] aborted by user after {len(results)} artifact(s).",
                      flush=True)
                break

            # Click the thumbnail
            pyautogui.moveTo(t["x"], t["y"], duration=config.MOUSE_MOVE_DURATION)
            pyautogui.click()
            time.sleep(config.POPUP_WAIT)

            # Read the popup
            popup_img = capture_popup()
            data, raw = extract_from_image(popup_img)
            data["_index"] = i
            data["_click"] = (t["x"], t["y"])
            data["_image"] = popup_img  # kept in memory for the rating UI; not exported
            results.append(data)

            # Echo to the console window (visible in the --console build) so you
            # can see exactly what the OCR read and how it parsed.
            print(f"\n===== Artifact {i + 1}/{total} =====")
            print("--- RAW OCR ---")
            print(raw)
            print("--- PARSED ---")
            print(
                f"  set={data.get('set')} | type={data.get('type')} | "
                f"main={data.get('mainStat')} | subs={data.get('substats')} | "
                f"unact={data.get('unactivatedSubstat')}"
            )

            if progress_cb:
                progress_cb(i + 1, total, data)

            # Dismiss so the next thumbnail isn't hidden behind the popup
            _dismiss_popup()
    finally:
        _disarm_abort()

    return results


def scan_single_at(x: int, y: int) -> tuple[dict, str]:
    """Click one given point, OCR its popup, dismiss. For debugging timing."""
    pyautogui.moveTo(x, y, duration=config.MOUSE_MOVE_DURATION)
    pyautogui.click()
    time.sleep(config.POPUP_WAIT)
    popup_img = capture_popup()
    data, raw = extract_from_image(popup_img)
    _dismiss_popup()
    return data, raw
