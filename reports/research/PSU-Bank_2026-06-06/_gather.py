"""Gather phase for the PSU-Bank investigation — driven by framework.batch.run_batch.

Per name: screener about + fundamentals (sourced) -> data/<sym>_*.json+csv,
price+volume+DMA chart (split-adjusted jugaad) -> charts/. Resumable via _tracker.json.
The agent (report writer) reads these outputs and assembles 00_report.md.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills/fundamentals/equity-research/scripts"))

from framework.batch import run_batch                       # noqa: E402
from framework.charts import price_volume_chart             # noqa: E402
from data.sources import JugaadData                         # noqa: E402
from screener_reader import (                               # noqa: E402
    fetch_company_about, fetch_company_fundamentals, fetch_company_signals,
    save_company_page_pdf,
)

HERE = Path(__file__).resolve().parent
SYMBOLS = ["SBIN", "BANKBARODA", "UNIONBANK", "CANBK", "PNB",
           "INDIANB", "BANKINDIA", "IOB", "MAHABANK", "UCOBANK"]   # top-10 PSU by mcap


def _write_table_csv(path: Path, table: dict) -> None:
    """A screener section table {'periods':[...], 'rows':{label:[floats]}} -> tidy CSV."""
    periods = table.get("periods") or []
    rows = table.get("rows") or {}
    if not rows:
        return
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["line_item", *periods])
        for label, vals in rows.items():
            w.writerow([label, *vals])


def gather(sym: str) -> str:
    about = fetch_company_about(sym, headless=True)
    fund = fetch_company_fundamentals(sym, headless=True)

    signals = fetch_company_signals(sym, headless=True)

    (HERE / "data" / f"{sym}_about.json").write_text(json.dumps(about, indent=2, default=str))
    (HERE / "data" / f"{sym}_fundamentals.json").write_text(json.dumps(fund, indent=2, default=str))
    (HERE / "data" / f"{sym}_signals.json").write_text(json.dumps(signals, indent=2, default=str))
    for tname, table in (fund.get("tables") or {}).items():
        if isinstance(table, dict):
            _write_table_csv(HERE / "data" / f"{sym}_{tname}.csv", table)

    # audit snapshot: whole screener page -> filings/<sym>_screener_page.pdf
    save_company_page_pdf(sym, HERE / "filings" / f"{sym}_screener_page.pdf", headless=True)

    # split-adjusted price+vol+DMA chart (>=1y lead-in for the 200-DMA)
    df = JugaadData().history(sym, date(2021, 1, 1), date.today(), adjust=True)
    if df is not None and not df.empty:
        if df.index.name != "date" and "date" in df.columns:
            df = df.set_index("date")
        df = df.sort_index()
        price_volume_chart(sym, df, HERE / "charts", since="2024-06-01")

    return f"data/{sym}_fundamentals.json"


if __name__ == "__main__":
    tr = run_batch(SYMBOLS, gather, HERE / "_tracker.json",
                   delay=4.0, jitter=2.0, max_retries=2, backoff=8.0)
    print("SUMMARY:", tr.summary())
