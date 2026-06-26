import os
from PIL import Image

import config
from ocr import extract_from_image

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_images")

FIELDS = ["set", "type", "mainStat", "numberOfSubstats", "substats", "unactivatedSubstat"]

# Each case: image filename + the correct expected parsed output.
CASES = [
    {
        "file": "Detail_popup_1.png",
        "expected": {
            "set": "Marechaussee Hunter",
            "type": "Circlet",
            "mainStat": "Healing",
            "numberOfSubstats": 3,
            "substats": ["%DEF", "DEF", "ER"],
            "unactivatedSubstat": "Crit Rate",
        },
    },
    # --- Add more below. Template:
    {
        "file": "Detail_popup_2.png",
        "expected": {
            "set": "Marechaussee Hunter",
            "type": "Sand",
            "mainStat": "%HP",
            "numberOfSubstats": 3,
            "substats": [
                "ATK",
                "Crit DMG",
                "DEF"
            ],
            "unactivatedSubstat": "HP",
        },
    },
    {
        "file": "Detail_popup_3.png",
        "expected": {
            "set": "Marechaussee Hunter",
            "type": "Circlet",
            "mainStat": "%DEF",
            "numberOfSubstats": 3,
            "substats": [
                "DEF",
                "EM",
                "ER"
            ],
            "unactivatedSubstat": "Crit DMG",
        },
    },
    {
        "file": "Detail_popup_4.png",
        "expected": {
            "set": "Celestial Gift",
            "type": "Circlet",
            "mainStat": "Healing",
            "numberOfSubstats": 3,
            "substats": [
                "Crit Rate",
                "ATK",
                "HP"
            ],
            "unactivatedSubstat": "DEF",
        },
    },
    {
        "file": "Detail_popup_5.png",
        "expected": {
            "set": "Celestial Gift",
            "type": "Flower",
            "mainStat": "HP",
            "numberOfSubstats": 3,
            "substats": [
                "ER",
                "EM",
                "%HP"
            ],
            "unactivatedSubstat": "ATK",
        },
    },
    {
        "file": "Detail_popup_6.png",
        "expected": {
            "set": "Finale of the Deep Galleries",
            "type": "Flower",
            "mainStat": "HP",
            "numberOfSubstats": 3,
            "substats": [
                "ER",
                "%HP",
                "Crit Rate"
            ],
            "unactivatedSubstat": "ATK",
        },
    },
    {
        "file": "Detail_popup_7.png",
        "expected": {
            "set": "Finale of the Deep Galleries",
            "type": "Sand",
            "mainStat": "EM",
            "numberOfSubstats": 3,
            "substats": [
                "%HP",
                "DEF",
                "ATK"
            ],
            "unactivatedSubstat": "HP",
        },
    },
    {
        "file": "Detail_popup_8.png",
        "expected": {
            "set": "Silken Moon's Serenade",
            "type": "Flower",
            "mainStat": "HP",
            "numberOfSubstats": 3,
            "substats": [
                "Crit DMG",
                "ATK",
                "%DEF"
            ],
            "unactivatedSubstat": "DEF",
        },
    },
    {
        "file": "Detail_popup_9.png",
        "expected": {
            "set": "Celestial Gift",
            "type": "Sand",
            "mainStat": "ER",
            "numberOfSubstats": 3,
            "substats": [
                "Crit Rate",
                "%ATK",
                "HP"
            ],
            "unactivatedSubstat": "Crit DMG",
        },
    },
    {
        "file": "Detail_popup_10.png",
        "expected": {
            "set": "Disenchantment in Deep Shadow",
            "type": "Sand",
            "mainStat": "%HP",
            "numberOfSubstats": 3,
            "substats": [
                "ATK",
                "EM",
                "ER"
            ],
            "unactivatedSubstat": "HP",
        },
    },
]


def _crop_popup(img: Image.Image) -> Image.Image:
    r = config.POPUP_REGION
    return img.crop(
        (r["left"], r["top"], r["left"] + r["width"], r["top"] + r["height"])
    )


def _compare(expected: dict, actual: dict) -> dict:
    results = {}
    for f in FIELDS:
        exp, act = expected.get(f), actual.get(f)
        if f == "substats":
            ok = sorted(exp or []) == sorted(act or [])
        else:
            ok = exp == act
        results[f] = (ok, exp, act)
    return results


def main():
    print(f"OCR preprocess: {config.OCR_PREPROCESS}\n")

    total = passed = failed_cases = 0

    for case in CASES:
        path = os.path.join(SAMPLE_DIR, case["file"])
        print("=" * 60)
        print(case["file"])
        print("=" * 60)

        if not os.path.exists(path):
            print(f"  MISSING FILE: {path}\n")
            failed_cases += 1
            continue

        # Samples are full 2560x1440 frames, so crop to the popup region first
        # to match what the live app (capture_popup) feeds the OCR.
        img = _crop_popup(Image.open(path).convert("RGB"))
        data, raw = extract_from_image(img)
        results = _compare(case["expected"], data)

        case_ok = True
        for f in FIELDS:
            ok, exp, act = results[f]
            total += 1
            if ok:
                passed += 1
                print(f"  [PASS] {f}: {act!r}")
            else:
                case_ok = False
                print(f"  [FAIL] {f}: expected {exp!r}, got {act!r}")

        if not case_ok:
            failed_cases += 1
            print("\n  --- RAW OCR ---")
            print("  " + raw.replace("\n", "\n  "))
        print()

    print("=" * 60)
    print(f"Fields: {passed}/{total} passed | "
          f"Cases failed: {failed_cases}/{len(CASES)}")


if __name__ == "__main__":
    main()
