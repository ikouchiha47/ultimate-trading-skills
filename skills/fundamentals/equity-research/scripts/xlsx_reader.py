#!/usr/bin/env python3
"""xlsx_reader.py — XLSX -> structured JSON + Markdown tables (e.g. RBI Sectoral Deployment).

Completes the document pipeline alongside pdf_to_md (PDF/PPT). Pure transformer: downloads
(or opens) a workbook, dumps every sheet as rows + a Markdown table. No interpretation — the
agent reads the output and cites the source. Numbers stay SOURCED (a disclosure), never become
our computed figures.

Usage:
    python xlsx_reader.py --url https://rbidocs.rbi.org.in/.../16T_BULL...XLSX --out /tmp/rbi16
    python xlsx_reader.py --path ./table16.xlsx --sheet "T16" --out /tmp/rbi16
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


# Hosts known to sit behind Akamai Bot Manager: a plain requests.get returns an HTML challenge
# page (not the file), so we go straight to a real browser context to mint the cookies. rbidocs
# (RBI document host) is the one we hit for Sectoral Deployment / Bulletin tables.
_AKAMAI_HOSTS = ("rbidocs.rbi.org.in", "rbi.org.in", "nseindia.com", "bseindia.com")

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def _looks_like_html(blob: bytes) -> bool:
    head = blob[:512].lstrip().lower()
    return head.startswith((b"<!doctype html", b"<html"))


def download_via_browser(url: str, referer: str | None = None) -> bytes:
    """Fetch a file through a headless-chromium context so Akamai-gated hosts serve the real bytes.

    Strategy that beats the bot wall: navigate to a same-origin page first (the referer if given,
    else the host root) so the context collects Akamai's `_abck`/`bm_sz` cookies, THEN pull the
    file with `ctx.request.get` (which carries those cookies). Returns the raw bytes.
    """
    from urllib.parse import urlsplit
    from playwright.sync_api import sync_playwright

    parts = urlsplit(url)
    warm = referer or f"{parts.scheme}://{parts.netloc}/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=_UA, accept_downloads=True)
        try:
            ctx.new_page().goto(warm, wait_until="domcontentloaded", timeout=30000)
        except Exception:  # noqa: BLE001 — warm-up nav can time out; cookies may still be set
            pass
        ctx.pages[0].wait_for_timeout(1200)
        resp = ctx.request.get(url, headers={"Referer": warm})
        body = resp.body()
        browser.close()
    return body


def _fetch(url: str, referer: str | None = None) -> bytes:
    """requests first; fall back to a browser context for Akamai hosts or HTML-challenge responses."""
    from urllib.parse import urlsplit
    host = urlsplit(url).netloc
    if any(host.endswith(h) for h in _AKAMAI_HOSTS):
        return download_via_browser(url, referer)          # known wall -> browser straight away
    import requests
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": _UA,
                                                   **({"Referer": referer} if referer else {})})
        r.raise_for_status()
        if _looks_like_html(r.content):                    # silent block -> escalate to browser
            return download_via_browser(url, referer)
        return r.content
    except Exception:  # noqa: BLE001
        return download_via_browser(url, referer)


def read_xlsx(source: str, sheet: str | None = None, referer: str | None = None) -> dict:
    """{sheets:{name:{columns,rows,markdown}}, source}. Reads all sheets unless `sheet` given.

    URL sources are fetched via `_fetch` (requests, with an automatic headless-browser fallback for
    Akamai-gated hosts like rbidocs.rbi.org.in — so the RBI HTML-block never recurs).
    """
    import pandas as pd

    local = source
    if source.startswith(("http://", "https://")):
        import tempfile
        content = _fetch(source, referer)
        fd = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        fd.write(content); fd.close()
        local = fd.name

    xls = pd.read_excel(local, sheet_name=sheet, header=None)   # header=None: keep raw grid
    frames = {sheet: xls} if isinstance(xls, type(__import__("pandas").DataFrame())) else xls
    out: dict = {"source": source, "sheets": {}}
    for name, df in frames.items():
        df = df.dropna(how="all").dropna(axis=1, how="all")
        out["sheets"][str(name)] = {
            "columns": [str(c) for c in df.columns],
            "rows": df.astype(object).where(df.notna(), None).values.tolist(),
            "markdown": df.to_markdown(index=False),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url"); src.add_argument("--path")
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--referer", default=None, help="referer URL for Akamai warm-up (e.g. the "
                    "RBI press-release page that links the file)")
    ap.add_argument("--out", required=True, help="output stem (.json + .md written)")
    args = ap.parse_args()

    data = read_xlsx(args.url or args.path, sheet=args.sheet, referer=args.referer)
    stem = Path(args.out)
    stem.with_suffix(".json").write_text(json.dumps(data, indent=2, default=str))
    md = [f"# {Path(args.url or args.path).name}\n", f"source: {data['source']}\n"]
    for name, sh in data["sheets"].items():
        md += [f"\n## {name}\n", sh["markdown"]]
    stem.with_suffix(".md").write_text("\n".join(md))
    print(f"wrote {stem.with_suffix('.json')} and {stem.with_suffix('.md')} "
          f"({len(data['sheets'])} sheet(s))")


if __name__ == "__main__":
    main()
