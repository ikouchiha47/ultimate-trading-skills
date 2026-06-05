#!/usr/bin/env python3
"""India uptrend / breadth-health analyzer — PORT of the US uptrend-analyzer.

Separate skill from sector-analyst, but shares the sector/uptrend math in
framework/india_sectors.py (no duplicated data code). Produces the same
0-100 composite breadth-health score from 5 components:

    1. Market Breadth (overall)   30%
    2. Sector Participation       25%
    3. Sector Rotation            15%
    4. Momentum                   20%
    5. Historical Context         10%

Usage:
    python3 uptrend_india.py [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from framework.india_sectors import (  # noqa: E402
    CYCLICAL_SECTORS,
    DEFENSIVE_SECTORS,
    compute_sector_data,
)

WEIGHTS = {"breadth": 0.30, "participation": 0.25, "rotation": 0.15, "momentum": 0.20, "historical": 0.10}
HISTORY_CACHE = Path(__file__).resolve().parents[4] / "data" / "uptrend_history.csv"


def _signal(score: float) -> str:
    return "healthy" if score >= 65 else "weak" if score < 40 else "mixed"


def c_breadth(sectors):
    avg = sum(s.ratio for s in sectors) / len(sectors)
    return {"score": round(avg * 100, 1), "signal": _signal(avg * 100), "avg_ratio": round(avg, 3)}


def c_participation(sectors):
    # how many sectors are broadly participating (ratio > 0.5)
    part = sum(1 for s in sectors if s.ratio > 0.5) / len(sectors)
    return {"score": round(part * 100, 1), "signal": _signal(part * 100), "participating": round(part, 3)}


def c_rotation(sectors):
    # healthy when cyclicals lead defensives (risk-on rotation)
    m = {s.sector: s.ratio for s in sectors}
    cyc = sum(m[s] for s in CYCLICAL_SECTORS if s in m) / max(1, len([s for s in CYCLICAL_SECTORS if s in m]))
    dfn = sum(m[s] for s in DEFENSIVE_SECTORS if s in m) / max(1, len([s for s in DEFENSIVE_SECTORS if s in m]))
    score = min(100, max(0, 50 + (cyc - dfn) * 100))
    return {"score": round(score, 1), "signal": _signal(score), "cyc_minus_def": round(cyc - dfn, 3)}


def c_momentum(sectors):
    moms = [s.momentum_20d for s in sectors if s.momentum_20d is not None]
    if not moms:
        return {"score": 50.0, "signal": "mixed", "note": "no momentum data"}
    pos = sum(1 for m in moms if m > 0) / len(moms)
    return {"score": round(pos * 100, 1), "signal": _signal(pos * 100), "pct_positive_20d": round(pos, 3)}


def c_historical(avg_ratio: float):
    """Percentile of today's avg ratio vs cached history. Neutral 50 if <20 samples."""
    today = str(date.today())
    hist: list[float] = []
    if HISTORY_CACHE.exists():
        for line in HISTORY_CACHE.read_text().splitlines()[1:]:
            try:
                hist.append(float(line.split(",")[1]))
            except (IndexError, ValueError):
                continue
    # append today (idempotent-ish: dedupe by date)
    HISTORY_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY_CACHE.exists():
        HISTORY_CACHE.write_text("date,avg_ratio\n")
    if today not in HISTORY_CACHE.read_text():
        with HISTORY_CACHE.open("a") as fh:
            fh.write(f"{today},{avg_ratio:.4f}\n")
    if len(hist) < 20:
        return {"score": 50.0, "signal": "mixed", "note": f"only {len(hist)} samples; need 20+"}
    pct = sum(1 for h in hist if h < avg_ratio) / len(hist)
    return {"score": round(pct * 100, 1), "signal": _signal(pct * 100), "percentile": round(pct, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--source", default="seed", choices=["seed", "nse_csv"],
                    help="sector→constituents source; seed=hardcoded fallback, "
                         "nse_csv=manually-downloaded NSE CSVs in data/constituents/")
    args = ap.parse_args()
    print(f"Computing India breadth-health (source={args.source})...", file=sys.stderr)
    sectors = compute_sector_data(source=args.source)
    avg_ratio = sum(s.ratio for s in sectors) / len(sectors)

    comps = {
        "breadth": c_breadth(sectors),
        "participation": c_participation(sectors),
        "rotation": c_rotation(sectors),
        "momentum": c_momentum(sectors),
        "historical": c_historical(avg_ratio),
    }
    composite = round(sum(comps[k]["score"] * w for k, w in WEIGHTS.items()), 1)
    result = {"as_of": str(date.today()), "composite_score": composite,
              "signal": _signal(composite), "components": comps}

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n=== India Breadth Health — {result['as_of']} ===")
        print(f"Composite: {composite}/100  ({result['signal']})\n")
        for k, w in WEIGHTS.items():
            c = comps[k]
            print(f"  {k:14s} {c['score']:>5}/100  (w={int(w*100)}%)  {c['signal']}")


if __name__ == "__main__":
    main()
