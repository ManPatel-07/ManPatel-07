"""
Pull the public contribution calendar for a GitHub user and save it as JSON.

No OAuth or personal access token needed: GitHub serves a plain HTML fragment
of the contribution calendar at

    https://github.com/users/<username>/contributions

which is the same markup the profile page itself consumes. We parse the day
cells out of it and store counts, levels, and a few derived stats.

Usage:
    python tools/pull_contributions.py
    # writes assets/contributions.json
"""

import json
import os
from collections import defaultdict
from datetime import date
from pathlib import Path

import httpx
from lxml import html

USER = os.environ.get("GH_USER", "ManPatel-07")
URL = f"https://github.com/users/{USER}/contributions"
OUT = Path("assets/contributions.json")

WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def fetch_days() -> list[dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (contribution-graph-renderer)",
        "Accept": "text/html",
        "X-Requested-With": "XMLHttpRequest",
    }
    resp = httpx.get(URL, headers=headers, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    tree = html.fromstring(resp.text)

    days = []
    for cell in tree.cssselect("td.ContributionCalendar-day"):
        d = cell.get("data-date")
        if not d:
            continue
        level = int(cell.get("data-level") or 0)
        # The count now lives in an adjacent tool-tip element; fall back to 0.
        count = cell.get("data-count")
        days.append({"date": d, "level": level, "count": int(count) if count else None})

    # Newer GitHub markup keeps counts in <tool-tip> siblings keyed by cell id.
    tips = {}
    for tip in tree.cssselect("tool-tip"):
        target = tip.get("for")
        text = (tip.text_content() or "").strip()
        n = 0
        if text and text[0].isdigit():
            n = int(text.split()[0].replace(",", ""))
        elif text.lower().startswith("no contribution"):
            n = 0
        tips[target] = n
    for cell, day in zip(tree.cssselect("td.ContributionCalendar-day"), days):
        cid = cell.get("id")
        if day["count"] is None:
            day["count"] = tips.get(cid, 0)

    days.sort(key=lambda x: x["date"])
    return days


def derive_stats(days: list[dict]) -> dict:
    total = sum(d["count"] or 0 for d in days)

    # Streaks (consecutive days with >0 contributions, up to today).
    cur = longest = run = 0
    for d in days:
        if (d["count"] or 0) > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    # Current streak: count back from the most recent day.
    for d in reversed(days):
        if (d["count"] or 0) > 0:
            cur += 1
        else:
            break

    by_weekday = defaultdict(int)
    for d in days:
        y, m, dd = map(int, d["date"].split("-"))
        by_weekday[WEEKDAYS[date(y, m, dd).isoweekday() % 7]] += d["count"] or 0
    busiest = max(by_weekday, key=by_weekday.get) if by_weekday else "-"

    return {
        "total": total,
        "current_streak": cur,
        "longest_streak": longest,
        "busiest_weekday": busiest,
        "by_weekday": dict(by_weekday),
    }


def main() -> None:
    days = fetch_days()
    if not days:
        raise SystemExit("No contribution cells found — did the markup change?")
    data = {"user": USER, "days": days, "stats": derive_stats(days)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    s = data["stats"]
    print(
        f"wrote {OUT}  ({len(days)} days, total={s['total']}, "
        f"streak={s['current_streak']}, longest={s['longest_streak']})"
    )


if __name__ == "__main__":
    main()
