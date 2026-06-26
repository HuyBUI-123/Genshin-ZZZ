"""
Converts raw OCR text from the artifact detail popup into structured data
matching the web app's schema.
"""
import re
from rapidfuzz import process, fuzz
from config import ARTIFACT_SETS

# --- Lookup tables ---

PIECE_TYPES = {
    "Flower of Life": "Flower",
    "Plume of Death": "Plume",
    "Sands of Eon": "Sand",
    "Goblet of Eonothem": "Goblet",
    "Circlet of Logos": "Circlet",
}

# What OCR reads → what the web app stores for main stat
MAIN_STAT_OCR = {
    "HP": "HP",
    "ATK": "ATK",
    "DEF": "DEF",
    "Elemental Mastery": "EM",
    "Energy Recharge": "ER",
    "CRIT Rate": "Crit Rate",
    "CRIT DMG": "Crit DMG",
    "Healing Bonus": "Healing",
    "Physical DMG Bonus": "Physical",
    "Pyro DMG Bonus": "Pyro",
    "Hydro DMG Bonus": "Hydro",
    "Cryo DMG Bonus": "Cryo",
    "Electro DMG Bonus": "Electro",
    "Anemo DMG Bonus": "Anemo",
    "Geo DMG Bonus": "Geo",
    "Dendro DMG Bonus": "Dendro",
}

# What OCR reads → what the web app stores for substats
SUBSTAT_OCR = {
    "HP": "HP",
    "ATK": "ATK",
    "DEF": "DEF",
    "Elemental Mastery": "EM",
    "Energy Recharge": "ER",
    "CRIT Rate": "Crit Rate",
    "CRIT DMG": "Crit DMG",
}

# Lines containing these strings are noise — skip them
NOISE_PATTERNS = [
    r"^\+\d+$",           # upgrade level like +0, +4, +20
    r"^[\*★\s]+$",        # star rating garbage
    r"^\d+-Piece",        # set bonus descriptions
    r"^When current",
    r"^Normal and",
    r"^An old",
    r"^A mask",
    r"^Its design",
]


def _is_noise(line: str) -> bool:
    for pat in NOISE_PATTERNS:
        if re.search(pat, line, re.IGNORECASE):
            return True
    return False


def _normalize(text: str) -> str:
    """Strip OCR artifacts: fullwidth chars, stray bullets, extra whitespace."""
    # Fullwidth parentheses and spaces → ASCII
    text = text.replace("（", "(").replace("）", ")").replace("　", " ")
    # Remove non-printable except newline
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _find_piece_type(lines: list[str]) -> tuple[str | None, int]:
    for i, line in enumerate(lines):
        for key, val in PIECE_TYPES.items():
            if fuzz.partial_ratio(key.lower(), line.lower()) >= 85:
                return val, i
    return None, -1


def _find_set_name(lines: list[str]) -> tuple[str | None, int]:
    for i, line in enumerate(lines):
        # Set name line ends with ":" in the popup
        candidate = line.strip().rstrip(":")
        match, score, _ = process.extractOne(
            candidate, ARTIFACT_SETS, scorer=fuzz.token_sort_ratio
        )
        if score >= 75:
            return match, i
    return None, -1


def _parse_main_stat(lines: list[str], after_idx: int) -> str | None:
    """
    Main stat name appears on one line, its value (e.g. "7.0%") on the next.
    Search the few lines right after the piece-type line.
    """
    search = lines[after_idx + 1: after_idx + 6]
    for i, line in enumerate(search):
        line = line.strip()
        # Value line: a bare number with optional %
        if re.match(r"^\d+\.?\d*%?$", line) and i > 0:
            stat_name = search[i - 1].strip()
            is_pct = "%" in line
            return _map_main_stat(stat_name, is_pct)
    return None


def _map_main_stat(raw: str, is_pct: bool) -> str | None:
    match, score, _ = process.extractOne(
        raw, list(MAIN_STAT_OCR.keys()), scorer=fuzz.token_sort_ratio
    )
    if score < 70:
        return None
    value = MAIN_STAT_OCR[match]
    # HP / ATK / DEF can be flat (Flower/Plume) or % (Sand/Goblet/Circlet)
    if value in ("HP", "ATK", "DEF") and is_pct:
        return f"%{value}"
    return value


def _parse_substat_line(line: str) -> tuple[str, bool] | None:
    """
    Parse one substat line like:
      · CRIT Rate+3.1%
      · HP+239　（unactivated）
    Returns (stat_web_app_value, is_unactivated) or None.
    """
    is_unactivated = "unactivated" in line.lower()

    # Strip bullet, spaces, and the (unactivated) tag
    cleaned = re.sub(r"^[·•.\-\*]\s*", "", line.strip())
    cleaned = re.sub(r"\s*[\(\[]\s*unactivated\s*[\)\]].*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    # Split STAT_NAME+VALUE on the first '+'. We deliberately DON'T parse the
    # numeric value strictly — OCR often misreads it (e.g. "7.O%" for 7.0%),
    # and the web app only needs the stat name + whether it's a percentage.
    if "+" not in cleaned:
        return None
    stat_raw, _, value_part = cleaned.partition("+")
    stat_raw = stat_raw.strip()

    # Sanity gate: a real substat value contains a digit. This rejects set-bonus
    # / description lines that happen to contain a '+'.
    if not re.search(r"\d", value_part):
        return None

    is_pct = "%" in value_part
    stat = _map_substat(stat_raw, is_pct)
    if stat is None:
        return None
    return stat, is_unactivated


def _map_substat(raw: str, is_pct: bool) -> str | None:
    match, score, _ = process.extractOne(
        raw, list(SUBSTAT_OCR.keys()), scorer=fuzz.token_sort_ratio
    )
    if score < 70:
        return None
    value = SUBSTAT_OCR[match]
    if value in ("HP", "ATK", "DEF") and is_pct:
        return f"%{value}"
    return value


def _parse_substats(
    lines: list[str], after_idx: int, stop_idx: int
) -> tuple[list[str], str | None]:
    """Extract substats from lines between piece-type and set-name."""
    substats: list[str] = []
    has_unactivated = False

    start = after_idx + 3
    end = stop_idx if stop_idx > 0 else len(lines)

    for line in lines[start:end]:
        stripped = line.strip()
        if not stripped or _is_noise(stripped):
            continue

        # Try to read the line as a substat first (handles the inline).
        result = _parse_substat_line(stripped)
        if result:
            stat, is_un = result
            if is_un:
                has_unactivated = True
            substats.append(stat)
        elif "unactivated" in stripped.lower():
            # just need to know an unactivated one exists.
            has_unactivated = True

    # In Genshin the unactivated substat is always last — pop it regardless of
    # where the "(unactivated)" marker appeared in the OCR output
    unactivated = substats.pop() if has_unactivated and substats else None

    return substats, unactivated


# --- Public API ---

def parse_popup_text(raw_text: str) -> dict:
    """
    Convert raw OCR text from the artifact detail popup into a dict ready
    for the web app's create/import endpoint.

    Returned keys:
      set, type, mainStat, numberOfSubstats, substats,
      unactivatedSubstat, source, _raw (debug), _ok (confidence flags)
    """
    text = _normalize(raw_text)
    lines = [l for l in text.split("\n") if l.strip() and not _is_noise(l)]

    piece_type, piece_idx = _find_piece_type(lines)
    set_name, set_idx = _find_set_name(lines)
    main_stat = _parse_main_stat(lines, piece_idx) if piece_idx >= 0 else None
    substats, unactivated = _parse_substats(lines, piece_idx, set_idx)

    return {
        "set": set_name,
        "type": piece_type,
        "mainStat": main_stat,
        "numberOfSubstats": len(substats),
        "substats": substats,
        "unactivatedSubstat": unactivated,
        "source": "Strongbox",
        # Debug fields
        "_raw": raw_text,
        "_lines": lines,
        "_ok": {
            "set": set_name is not None,
            "type": piece_type is not None,
            "mainStat": main_stat is not None,
            "substats": len(substats) > 0,
        },
    }
