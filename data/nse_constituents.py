"""Fetch LIVE NSE sector constituents from niftyindices.com (the authoritative source).

Layered for robustness (the host 403s / empties intermittently):
  1. requests.Session with browser headers + a homepage cookie-warmup, with retries.
  2. Playwright headless (real browser) as fallback — install with the `scrape` extra
     then `playwright install chromium`.

Verified 2026-06: the plain header path works for all 11 sectoral indices. Playwright is
there for the days it doesn't. Fetched lists are cached to data/constituents/<Sector>.csv
in NSE's native format, so a successful fetch also doubles as the manual-download artifact
(reproducible / committable — see data/constituents/README.md).
"""

from __future__ import annotations

import time
from pathlib import Path

CONSTITUENTS_DIR = Path(__file__).resolve().parent / "constituents"

# sector key -> niftyindices CSV slug (resolved & verified against live endpoints).
NIFTY_CSV_SLUG: dict[str, str] = {
    "PSU Bank": "niftypsubank",
    "Private Bank": "nifty_privatebank",
    "Financial Services": "niftyfinance",
    "Auto": "niftyauto",
    "IT": "niftyit",
    "Pharma": "niftypharma",
    "FMCG": "niftyfmcg",
    "Metal": "niftymetal",
    "Energy": "niftyenergy",
    "Realty": "niftyrealty",
    "Infra": "niftyinfra",
}

_BASE = "https://www.niftyindices.com/IndexConstituent/ind_{slug}list.csv"
_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "text/csv,application/csv,*/*",
    "Referer": "https://www.niftyindices.com/",
    "Accept-Language": "en-US,en;q=0.9",
}


def _looks_like_csv(text: str) -> bool:
    return bool(text) and "Symbol" in text[:120]


def _fetch_requests(slug: str, retries: int = 3, backoff: float = 1.5) -> str | None:
    """Primary path: cookie-warmed Session + browser headers, with retries."""
    import requests

    sess = requests.Session()
    sess.headers.update(_HEADERS)
    try:  # warm up cookies from the homepage (helps the CSV host trust us)
        sess.get("https://www.niftyindices.com/", timeout=20)
    except Exception:  # noqa: BLE001
        pass
    url = _BASE.format(slug=slug)
    for attempt in range(retries):
        try:
            r = sess.get(url, timeout=25)
            if r.status_code == 200 and _looks_like_csv(r.text):
                return r.text
        except Exception:  # noqa: BLE001
            pass
        time.sleep(backoff * (attempt + 1))
    return None


def _fetch_playwright(slug: str) -> str | None:
    """Fallback path: real headless browser. Needs `playwright install chromium`."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    url = _BASE.format(slug=slug)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=_HEADERS["User-Agent"])
            page = ctx.new_page()
            # Optional cookie warmup — the homepage is slow and may time out; that's fine,
            # the same-context CSV request below still succeeds, so don't let it abort us.
            try:
                page.goto("https://www.niftyindices.com/", wait_until="domcontentloaded", timeout=15000)
            except Exception:  # noqa: BLE001
                pass
            resp = page.request.get(url, timeout=30000)
            text = resp.text() if resp.ok else None
            browser.close()
            return text if (text and _looks_like_csv(text)) else None
    except Exception:  # noqa: BLE001
        return None


def _symbols_from_csv_text(text: str) -> list[str]:
    import csv
    import io
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return []
    key = next((k for k in rows[0] if k and k.strip().lower() == "symbol"), None)
    return [r[key].strip() for r in rows if key and r.get(key) and r[key].strip()]


def fetch_sector_constituents(
    sectors: list[str] | None = None,
    *,
    cache_dir: Path = CONSTITUENTS_DIR,
    use_playwright_fallback: bool = True,
    write_cache: bool = True,
) -> dict[str, list[str]]:
    """Fetch live constituents for the given sectors (default: all known).

    Returns {sector: [symbols]} for sectors that fetched successfully (missing ones are
    simply absent — the caller layers SEED_SECTORS underneath). On success, writes the raw
    NSE CSV to cache_dir/<Sector>.csv so it's reusable offline and via source='nse_csv'.
    """
    targets = sectors or list(NIFTY_CSV_SLUG)
    out: dict[str, list[str]] = {}
    if write_cache:
        cache_dir.mkdir(parents=True, exist_ok=True)
    for sector in targets:
        slug = NIFTY_CSV_SLUG.get(sector)
        if not slug:
            continue
        text = _fetch_requests(slug)
        if text is None and use_playwright_fallback:
            text = _fetch_playwright(slug)
        if text is None:
            continue
        syms = _symbols_from_csv_text(text)
        if not syms:
            continue
        out[sector] = syms
        if write_cache:
            (cache_dir / f"{sector}.csv").write_text(text)
    return out


if __name__ == "__main__":  # quick manual check
    m = fetch_sector_constituents()
    for sec in NIFTY_CSV_SLUG:
        got = m.get(sec)
        print(f"{sec:20s} {'%2d syms' % len(got) if got else 'FAILED':>8}")
