import os
import sys
import json


def _app_dir() -> str:
    """Folder to write output to: next to the .exe when frozen, else this script."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# Final export, ready to upload to the web app (written next to the app)
EXPORT_FILE = os.path.join(_app_dir(), "artifacts_export.json")

# Small settings file that persists user choices (e.g. last save path)
# across runs, including in the built .exe.
SETTINGS_FILE = os.path.join(_app_dir(), "scanner_settings.json")


def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(data: dict) -> None:
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def get_export_path() -> str:
    """Last-used save path, falling back to the default export file."""
    return load_settings().get("export_path") or EXPORT_FILE


def set_export_path(path: str) -> None:
    s = load_settings()
    s["export_path"] = path
    save_settings(s)


def get_source() -> str:
    """Last-used source, falling back to the default."""
    val = load_settings().get("source")
    return val if val in SOURCE_OPTIONS else SOURCE


def set_source(value: str) -> None:
    s = load_settings()
    s["source"] = value
    save_settings(s)

# --- OCR ---
# Whether to apply the upscale+sharpen preprocessing before OCR. Needed: it
# preserves spacing in the crisp popup text (off → "Sands of Eon" misreads).
OCR_PREPROCESS = True

# Target resolution
SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440

# Artifact detail popup region at 2560x1440.
POPUP_REGION = {
    "left": 948,
    "top": 210,
    "width": 660,
    "height": 738,
}

# --- "Obtained" frame thumbnail detection ---
# The 5-star artifact thumbnails have a gold/orange gradient background.
# We threshold for that color in HSV to find them, regardless of grid layout.

OBTAINED_REGION = {
    "left": 2,
    "top": 567,
    "width": 2552,
    "height": 324,
}

# HSV color range for the gold/orange thumbnail background (OpenCV HSV: H 0-179)
THUMB_HSV_LOWER = (8, 80, 120)
THUMB_HSV_UPPER = (28, 255, 255)

# Size filtering for detected thumbnails (in pixels, at 2560x1440)
THUMB_MIN_AREA = 4000      # reject tiny orange specks
THUMB_MAX_AREA = 40000     # reject huge orange regions
THUMB_MIN_ASPECT = 0.7     # roughly square (w/h)
THUMB_MAX_ASPECT = 1.4
THUMB_ROW_TOLERANCE = 40   # px: thumbnails within this Y range count as same row

# Fill-ratio (extent) = contour area / bounding-box area.
# A 5-star artifact's gold background is a solid rectangle (~0.9+).
THUMB_MIN_EXTENT = 0.82

# --- Click automation ---
# A safe empty spot to click to dismiss the open detail popup.
POPUP_DISMISS_POINT = (1900, 740)

MOUSE_MOVE_DURATION = 0.1   # seconds for the cursor to glide to a target
POPUP_WAIT = 0.2             # wait after clicking a thumbnail for popup to render
DISMISS_WAIT = 0.2           # wait after dismissing before the next click
START_DELAY = 3.0            # countdown after launch to switch to the game

# Scores matching the web app (constants.ts)
SCORES = [
    "Complete trash",
    "Trash",
    "Usable",
    "Good",
    "Excellent",
    "Marvelous",
    "Unknown",
]

# Source options the user picks on the start page (must match the web app).
SOURCE_OPTIONS = ["Strongbox", "Domain farming", "Stygian Onslaught"]
SOURCE = "Strongbox"  # default

# Artifact sets (constants.ts)
ARTIFACT_SETS = [
    "Archaic Petra",
    "Blizzard Strayer",
    "Bloodstained Chivalry",
    "Crimson Witch of Flames",
    "Deepwood Memories",
    "Desert Pavilion Chronicle",
    "Echoes of an Offering",
    "Emblem of Severed Fate",
    "Flower of Paradise Lost",
    "Fragment of Harmonic Whimsy",
    "Gilded Dreams",
    "Gladiator's Finale",
    "Golden Troupe",
    "Heart of Depth",
    "Husk of Opulent Dreams",
    "Lavawalker",
    "Maiden Beloved",
    "Marechaussee Hunter",
    "Nighttime of Whispers in the Echoing Woods",
    "Noblesse Oblige",
    "Nymph's Dream",
    "Obsidian Codex",
    "Ocean-Hued Clam",
    "Pale Flame",
    "Retracing Bolide",
    "Scroll of the Hero of Cinder City",
    "Shimenawa's Reminiscence",
    "Song of Days Past",
    "Tenacity of the Millelith",
    "Thundering Fury",
    "Thundersoother",
    "Unfinished Reverie",
    "Vermillion Hereafter",
    "Viridescent Venerer",
    "Vourukasha's Glow",
    "Wanderer's Troupe",
    "Long Night's Oath",
    "Finale of the Deep Galleries",
    "Silken Moon's Serenade",
    "Night of the Sky's Unveiling",
    "A Day Carved From Rising Winds",
    "Aubade of Morningstar and Moon",
    "Celestial Gift",
    "Disenchantment in Deep Shadow",
]
