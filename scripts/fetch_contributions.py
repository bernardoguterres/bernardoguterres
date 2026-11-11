#!/usr/bin/env python3
"""Fetch the public GitHub contribution calendar into data/contributions.json.

Source: https://github.com/users/<login>/contributions, the same page that draws the
public profile graph, so no token is needed and private activity is never included.
The public repository count comes from the REST API (GITHUB_TOKEN is used when set,
only to avoid rate limits).

The new data is validated before it replaces the old file. On any fetch or
validation failure the script leaves data/contributions.json untouched, prints a
warning and exits with status 0 unless --strict is given, so the last good data
is kept. Run it by hand, then scripts/render_readme_cards.py, to refresh the cards.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
LOGIN = "bernardoguterres"
UA = "bernardoguterres-profile-readme-cards"

TD_RE = re.compile(r"<td\b[^>]*\bdata-date=\"(\d{4}-\d{2}-\d{2})\"[^>]*>", re.S)
ATTR_RE = lambda name: re.compile(rf'\b{name}="([^"]*)"')  # noqa: E731
TIP_RE = re.compile(r'<tool-tip\b[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', re.S)
TOTAL_RE = re.compile(r'id="js-contribution-activity-description"[^>]*>\s*([\d,]+)\s+contributions?', re.S)


def get(url: str, token: str | None = None) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse_calendar(page: str) -> tuple[list[dict], int]:
    tips = {}
    for target, text in TIP_RE.findall(page):
        text = html.unescape(text).strip()
        m = re.match(r"(No|\d[\d,]*) contributions? on ", text)
        if not m:
            raise ValueError(f"unrecognised tooltip: {text!r}")
        tips[target] = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))
    days = []
    for m in TD_RE.finditer(page):
        tag = m.group(0)
        cell_id = ATTR_RE("id").search(tag)
        level = ATTR_RE("data-level").search(tag)
        if not cell_id or not level or cell_id.group(1) not in tips:
            raise ValueError(f"calendar cell without count: {tag[:120]}")
        days.append({"date": m.group(1), "count": tips[cell_id.group(1)], "level": int(level.group(1))})
    days.sort(key=lambda d: d["date"])
    total = TOTAL_RE.search(page)
    if not total:
        raise ValueError("total contributions heading not found")
    return days, int(total.group(1).replace(",", ""))


def validate(days: list[dict], heading_total: int) -> None:
    if not 364 <= len(days) <= 372:
        raise ValueError(f"expected about a year of days, got {len(days)}")
    dates = [dt.date.fromisoformat(d["date"]) for d in days]
    for a, b in zip(dates, dates[1:]):
        if (b - a).days != 1:
            raise ValueError(f"calendar is not contiguous between {a} and {b}")
    for d in days:
        if d["count"] < 0 or not 0 <= d["level"] <= 4 or (d["count"] == 0) != (d["level"] == 0):
            raise ValueError(f"inconsistent day {d}")
    total = sum(d["count"] for d in days)
    if total != heading_total:
        raise ValueError(f"sum of days {total} != published total {heading_total}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="exit non-zero on failure")
    args = ap.parse_args()
    try:
        page = get(f"https://github.com/users/{LOGIN}/contributions")
        days, heading_total = parse_calendar(page)
        validate(days, heading_total)
        user = json.loads(get(f"https://api.github.com/users/{LOGIN}", os.environ.get("GITHUB_TOKEN")))
        public_repos = int(user["public_repos"])
        if public_repos <= 0:
            raise ValueError("public repository count missing")
    except Exception as exc:  # keep the last good data on any failure
        msg = f"Contribution refresh failed, keeping last good data: {exc}"
        print(f"::warning::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"warning: {msg}", file=sys.stderr)
        return 1 if args.strict else 0

    payload = {
        "login": LOGIN,
        "source": f"https://github.com/users/{LOGIN}/contributions",
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total": heading_total,
        "public_repos": public_repos,
        "days": days,
    }
    DATA.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA.with_suffix(".json.tmp")
    # One day per line keeps refresh diffs small and reviewable.
    head = {k: v for k, v in payload.items() if k != "days"}
    body = ",\n".join("  " + json.dumps(d, separators=(", ", ": ")) for d in days)
    tmp.write_text(json.dumps(head, indent=1)[:-2] + ',\n "days": [\n' + body + "\n ]\n}\n")
    json.loads(tmp.read_text())  # never install a file that does not parse
    tmp.replace(DATA)
    print(f"wrote {DATA.relative_to(ROOT)}: {len(days)} days, {heading_total} contributions, {public_repos} public repos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
