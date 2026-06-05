#!/usr/bin/env python3
"""Sector deep-dive orchestrator (India).

Pipeline (this script implements the QUANTITATIVE stages 1-3 + charts):

    1. resolve constituents        load_sector_constituents -> <sector>
    2. per-stock performance       per-symbol table: CAGR, drawdown, risk-adj (Calmar),
                                    20d return, avg delivery %, excess vs sector index
    3. sector-vs-market            sector NSE index vs NIFTY 50 relative strength
    5. charts (--report)           matplotlib PNGs: rel-strength, returns, drawdown
    --- next stages (kept separate, anchored to the numbers above) ---
    4. event overlay               mark RBI/policy dates on the timeline      (TODO)
    6. narrative pass              concall/news -> "who pivoted, who didn't"  (Claude)

Stages 4 and 6 are deliberately NOT in this script: stage 6 is causal/narrative and must
be done by Claude reading this script's verified numbers + the fundamentals/news skills —
never freestanding (see manuals/01, and CLAUDE.md conventions).

Usage:
    python3 sector_deep_dive.py "PSU Bank" --since 2020-01-01 --report
    python3 sector_deep_dive.py IT --since 2022-01-01 --price-source yfinance --json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from framework.india_sectors import (  # noqa: E402
    SECTOR_INDEX,
    compute_constituent_metrics,
    load_sector_constituents,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
BENCHMARK_INDEX = "NIFTY 50"


def _parse_since(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _history_fn(price_source: str):
    """Return a (symbol, start, end) -> normalized OHLCV callable for the chosen source."""
    if price_source == "jugaad":
        from data.sources import JugaadData
        return JugaadData().history          # adds delivery_pct (manuals/02)
    from data.sources import YFinanceSource
    return YFinanceSource().history          # faster, no delivery


def _index_series(index_name: str, start: date, end: date):
    """Close series for an NSE index, or None if unavailable."""
    try:
        from data.sources import NseIndexSource
        df = NseIndexSource().history(index_name, start, end)
        return df["close"].astype(float) if not df.empty else None
    except Exception:  # noqa: BLE001
        return None


def _window_return(s) -> float | None:
    return float(s.iloc[-1] / s.iloc[0] - 1) if s is not None and len(s) > 1 else None


def per_stock_table(symbols, since: date, price_source: str):
    """Stage 2 — per-symbol metric table with risk-adjusted (Calmar) ranking."""
    import numpy as np

    lookback = (date.today() - since).days
    m = compute_constituent_metrics(symbols, history_fn=_history_fn(price_source),
                                    lookback_days=lookback)
    if m.empty:
        return m
    # Calmar-style risk-adjusted return: annualized return per unit of max drawdown.
    m["calmar"] = m["cagr"] / m["max_drawdown"].abs().replace(0, np.nan)
    m = m.sort_values("calmar", ascending=False)
    m.insert(0, "rank", range(1, len(m) + 1))
    return m


def rel_strength(sector: str, since: date):
    """Stage 3 — sector index vs NIFTY 50 relative strength (normalized to 100)."""
    import pandas as pd

    end = date.today()
    idx_name = SECTOR_INDEX.get(sector)
    sec = _index_series(idx_name, since, end) if idx_name else None
    bench = _index_series(BENCHMARK_INDEX, since, end)
    out = {"sector_index": idx_name, "benchmark": BENCHMARK_INDEX,
           "sector_return": _window_return(sec), "benchmark_return": _window_return(bench),
           "series": None}
    if sec is not None and bench is not None:
        df = pd.concat([sec.rename("sector"), bench.rename("bench")], axis=1).dropna()
        if not df.empty:
            norm = df / df.iloc[0] * 100.0
            norm["rel"] = norm["sector"] / norm["bench"] * 100.0
            out["series"] = norm
            out["relative_strength_change_pct"] = round(float(norm["rel"].iloc[-1] - 100.0), 2)
    return out


def make_charts(sector: str, asof: str, table, rs) -> list[str]:
    """Stage 5 — PNGs to reports/sector-deep-dive/<sector>_<asof>/."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    outdir = REPO_ROOT / "reports" / "sector-deep-dive" / f"{sector.replace(' ', '_')}_{asof}"
    outdir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []

    if rs.get("series") is not None:
        s = rs["series"]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(s.index, s["sector"], label=rs["sector_index"])
        ax.plot(s.index, s["bench"], label=rs["benchmark"], alpha=0.8)
        ax.plot(s.index, s["rel"], label="relative strength", linestyle="--")
        ax.axhline(100, color="grey", lw=0.6)
        ax.set_title(f"{sector}: sector vs {rs['benchmark']} (rebased to 100)")
        ax.legend(); ax.set_ylabel("index (=100 at start)")
        p = outdir / "rel_strength.png"; fig.savefig(p, dpi=110, bbox_inches="tight"); plt.close(fig)
        paths.append(str(p))

    if not table.empty:
        for col, title, fname in [
            ("ret_window", f"{sector}: total return over window", "returns.png"),
            ("max_drawdown", f"{sector}: max drawdown", "drawdown.png"),
        ]:
            d = table.sort_values(col)
            fig, ax = plt.subplots(figsize=(10, max(3, 0.4 * len(d))))
            ax.barh(d.index, d[col] * 100)
            ax.set_title(title); ax.set_xlabel("%"); ax.axvline(0, color="grey", lw=0.6)
            p = outdir / fname; fig.savefig(p, dpi=110, bbox_inches="tight"); plt.close(fig)
            paths.append(str(p))
    return paths


def main():
    ap = argparse.ArgumentParser(description="India sector deep-dive (quant stages 1-3 + charts)")
    ap.add_argument("sector", help='sector key, e.g. "PSU Bank", IT, Pharma')
    ap.add_argument("--since", default=None, help="start date YYYY-MM-DD (default 5y ago)")
    ap.add_argument("--source", default="nse_csv", choices=["seed", "nse_fetch", "nse_csv"],
                    help="constituents source (default nse_csv = cached live)")
    ap.add_argument("--price-source", default="jugaad", choices=["jugaad", "yfinance"],
                    help="per-stock price source (jugaad adds delivery %)")
    ap.add_argument("--report", action="store_true", help="render charts to reports/")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    since = _parse_since(args.since) if args.since else date(date.today().year - 5, 1, 1)
    asof = str(date.today())

    # Stage 1 — constituents
    cmap = load_sector_constituents(source=args.source)
    if args.sector not in cmap:
        sys.exit(f"Unknown sector '{args.sector}'. Known: {', '.join(sorted(cmap))}")
    symbols = cmap[args.sector]
    print(f"[{args.sector}] {len(symbols)} constituents; since {since}; "
          f"prices={args.price_source}...", file=sys.stderr)

    # Stage 2 — per-stock table
    table = per_stock_table(symbols, since, args.price_source)
    # Stage 3 — sector vs market
    rs = rel_strength(args.sector, since)
    if not table.empty and rs.get("sector_return") is not None:
        table["excess_vs_sector"] = table["ret_window"] - rs["sector_return"]

    # Stage 5 — charts
    charts = make_charts(args.sector, asof, table, rs) if args.report else []

    result = {
        "sector": args.sector, "as_of": asof, "since": str(since),
        "n_constituents": len(symbols), "n_with_data": int(len(table)),
        "relative_strength": {k: v for k, v in rs.items() if k != "series"},
        "ranking": (table.reset_index().to_dict(orient="records") if not table.empty else []),
        "charts": charts,
        "next_stages": {
            "4_event_overlay": "TODO: mark RBI/policy dates on the timeline",
            "6_narrative": "Claude: read this JSON + fundamentals/news skills -> who pivoted, "
                           "anchored to these numbers (never freestanding).",
        },
    }

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return

    print(f"\n=== {args.sector} deep-dive — {asof} (since {since}) ===")
    r = result["relative_strength"]
    print(f"Sector {r.get('sector_index')} return: "
          f"{_fmt_pct(r.get('sector_return'))}  |  {r.get('benchmark')}: {_fmt_pct(r.get('benchmark_return'))}"
          f"  |  rel-strength Δ: {r.get('relative_strength_change_pct')}")
    if not table.empty:
        print("\nRank  Symbol         CAGR    MaxDD   Calmar  Ret(win)  ExcessVsSec  AvgDeliv%")
        for sym, row in table.iterrows():
            print(f"{int(row['rank']):>3}  {sym:14s} "
                  f"{_fmt_pct(row.get('cagr')):>7} {_fmt_pct(row.get('max_drawdown')):>7} "
                  f"{_num(row.get('calmar')):>6} {_fmt_pct(row.get('ret_window')):>8} "
                  f"{_fmt_pct(row.get('excess_vs_sector')):>11} {_num(row.get('avg_delivery_pct')):>8}")
    if charts:
        print("\nCharts:")
        for c in charts:
            print(f"  {c}")
    print("\nNext: stage 4 (event overlay) + stage 6 (narrative — Claude reads the above).")


def _fmt_pct(x):
    try:
        return f"{x*100:.1f}%" if x is not None and x == x else "—"
    except (TypeError, ValueError):
        return "—"


def _num(x):
    try:
        return f"{x:.2f}" if x is not None and x == x else "—"
    except (TypeError, ValueError):
        return "—"


if __name__ == "__main__":
    main()
