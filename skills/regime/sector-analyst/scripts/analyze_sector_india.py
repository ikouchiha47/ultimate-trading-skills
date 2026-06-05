#!/usr/bin/env python3
"""India sector rotation analysis — PORT of the US sector-analyst.

The US version fetched a pre-computed sector_summary.csv. No such feed exists for
India, so the sector/uptrend math lives in framework/india_sectors.py (shared with
uptrend-analyzer). This script adds the rotation / cyclical-vs-defensive / cycle-phase
logic on top.

Usage:
    python3 analyze_sector_india.py [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# repo root on path so we can import the shared sector engine
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from framework.india_sectors import (  # noqa: E402
    CYCLICAL_SECTORS,
    DEFENSIVE_SECTORS,
    COMMODITY_SECTORS,
    compute_sector_data,
)

# Cycle phases (India): which sectors lead/lag. Mirrors the Bandhan business-cycle table.
CYCLE_PHASES = {
    "early": {"leaders": ["PSU Bank", "Private Bank", "Auto", "Realty"], "laggards": ["IT", "FMCG", "Pharma"]},
    "mid": {"leaders": ["Financial Services", "Auto", "Infra", "Metal"], "laggards": ["FMCG", "Pharma"]},
    "late": {"leaders": ["Metal", "Energy", "Pharma"], "laggards": ["Auto", "Realty", "PSU Bank"]},
    "recession": {"leaders": ["IT", "FMCG", "Pharma"], "laggards": ["Auto", "Realty", "PSU Bank", "Metal"]},
}


def _avg(xs):
    return sum(xs) / len(xs) if xs else None


def rank_sectors(sectors):
    return [dict(rank=i + 1, sector=s.sector, ratio_pct=round(s.ratio * 100, 1), trend=s.trend, status=s.status)
            for i, s in enumerate(sorted(sectors, key=lambda x: x.ratio, reverse=True))]


def analyze_groups(sectors):
    m = {s.sector: s.ratio for s in sectors}
    cyc = _avg([m[s] for s in CYCLICAL_SECTORS if s in m])
    dfn = _avg([m[s] for s in DEFENSIVE_SECTORS if s in m])
    com = _avg([m[s] for s in COMMODITY_SECTORS if s in m])
    if cyc is None or dfn is None:
        return {"regime": "incomplete", "score": 50}
    diff = cyc - dfn
    score = round(min(100, max(0, 50 + diff * 100)))
    regime = ("risk-on (cyclical leadership)" if score > 60
              else "risk-off (defensive leadership)" if score < 40 else "neutral")
    return {"cyclical_avg_pct": round(cyc * 100, 1), "defensive_avg_pct": round(dfn * 100, 1),
            "commodity_avg_pct": round(com * 100, 1) if com is not None else None,
            "difference_pct": round(diff * 100, 1), "score": score, "regime": regime,
            "late_cycle_flag": bool(com is not None and com > cyc and com > dfn)}


def estimate_cycle_phase(sectors):
    sb = sorted(sectors, key=lambda s: s.ratio, reverse=True)
    n = len(sb)
    top = {s.sector for s in sb[: n // 2 + 1]}
    bot = {s.sector for s in sb[n // 2:]}
    tmap = {s.sector: s.trend for s in sectors}
    scores = {}
    for ph, d in CYCLE_PHASES.items():
        ld, lg = d["leaders"], d["laggards"]
        ls = sum(1 for s in ld if s in top) / len(ld)
        gs = sum(1 for s in lg if s in bot) / len(lg)
        tt = [s for s in ld if s in tmap] + [s for s in lg if s in tmap]
        th = sum(1 for s in ld if tmap.get(s) == "up") + sum(1 for s in lg if tmap.get(s) == "down")
        ts = th / len(tt) if tt else 0
        scores[ph] = round((ls * 0.4 + gs * 0.3 + ts * 0.3) * 100, 1)
    sp = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best, bestv = sp[0]
    gap = bestv - (sp[1][1] if len(sp) > 1 else 0)
    conf = "high" if gap > 20 else "moderate" if gap > 10 else "low"
    return {"phase": best, "confidence": conf, "scores": scores}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--source", default="seed", choices=["seed", "niftystocks", "nse"],
                    help="sector→constituents source; seed=hardcoded fallback")
    args = ap.parse_args()
    print(f"Computing India sector uptrend ratios (source={args.source})...", file=sys.stderr)
    sectors = compute_sector_data(source=args.source)
    result = {
        "as_of": str(date.today()),
        "ranking": rank_sectors(sectors),
        "regime": analyze_groups(sectors),
        "cycle_phase": estimate_cycle_phase(sectors),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        r, p = result["regime"], result["cycle_phase"]
        print(f"\n=== India Sector Rotation — {result['as_of']} ===")
        print(f"Regime: {r['regime']} (score {r['score']}/100, cyc-def {r.get('difference_pct')}pp)")
        print(f"Cycle phase estimate: {p['phase'].upper()} (confidence {p['confidence']})")
        print("\nRank  Sector               Uptrend%  Trend  Status")
        for row in result["ranking"]:
            print(f"{row['rank']:>3}  {row['sector']:20s} {row['ratio_pct']:>6}  {row['trend']:5s}  {row['status']}")


if __name__ == "__main__":
    main()
