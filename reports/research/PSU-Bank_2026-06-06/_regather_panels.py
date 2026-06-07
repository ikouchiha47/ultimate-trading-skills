"""Re-gather the FULL screener About/Key-Points panel (READ MORE) + corporate-actions
tabs for the 9 non-CANBK banks, whose about.json was only the short blurb.

Leaves fundamentals/CSVs untouched (they already tally with _digest_all10.json).
Resumable via _regather_tracker.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills/fundamentals/equity-research/scripts"))

from framework.batch import run_batch              # noqa: E402
from screener_reader import (                      # noqa: E402
    fetch_company_about, fetch_company_signals,
)

HERE = Path(__file__).resolve().parent
SYMBOLS = ["SBIN", "BANKBARODA", "UNIONBANK", "PNB",
           "INDIANB", "BANKINDIA", "IOB", "MAHABANK", "UCOBANK"]  # CANBK already full


def regather(sym: str) -> str:
    about = fetch_company_about(sym, headless=True)
    (HERE / "data" / f"{sym}_about.json").write_text(
        json.dumps(about, indent=2, default=str))

    signals = fetch_company_signals(sym, headless=True)
    (HERE / "data" / f"{sym}_signals.json").write_text(
        json.dumps(signals, indent=2, default=str))

    kp = len(json.dumps(about.get("key_points") or ""))
    ca = len(signals.get("corporate_actions") or {})
    return f"{sym}: key_points={kp}b corp_action_tabs={ca}"


if __name__ == "__main__":
    tr = run_batch(SYMBOLS, regather, HERE / "_regather_tracker.json",
                   delay=4.0, jitter=2.0, max_retries=2, backoff=8.0)
    print("SUMMARY:", tr.summary())
