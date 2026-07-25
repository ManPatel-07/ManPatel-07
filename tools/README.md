# Profile generators

Self-contained scripts that render the animated SVGs used by the profile
`README.md`. Every asset is a plain SVG committed to the repo — no external
badge services, API tokens, or client-side JavaScript.

| File | Output | When to run |
|------|--------|-------------|
| `clean_photo.py` | `assets/photo-ready.png` | Only when redoing the portrait |
| `render_portrait.py` | `portrait.svg` | After tweaking the portrait |
| `render_panel.py` | `sysinfo.svg` | After editing the info rows |
| `pull_contributions.py` | `assets/contributions.json` | Daily, via GitHub Actions |
| `render_graph.py` | `graph.svg` | Daily, via GitHub Actions |

## Two dependency sets

```bash
# Daily automation (lightweight — used by the cron workflow)
pip install -r tools/requirements-daily.txt

# Portrait pipeline (heavier — image processing, only when redoing the art)
pip install -r tools/requirements-art.txt
```

## Redo the portrait from a new photo

```bash
python tools/clean_photo.py assets/source-photo.jpeg   # -> assets/photo-ready.png
python tools/render_portrait.py                        # -> portrait.svg
```

`clean_photo.py` removes the background (rembg), evens out lighting (CLAHE), and
drops the subject on a white canvas so empty space maps to the light end of the
character ramp. `render_portrait.py` then samples it to a character grid and
animates each row drawing in.

## Rebuild the info panel

```bash
PREVIEW=1 python tools/render_panel.py   # still frame for previewing
python tools/render_panel.py             # -> sysinfo.svg (animated)
```

Edit the `ROWS` list at the top of `render_panel.py` to change what it shows.

## Refresh the contribution graph

```bash
GH_USER=ManPatel-07 python tools/pull_contributions.py   # -> assets/contributions.json
python tools/render_graph.py                             # -> graph.svg
```

This runs automatically once a day via `.github/workflows/refresh-graph.yml`.
Trigger it manually from the **Actions** tab (`workflow_dispatch`) to confirm it
commits a fresh `graph.svg`.
