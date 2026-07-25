"""
Stage 2 of the portrait pipeline.

Takes the cleaned grayscale image (assets/photo-ready.png) and renders it as a
self-drawing monochrome ASCII portrait in a single SVG file.

The motion: each row of characters lives behind its own clip rectangle whose
width animates from 0 to full. The rows are staggered so the portrait appears
to draw itself top-to-bottom, then holds on the final frame (no infinite loop).

Usage:
    python tools/render_portrait.py
    # writes portrait.svg
"""

from pathlib import Path

import numpy as np
from PIL import Image

SRC = Path("assets/photo-ready.png")
OUT = Path("portrait.svg")

# left = light / empty, right = dense / dark. Reads softer than the @%# style.
GLYPHS = " '.,:;~+*xXO#"

COLS = 82           # character columns across
FONT = 13.0         # px
CW = FONT * 0.60    # monospace advance width per char
CH = FONT * 1.16    # line height
PAD = 22            # px padding around the art

ACCENT = "#7aa2f7"  # single fill color (Tokyo Night blue)
BG = "#0d1117"

ROW_STAGGER = 0.045  # seconds between each row starting to draw
ROW_DRAW = 0.55      # seconds for one row to sweep in


def crop_to_subject(gray: np.ndarray, pad: int = 8) -> np.ndarray:
    """Trim the flat white margins so the subject fills the frame."""
    mask = gray < 245
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return gray
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, gray.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, gray.shape[1])
    return gray[y0:y1, x0:x1]


def main() -> None:
    gray = np.array(Image.open(SRC).convert("L"))
    gray = crop_to_subject(gray)

    h, w = gray.shape
    rows = max(1, round(COLS * (h / w) * (CW / CH)))

    small = np.array(
        Image.fromarray(gray).resize((COLS, rows), Image.Resampling.LANCZOS),
        dtype=np.float32,
    )

    # brightness -> glyph. White (255) -> space; black (0) -> densest glyph.
    idx = ((255.0 - small) / 255.0 * (len(GLYPHS) - 1)).round().astype(int)
    idx = np.clip(idx, 0, len(GLYPHS) - 1)

    art_w = COLS * CW
    art_h = rows * CH
    width = art_w + PAD * 2
    height = art_h + PAD * 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="\'JetBrains Mono\',\'Fira Code\',Consolas,monospace" '
        f'font-size="{FONT}" role="img" aria-label="ASCII portrait of Man Patel">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        "<defs>",
    ]

    # One clip rect per row, each animating its width 0 -> full.
    for r in range(rows):
        begin = r * ROW_STAGGER
        parts.append(
            f'<clipPath id="c{r}">'
            f'<rect x="{PAD:.1f}" y="{PAD + r * CH:.2f}" '
            f'width="0" height="{CH:.2f}">'
            f'<animate attributeName="width" from="0" to="{art_w:.1f}" '
            f'begin="{begin:.3f}s" dur="{ROW_DRAW}s" '
            f'fill="freeze" calcMode="spline" keyTimes="0;1" '
            f'keySplines="0.4 0 0.2 1"/>'
            f"</rect></clipPath>"
        )
    parts.append("</defs>")

    # One text element per row, revealed by its clip.
    for r in range(rows):
        chars = "".join(GLYPHS[i] for i in idx[r])
        chars = chars.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        y = PAD + r * CH + FONT * 0.85
        parts.append(
            f'<text x="{PAD:.1f}" y="{y:.2f}" xml:space="preserve" '
            f'clip-path="url(#c{r})" fill="{ACCENT}" '
            f'letter-spacing="0">{chars}</text>'
        )

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT}  ({OUT.stat().st_size // 1024} KB, {COLS}x{rows} chars)")


if __name__ == "__main__":
    main()
