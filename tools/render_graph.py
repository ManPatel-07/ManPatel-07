"""
Render the contribution calendar (assets/contributions.json) as an animated SVG.

The grid is redrawn as rounded squares using a custom color ramp (not GitHub's
greens) so it matches the portrait's accent. Squares reveal column by column
(week by week) like a wave, then freeze once fully drawn. A small legend and a
one-line stats summary sit underneath.

Usage:
    python tools/render_graph.py
    # writes graph.svg
"""

import json
from datetime import date
from pathlib import Path

SRC = Path("assets/contributions.json")
OUT = Path("graph.svg")

# index 0 = no activity ... index 4 = top tier. Matches the blue portrait accent.
LEVELS = ["#161b22", "#0e3a5e", "#1c5d8f", "#2f81c4", "#7cb7f0"]

CELL = 12          # square size
GAP = 3            # gap between squares
RADIUS = 2.5       # corner radius
PAD_X = 20
PAD_TOP = 34       # room for month labels
PAD_BOTTOM = 58    # room for legend + stats
LABEL_COL = 30     # room for weekday labels on the left

BG = "#0d1117"
FG = "#c0caf5"
MUTED = "#565f89"
ACCENT = "#7aa2f7"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

COL_STAGGER = 0.018   # seconds between each week column appearing
CELL_POP = 0.45       # seconds for one cell to fade+scale in


def build_columns(days):
    """Arrange the flat day list into week columns (Sunday-first)."""
    cols = []
    col = [None] * 7
    for d in days:
        y, m, dd = map(int, d["date"].split("-"))
        wd = date(y, m, dd).isoweekday() % 7  # Sun=0 .. Sat=6
        col[wd] = d
        if wd == 6:
            cols.append(col)
            col = [None] * 7
    if any(x is not None for x in col):
        cols.append(col)
    return cols


def month_label_positions(cols):
    """Return (col_index, 'Mon') for columns where a new month starts."""
    labels = []
    last_month = None
    for ci, col in enumerate(cols):
        first = next((d for d in col if d), None)
        if not first:
            continue
        month = int(first["date"].split("-")[1])
        if month != last_month:
            labels.append((ci, MONTHS[month - 1]))
            last_month = month
    return labels


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    days = data["days"]
    stats = data.get("stats", {})
    cols = build_columns(days)

    grid_w = len(cols) * (CELL + GAP)
    width = LABEL_COL + grid_w + PAD_X * 2
    height = PAD_TOP + 7 * (CELL + GAP) + PAD_BOTTOM

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'font-family="\'JetBrains Mono\',\'Fira Code\',Consolas,monospace" '
        f'role="img" aria-label="Contribution graph for {data.get("user","")}">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
    ]

    ox = PAD_X + LABEL_COL
    oy = PAD_TOP

    # Month labels along the top.
    for ci, label in month_label_positions(cols):
        x = ox + ci * (CELL + GAP)
        p.append(
            f'<text x="{x}" y="{oy - 8}" fill="{MUTED}" '
            f'font-size="10">{label}</text>'
        )

    # Weekday labels (Mon / Wed / Fri) down the left.
    for wd, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = oy + wd * (CELL + GAP) + CELL - 2
        p.append(
            f'<text x="{PAD_X}" y="{y}" fill="{MUTED}" font-size="9">{name}</text>'
        )

    # The cells.
    for ci, col in enumerate(cols):
        begin = ci * COL_STAGGER
        cx = ox + ci * (CELL + GAP)
        for wd, day in enumerate(col):
            if day is None:
                continue
            cy = oy + wd * (CELL + GAP)
            fill = LEVELS[min(day.get("level", 0), 4)]
            count = day.get("count", 0)
            title = (
                f'{count} contribution{"s" if count != 1 else ""} on {day["date"]}'
            )
            p.append(
                f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" '
                f'rx="{RADIUS}" fill="{fill}" opacity="0">'
                f'<title>{title}</title>'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.3f}s" dur="{CELL_POP}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="scale" '
                f'from="0.4" to="1" additive="sum" '
                f'begin="{begin:.3f}s" dur="{CELL_POP}s" fill="freeze" '
                f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.8 0.2 1" '
                f'transform-origin="{cx + CELL/2} {cy + CELL/2}"/>'
                f"</rect>"
            )

    # Legend (Less [] [] [] [] [] More) bottom-right.
    legend_y = oy + 7 * (CELL + GAP) + 22
    lx = ox + grid_w - (5 * (CELL + GAP) + 70)
    p.append(f'<text x="{lx}" y="{legend_y + 9}" fill="{MUTED}" font-size="10">Less</text>')
    for i, c in enumerate(LEVELS):
        p.append(
            f'<rect x="{lx + 34 + i * (CELL + GAP)}" y="{legend_y}" '
            f'width="{CELL}" height="{CELL}" rx="{RADIUS}" fill="{c}"/>'
        )
    p.append(
        f'<text x="{lx + 34 + 5 * (CELL + GAP) + 4}" y="{legend_y + 9}" '
        f'fill="{MUTED}" font-size="10">More</text>'
    )

    # Stats summary bottom-left.
    summary = (
        f'{stats.get("total", 0)} contributions in the last year   '
        f'·   current streak {stats.get("current_streak", 0)}d   '
        f'·   longest {stats.get("longest_streak", 0)}d   '
        f'·   busiest {stats.get("busiest_weekday", "-")}'
    )
    p.append(
        f'<text x="{ox}" y="{legend_y + 9}" fill="{FG}" font-size="11">'
        f'<tspan fill="{ACCENT}">$</tspan> {summary}</text>'
    )

    p.append("</svg>")
    OUT.write_text("\n".join(p), encoding="utf-8")
    print(f"wrote {OUT}  ({len(cols)} weeks, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
