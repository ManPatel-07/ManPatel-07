"""
Stage 1 of the portrait pipeline.

Takes a straight-out-of-camera photo and produces a clean, high-contrast
grayscale image on a white canvas that maps well to an ASCII character ramp.

Steps:
  1. Remove the background with rembg so only the subject remains.
  2. Composite the subject onto a solid white canvas (so empty space lands at
     the light end of the character ramp instead of the dark end).
  3. Convert to grayscale and even out lighting with CLAHE (adaptive
     histogram equalization) to pull real detail out of a flat-lit face.

Usage:
    python tools/clean_photo.py assets/source-photo.jpeg
    # writes assets/photo-ready.png
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("assets/source-photo.jpeg")
OUT = Path("assets/photo-ready.png")


def main() -> None:
    img = Image.open(SRC).convert("RGBA")

    # 1. Cut the background -> subject on transparent alpha.
    cut = remove(img)

    # 2. Composite onto a white canvas.
    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    composed = Image.alpha_composite(white, cut).convert("RGB")

    arr = np.array(composed)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Keep track of where the subject actually is (non-white pixels) so CLAHE
    # only stretches contrast across the subject, not the flat white backdrop.
    alpha = np.array(cut.split()[-1])
    subject = alpha > 20

    # 3. Adaptive contrast on the subject region.
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)

    # Blend: subject gets the equalized version, background stays clean white.
    out = np.where(subject, equalized, 255).astype(np.uint8)

    # Gentle gamma to open up midtones a touch.
    lut = np.array([((i / 255.0) ** 0.9) * 255 for i in range(256)], dtype=np.uint8)
    out = cv2.LUT(out, lut)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(OUT)
    print(f"wrote {OUT}  ({OUT.stat().st_size // 1024} KB, {out.shape[1]}x{out.shape[0]})")


if __name__ == "__main__":
    main()
