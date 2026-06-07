"""Background batch: download + extract each top-10 PSU bank's latest annual report (FY2025,
the latest COMPLETE AR) into filings/ar/. Resumable via _ar_tracker.json. The agent then greps
the extracted text for the segment / business-ratio note (loan-book exposure) per bank.

AR URLs come from each bank's already-gathered _signals.json (screener Documents -> annual_reports).
We take the FY2025 entry (FY2026 may be a partial/just-filed AR; FY2025 is the full audited one).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                  # .../ultimate-trading-skills (repo root)
sys.path.insert(0, str(ROOT))
from framework.batch import run_batch  # noqa: E402

SYMBOLS = ["SBIN", "BANKBARODA", "UNIONBANK", "CANBK", "PNB",
           "INDIANB", "BANKINDIA", "IOB", "MAHABANK", "UCOBANK"]
READER = str(ROOT / "skills/fundamentals/equity-research/scripts/annual_report_reader.py")


def _ar_url(sym: str, year_label: str = "Financial Year 2025") -> str | None:
    sig = json.loads((HERE / "data" / f"{sym}_signals.json").read_text())
    for ar in sig.get("annual_reports", []):
        if year_label in ar["text"]:
            return ar["url"]
    # fallback: first annual report link
    ars = sig.get("annual_reports", [])
    return ars[0]["url"] if ars else None


def fetch_ar(sym: str) -> str:
    url = _ar_url(sym)
    if not url:
        raise RuntimeError("no annual-report URL in signals")
    out = HERE / "filings" / "ar" / f"{sym}_AR2025.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["uv", "run", "--extra", "data", "--extra", "scrape", "python", READER,
         "--url", url, "--year", "2025", "--output", str(out)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=400)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"reader failed: {r.stderr[-300:]}")
    return f"filings/ar/{sym}_AR2025.json"


if __name__ == "__main__":
    tr = run_batch(SYMBOLS, fetch_ar, HERE / "_ar_tracker.json",
                   delay=5.0, jitter=3.0, max_retries=1, backoff=15.0)
    print("AR SUMMARY:", tr.summary())
