#!/usr/bin/env python3
"""Render the animated SVG cards for the GitHub profile README.

    python3 scripts/render_readme_cards.py            # animated cards -> cards/
    STATIC=1 python3 scripts/render_readme_cards.py   # finished frames -> build/static-cards/

Every card is written in a dark and a light variant; README.md picks one with
<picture> and prefers-color-scheme. Cards are self-contained: fonts are subset
to the characters each card uses and embedded as base64 WOFF data URIs, and no
card loads scripts, images or anything else from outside the file.

Every card's first frame is already complete: names, claims, numbers, cells,
bars, boxes and arrows are drawn without animation, so a card stays readable
when motion is disabled, unsupported or interrupted. One-shot motion is used
only for optional accents layered on top (the surname's SMIL copper sweep, a
scan band, ring/sheen/arrow nudges, path traces). `prefers-reduced-motion:
reduce` turns CSS animation off and swaps SMIL groups (.motion) for static twins
(.still). STATIC=1 omits all motion from the file. Output depends only on data/contributions.json and this
script, so rendering the same input twice yields identical bytes.
"""
from __future__ import annotations

import base64
import calendar
import datetime as dt
import io
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
DATA = ROOT / "data" / "contributions.json"
STATIC = os.environ.get("STATIC") == "1"
OUT = Path(os.environ.get("OUT_DIR") or (ROOT / ("build/static-cards" if STATIC else "cards")))

# ---------------------------------------------------------------- palette
# Hex equivalents of the portfolio's oklch tokens (charcoal, card, cream, copper).
THEMES = {
    "dark": dict(card="#1d1610", edge="#3a2f25", text="#f2eee6", muted="#aba397",
                 accent="#df825e", accent2="#f0a27f", chip="#2a2018", heat0="#2a2018"),
    "light": dict(card="#fbf8f2", edge="#e1d8c8", text="#1d1610", muted="#5f574c",
                  accent="#91301f", accent2="#b8532f", chip="#f1e9dc", heat0="#ece4d6"),
}


def mix(a: str, b: str, t: float) -> str:
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def heat(t: dict, level: int) -> str:
    return t["heat0"] if level == 0 else mix(t["heat0"], t["accent"], (0.28, 0.5, 0.74, 1.0)[level - 1])


# ---------------------------------------------------------------- fonts
class Face:
    def __init__(self, key: str, file: str, family: str, weight: int, fallback: str):
        self.key, self.path, self.family, self.weight, self.fallback = key, FONTS / file, family, weight, fallback
        self.font = TTFont(self.path, recalcTimestamp=False, lazy=True)
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font["hmtx"]
        self.upem = self.font["head"].unitsPerEm

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        total = 0
        for ch in text:
            if ord(ch) not in self.cmap:
                raise ValueError(f"{self.family} has no glyph for {ch!r}")
            total += self.hmtx[self.cmap[ord(ch)]][0]
        return total * size / self.upem + tracking * size * len(text)


SERIF_FB = "Georgia, 'Times New Roman', serif"
SANS_FB = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO_FB = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FACES = {
    "serif": Face("serif", "Newsreader-Display-Regular.ttf", "BG Newsreader", 400, SERIF_FB),
    "serif5": Face("serif5", "Newsreader-Display-Medium.ttf", "BG Newsreader", 500, SERIF_FB),
    "sans": Face("sans", "SourceSans3-Regular.ttf", "BG Source Sans", 400, SANS_FB),
    "sans6": Face("sans6", "SourceSans3-SemiBold.ttf", "BG Source Sans", 600, SANS_FB),
    "mono": Face("mono", "IBMPlexMono-Regular.ttf", "BG Plex Mono", 400, MONO_FB),
    "mono5": Face("mono5", "IBMPlexMono-Medium.ttf", "BG Plex Mono", 500, MONO_FB),
}
_SUBSET_CACHE: dict[tuple[str, str], str] = {}


def woff_data_uri(face: Face, chars: str) -> str:
    key = (face.key, chars)
    if key not in _SUBSET_CACHE:
        font = TTFont(face.path, recalcTimestamp=False)
        opts = subset.Options()
        opts.flavor = "woff"
        opts.layout_features = ["kern", "liga", "calt", "locl"]
        opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]  # keep copyright and licence records
        opts.notdef_outline = True
        opts.recalc_timestamp = False
        opts.drop_tables = opts.drop_tables + ["meta", "DSIG"]
        sub = subset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(font)
        font.flavor = "woff"
        buf = io.BytesIO()
        font.save(buf, reorderTables=True)
        _SUBSET_CACHE[key] = base64.b64encode(buf.getvalue()).decode("ascii")
    return "data:font/woff;base64," + _SUBSET_CACHE[key]


# ---------------------------------------------------------------- svg canvas
class Card:
    """Collects SVG elements and the characters each embedded face must cover."""

    def __init__(self, w: int, h: int, theme: dict, title: str, desc: str):
        self.w, self.h, self.t, self.title, self.desc = w, h, theme, title, desc
        self.parts: list[str] = []
        self.used: dict[str, set[str]] = OrderedDict()
        self.css: list[str] = []

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, face="sans", size=16, fill="text", anchor="start", tracking=0.0,
             cls="", delay=None, extra="") -> float:
        f = FACES[face]
        self.used.setdefault(face, set()).update(s)
        color = self.t.get(fill, fill)
        cls_attr = f' class="{(f.key + " " + cls).strip()}"'
        style = f' style="animation-delay:{delay:.2f}s"' if delay is not None and not STATIC else ""
        anchor_attr = f' text-anchor="{anchor}"' if anchor != "start" else ""
        track = f' letter-spacing="{fmt(tracking * size)}"' if tracking else ""
        self.add(f'<text x="{fmt(x)}" y="{fmt(y)}"{cls_attr} font-size="{fmt(size)}" fill="{color}"'
                 f'{anchor_attr}{track}{style}{extra}>{escape(s)}</text>')
        return f.width(s, size, tracking)

    def svg(self) -> str:
        faces = []
        for key, chars in self.used.items():
            f = FACES[key]
            faces.append(f"@font-face{{font-family:'{f.family}';font-weight:{f.weight};font-style:normal;"
                         f"src:url({woff_data_uri(f, ''.join(sorted(chars)))}) format('woff')}}")
        classes = "".join(f".{f.key}{{font-family:'{f.family}',{f.fallback};font-weight:{f.weight}}}"
                          for f in FACES.values() if f.key in self.used)
        motion_css = "" if STATIC else (
            ".draw{stroke-dasharray:1;animation:draw 1.2s ease-in-out both}"
            "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
            + "".join(self.css) +
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}"
            ".motion{display:none}.still{display:inline}}"
        )
        still = ".still{display:none}" if not STATIC else ".motion{display:none}"
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{escape(self.title)}</title>\n<desc id="desc">{escape(self.desc)}</desc>\n'
            f"<style>{''.join(faces)}{classes}{still}{motion_css}</style>\n"
            f'<rect x="1" y="1" width="{self.w - 2}" height="{self.h - 2}" rx="16" fill="{self.t["card"]}" '
            f'stroke="{self.t["edge"]}" stroke-width="1.5"/>\n' + "\n".join(self.parts) + "\n</svg>\n"
        )


def fmt(v) -> str:
    if isinstance(v, (int,)):
        return str(v)
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s != "-0" else "0"


def anim(delay: float) -> str:
    return "" if STATIC else f' style="animation-delay:{delay:.2f}s"'


# ---------------------------------------------------------------- data
def load() -> dict:
    data = json.loads(DATA.read_text())
    days = [(dt.date.fromisoformat(d["date"]), d["count"], d["level"]) for d in data["days"]]
    total = sum(c for _, c, _ in days)
    assert total == data["total"], "data total does not match its days"
    active = sum(1 for _, c, _ in days if c > 0)

    longest = run = 0
    longest_end = None
    for d, c, _ in days:
        run = run + 1 if c > 0 else 0
        if run > longest:
            longest, longest_end = run, d
    # Current streak: consecutive active days ending on the last day of the range,
    # or the day before it when the last day (still in progress) has none yet.
    cur, i = 0, len(days) - 1
    if days[i][1] == 0:
        i -= 1
    while i >= 0 and days[i][1] > 0:
        cur, i = cur + 1, i - 1
    busiest_day = max(days, key=lambda x: (x[1], -x[0].toordinal()))

    months: "OrderedDict[tuple[int, int], int]" = OrderedDict()
    for d, c, _ in days:
        months[(d.year, d.month)] = months.get((d.year, d.month), 0) + c
    start, end = days[0][0], days[-1][0]
    partial = {(start.year, start.month): start.day != 1,
               (end.year, end.month): end.day != calendar.monthrange(end.year, end.month)[1]}
    busiest_month = max(months.items(), key=lambda kv: (kv[1], -(kv[0][0] * 12 + kv[0][1])))
    return dict(days=days, total=total, active=active, longest=longest,
                longest_start=(longest_end - dt.timedelta(days=longest - 1)) if longest else None,
                longest_end=longest_end, current=cur, busiest_day=busiest_day, months=months,
                partial=partial, busiest_month=busiest_month, start=start, end=end,
                public_repos=data["public_repos"])


def dfmt(d: dt.date, year=True) -> str:
    return f"{d.strftime('%b')} {d.day}, {d.year}" if year else f"{d.strftime('%b')} {d.day}"


# ---------------------------------------------------------------- timeline (seconds)
T_HERO, T_HEAT, T_MONTH, T_TILES, T_ALPHA, T_SMALL = 0.0, 0.9, 1.6, 2.4, 2.9, 3.6


# ---------------------------------------------------------------- cards
def hero(t: dict) -> Card:
    c = Card(1000, 300, t, "Bernardo Guterres",
             "Bernardo Guterres. MSc Data Science and Machine Learning at UCL. I build ML systems, "
             "local-first AI, and tools for trading research. A BG monogram sits on the left.")
    c.css.append(".row{animation:row .35s steps(4,end) both}"
                 "@keyframes row{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}")
    # Monogram: a copper-edged square with BG built from rows of mono glyph texture.
    c.add(f'<g><rect x="48" y="50" width="200" height="200" rx="18" '
          f'fill="{t["chip"]}" stroke="{t["accent"]}" stroke-width="1.5"/></g>')
    pattern = ["· · · · · · · · · ·", "· : · : · : · : · :", ": · : · : · : · : ·"]
    for i in range(9):
        c.text(64, 78 + i * 20, pattern[i % 3], "mono", 13, "edge", cls="row", delay=T_HERO + 0.1 + i * 0.06)
    c.text(148, 183, "BG", "serif5", 96, "accent", anchor="middle")

    x = 292
    c.text(x, 92, "LONDON, UK · DATA SCIENCE & ML", "mono5", 13, "accent", tracking=0.12)
    first = "Bernardo "
    c.text(x - 3, 160, first, "serif", 64, "text")
    sx = x - 3 + FACES["serif"].width(first, 64)
    sw = FACES["serif"].width("Guterres", 64)
    # Surname: SMIL gradient sweep from cream to copper (motion), solid copper (still).
    c.add('<defs><linearGradient id="sweep" gradientUnits="userSpaceOnUse" '
          f'x1="{fmt(sx - sw)}" x2="{fmt(sx)}" y1="0" y2="0">'
          f'<stop offset="0" stop-color="{t["accent"]}"/><stop offset=".82" stop-color="{t["accent2"]}"/>'
          f'<stop offset="1" stop-color="{t["text"]}"/>'
          + ("" if STATIC else
             f'<animate attributeName="x1" from="{fmt(sx - sw)}" to="{fmt(sx + sw)}" begin="{T_HERO + 1.1}s" '
             f'dur="1.1s" fill="freeze" calcMode="spline" keySplines=".4 0 .2 1" keyTimes="0;1"/>'
             f'<animate attributeName="x2" from="{fmt(sx)}" to="{fmt(sx + 2 * sw)}" begin="{T_HERO + 1.1}s" '
             f'dur="1.1s" fill="freeze" calcMode="spline" keySplines=".4 0 .2 1" keyTimes="0;1"/>')
          + "</linearGradient></defs>")
    c.add('<g class="motion">')
    c.text(sx, 160, "Guterres", "serif", 64, "url(#sweep)")
    c.add('</g><g class="still">')
    c.text(sx, 160, "Guterres", "serif", 64, "accent")
    c.add("</g>")
    c.text(x, 202, "MSc Data Science & Machine Learning at UCL", "sans6", 24, "text")
    c.text(x, 236, "I build ML systems, local-first AI, and tools for trading research.", "sans", 20,
           "muted")
    return c


def heatmap(t: dict, s: dict) -> Card:
    days = s["days"]
    c = Card(1000, 290, t, "Public GitHub contributions",
             f"Heatmap of {s['total']} public GitHub contributions from {dfmt(s['start'])} to {dfmt(s['end'])}, "
             f"one cell per day, darker copper for more contributions.")
    c.text(40, 46, "CONTRIBUTIONS", "mono5", 12.5, "accent", tracking=0.12)
    c.text(40, 74, f"{dfmt(s['start'])} – {dfmt(s['end'])}", "serif", 24, "text")
    c.text(960, 74, f"{s['total']:,} public contributions", "sans6", 18, "text", anchor="end")

    pitch, cell, x0, y0 = 16.6, 13, 74, 112
    first = days[0][0]
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    ncols = (offset + len(days) + 6) // 7
    cols: dict[int, list[str]] = {}
    last_month_col = -3
    for i, (d, n, lvl) in enumerate(days):
        k = offset + i
        col, row = k // 7, k % 7
        tip = f"{n} contribution{'s' if n != 1 else ''} on {dfmt(d)}"
        cols.setdefault(col, []).append(
            f'<rect x="{fmt(x0 + col * pitch)}" y="{fmt(y0 + row * pitch)}" width="{cell}" height="{cell}" '
            f'rx="2.5" fill="{heat(t, lvl)}"><title>{tip}</title></rect>')
        if d.day <= 7 and row == 0 and col - last_month_col >= 3:
            c.text(x0 + col * pitch, y0 - 10, d.strftime("%b"), "mono", 11.5, "muted")
            last_month_col = col
    for r, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        c.text(x0 - 10, y0 + r * pitch + 10.5, lab, "mono", 11, "muted", anchor="end")
    for col in range(ncols):
        c.add("<g>" + "".join(cols.get(col, [])) + "</g>")
    grid_w = (ncols - 1) * pitch + cell
    if not STATIC:  # accent only: a copper band scans the finished grid once, then fades out
        c.css.append(".band{animation:band 1.6s ease-in-out both}"
                     f"@keyframes band{{0%{{opacity:0;transform:none}}15%{{opacity:1}}85%{{opacity:1}}"
                     f"100%{{opacity:0;transform:translateX({fmt(grid_w - 40)}px)}}}}")
        c.add(f'<defs><linearGradient id="band" x1="0" x2="1"><stop offset="0" stop-color="{t["accent2"]}" '
              f'stop-opacity="0"/><stop offset=".5" stop-color="{t["accent2"]}" stop-opacity=".35"/>'
              f'<stop offset="1" stop-color="{t["accent2"]}" stop-opacity="0"/></linearGradient></defs>'
              f'<rect class="band" x="{x0}" y="{y0 - 3}" width="40" height="{fmt(7 * pitch + 2)}" rx="4" '
              f'fill="url(#band)" opacity="0"{anim(T_HEAT)}/>')

    ly = y0 + 7 * pitch + 22
    c.text(x0, ly + 10, "Source: public profile calendar · levels set by GitHub", "mono", 11.5, "muted")
    lx = 960 - 5 * pitch - FACES["mono"].width("More", 11.5)
    c.text(lx - 8, ly + 10, "Less", "mono", 11.5, "muted", anchor="end")
    legend = "".join(f'<rect x="{fmt(lx + i * pitch)}" y="{ly}" width="{cell}" height="{cell}" rx="2.5" '
                     f'fill="{heat(t, i)}"/>' for i in range(5))
    c.add(f'<g>{legend}</g>')
    c.text(lx + 5 * pitch + 4, ly + 10, "More", "mono", 11.5, "muted")
    return c


def monthly(t: dict, s: dict) -> Card:
    months = s["months"]
    (by, bm), bcount = s["busiest_month"]
    bname = f"{calendar.month_name[bm]} {by}"
    bd, bdn, _ = s["busiest_day"]
    c = Card(1000, 340, t, "Monthly GitHub activity",
             f"Monthly public contributions from {dfmt(s['start'])} to {dfmt(s['end'])}. Busiest month: {bname} "
             f"with {bcount}. Total {s['total']} contributions, {s['active']} active days, current streak "
             f"{s['current']} days, longest streak {s['longest']} days, busiest day {dfmt(bd)} with {bdn}.")
    c.css.append(".pulse{animation:pulse 1.4s ease-in-out both}"
                 "@keyframes pulse{0%{opacity:0}40%{opacity:1}100%{opacity:0}}")
    c.text(40, 46, "MONTHLY ACTIVITY", "mono5", 12.5, "accent", tracking=0.12)
    c.text(40, 74, "Contributions per month", "serif", 24, "text")

    x0, base, chart_w, chart_h = 40, 272, 580, 150
    n = len(months)
    slot = chart_w / n
    bw = slot * 0.62
    peak = max(months.values()) or 1
    for i, ((y, m), v) in enumerate(months.items()):
        h = max(2.0, chart_h * v / peak) if v else 2.0
        x = x0 + i * slot + (slot - bw) / 2
        is_peak = (y, m) == (by, bm)
        fill = t["accent"] if is_peak else mix(t["chip"], t["accent"], 0.42)
        star = "*" if s["partial"].get((y, m)) else ""
        c.add(f'<rect x="{fmt(x)}" y="{fmt(base - h)}" width="{fmt(bw)}" height="{fmt(h)}" rx="3" '
              f'fill="{fill}"><title>{calendar.month_name[m]} {y}: {v}'
              f'{" (partial month)" if star else ""}</title></rect>')
        c.text(x + bw / 2, base + 20, calendar.month_abbr[m] + star, "mono", 11, "accent" if is_peak else "muted",
               anchor="middle")
        if m == 1 or i == 0:
            c.text(x + bw / 2, base + 36, str(y), "mono", 10.5, "muted", anchor="middle")
        if is_peak:
            c.text(x + bw / 2, base - h - 10, f"{v}", "mono5", 14, "accent", anchor="middle")
            if not STATIC:
                c.add(f'<rect class="pulse" x="{fmt(x - 4)}" y="{fmt(base - h - 4)}" width="{fmt(bw + 8)}" '
                      f'height="{fmt(h + 4)}" rx="5" fill="none" stroke="{t["accent2"]}" stroke-width="2" '
                      f'opacity="0"{anim(T_MONTH)}/>')
    c.add(f'<path d="M{x0} {base}H{x0 + chart_w}" stroke="{t["edge"]}" stroke-width="1"/>')
    if any(s["partial"].values()):
        c.text(x0, 326, "* partial month: the one-year range starts and ends mid-month", "mono", 10.5, "muted")

    # Stats panel
    px = 660
    c.add(f'<g><rect x="{px}" y="96" width="300" height="214" rx="12" '
          f'fill="{t["chip"]}" stroke="{t["edge"]}"/></g>')
    ls = s["longest_start"]
    stats = [
        ("Total contributions", f"{s['total']:,}", None),
        ("Active days", f"{s['active']}", f"of {len(s['days'])}"),
        ("Current streak", f"{s['current']} day{'s' if s['current'] != 1 else ''}", f"to {dfmt(s['end'], False)}"),
        ("Longest streak", f"{s['longest']} days", f"{dfmt(ls, False)}–{dfmt(s['longest_end'], False)}" if ls else None),
        ("Busiest day", f"{bdn}", dfmt(bd)),
        ("Busiest month", f"{bcount}", bname),
    ]
    for i, (label, value, note) in enumerate(stats):
        y = 128 + i * 33
        c.text(px + 20, y, label, "sans", 15.5, "muted")
        vw = FACES["mono5"].width(value, 16)
        c.text(px + 280, y, value, "mono5", 16, "text", anchor="end")
        if note:
            c.text(px + 280 - vw - 8, y, note, "mono", 11, "muted", anchor="end")
    return c


TILES = [
    ("portfolio", "Portfolio", "bernardoguterres.vercel.app", "Projects and CV", None),
    ("repositories", "Repositories", "github.com/bernardoguterres", None, "public_repos"),
    ("linkedin", "LinkedIn", "in/bernardoguterres", "Experience and contact", None),
]


def tile(t: dict, s: dict, idx: int) -> Card:
    key, title, host, sub, metric = TILES[idx]
    d0 = T_TILES + idx * 0.18
    value = s.get(metric) if metric else None
    desc = f"{title} link tile ({host})." + (f" Shows {value} public repositories." if value else "")
    c = Card(300, 170, t, title, desc)
    c.css.append(
        ".ring{transform-box:fill-box;transform-origin:50% 50%;animation:ring .8s cubic-bezier(.2,.9,.25,1.15) both}"
        "@keyframes ring{0%{opacity:0;transform:translateY(6px) rotate(-2.5deg)}60%{opacity:.55;transform:rotate(.7deg)}"
        "100%{opacity:.55;transform:none}}"
        ".sheen{animation:sheen 1.1s ease-in-out both}"
        "@keyframes sheen{from{transform:translateX(-340px)}to{transform:translateX(340px)}}"
        ".nudge{animation:nudge .5s ease-in-out 2 alternate both}"
        "@keyframes nudge{from{transform:none}to{transform:translate(4px,-4px)}}")
    c.add("<g>")
    c.add(f'<rect class="ring" x="10" y="10" width="280" height="150" rx="12" fill="none" stroke="{t["accent"]}" '
          f'stroke-width="1.2" opacity=".55"{anim(d0)}/>')
    if not STATIC:
        c.add(f'<defs><linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="{t["accent2"]}" '
              f'stop-opacity="0"/><stop offset=".5" stop-color="{t["accent2"]}" stop-opacity=".22"/>'
              f'<stop offset="1" stop-color="{t["accent2"]}" stop-opacity="0"/></linearGradient>'
              f'<clipPath id="cp"><rect x="10" y="10" width="280" height="150" rx="12"/></clipPath></defs>'
              f'<g clip-path="url(#cp)"><rect class="sheen" x="0" y="0" width="160" height="170" '
              f'fill="url(#sh)" transform="translate(-340 0)"{anim(d0 + 0.5)}/></g>')
    c.text(30, 48, f"0{idx + 1}", "mono5", 13, "accent", tracking=0.1)
    c.add(f'<g class="nudge"{anim(d0 + 0.9)}>')
    c.text(270, 52, "↗", "sans6", 28, "accent", anchor="end")
    c.add("</g>")
    c.text(28, 102, title, "serif", 36, "text")
    if value is not None:
        # The real number is always drawn; only a copper underline draws in as an accent.
        vx = 270
        c.text(vx, 140, str(value), "serif5", 34, "accent", anchor="end")
        uw = FACES["serif5"].width(str(value), 34)
        c.add(f'<path d="M{fmt(vx - uw)} 148 H{vx}" pathLength="1" class="draw" fill="none" '
              f'stroke="{t["accent2"]}" stroke-width="2" stroke-linecap="round"{anim(d0 + 0.5)}/>')
        c.text(30, 138, "public repositories", "mono", 13, "muted")
    else:
        c.text(30, 138, sub, "sans", 17, "muted")
    c.add("</g>")
    return c


def alpha(t: dict) -> Card:
    c = Card(1000, 520, t, "Alpha System: AlphaLab to AlphaLive",
             "AlphaLab backtests strategies and exports a schema-validated strategy JSON that a person moves "
             "manually into AlphaLive. AlphaLive re-implements the signals and executes them with idempotent "
             "orders, circuit breakers and restart-safe state. AlphaSignal is an optional, fail-open sentiment "
             "gate on BUY entries. A CI parity test shows zero decision-bar mismatches across seven strategies "
             "on historical SPY and MSFT data.")
    T = T_ALPHA
    c.text(44, 54, "FEATURED · TRADING RESEARCH", "mono5", 12.5, "accent", tracking=0.12)
    c.text(42, 98, "Alpha System", "serif", 40, "text")
    c.text(44, 128, "Backtest in research, export by hand, execute under risk controls.", "sans", 19, "muted")

    def box(x, y, w, h, name, tag, lines, d, strong=False, size=28):
        c.add(f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{t["chip"]}" '
              f'stroke="{t["accent"] if strong else t["edge"]}" stroke-width="1.3"/></g>')
        c.text(x + 24, y + 42, name, "serif", size, "text")
        c.text(x + 24, y + 66, tag, "mono5", 12, "accent", tracking=0.1)
        for i, ln in enumerate(lines):
            c.text(x + 24, y + 96 + i * 24, ln, "mono", 14, "muted")

    box(44, 164, 300, 180, "AlphaLab", "BACKTESTING", ["next-bar execution", "transaction costs",
                                                       "walk-forward selection"], T + 0.3)
    # export arrow + packet
    c.add(f'<path d="M352 254 H640" fill="none" stroke="{t["accent"]}" stroke-width="2" stroke-linecap="round"/>')
    if not STATIC:  # accent only: a light stroke traces the export path and a dot travels along it
        c.css.append(".trace{stroke-dasharray:.25 1;animation:trace 1.3s ease-in-out both}"
                     "@keyframes trace{0%{stroke-dashoffset:.25;opacity:1}85%{opacity:1}"
                     "100%{stroke-dashoffset:-1;opacity:0}}")
        c.add(f'<path d="M352 254 H640" pathLength="1" class="trace" fill="none" stroke="{t["accent2"]}" '
              f'stroke-width="4" stroke-linecap="round" opacity="0"{anim(T + 0.4)}/>')
    c.add(f'<path d="M630 246 L641 254 L630 262" fill="none" stroke="{t["accent"]}" stroke-width="2" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    c.add(f'<g><rect x="436" y="222" width="122" height="24" rx="5" fill="{t["card"]}" '
          f'stroke="{t["accent"]}"/></g>')
    c.text(497, 239, "strategy.json", "mono", 11.5, "accent", anchor="middle")
    c.text(496, 282, "schema-validated export", "mono", 13, "muted", anchor="middle")
    c.text(496, 302, "moved manually", "mono5", 13, "text", anchor="middle")

    box(652, 164, 304, 180, "AlphaLive", "EXECUTION · RISK", ["re-implements signals", "idempotent orders",
                                                              "circuit breakers"], T + 1.3, strong=True)
    # AlphaSignal input
    c.add(f'<g><path d="M804 392 V352" fill="none" stroke="{t["accent"]}" stroke-width="1.6" '
          f'stroke-dasharray="5 5"/><path d="M797 361 L804 351 L811 361" fill="none" stroke="{t["accent"]}" '
          f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
          f'<rect x="652" y="392" width="304" height="92" rx="12" fill="{t["chip"]}" stroke="{t["edge"]}" '
          f'stroke-width="1.3"/></g>')
    c.text(676, 426, "AlphaSignal", "serif", 23, "text")
    c.text(676, 450, "optional sentiment gate", "mono", 13, "muted")
    c.text(676, 470, "fail-open · BUY entries only", "mono", 13, "muted")
    # parity panel
    c.add(f'<g><rect x="44" y="392" width="560" height="92" rx="12" '
          f'fill="{mix(t["card"], t["accent"], .1)}" stroke="{t["edge"]}"/></g>')
    c.text(68, 420, "MEASURED PARITY · CI TEST", "mono5", 12, "accent", tracking=0.1)
    c.text(68, 450, "0 decision-bar mismatches", "serif", 24, "text")
    c.text(68, 472, "7 strategies · historical SPY/MSFT data", "mono", 13, "muted")
    return c


def small(t: dict, which: str) -> Card:
    if which == "jarvis":
        c = Card(490, 270, t, "Jarvis",
                 "Jarvis: a local-first macOS assistant with persistent memory that asks for confirmation "
                 "before any external action.")
        d = T_SMALL
        c.text(32, 48, "LOCAL-FIRST AI", "mono5", 12.5, "accent", tracking=0.12)
        c.text(30, 94, "Jarvis", "serif", 40, "text")
        c.text(32, 126, "macOS assistant with persistent memory", "sans", 19, "muted")
        c.add('<g>'
              + "".join(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{t["accent"]}" opacity="{o}"/>'
                        for x, y, o in ((42, 166, 1), (66, 158, .75), (60, 184, .55)))
              + f'<path d="M42 166 L66 158 L60 184 Z" fill="none" stroke="{t["accent"]}" opacity=".5"/></g>')
        c.text(90, 177, "memory stays on this Mac", "mono", 14, "text")
        c.add(f'<g><rect x="30" y="204" width="430" height="40" rx="9" '
              f'fill="{t["chip"]}" stroke="{t["edge"]}"/></g>')
        c.text(48, 229, "external action?", "mono", 14, "muted")
        c.text(444, 229, "confirm first →", "mono5", 14, "accent", anchor="end")
        if not STATIC:  # accent only: a copper ring pings once around the confirmation step
            c.css.append(".ping{transform-box:fill-box;transform-origin:50% 50%;animation:ping 1.2s ease-out both}"
                         "@keyframes ping{0%{opacity:0;transform:scale(.96)}30%{opacity:.9}"
                         "100%{opacity:0;transform:scale(1.04)}}")
            c.add(f'<rect class="ping" x="30" y="204" width="430" height="40" rx="9" fill="none" '
                  f'stroke="{t["accent2"]}" stroke-width="1.6" opacity="0"{anim(d + 0.6)}/>')
        return c
    c = Card(490, 270, t, "RunnasUp",
             "RunnasUp: running analytics with an explainable personal performance rating, drawn as a rising "
             "line. A working prototype checked on synthetic data only.")
    d = T_SMALL + 0.2
    c.text(32, 48, "RUNNING ANALYTICS", "mono5", 12.5, "accent", tracking=0.12)
    c.text(30, 94, "RunnasUp", "serif", 40, "text")
    c.text(32, 126, "explainable personal performance rating", "sans", 19, "muted")
    pts = [(34, 222), (80, 212), (122, 216), (168, 198), (212, 203), (256, 184), (302, 189), (348, 168),
           (392, 173), (452, 152)]
    c.add(f'<path d="M34 232 H456" stroke="{t["edge"]}"/>')
    line = "M" + " L".join(f"{x} {y}" for x, y in pts)
    c.add(f'<path d="{line}" fill="none" stroke="{mix(t["card"], t["accent"], .55)}" stroke-width="2.4" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    c.add(f'<path d="{line}" pathLength="1" class="draw" fill="none" stroke="{t["accent"]}" stroke-width="2.4" '
          f'stroke-linecap="round" stroke-linejoin="round"{anim(d + 0.4)}/>')
    c.add(f'<circle cx="452" cy="152" r="5" fill="{t["accent"]}"/>')
    c.text(456, 254, "prototype · synthetic data", "mono", 12, "muted", anchor="end")
    return c


# ---------------------------------------------------------------- README stats
README = ROOT / "README.md"
MARK_START, MARK_END = "<!-- stats:start -->", "<!-- stats:end -->"


def stats_markdown(s: dict) -> str:
    (by, bm), bcount = s["busiest_month"]
    bd, bdn, _ = s["busiest_day"]
    ls = s["longest_start"]
    longest = f"{s['longest']} days ({dfmt(ls)} – {dfmt(s['longest_end'])})" if ls else "0 days"
    return (f"{MARK_START}\n"
            f"Public contributions, {dfmt(s['start'])} – {dfmt(s['end'])}: **{s['total']:,} total** · "
            f"{s['active']} active days · current streak {s['current']} days · longest streak {longest} · "
            f"busiest day {dfmt(bd)} ({bdn}) · busiest month {calendar.month_name[bm]} {by} ({bcount}).\n"
            f"{MARK_END}")


def update_readme(s: dict) -> None:
    text = README.read_text()
    a, b = text.find(MARK_START), text.find(MARK_END)
    if a < 0 or b < a:
        raise SystemExit("README.md is missing the stats markers")
    new = text[:a] + stats_markdown(s) + text[b + len(MARK_END):]
    if new != text:
        README.write_text(new)


# ---------------------------------------------------------------- main
def main() -> int:
    s = load()
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = {
        "hero": lambda t: hero(t),
        "contributions": lambda t: heatmap(t, s),
        "monthly": lambda t: monthly(t, s),
        "tile-portfolio": lambda t: tile(t, s, 0),
        "tile-repositories": lambda t: tile(t, s, 1),
        "tile-linkedin": lambda t: tile(t, s, 2),
        "alpha-system": lambda t: alpha(t),
        "jarvis": lambda t: small(t, "jarvis"),
        "runnasup": lambda t: small(t, "runnasup"),
    }
    for name, fn in jobs.items():
        for theme, t in THEMES.items():
            path = OUT / f"{name}-{theme}.svg"
            svg = fn(t).svg()
            if not path.exists() or path.read_text() != svg:
                path.write_text(svg)
    if not STATIC:
        update_readme(s)
    print(f"rendered {len(jobs) * len(THEMES)} cards to {OUT.relative_to(ROOT) if OUT.is_relative_to(ROOT) else OUT}"
          f"{' (static)' if STATIC else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
