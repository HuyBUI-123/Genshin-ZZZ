"""
Draws the POPUP_REGION box on a screenshot so you can verify alignment.

Usage:
  python visualize_region.py sample_images/your_screenshot.png
  python visualize_region.py sample_images/your_screenshot.png --out check.png
"""
import sys
from PIL import Image, ImageDraw, ImageFont
from config import POPUP_REGION


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python visualize_region.py <screenshot.png> [--out output.png]")
        sys.exit(1)

    image_path = args[0]
    out_path = "region_check.png"
    if "--out" in args:
        out_path = args[args.index("--out") + 1]

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    r = POPUP_REGION
    x0, y0 = r["left"], r["top"]
    x1, y1 = x0 + r["width"], y0 + r["height"]

    # Draw box
    draw.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=3)

    # Label with coordinates
    label = f"({x0},{y0})  {r['width']}x{r['height']}px"
    draw.rectangle([x0, y0 - 22, x0 + len(label) * 8, y0], fill=(255, 0, 0))
    draw.text((x0 + 2, y0 - 20), label, fill=(255, 255, 255))

    img.save(out_path)
    print(f"Saved → {out_path}")
    print(f"Box: left={x0}, top={y0}, right={x1}, bottom={y1}")
    print(f"If misaligned, edit POPUP_REGION in config.py and re-run.")


if __name__ == "__main__":
    main()
