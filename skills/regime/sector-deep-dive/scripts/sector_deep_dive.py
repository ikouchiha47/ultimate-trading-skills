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
    """Close series for an NSE index via the seam (nselib, Akamai-free), or None."""
    try:
        from framework import data_api
        df = data_api.index(index_name, since=start, until=end)
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


def make_charts(sector: str, asof: str, table, rs, events: list[dict] | None = None) -> list[str]:
    """Stage 5 — PNGs to reports/sector-deep-dive/<sector>_<asof>/ (with stage-4 event overlay)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

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
        for ev in (events or []):   # Stage 4 — RBI/policy event overlay
            try:
                x = pd.Timestamp(ev["date"])
            except Exception:  # noqa: BLE001
                continue
            ax.axvline(x, color="#cf222e", lw=0.8, alpha=0.5)
            ax.text(x, ax.get_ylim()[1], ev.get("label", "")[:18], rotation=90,
                    fontsize=6, va="top", color="#cf222e")
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


def policy_events(since: date, end: date) -> list[dict]:
    """Stage 4 — RBI/policy events in the window, from an EDITABLE data file (agent-extendable).

    Reads data/events/policy.csv (columns: date,label,kind). The agent appends dated, SOURCED
    events (from news()/WebSearch) — the script never invents events. Returns those in-window.
    """
    import csv
    f = REPO_ROOT / "data" / "events" / "policy.csv"
    if not f.exists():
        return []
    out = []
    with f.open(newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                d = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue
            if since <= d <= end:
                out.append({"date": str(d), "label": row.get("label", "").strip(),
                            "kind": row.get("kind", "").strip()})
    return sorted(out, key=lambda e: e["date"])


def causal_scaffold(sector: str, since: date) -> dict:
    """Stage 6 INPUTS (not the narrative) — the influence-graph causes for this sector + a news
    directive. The AGENT writes the narrative from: measured inflections (stages 2-3) + these
    validated causes + dated news() + fundamentals. Never freestanding (manuals/01, /12)."""
    scaffold: dict = {"drivers": [], "bellwethers": [], "news_directive": None}
    try:
        from framework.influence_graph import build_sector_graph, company_sector_graph
        nodes, edges = build_sector_graph(sector, since=str(since), with_constituents=False)
        scaffold["drivers"] = [
            {"driver": e.src, "verdict": e.verdict, "corr0": e.corr0, "lead_lag": e.lead_lag}
            for e in edges]
        bells = company_sector_graph(sector, since=str(since))[:5]
        scaffold["bellwethers"] = [{"symbol": e.src, "corr0": e.corr0, "verdict": e.verdict}
                                   for e in bells]
    except Exception as exc:  # noqa: BLE001
        scaffold["error"] = str(exc)[:120]
    try:
        from framework import data_api
        d = data_api.news(f"{sector} sector RBI policy regulation", since=str(since))
        scaffold["news_directive"] = getattr(d, "suggested_query", None)
    except Exception:  # noqa: BLE001
        pass
    return scaffold


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

    # Stage 4 — policy events in window (editable data file; agent-sourced)
    events = policy_events(since, date.today())
    # Stage 5 — charts (with event overlay)
    charts = make_charts(args.sector, asof, table, rs, events) if args.report else []
    # Stage 6 — causal scaffold (influence-graph causes + news directive; agent writes narrative)
    scaffold = causal_scaffold(args.sector, since)

    result = {
        "sector": args.sector, "as_of": asof, "since": str(since),
        "n_constituents": len(symbols), "n_with_data": int(len(table)),
        "relative_strength": {k: v for k, v in rs.items() if k != "series"},
        "ranking": (table.reset_index().to_dict(orient="records") if not table.empty else []),
        "charts": charts,
        "stage4_events": events,
        "stage6_scaffold": scaffold,
        "stage6_instructions": ("AGENT writes the narrative ONLY from: the measured inflections "
                                "(ranking + rel-strength), the validated drivers/bellwethers in "
                                "stage6_scaffold, the dated events, and sourced news() — never "
                                "from memory (manuals/01)."),
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
        print("\nRank  Symbol         CAGR    MaxDD   Calmar  Up  25dmaZ   VolX  Deliv%  Absorp")
        for sym, row in table.iterrows():
            up = "↑" if row.get("uptrend") else "·"
            print(f"{int(row['rank']):>3}  {sym:14s} "
                  f"{_fmt_pct(row.get('cagr')):>7} {_fmt_pct(row.get('max_drawdown')):>7} "
                  f"{_num(row.get('calmar')):>6}  {up:>2}  {_num(row.get('dist_25dma_z')):>6} "
                  f"{_num(row.get('vol_ratio')):>6} {_num(row.get('delivery_recent')):>7} "
                  f"{_num(row.get('absorption')):>7}")
        print("(25dmaZ << 0 = stretched below 25-DMA = BNF dip; but price ALONE is a trap-finder. "
              "Fade only when VolX (volume spike) + Deliv% (real owners) + Absorp (0..1, buyer "
              "soaking up supply) confirm flow-driven absorption, not an information-driven knife "
              "— manuals/02,/03.)")
    if events:
        print("\nStage 4 — policy events in window:")
        for ev in events:
            print(f"  {ev['date']}  {ev.get('kind',''):10s} {ev.get('label','')}")
    if charts:
        print("\nCharts:")
        for c in charts:
            print(f"  {c}")
    sc = result.get("stage6_scaffold", {})
    if sc.get("drivers") or sc.get("bellwethers"):
        print("\nStage 6 scaffold (causes — AGENT writes the narrative anchored to these):")
        for d in sc.get("drivers", []):
            print(f"  driver {d['driver']:>8}: {d['verdict']}")
        if sc.get("bellwethers"):
            print("  bellwethers: " + ", ".join(b["symbol"] for b in sc["bellwethers"]))
        if sc.get("news_directive"):
            print(f"  news -> run WebSearch: {sc['news_directive']!r} (cite dated, sourced)")


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
