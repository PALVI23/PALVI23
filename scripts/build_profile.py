#!/usr/bin/env python3
"""Render the deep-blue profile README panels as SVG.

GitHub READMEs cannot set a page background, so every section of the profile
is drawn as an SVG panel with its own deep-blue background. Stats are fetched
from the GitHub GraphQL API (needs GITHUB_TOKEN) and baked into body.svg.

Usage:
  python scripts/build_profile.py            # live data (GITHUB_TOKEN required)
  python scripts/build_profile.py --offline  # no API call, stats shown as "—"
"""
import base64
import datetime as dt
import json
import math
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

USER = "PALVI23"
ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "panels"
ICONS = json.loads((HERE / "icons.json").read_text())

W = 1000
FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Arial, sans-serif"

# palette
BG_TOP = "#0a1f55"
BG_BOT = "#0a1f55"  # flat: panels must match where they meet
CARD = "#0b2257"
CARD2 = "#0e2b6b"
BORDER = "#2f7bff"
BORDER_SOFT = "#2557b8"
ACCENT = "#4fb3ff"
TEXT = "#eaf2ff"
MUTED = "#b9cdf2"
DIM = "#7f98cc"
LANG_COLORS = ["#f7d84a", "#3b8bff", "#a66bff", "#e07ce8", "#7d8cad"]


# --------------------------------------------------------------------------- helpers
def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()


def text_w(s, size, bold=False):
    """Rough text width estimate for layout (Segoe UI-ish metrics)."""
    narrow = set("iljtfr.,:;|!'I ")
    wide = set("mwMW@")
    w = 0.0
    for ch in s:
        if ch in narrow:
            w += 0.32
        elif ch in wide:
            w += 0.85
        elif ch.isupper() or ch.isdigit():
            w += 0.64
        else:
            w += 0.53
    return w * size * (1.06 if bold else 1.0)


def defs():
    return f"""
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOT}"/>
    </linearGradient>
    <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{CARD2}"/><stop offset="1" stop-color="{CARD}"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#5cc2ff"/><stop offset="0.5" stop-color="{BORDER}"/><stop offset="1" stop-color="#5cc2ff"/>
    </linearGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{BORDER}" stop-opacity="0.9"/><stop offset="1" stop-color="{BORDER}" stop-opacity="0.05"/>
    </linearGradient>
    <linearGradient id="sparkle" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#9fe0ff"/><stop offset="1" stop-color="#2f8bff"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="softglow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="6"/>
    </filter>
  </defs>"""


def svg(h, body, rounded="none"):
    """Wrap a panel. rounded: none | top | bottom | all."""
    r = 18
    if rounded == "top":
        shape = f'<path d="M0 {r} Q0 0 {r} 0 H{W - r} Q{W} 0 {W} {r} V{h} H0 Z" fill="url(#bg)"/>'
    elif rounded == "bottom":
        shape = f'<path d="M0 0 H{W} V{h - r} Q{W} {h} {W - r} {h} H{r} Q0 {h} 0 {h - r} Z" fill="url(#bg)"/>'
    elif rounded == "all":
        shape = f'<rect width="{W}" height="{h}" rx="{r}" fill="url(#bg)"/>'
    else:
        shape = f'<rect width="{W}" height="{h}" fill="url(#bg)"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="{FONT}">{defs()}\n{shape}\n{body}\n</svg>\n')


def sparkle(x, y, s=9, fill="url(#sparkle)"):
    return (f'<path transform="translate({x} {y})" fill="{fill}" filter="url(#glow)" '
            f'd="M0 {-s} C{s*.15} {-s*.15} {s*.15} {-s*.15} {s} 0 C{s*.15} {s*.15} {s*.15} {s*.15} 0 {s} '
            f'C{-s*.15} {s*.15} {-s*.15} {s*.15} {-s} 0 C{-s*.15} {-s*.15} {-s*.15} {-s*.15} 0 {-s} Z"/>')


def heading(x, y, title, deco="sparkle", rule_w=None):
    tw = text_w(title, 25, bold=True)
    out = [f'<text x="{x}" y="{y}" font-size="25" font-weight="700" fill="{TEXT}">{escape(title)}</text>']
    dx = x + tw + 18
    if deco == "sparkle":
        out.append(sparkle(dx, y - 9))
    elif deco == "leaf":
        out.append(f'<g transform="translate({dx - 10} {y - 22})" fill="none" stroke="{ACCENT}" stroke-width="2.2" stroke-linecap="round" filter="url(#glow)">'
                   '<path d="M10 22 C10 14 4 10 1 9"/><path d="M10 22 C10 13 16 8 20 7"/><path d="M10 22 C9 12 11 5 12 0"/>'
                   '<path d="M10 22 C6 18 3 18 0 18"/><path d="M10 22 C14 18 18 18 21 17"/></g>')
    elif deco == "bars":
        out.append(f'<g transform="translate({dx - 9} {y - 20})" fill="{ACCENT}" filter="url(#glow)">'
                   '<rect x="0" y="9" width="4" height="11" rx="1"/><rect x="6" y="4" width="4" height="16" rx="1"/>'
                   '<rect x="12" y="0" width="4" height="20" rx="1"/><rect x="18" y="6" width="4" height="14" rx="1"/></g>')
    rw = rule_w if rule_w else W - 2 * x
    out.append(f'<rect x="{x}" y="{y + 14}" width="{rw}" height="1.5" fill="url(#rule)"/>')
    return "\n".join(out)


def card(x, y, w, h, r=14):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#card)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="{BORDER}" stroke-width="6" opacity=".18" filter="url(#softglow)"/>'
            f'<rect x="{x + .75}" y="{y + .75}" width="{w - 1.5}" height="{h - 1.5}" rx="{r}" fill="none" stroke="url(#edge)" stroke-width="1.5"/>')


def icon(name, x, y, size, fill):
    s = size / 24
    return f'<path transform="translate({x} {y}) scale({s})" fill="{fill}" d="{ICONS[name]}"/>'


def fmt(n):
    return "—" if n is None else f"{n:,}"


# --------------------------------------------------------------------------- data
GQL = "https://api.github.com/graphql"


def gql(token, query, variables):
    req = urllib.request.Request(GQL, data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme-builder"})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.load(r)
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    return res["data"]


def fetch(token):
    q = """query($login:String!){ user(login:$login){
      name login createdAt location
      followers{totalCount}
      publicRepos: repositories(privacy:PUBLIC){totalCount}
      pullRequests{totalCount}
      issues{totalCount}
      repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,REPOSITORY]){totalCount}
      repositories(ownerAffiliations:OWNER, isFork:false, first:100){ nodes{
        stargazerCount
        languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{name} } } } }
    } }"""
    u = gql(token, q, {"login": USER})["user"]
    yq = """query($login:String!,$from:DateTime!,$to:DateTime!){ user(login:$login){
      contributionsCollection(from:$from,to:$to){
        totalCommitContributions restrictedContributionsCount totalPullRequestReviewContributions
        contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }"""
    created = dt.datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    days, commits, reviews = {}, 0, 0
    start = created
    while start < now:
        end = min(start + dt.timedelta(days=365), now)
        c = gql(token, yq, {"login": USER, "from": start.isoformat(), "to": end.isoformat()})["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        reviews += c["totalPullRequestReviewContributions"]
        for wk in c["contributionCalendar"]["weeks"]:
            for d in wk["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
        start = end
    langs = {}
    stars = 0
    for r in u["repositories"]["nodes"]:
        stars += r["stargazerCount"]
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return {
        "name": u["name"] or u["login"], "login": u["login"], "joined": created.year,
        "location": u["location"] or "", "followers": u["followers"]["totalCount"],
        "repos": u["publicRepos"]["totalCount"], "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"], "contributed": u["repositoriesContributedTo"]["totalCount"],
        "stars": stars, "commits": commits, "reviews": reviews, "days": days, "langs": langs,
    }


def streaks(days):
    today = dt.date.today()
    seq = sorted((dt.date.fromisoformat(k), v) for k, v in days.items() if dt.date.fromisoformat(k) <= today)
    longest = run = 0
    for _, v in seq:
        run = run + 1 if v > 0 else 0
        longest = max(longest, run)
    cur = 0
    i = len(seq) - 1
    if i >= 0 and seq[i][1] == 0:  # today without contributions doesn't break the streak
        i -= 1
    while i >= 0 and seq[i][1] > 0:
        cur += 1
        i -= 1
    return cur, longest, sum(v for _, v in seq)


def rank(d):
    """Same scoring as github-readme-stats (all-commits mode)."""
    exp = lambda x: 1 - 2 ** -x
    logn = lambda x: x / (1 + x)
    parts = [(2, exp(d["commits"] / 1000)), (3, exp(d["prs"] / 50)), (1, exp(d["issues"] / 25)),
             (1, exp(d["reviews"] / 2)), (4, logn(d["stars"] / 50)), (1, logn(d["followers"] / 10))]
    pct = (1 - sum(w * v for w, v in parts) / sum(w for w, _ in parts)) * 100
    for t, lvl in zip([1, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100], ["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C"]):
        if pct <= t:
            return lvl, pct
    return "C", pct


# --------------------------------------------------------------------------- panels
def header_panel():
    h = 438
    bx, by, bw = 22, 22, W - 44
    bh = round(bw * 533 / 1600)
    body = f"""
<clipPath id="bclip"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="14"/></clipPath>
<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="14" fill="none" stroke="{BORDER}" stroke-width="10" opacity=".25" filter="url(#softglow)"/>
<image x="{bx}" y="{by}" width="{bw}" height="{bh}" clip-path="url(#bclip)" preserveAspectRatio="xMidYMid slice" href="data:image/webp;base64,{b64(HERE / 'banner-embed.webp')}"/>
<rect x="{bx + .75}" y="{by + .75}" width="{bw - 1.5}" height="{bh - 1.5}" rx="14" fill="none" stroke="url(#edge)" stroke-width="1.5" opacity=".8"/>
{heading(30, by + bh + 58, "Connect with me.", deco="leaf")}"""
    return svg(h, body, rounded="top")


BUTTONS = [  # (file, label, icon, icon colour, image width)
    ("btn-linkedin", "LinkedIn", "linkedin", "#ffffff", 175),
    ("btn-github", "GitHub", "github", "#ffffff", 145),
    ("btn-kaggle", "Kaggle", "kaggle", "#20beff", 145),
    ("btn-portfolio", "Portfolio", "link", "#ffffff", 160),
]


def button_panel(label, ic, colour, w, first):
    h = 78
    x0 = 30 if first else 12
    bw = w - x0 - 4
    by, bh = 14, 46
    if ic == "kaggle":
        glyph = f'<text x="{x0 + 20}" y="{by + 33}" font-size="27" font-weight="800" fill="{colour}" filter="url(#glow)">k</text>'
    elif ic == "link":
        glyph = (f'<g transform="translate({x0 + 18} {by + 12})" fill="none" stroke="{colour}" stroke-width="2.4" stroke-linecap="round">'
                 '<path d="M9.5 12.5 a4.5 4.5 0 0 0 6.4 0 l3.2 -3.2 a4.5 4.5 0 0 0 -6.4 -6.4 l-1.6 1.6"/>'
                 '<path d="M12.5 9.5 a4.5 4.5 0 0 0 -6.4 0 l-3.2 3.2 a4.5 4.5 0 0 0 6.4 6.4 l1.6 -1.6"/></g>')
    else:
        glyph = icon(ic, x0 + 18, by + 12, 22, colour)
    tx = x0 + 18 + 22 + 12
    body = f"""
{card(x0, by, bw, bh, r=10)}
{glyph}
<text x="{tx}" y="{by + 30}" font-size="18" font-weight="600" fill="{TEXT}">{escape(label)}</text>"""
    return svg(h, body).replace(f'width="{W}" height="{h}" viewBox="0 0 {W} {h}"',
                                f'width="{w}" height="{h}" viewBox="0 0 {w} {h}"').replace(
        f'<rect width="{W}" height="{h}" fill="url(#bg)"/>',
        f'<rect width="{w}" height="{h}" fill="{BG_TOP}"/><rect width="{w}" height="{h}" fill="url(#bg)" opacity="0"/>')


def filler_panel(w):
    h = 78
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="{BG_TOP}"/></svg>\n')


def bullet_icon(kind, x, y):
    g = f'<g transform="translate({x} {y})" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)">'
    paths = {
        "code": '<path d="M7 5 L1 11 L7 17"/><path d="M15 5 L21 11 L15 17"/><path d="M12.5 3 L9.5 19"/>',
        "layers": '<path d="M11 2 L21 7 L11 12 L1 7 Z"/><path d="M1 11 L11 16 L21 11"/><path d="M1 15 L11 20 L21 15"/>',
        "book": '<path d="M11 5 C8 3 4 3 1 4 V18 C4 17 8 17 11 19 C14 17 18 17 21 18 V4 C18 3 14 3 11 5 Z"/><path d="M11 5 V19"/>',
        "target": '<circle cx="11" cy="11" r="9.5"/><circle cx="11" cy="11" r="5.5"/><circle cx="11" cy="11" r="1.6" fill="' + ACCENT + '"/><path d="M11 11 L20 2"/><path d="M16 2 H20 V6"/>',
    }
    return g + paths[kind] + "</g>"


def stack_pills(y):
    items = [("Python", "python", "#ffd43b"), ("SQL", "db", "#4fa3ff"), ("PyTorch", "pytorch", "#ee4c2c"),
             ("scikit-learn", "scikitlearn", "#f7931e"), ("Pandas", "pandas", "#d6e4ff"),
             ("AWS", "amazonwebservices", "#ff9900"), ("Streamlit", "streamlit", "#ff4b4b"),
             ("Vertex AI", "googlecloud", "#6ea8ff")]
    widths = [text_w(t, 14.5) + 54 for t, _, _ in items]
    gap = (W - 60 - sum(widths)) / (len(items) - 1)
    out, x = [], 30.0
    for (label, ic, col), w in zip(items, widths):
        out.append(card(round(x, 1), y, round(w, 1), 44, r=10))
        if ic == "db":
            out.append(f'<g transform="translate({x + 15:.1f} {y + 10})" fill="{col}">'
                       '<ellipse cx="10" cy="4" rx="9" ry="3.6"/><path d="M1 6.5 C1 9 19 9 19 6.5 V11 C19 13.5 1 13.5 1 11 Z"/>'
                       '<path d="M1 13.5 C1 16 19 16 19 13.5 V18 C19 20.5 1 20.5 1 18 Z"/></g>')
        else:
            out.append(icon(ic, round(x + 14, 1), y + 11, 22, col))
        out.append(f'<text x="{x + 44:.1f}" y="{y + 27.5}" font-size="14.5" font-weight="500" fill="{TEXT}">{escape(label)}</text>')
        x += w + gap
    return "\n".join(out)


def tile(x, y, w, h, kind, value, label):
    cx = x + w / 2
    icons = {
        "github": icon("github", cx - 16, y + 20, 32, "#ffffff"),
        "fire": (f'<g transform="translate({cx - 14} {y + 18})" filter="url(#glow)"><path fill="#ff9f2e" d="M14 0 C16 7 26 11 26 22 C26 30 20 36 14 36 C7 36 2 30 2 23 C2 16 7 13 8 7 C10 11 11 13 13 14 C14 9 13 5 14 0 Z"/>'
                 f'<path fill="#ffd25a" d="M14 16 C15 21 20 23 20 28 C20 32 17 35 14 35 C10 35 8 32 8 29 C8 25 11 24 12 20 C13 22 13 22 14 23 Z"/></g>'),
        "trophy": (f'<g transform="translate({cx - 17} {y + 18})" fill="none" stroke="#ffc93c" stroke-width="2.6" stroke-linejoin="round" filter="url(#glow)">'
                   '<path d="M9 2 H25 V12 C25 18 21 22 17 22 C13 22 9 18 9 12 Z" fill="#ffc93c" fill-opacity=".25"/>'
                   '<path d="M9 5 H3 C3 11 6 14 9.5 14"/><path d="M25 5 H31 C31 11 28 14 24.5 14"/>'
                   '<path d="M17 22 V28"/><path d="M11 33 H23 L21 28 H13 Z" fill="#ffc93c" fill-opacity=".25"/></g>'),
    }
    return (card(x, y, w, h) + icons[kind] +
            f'<text x="{cx}" y="{y + 98}" text-anchor="middle" font-size="36" font-weight="700" fill="{TEXT}">{escape(value)}</text>'
            f'<text x="{cx}" y="{y + 128}" text-anchor="middle" font-size="16" fill="{MUTED}">{escape(label)}</text>')


def small_icon(kind, x, y, col=ACCENT):
    g = f'<g transform="translate({x} {y})" fill="none" stroke="{col}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    p = {
        "star": '<path d="M8 1 L10.1 5.6 L15 6.1 L11.3 9.4 L12.4 14.3 L8 11.8 L3.6 14.3 L4.7 9.4 L1 6.1 L5.9 5.6 Z"/>',
        "clock": '<circle cx="8" cy="8" r="6.8"/><path d="M8 4 V8 L10.6 9.6"/>',
        "pr": '<circle cx="4" cy="3" r="2"/><circle cx="4" cy="13" r="2"/><circle cx="12" cy="13" r="2"/><path d="M4 5 V11"/><path d="M12 11 V6 C12 4 11 3 9 3 H7"/><path d="M8.5 1.5 L7 3 L8.5 4.5"/>',
        "issue": '<circle cx="8" cy="8" r="6.8"/><circle cx="8" cy="8" r="1.4" fill="' + col + '"/>',
        "book": '<path d="M3 2 H13 V14 H4.5 C3.7 14 3 13.3 3 12.5 Z"/><path d="M3 12.5 C3 11.7 3.7 11 4.5 11 H13"/>',
        "repo": '<path d="M8 1 L14 4.5 V11.5 L8 15 L2 11.5 V4.5 Z"/><path d="M2 4.5 L8 8 L14 4.5"/><path d="M8 8 V15"/>',
        "pin": '<path d="M8 15 C8 15 13 9.8 13 6.2 A5 5 0 0 0 3 6.2 C3 9.8 8 15 8 15 Z"/><circle cx="8" cy="6.2" r="1.8"/>',
    }[kind]
    return g + p + "</g>"


def stats_card(x, y, w, h, d):
    rows = [("star", "Total Stars Earned:", d.get("stars")), ("clock", "Total Commits:", d.get("commits")),
            ("pr", "Total PRs:", d.get("prs")), ("issue", "Total Issues:", d.get("issues")),
            ("book", "Contributed to:", d.get("contributed"))]
    out = [card(x, y, w, h)]
    out.append(f'<text x="{x + 30}" y="{y + 32}" font-size="19" font-weight="700" fill="{TEXT}">GitHub Stats</text>')
    out.append(f'<g transform="translate({x + 30 + text_w("GitHub Stats", 19, True) + 12} {y + 18})" fill="#3ddc84">'
               '<rect x="0" y="10" width="3.5" height="6" rx="1"/><rect x="5" y="6" width="3.5" height="10" rx="1"/>'
               '<rect x="10" y="2" width="3.5" height="14" rx="1"/><rect x="15" y="0" width="3.5" height="16" rx="1"/></g>')
    for i, (ic, label, val) in enumerate(rows):
        ry = y + 62 + i * 20
        out.append(small_icon(ic, x + 30, ry - 12, "#3ddc84"))
        out.append(f'<text x="{x + 56}" y="{ry}" font-size="14" fill="{MUTED}">{label}</text>')
        out.append(f'<text x="{x + 205}" y="{ry}" font-size="14" font-weight="600" fill="{TEXT}">{fmt(val)}</text>')
    # grade ring
    gx, gy, r = x + w - 78, y + h / 2, 44
    grade, pct = d.get("grade", ("—", 100))
    frac = max(0.06, min(1.0, 1 - pct / 100)) if grade != "—" else 0
    circ = 2 * math.pi * r
    out.append(f'<circle cx="{gx}" cy="{gy}" r="{r}" fill="none" stroke="{ACCENT}" stroke-opacity=".18" stroke-width="7"/>')
    if frac:
        out.append(f'<circle cx="{gx}" cy="{gy}" r="{r}" fill="none" stroke="{ACCENT}" stroke-width="7" stroke-linecap="round" '
                   f'stroke-dasharray="{circ * frac:.1f} {circ:.1f}" transform="rotate(-90 {gx} {gy})" filter="url(#glow)"/>')
    out.append(f'<text x="{gx}" y="{gy + 11}" text-anchor="middle" font-size="32" font-weight="800" fill="{TEXT}">{escape(grade)}</text>')
    return "\n".join(out)


def langs_card(x, y, w, h, langs):
    out = [card(x, y, w, h)]
    out.append(f'<g transform="translate({x + 26} {y + 22})" fill="none" stroke="{ACCENT}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
               '<path d="M6 3 L1 9 L6 15"/><path d="M15 3 L20 9 L15 15"/><path d="M12 1 L9 17"/></g>')
    out.append(f'<text x="{x + 58}" y="{y + 38}" font-size="18" font-weight="700" fill="{TEXT}">Most Used Languages.</text>')
    total = sum(langs.values())
    items = sorted(langs.items(), key=lambda kv: -kv[1])
    top = items[:4]
    rest = sum(v for _, v in items[4:])
    if rest:
        top.append(("Others", rest))
    bx, by, bw = x + 26, y + 58, w - 52
    out.append(f'<clipPath id="barclip"><rect x="{bx}" y="{by}" width="{bw}" height="12" rx="6"/></clipPath>')
    out.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="12" rx="6" fill="{CARD2}"/>')
    cx = bx
    for i, (name, v) in enumerate(top):
        seg = bw * v / total if total else 0
        out.append(f'<rect clip-path="url(#barclip)" x="{cx:.1f}" y="{by}" width="{seg + .5:.1f}" height="12" fill="{LANG_COLORS[i]}"/>')
        cx += seg
    if not top:
        out.append(f'<text x="{bx}" y="{by + 44}" font-size="14" fill="{DIM}">Updates automatically from your repositories.</text>')
    for i, (name, v) in enumerate(top):
        ly = by + 40 + i * 21
        out.append(f'<circle cx="{bx + 7}" cy="{ly - 5}" r="5.5" fill="{LANG_COLORS[i]}"/>')
        out.append(f'<text x="{bx + 22}" y="{ly}" font-size="14" fill="{MUTED}">{escape(name)}  <tspan fill="{TEXT}" font-weight="600">{100 * v / total:.1f}%</tspan></text>')
    return "\n".join(out)


def smooth_path(pts):
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def profile_card(x, y, w, h, d):
    out = [card(x, y, w, h)]
    out.append(f'<text x="{x + 26}" y="{y + 38}" font-size="18" font-weight="600" fill="{TEXT}">{escape(d["login"])} ({escape(d["name"])})</text>')
    rows = [("github", f'{fmt(d.get("total"))} Contributions'), ("repo", f'{fmt(d.get("repos"))} Public Repositories'),
            ("star", f'Joined GitHub in {d.get("joined") or "—"}'), ("pin", d.get("location") or "Bangalore, India")]
    for i, (ic, label) in enumerate(rows):
        ry = y + 72 + i * 24
        if ic == "github":
            out.append(icon("github", x + 26, ry - 13, 16, MUTED))
        else:
            out.append(small_icon(ic, x + 26, ry - 13, MUTED))
        out.append(f'<text x="{x + 52}" y="{ry}" font-size="14.5" fill="{MUTED}">{escape(label)}</text>')
    # contribution area chart (last 52 weeks, weekly totals)
    gx0, gx1, gy0, gy1 = x + 250, x + w - 14, y + 50, y + h - 22
    days = d.get("days") or {}
    today = dt.date.today()
    weeks = []
    for k in range(52, 0, -1):
        s = 0
        for j in range(7):
            s += days.get((today - dt.timedelta(days=7 * k - j)).isoformat(), 0)
        weeks.append(s)
    # light smoothing so it reads as a soft wave
    for _ in range(3):  # repeated moving average -> soft rolling hills
        weeks = [sum(weeks[max(0, i - 2):i + 3]) / len(weeks[max(0, i - 2):i + 3]) for i in range(len(weeks))]
    sm = weeks[::2] + [weeks[-1]]
    peak = max(sm) or 1
    pts = [(gx0 + (gx1 - gx0) * i / (len(sm) - 1), gy1 - (gy1 - gy0) * v / peak * 0.95) for i, v in enumerate(sm)]
    line = smooth_path(pts)
    out.append(f'<linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b8bff" stop-opacity=".75"/>'
               f'<stop offset="1" stop-color="#1a5cff" stop-opacity="0.05"/></linearGradient>')
    out.append(f'<path d="{line} L{gx1:.1f} {gy1} L{gx0:.1f} {gy1} Z" fill="url(#area)"/>')
    out.append(f'<path d="{line}" fill="none" stroke="#6fc3ff" stroke-width="2.2" filter="url(#glow)"/>')
    return "\n".join(out)


def body_panel(d):
    orb = b64(HERE / "orb-embed.webp")
    o = []
    # ---- About
    o.append(f"""<radialGradient id="orbfade" cx="0.5" cy="0.5" r="0.5"><stop offset="0.62" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
<mask id="orbmask"><rect x="650" y="0" width="350" height="330" fill="url(#orbfade)"/></mask>
<image x="672" y="-12" width="330" height="330" mask="url(#orbmask)" href="data:image/webp;base64,{orb}"/>""")
    o.append(heading(30, 44, "About Me.", rule_w=600))
    para = ["I'm an AI Engineer with a background in Computer Science and Engineering,",
            "interested in designing and building practical AI solutions. My work and",
            "learning span machine learning, generative AI, data engineering, and",
            "intelligent applications."]
    for i, line in enumerate(para):
        o.append(f'<text x="30" y="{92 + i * 25}" font-size="17" fill="{MUTED}">{escape(line)}</text>')
    bullets = [("code", "Building AI/ML and GenAI applications."),
               ("layers", "Working with data, models, and real-world use cases."),
               ("book", "Exploring research-driven ideas and advanced AI methods."),
               ("target", "Currently preparing for a Master's in Data Science &amp; Artificial Intelligence (Germany).")]
    for i, (ic, t) in enumerate(bullets):
        by = 210 + i * 30
        o.append(bullet_icon(ic, 32, by - 16))
        o.append(f'<text x="68" y="{by}" font-size="16.5" fill="{TEXT}">{t}</text>')
    # ---- Technical stack
    o.append(heading(30, 372, "Technical Stack."))
    o.append(stack_pills(404))
    # ---- GitHub stats
    o.append(heading(30, 506, "GitHub Stats.", deco="bars"))
    ty, th, tw, tg = 536, 150, 168, 14
    o.append(tile(30, ty, tw, th, "github", fmt(d.get("total")), "Total Contributions"))
    o.append(tile(30 + tw + tg, ty, tw, th, "fire", fmt(d.get("current")), "Current Streak"))
    o.append(tile(30 + 2 * (tw + tg), ty, tw, th, "trophy", fmt(d.get("longest")), "Longest Streak"))
    sx = 30 + 3 * (tw + tg)
    o.append(stats_card(sx, ty, W - 30 - sx, th, d))
    ry, rh = ty + th + 18, 206
    o.append(langs_card(30, ry, 370, rh, d.get("langs") or {}))
    o.append(profile_card(418, ry, W - 30 - 418, rh, d))
    # ---- footer wave
    fy = ry + rh + 20
    o.append(f"""<linearGradient id="wave" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1a5cff" stop-opacity="0"/><stop offset=".5" stop-color="#5cc2ff"/><stop offset="1" stop-color="#1a5cff" stop-opacity="0"/></linearGradient>
<g fill="none" stroke="url(#wave)" filter="url(#glow)">
  <path stroke-width="2.4" d="M0 {fy + 45} C 200 {fy + 10} 400 {fy + 75} 600 {fy + 40} S 1000 {fy + 10} 1000 {fy + 45}"><animate attributeName="d" dur="8s" repeatCount="indefinite" values="M0 {fy + 45} C 200 {fy + 10} 400 {fy + 75} 600 {fy + 40} S 1000 {fy + 10} 1000 {fy + 45};M0 {fy + 40} C 200 {fy + 70} 400 {fy + 15} 600 {fy + 45} S 1000 {fy + 70} 1000 {fy + 40};M0 {fy + 45} C 200 {fy + 10} 400 {fy + 75} 600 {fy + 40} S 1000 {fy + 10} 1000 {fy + 45}"/></path>
  <path stroke-width="1.4" opacity=".6" d="M0 {fy + 58} C 250 {fy + 28} 450 {fy + 82} 650 {fy + 52} S 1000 {fy + 30} 1000 {fy + 58}"/>
  <path stroke-width="1" opacity=".4" d="M0 {fy + 36} C 300 {fy + 62} 500 {fy + 14} 700 {fy + 38} S 1000 {fy + 60} 1000 {fy + 32}"/>
</g>""")
    return svg(fy + 96, "\n".join(o), rounded="bottom")


# --------------------------------------------------------------------------- main
def main():
    offline = "--offline" in sys.argv
    sample = "--sample" in sys.argv  # local preview only, never committed
    d = {"login": USER, "name": "Palvisha Changkakati", "location": "Bangalore, India"}
    if sample:
        import random
        random.seed(3)
        today = dt.date.today()
        days = {(today - dt.timedelta(days=i)).isoformat(): (random.choice([0, 1, 2, 3, 5]) if i > 14 else 2) for i in range(400)}
        d.update(stars=12, commits=300, prs=20, issues=5, contributed=8, followers=3, reviews=1, repos=10, joined=2024,
                 days=days, langs={"Python": 615, "SQL": 168, "HTML": 92, "CSS": 63, "Jupyter Notebook": 40, "Shell": 22})
    elif not offline:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            sys.exit("GITHUB_TOKEN not set (use --offline to render without stats)")
        d.update(fetch(token))
    if d.get("days"):
        d["current"], d["longest"], d["total"] = streaks(d["days"])
        d["grade"] = rank(d)
    OUT.mkdir(parents=True, exist_ok=True)
    files = {"header.svg": header_panel(), "body.svg": body_panel(d)}
    for i, (name, label, ic, col, w) in enumerate(BUTTONS):
        files[f"{name}.svg"] = button_panel(label, ic, col, w, first=(i == 0))
    files["btn-filler.svg"] = filler_panel(W - sum(b[4] for b in BUTTONS))
    for name, content in files.items():
        (OUT / name).write_text(content)
    print("wrote", ", ".join(sorted(files)), "->", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
