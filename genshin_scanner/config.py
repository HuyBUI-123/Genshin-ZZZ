# Target resolution
SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440

# Artifact detail popup region at 2560x1440.
# These are approximate — run calibrate.py to fine-tune if OCR crops wrong.
POPUP_REGION = {
    "left": 948,
    "top": 210,
    "width": 660,
    "height": 651,
}

# --- "Obtained" frame thumbnail detection ---
# The 5-star artifact thumbnails have a gold/orange gradient background.
# We threshold for that color in HSV to find them, regardless of grid layout.
#
# Optional region to limit the search to the area where thumbnails appear
# (avoids picking up other orange UI). Set to None to search the full screen.
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
# Mora and other round gold icons are circles (~0.78), so we reject them.
THUMB_MIN_EXTENT = 0.82

# --- Click automation ---
# A safe empty spot to click to dismiss the open detail popup. Must NOT
# overlap POPUP_REGION, any thumbnail, or a button. Default: dark area far-left.
POPUP_DISMISS_POINT = (1900, 740)

MOUSE_MOVE_DURATION = 0.15   # seconds for the cursor to glide to a target
POPUP_WAIT = 0.5             # wait after clicking a thumbnail for popup to render
DISMISS_WAIT = 0.3           # wait after dismissing before the next click
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

# Always Strongbox when using this tool
SOURCE = "Strongbox"

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
