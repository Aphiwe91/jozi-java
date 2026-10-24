#!/usr/bin/env python3
"""Create responsive WebP derivatives; preserve every client original.

Requires Pillow (already installed in the development environment).
Small originals are never upscaled. The builder uses their real candidate widths
in srcset rather than assuming every original is at least 960px wide.
"""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images/jozi"
OUT = ROOT / "images/optimized"
NAMES = [
    "jozi-logo.jpeg", "jozi-story.jpeg", "jozi-03.jpeg", "jozi-04.jpeg", "jozi-05.jpeg",
    "jozi-06.jpeg", "jozi-09.jpeg", "jozi-13.jpeg", "jozi-24.jpeg",
    "jozi-bg.jpeg", "jozi-01.jpeg", "jozi-02.jpeg", "jozi-08.jpeg", "jozi-14.jpeg",
    "jozi-20.jpeg", "jozi-33.jpeg", "jozi-35.jpeg", "jozi-36.jpeg", "jozi-37.jpeg",
    "jozi-39.jpeg", "jozi-46.jpeg", "jozi-47.jpeg",
    "Casadio_Nettuno_2-Group.jpg", "Hey_Buddy_Grinder_Black.jpg",
    "Hey_Buddy_Grinder_White.jpg", "coffee-1.jpg", "Coffee-Hero.jpg", "Coffee-mid.jpg"
]

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    total_source = total_web = 0
    for name in NAMES:
        path = SOURCE / name
        total_source += path.stat().st_size
        with Image.open(path) as original:
            original = ImageOps.exif_transpose(original).convert("RGB")
            for width in ([320, 480, 960] if name == "jozi-logo.jpeg" else [480, 960]):
                target = OUT / f"{path.stem}-{width}.webp"
                if not target.exists() or target.stat().st_mtime < max(path.stat().st_mtime, Path(__file__).stat().st_mtime):
                    actual_width = min(width, original.width)
                    height = round(original.height * actual_width / original.width)
                    resized = original.resize((actual_width, height), Image.Resampling.LANCZOS)
                    resized.save(target, "WEBP", quality=82, method=6)
                if width == 960:
                    total_web += target.stat().st_size
    print(f"Preserved originals. Main derivatives: {total_source:,} → {total_web:,} bytes ({100*(1-total_web/total_source):.0f}% smaller).")
