#!/usr/bin/env python3
"""Renders the 2x2 showcase cards (4 core crates + 4 core skills) for the profile README.

Design system: Kirky "Ink on Paper" (resume-web .maliang/DESIGN.md).
- D-P1-1  dual neutral palette: ink #141414 / paper #F8F8F8, no naive inversion
- D-P1-2  zero colored accents on the UI layer; accent = ink/paper inversion
- D-P1-4  color is allowed ONLY inside image assets -> the download sparkline is the
          single colored element and lives inside the SVG (image channel), matching the
          GitHub contribution-snake semantics. Everything else stays ink/paper.
- key_effects: ghost-watermark (brand sanctioned), used as domain motif / name glyph.
Exemption record (ai-tells SS0): mono digits = tabular data; ghost marks = brand
identity, not decorative numbering; 2x2 grid = user-directed.

Runs locally and in CI (ubuntu-latest). Skill release versions come from `gh api`
when available, otherwise the version suffix is omitted. Secrets are never involved.
"""

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

DIST = Path(__file__).resolve().parent.parent / "dist"

W, H = 400, 210
PAD = 28

# D-P1-1 tokens
INK = dict(bg="#141414", border="#2A2A2A", text="#ECECEA", sub="#A8A8A4", fog="#8A8A86", ghost="#ECECEA")
PAPER = dict(bg="#F8F8F8", border="#E4E4E4", text="#222222", sub="#565656", fog="#7B7B7B", ghost="#222222")
# Data greens: GitHub contribution ramps (dark ramp on ink cards, deep ramp on paper for >=3:1)
GREENS_INK = ["#0E4429", "#006D32", "#26A641", "#39D353"]
GREENS_PAPER = ["#01311F", "#034525", "#0F6D31", "#0F8A3C"]

SANS = "ui-sans-serif, system-ui, 'Segoe UI', 'Helvetica Neue', 'Noto Sans SC', sans-serif"
MONO = "ui-monospace, 'Cascadia Mono', Menlo, Consolas, monospace"
CJK = "'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif"

UA = "kirky-profile-readme (github.com/Kirky-X)"

PROJECTS = [
    dict(name="oxcache", focus=("Multi-level cache, usage kept simple.",
                                "Single-flight and SWR stop stampedes by default."),
         motif="layers"),
    dict(name="trait-kit", focus=("Trait assembly boilerplate, removed.",
                                  "Typestate validation and a service registry, no heavy DI."),
         motif="nodes"),
    dict(name="confers", focus=("Layered configuration, merge pitfalls solved.",
                                "Derive-based, hot reload with canary rollout."),
         motif="merge"),
    dict(name="inklog", focus=("Async logging that keeps your macros.",
                               "PII redaction, rotation, backpressure, audit chain."),
         motif="streams"),
]
SKILLS = [
    dict(name="maliang", cn="马良", glyph="马", repo="maliang",
         focus=("Frontend design generation.",
                "DESIGN.md to design tokens to cross-platform code.")),
    dict(name="tiangang", cn="天罡", glyph="罡", repo="tiangang",
         focus=("SAST security scanning.",
                "Semgrep plus language-specific scanners with CI gates.")),
    dict(name="diting", cn="谛听", glyph="谛", repo="diting",
         focus=("Code quality review.",
                "Dimensional review, decay diagnosis, simplification.")),
    dict(name="kueiku", cn="鬼谷子", glyph="谷", repo="kueiku",
         focus=("Methodology navigation compass.",
                "Routes each task to the right framework across 19 categories.")),
]


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def fetch_crate_data():
    """downloads + last-10 version downloads (chronological) per core crate."""
    data = {}
    for p in PROJECTS:
        c = http_json(f"https://crates.io/api/v1/crates/{p['name']}")["crate"]
        vers = http_json(f"https://crates.io/api/v1/crates/{p['name']}/versions")["versions"]
        vers = sorted(vers, key=lambda v: v["created_at"])[-10:]
        data[p["name"]] = dict(downloads=c["downloads"], spark=[v["downloads"] for v in vers])
    return data


def fetch_skill_versions():
    """latest release tag per skill repo via gh; empty string on any failure."""
    tags = {}
    for s in SKILLS:
        try:
            out = subprocess.run(
                ["gh", "api", f"repos/Kirky-X/{s['repo']}/releases/latest", "--jq", ".tag_name"],
                capture_output=True, text=True, timeout=15)
            tags[s["name"]] = out.stdout.strip().lstrip("v") if out.returncode == 0 else ""
        except Exception:
            tags[s["name"]] = ""
    return tags


def fmt(n):
    return f"{n:,}"


def motif(name, color, ox, oy):
    """Brand-sanctioned ghost-watermark: domain geometry per crate, right side, ~6% ink."""
    g = f'<g fill="none" stroke="{color}" stroke-width="3" opacity="0.07">'
    if name == "layers":  # multi-level cache: stacked strata
        for i, w in enumerate((96, 78, 60)):
            g += f'<rect x="{ox + i * 9}" y="{oy + i * 20}" width="{w}" height="14" rx="4"/>'
    elif name == "nodes":  # capability registry: assembled nodes
        pts = [(36, 10), (96, 22), (18, 62), (78, 74)]
        for i in range(len(pts) - 1):
            g += f'<line x1="{ox + pts[i][0]}" y1="{oy + pts[i][1]}" x2="{ox + pts[i + 1][0]}" y2="{oy + pts[i + 1][1]}"/>'
        for x, y in pts:
            g += f'<circle cx="{ox + x}" cy="{oy + y}" r="7" fill="{color}" stroke="none"/>'
    elif name == "merge":  # config layers merging into one chain
        g += f'<path d="M{ox} {oy} v26 q0 14 14 14 h58"/>'
        g += f'<path d="M{ox + 34} {oy - 14} v40 q0 14 14 14 h24"/>'
        g += f'<path d="M{ox + 68} {oy - 28} v54 q0 14 14 14 h4"/>'
    elif name == "streams":  # log streams with backpressure
        for i, w in enumerate((104, 82, 92, 64)):
            g += f'<line x1="{ox}" y1="{oy + i * 18}" x2="{ox + w}" y2="{oy + i * 18}" stroke-linecap="round"/>'
    return g + "</g>"


def sparkline(values, greens, x, base_y, max_h=64, bw=12, gap=5):
    if not values:
        return ""
    vmax = max(values) or 1
    out = []
    for i, v in enumerate(values):
        h = max(4, round(v / vmax * max_h))
        # ramp position: higher bar -> deeper step of the contribution ramp
        step = min(3, int(v / vmax * 4))
        out.append(f'<rect x="{x + i * (bw + gap)}" y="{base_y - h}" width="{bw}" height="{h}" '
                   f'rx="3" fill="{greens[step]}"/>')
    return "<g>" + "".join(out) + "</g>"


def text(x, y, s, size, fill, weight=400, family=SANS, spacing=None):
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}"{sp}>{s}</text>')


def card_project(p, d, variant):
    name = p["name"]
    t = INK if variant == "ink" else PAPER
    greens = GREENS_INK if variant == "ink" else GREENS_PAPER
    m = motif(p["motif"], t["ghost"], 268, 26)
    spark = sparkline(d["spark"], greens, 200, 182)
    label = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" role="img" '
        f'aria-label="{name}, {fmt(d["downloads"])} downloads. {p["focus"][0]} {p["focus"][1]}">'
        f'<rect width="{W}" height="{H}" rx="16" fill="{t["bg"]}"/>'
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="15.5" fill="none" stroke="{t["border"]}"/>'
        + m
        + text(PAD, 48, name, 21, t["text"], 700)
        + text(PAD, 76, p["focus"][0], 12.5, t["sub"])
        + text(PAD, 94, p["focus"][1], 12.5, t["sub"])
        + text(PAD, 172, fmt(d["downloads"]), 26, t["text"], 600, MONO)
        + text(PAD, 190, "downloads", 10.5, t["fog"])
        + spark
        + "</svg>"
    )
    return label


def card_skill(s, version, variant):
    t = INK if variant == "ink" else PAPER
    ver = f" · v{version}" if version else ""
    lic = text(PAD, 172, f"MIT{ver}", 13, t["sub"], 500, MONO)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" role="img" '
        f'aria-label="{s["name"]} ({s["cn"]}). {s["focus"][0]} {s["focus"][1]}">'
        f'<rect width="{W}" height="{H}" rx="16" fill="{t["bg"]}"/>'
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="15.5" fill="none" stroke="{t["border"]}"/>'
        f'<text x="330" y="170" font-family="{CJK}" font-size="120" font-weight="500" '
        f'fill="{t["ghost"]}" opacity="0.06" text-anchor="middle">{s["glyph"]}</text>'
        + text(PAD, 48, s["name"], 21, t["text"], 700)
        + text(PAD + 118, 47, s["cn"], 15, t["fog"], 500, CJK)
        + text(PAD, 76, s["focus"][0], 12.5, t["sub"])
        + text(PAD, 94, s["focus"][1], 12.5, t["sub"])
        + lic
        + "</svg>"
    )


def inner(card_svg):
    """strip outer <svg> wrapper -> inner group for the contact sheet."""
    return card_svg[card_svg.index(">") + 1: card_svg.rindex("</svg>")]


def main():
    DIST.mkdir(exist_ok=True)
    crates = fetch_crate_data()
    tags = fetch_skill_versions()

    files = {}
    for p in PROJECTS:
        files[f"card-p-{p['name']}.svg"] = card_project(p, crates[p["name"]], "ink" if p["name"] in ("oxcache", "inklog") else "paper")
    for s in SKILLS:
        files[f"card-s-{s['name']}.svg"] = card_skill(s, tags[s["name"]], "paper" if s["name"] in ("maliang", "kueiku") else "ink")
    for fn, svg in files.items():
        (DIST / fn).write_text(svg, encoding="utf-8")
        print(f"wrote {fn}")

    # contact sheet for visual self-check (not shipped)
    cells, x, y = [], 0, 0
    for i, (fn, svg) in enumerate(files.items()):
        x = (i % 2) * (W + 20)
        y = (i // 2) * (H + 20)
        cells.append(f'<g transform="translate({x},{y})">{inner(svg)}</g>')
    sheet = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * 2 + 20}" height="{(H + 20) * 4}" '
             f'fill="#888888"><rect width="100%" height="100%" fill="#888888"/>' + "".join(cells) + "</svg>")
    (DIST / "_contact.svg").write_text(sheet, encoding="utf-8")
    print("wrote _contact.svg")


if __name__ == "__main__":
    sys.exit(main())
