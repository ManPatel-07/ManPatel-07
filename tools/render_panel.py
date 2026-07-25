"""
Render a terminal "system info" style panel (neofetch-esque) as an SVG that
types itself out row by row, then holds with a blinking cursor.

Set PREVIEW=1 to render a still frame (all rows shown, no animation) so you can
eyeball it in a normal image viewer.

Usage:
    PREVIEW=1 python tools/render_panel.py   # still frame preview
    python tools/render_panel.py             # writes sysinfo.svg
"""

import os
from pathlib import Path

OUT = Path("sysinfo.svg")
PREVIEW = os.environ.get("PREVIEW") == "1"

USER = "man@amnex"
TITLE = "man@amnex: ~/profile"

# (label, value) rows. Label is accent-colored, value is foreground.
ROWS = [
    ("role", "Associate Software Developer"),
    ("company", "Amnex Infotechnologies"),
    ("focus", "Microservices · Spring Boot · REST"),
    ("stack", "Java · Spring · PostgreSQL · Angular"),
    ("tools", "Eureka · API Gateway · Hibernate · Git"),
    ("now", "Scalable microservices from scratch"),
    ("since", "Jun 2025  ·  100+ prod issues resolved"),
]

BG = "#0d1117"
BAR = "#161b22"
FG = "#c0caf5"
ACCENT = "#7aa2f7"
MUTED = "#565f89"
ORANGE = "#ff9e64"

FONT = 14.0
CW = FONT * 0.60          # monospace advance
LH = 26                   # line height
PAD_X = 22
BAR_H = 34
TOP = BAR_H + 24          # first content line baseline offset
LABEL_W = 9               # chars reserved for the label column

ROW_STAGGER = 0.32        # seconds between rows starting to type
TYPE_DUR = 0.5            # seconds to type one row


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    # Width from the longest rendered line.
    longest = max(len(f"{lbl:<{LABEL_W}}{val}") for lbl, val in ROWS)
    longest = max(longest, len(USER) + 2, len("$ neofetch") + 2)
    width = round(PAD_X * 2 + longest * CW) + 10
    height = TOP + (len(ROWS) + 2) * LH + 24

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="\'JetBrains Mono\',\'Fira Code\',Consolas,monospace" '
        f'font-size="{FONT}" role="img" aria-label="System info panel">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        # title bar
        f'<rect width="100%" height="{BAR_H}" rx="10" fill="{BAR}"/>',
        f'<rect y="{BAR_H-10}" width="100%" height="10" fill="{BAR}"/>',
        f'<circle cx="20" cy="{BAR_H/2}" r="6" fill="#ff5f56"/>',
        f'<circle cx="40" cy="{BAR_H/2}" r="6" fill="#ffbd2e"/>',
        f'<circle cx="60" cy="{BAR_H/2}" r="6" fill="#27c93f"/>',
        f'<text x="{width/2}" y="{BAR_H/2 + 4}" text-anchor="middle" '
        f'fill="{MUTED}" font-size="12">{esc(TITLE)}</text>',
        "<defs>",
    ]

    # Prompt line + header (user, underline) render immediately.
    lines = []  # (y, svg_text, animate?)

    y = TOP
    lines.append((y, f'<tspan fill="{ORANGE}">$</tspan> neofetch', False))
    y += LH
    lines.append((y, f'<tspan fill="{ACCENT}">{esc(USER)}</tspan>', False))
    y += LH - 6
    # underline
    p.append(
        f'<rect x="{PAD_X}" y="{y-12}" width="{len(USER)*CW:.0f}" height="2" '
        f'fill="{MUTED}"/>'
    )
    y += 12

    # Data rows type in one after another.
    row_specs = []
    for i, (lbl, val) in enumerate(ROWS):
        text = f'<tspan fill="{ACCENT}">{esc(lbl):<{LABEL_W}}</tspan>{esc(val)}'
        # padding via non-breaking spaces to preserve the label column width
        pad = "&#160;" * (LABEL_W - len(lbl))
        text = f'<tspan fill="{ACCENT}">{esc(lbl)}</tspan>{pad}{esc(val)}'
        full_chars = LABEL_W + len(val)
        row_specs.append((y, text, i, full_chars))
        y += LH

    # clip defs for typing rows
    for (ry, text, i, full_chars) in row_specs:
        cw_full = full_chars * CW
        if PREVIEW:
            p.append(
                f'<clipPath id="r{i}"><rect x="{PAD_X}" y="{ry-FONT}" '
                f'width="{cw_full:.0f}" height="{LH}"/></clipPath>'
            )
        else:
            begin = i * ROW_STAGGER
            p.append(
                f'<clipPath id="r{i}"><rect x="{PAD_X}" y="{ry-FONT}" '
                f'width="0" height="{LH}">'
                f'<animate attributeName="width" from="0" to="{cw_full:.0f}" '
                f'begin="{begin:.3f}s" dur="{TYPE_DUR}s" fill="freeze" '
                f'calcMode="linear"/></rect></clipPath>'
            )
    p.append("</defs>")

    # static lines
    for (ly, text, anim) in lines:
        p.append(
            f'<text x="{PAD_X}" y="{ly}" xml:space="preserve" fill="{FG}">{text}</text>'
        )

    # typing rows
    for (ry, text, i, full_chars) in row_specs:
        p.append(
            f'<text x="{PAD_X}" y="{ry}" xml:space="preserve" fill="{FG}" '
            f'clip-path="url(#r{i})">{text}</text>'
        )

    # blinking cursor after the last row finishes
    cursor_begin = len(ROWS) * ROW_STAGGER
    cy = row_specs[-1][0] + LH
    p.append(
        f'<rect x="{PAD_X}" y="{cy-FONT+2}" width="{CW:.0f}" height="{FONT:.0f}" '
        f'fill="{ACCENT}" opacity="{1 if PREVIEW else 0}">'
    )
    if not PREVIEW:
        p.append(
            f'<animate attributeName="opacity" values="0;0;1" '
            f'keyTimes="0;{cursor_begin/(cursor_begin+1):.3f};1" '
            f'dur="{cursor_begin+0.1}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" '
            f'begin="{cursor_begin+0.1:.2f}s" repeatCount="indefinite"/>'
        )
    p.append("</rect>")

    p.append("</svg>")
    OUT.write_text("\n".join(p), encoding="utf-8")
    print(f"wrote {OUT}  ({width}x{height}, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
