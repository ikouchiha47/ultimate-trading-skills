#!/usr/bin/env python3
"""Build a MkDocs Material site from reports/research/* — for GitHub Pages.

Generic: auto-discovers every report folder under reports/research/, publishes its narrative
(.md) + charts (.png) + downloadable data (csv/json/pdf), and SKIPS the code (driver scripts
`_*.py`, trackers `_*.json`/`*_tracker.json`, logs). Generates per-report index pages, a landing
page, and an mkdocs.yml with full nav. Re-run any time; it rebuilds docs/ from scratch.

    uv run python tools/build_pages.py          # assemble docs/ + mkdocs.yml
    uvx --with mkdocs-material mkdocs build      # render to site/   (or `mkdocs serve` to preview)
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "reports" / "research"
DOCS = ROOT / "docs"

# What NOT to publish: the executable pipeline (drivers, trackers, logs). Everything else
# (reports, charts, data, filings) is research output and ships.
def _skip(p: Path) -> bool:
    n = p.name
    if n.startswith("_"):                       # _gather.py, _tracker.json, _logs/, _strategies.py …
        return True
    if n.endswith((".pyc",)) or n == "__pycache__":
        return True
    if n.endswith("_tracker.json"):
        return True
    return False


def _title(folder: str) -> str:
    import re as _re
    m = _re.match(r"(.+)_(\d{4}-\d{2}-\d{2})$", folder)
    if m:
        return f"{m.group(1).replace('-', ' ')} — {m.group(2)}"   # "PSU Bank — 2026-06-06"
    return folder.replace("_", " ").replace("-", " ")


# Order the markdown reports sensibly: comprehensive, observations, industry, then per-name A-Z.
def _md_order(name: str) -> tuple:
    pri = {"00_comprehensive.md": 0, "00_industry.md": 1, "01_observations.md": 2,
           "GLOSSARY.md": 8, "references.md": 9}
    return (pri.get(name, 5), name)


_LABELS = {"00_comprehensive.md": "Overview (screener)", "00_industry.md": "Industry analysis",
           "01_observations.md": "Observations (buy/sell)", "GLOSSARY.md": "Glossary",
           "references.md": "References"}


def _page_label(name: str) -> str:
    if name in _LABELS:
        return _LABELS[name]
    if name.endswith("_equity_research.md"):
        return name.replace("_equity_research.md", "")
    return Path(name).stem.replace("_", " ")


def copy_report(folder: Path) -> dict:
    """Copy one report folder into docs/research/<folder>, skipping code. Return its md/asset lists."""
    dst = DOCS / "research" / folder.name
    dst.mkdir(parents=True, exist_ok=True)
    mds: list[str] = []
    for src in sorted(folder.rglob("*")):
        if src.is_dir() or _skip(src) or any(_skip(par) for par in src.relative_to(folder).parents):
            continue
        rel = src.relative_to(folder)
        if rel.parts[:2] == ("filings", "ar"):       # skip large full-text AR extraction dumps
            continue
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        if src.suffix == ".md":
            mds.append(str(rel))
    mds.sort(key=lambda m: _md_order(Path(m).name))
    return {"name": folder.name, "title": _title(folder.name), "mds": mds}


def write_report_index(rep: dict) -> None:
    dst = DOCS / "research" / rep["name"] / "index.md"
    lines = [f"# {rep['title']}\n", "Research report. Reports below; data/CSV, filings/PDF and "
             "charts are published alongside for audit.\n"]
    for m in rep["mds"]:
        if Path(m).name == "index.md":
            continue
        lines.append(f"- [{Path(m).stem.replace('_',' ')}]({m})")
    dst.write_text("\n".join(lines) + "\n")


def write_landing(reports: list[dict]) -> None:
    lines = ["# Systematic Trading Research\n",
             "India (NSE/BSE) sector & company research. Every figure is either **computed** by our "
             "scripts (split-adjusted prices, backtests vs a null) or a **dated sourced** disclosure; "
             "unsourceable items are marked `unknown`.\n", "## Reports\n"]
    for r in sorted(reports, key=lambda x: x["name"], reverse=True):
        lines.append(f"### [{r['title']}](research/{r['name']}/index.md)")
        for m in r["mds"][:3]:
            lines.append(f"- [{Path(m).stem.replace('_',' ')}](research/{r['name']}/{m})")
        lines.append("")
    (DOCS / "index.md").write_text("\n".join(lines) + "\n")


def write_mkdocs_yml(reports: list[dict]) -> None:
    nav = ["nav:", "  - Home: index.md"]
    for r in sorted(reports, key=lambda x: x["name"], reverse=True):
        nav.append(f"  - {r['title']}:")
        base = f"research/{r['name']}"
        top = [m for m in r["mds"] if "/" not in m and Path(m).name != "index.md"]  # nav = top-level only
        companies = [m for m in top if Path(m).name.endswith("_equity_research.md")]
        others = [m for m in top if m not in companies]
        for m in others:                                   # Overview, Industry, Observations, ...
            nav.append(f"      - {_page_label(Path(m).name)}: {base}/{m}")
        if companies:                                      # nest the per-company pages
            nav.append("      - Companies:")
            for m in sorted(companies):
                nav.append(f"          - {_page_label(Path(m).name)}: {base}/{m}")
    yml = f"""site_name: Systematic Trading Research
site_description: India sector & company research — computed + sourced, audit-first
theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      toggle: {{ icon: material/weather-night, name: Dark }}
    - scheme: slate
      primary: indigo
      toggle: {{ icon: material/weather-sunny, name: Light }}
  features: [navigation.sections, navigation.top, search.suggest, content.code.copy, toc.integrate]
markdown_extensions:
  - tables
  - admonition
  - pymdownx.superfences
  - toc: {{ permalink: true }}
plugins:
  - search
{chr(10).join(nav)}
"""
    (ROOT / "mkdocs.yml").write_text(yml)


def validate_no_code(root: Path) -> list[str]:
    """Fail-closed audit: return any code/driver/tracker/log files that slipped into `root`.
    The published site must contain ONLY research output (md/charts/data/pdf), never the pipeline."""
    bad: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        n = p.name
        if n.startswith("_") or n.endswith((".py", ".pyc", ".log")) or n.endswith("_tracker.json"):
            bad.append(str(p.relative_to(root)))
    return bad


def main() -> None:
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)
    reports = []
    for folder in sorted(p for p in RESEARCH.iterdir() if p.is_dir()):
        rep = copy_report(folder)
        if not rep["mds"]:
            continue
        write_report_index(rep)
        reports.append(rep)
    write_landing(reports)
    write_mkdocs_yml(reports)
    print(f"built docs/ for {len(reports)} report(s): {[r['name'] for r in reports]}")

    leaks = validate_no_code(DOCS)
    if leaks:
        print(f"FAIL: {len(leaks)} code/driver file(s) leaked into docs/: {leaks[:10]}")
        raise SystemExit(1)
    print("PASS: no code/driver/tracker/log files in docs/ (research output only)")
    print("preview: uvx --with mkdocs-material mkdocs serve")


if __name__ == "__main__":
    main()
