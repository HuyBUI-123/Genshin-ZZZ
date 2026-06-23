"""
CLI test tool for the OCR pipeline.

Usage:
  # Image is already cropped to just the popup:
  python test_ocr.py sample_images/popup.png

  # Full game screenshot — auto-crop using POPUP_REGION from config.py:
  python test_ocr.py sample_images/full_screenshot.png --crop

  # Save the cropped region so you can visually verify alignment:
  python test_ocr.py sample_images/full_screenshot.png --crop --save-crop
"""
import sys
import json
from PIL import Image

from config import POPUP_REGION
from ocr import run_ocr, extract_from_image


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    image_path = args[0]
    do_crop = "--crop" in args
    save_crop = "--save-crop" in args

    img = Image.open(image_path).convert("RGB")

    if do_crop:
        r = POPUP_REGION
        box = (r["left"], r["top"], r["left"] + r["width"], r["top"] + r["height"])
        img = img.crop(box)
        print(f"Cropped to {box}  ({img.width}x{img.height}px)")
        if save_crop:
            out = "debug_crop.png"
            img.save(out)
            print(f"Saved crop → {out}  (open this to verify alignment)")

    print("\n" + "=" * 50)
    print("RAW OCR OUTPUT")
    print("=" * 50)
    raw = run_ocr(img)
    print(raw)

    print("\n" + "=" * 50)
    print("PARSED RESULT")
    print("=" * 50)
    data, _ = extract_from_image(img)

    # Print clean view (no debug fields)
    clean = {k: v for k, v in data.items() if not k.startswith("_")}
    print(json.dumps(clean, indent=2))

    print("\n" + "=" * 50)
    print("CONFIDENCE")
    print("=" * 50)
    all_ok = True
    for field, ok in data["_ok"].items():
        status = "OK " if ok else "FAIL"
        print(f"  [{status}] {field}")
        if not ok:
            all_ok = False

    if not all_ok:
        print("\nSome fields failed. Check RAW OCR OUTPUT above.")
        print("If alignment looks wrong, adjust POPUP_REGION in config.py and re-run with --crop --save-crop.")

    print()


if __name__ == "__main__":
    main()
