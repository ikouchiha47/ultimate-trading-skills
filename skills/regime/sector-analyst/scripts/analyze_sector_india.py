#!/usr/bin/env python3
"""India sector rotation analysis — PORT of the US sector-analyst.

The US version fetched a pre-computed sector_summary.csv (TraderMonty's uptrend
dashboard). No such feed exists for India, so this version COMPUTES the per-sector
uptrend ratio from constituents of the NSE sectoral indices, then runs the same
downstream logic: ranking, cyclical/defensive regime score, overbought/oversold,
and cycle-phase estimation.

Sector→constituent map is taken from the ajeesh repo's sector_mapping.md
(skills/screeners/india-news-tracker/references/sector_mapping.md).

Cyclical/defensive classification is INDIA-specific:
  - IT is DEFENSIVE here (USD export earner / INR hedge), unlike the US.
  - Metal + Energy/Oil&Gas are the commodity bucket.

Data: defaults to yfinance (.NS); swap to jugaad/openalgo via data/sources.py.
Uptrend ratio = fraction of a sector's constituents in an uptrend
  (close > 50DMA AND 50DMA > 200DMA).

Usage:
    python3 analyze_sector_india.py            # human-readable
    python3 analyze_sector_india.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, timedelta

# --- India sector → representative constituents (from ajeesh sector_mapping.md) ---
INDIAN_SECTORS: dict[str, list[str]] = {
    "PSU Bank": ["SBIN", "BANKBARODA", "PNB", "CANBK", "UNIONBANK", "INDIANB", "BANKINDIA"],
    "Private Bank": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "FEDERALBNK", "IDFCFIRSTB"],
    "Financial Services": ["BAJFINANCE", "BAJAJFINSV", "HDFCAMC", "SBILIFE", "ICICIGI", "CHOLAFIN"],
    "Auto": ["M&M", "TATAMOTORS", "MARUTI", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT", "ASHOKLEY", "TVSMOTOR", "BOSCHLTD"],
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "MPHASIS", "COFORGE", "PERSISTENT"],
    "Pharma": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "TORNTPHARM", "LUPIN", "AUROPHARMA", "ALKEM", "BIOCON"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "GODREJCP", "DABUR", "MARICO", "COLPAL", "TATACONSUM"],
    "Metal": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "NMDC", "NATIONALUM", "SAIL", "JINDALSTEL"],
    "Energy": ["RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL", "IOC", "GAIL", "TATAPOWER", "COALINDIA"],
    "Realty": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "PHOENIXLTD", "LODHA", "BRIGADE", "SOBHA"],
    "Infra": ["LT", "ADANIPORTS", "ULTRACEMCO", "GRASIM", "SIEMENS", "ABB"],
}

CYCLICAL_SECTORS = ["PSU Bank", "Private Bank", "Financial Services", "Auto", "Realty", "Infra"]
DEFENSIVE_SECTORS = ["IT", "Pharma", "FMCG"]            # IT defensive in India
COMMODITY_SECTORS = ["Metal", "Energy"]

OVERBOUGHT_THRESHOLD = 0.80   # ratio scale 0..1 (fraction of constituents in uptrend)
OVERSOLD_THRESHOLD = 0.20

# Cycle phases (India): which sectors lead/lag. Mirrors the Bandhan business-cycle table.
CYCLE_PHASES = {
    "early": {"leaders": ["PSU Bank", "Private Bank", "Auto", "Realty"], "laggards": ["IT", "FMCG", "Pharma"]},
    "mid": {"leaders": ["Financial Services", "Auto", "Infra", "Metal"], "laggards": ["FMCG", "Pharma"]},
    "late": {"leaders": ["Metal", "Energy", "Pharma"], "laggards": ["Auto", "Realty", "PSU Bank"]},
    "recession": {"leaders": ["IT", "FMCG", "Pharma"], "laggards": ["Auto", "Realty", "PSU Bank", "Metal"]},
}


@dataclass
class SectorData:
    sector: str
    ratio: float
    trend: str
    slope: float | None = None
    status: str = ""


def _uptrend_ratio(symbols: list[str]) -> tuple[float, int]:
    """Fraction of constituents with close > 50DMA AND 50DMA > 200DMA."""
    import yfinance as yf
    end = date.today()
    start = end - timedelta(days=400)
    up = 0
    counted = 0
    for s in symbols:
        sym = s if s.endswith(".NS") else s + ".NS"
        try:
            df = yf.download(sym, start=start, end=end, interval="1d", progress=False)
            if df.empty or len(df) < 200:
                continue
            close = df["Close"].squeeze()
            ma50 = close.rolling(50).mean().iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1]
            last = close.iloc[-1]
            counted += 1
            if last > ma50 and ma50 > ma200:
                up += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  warn {sym}: {exc}", file=sys.stderr)
    return (up / counted if counted else 0.0), counted


def build_sector_data() -> list[SectorData]:
    out: list[SectorData] = []
    for sector, syms in INDIAN_SECTORS.items():
        ratio, n = _uptrend_ratio(syms)
        trend = "up" if ratio >= 0.5 else "down"
        status = "overbought" if ratio > OVERBOUGHT_THRESHOLD else "oversold" if ratio < OVERSOLD_THRESHOLD else "neutral"
        print(f"  {sector:20s} ratio={ratio:.2f} ({n} stks) {status}", file=sys.stderr)
        out.append(SectorData(sector, round(ratio, 4), trend, None, status))
    return out


# --- downstream logic preserved from the US original (ranking / regime / phase) ---

def rank_sectors(sectors):
    return [dict(rank=i + 1, sector=s.sector, ratio_pct=round(s.ratio * 100, 1), trend=s.trend, status=s.status)
            for i, s in enumerate(sorted(sectors, key=lambda x: x.ratio, reverse=True))]


def _avg(xs): return sum(xs) / len(xs) if xs else None


def analyze_groups(sectors):
    m = {s.sector: s.ratio for s in sectors}
    cyc = _avg([m[s] for s in CYCLICAL_SECTORS if s in m])
    dfn = _avg([m[s] for s in DEFENSIVE_SECTORS if s in m])
    com = _avg([m[s] for s in COMMODITY_SECTORS if s in m])
    if cyc is None or dfn is None:
        return {"regime": "incomplete", "score": 50}
    diff = cyc - dfn
    score = round(min(100, max(0, 50 + diff * 100)))
    late = bool(com is not None and com > cyc and com > dfn)
    regime = "risk-on (cyclical leadership)" if score > 60 else "risk-off (defensive leadership)" if score < 40 else "neutral"
    return {"cyclical_avg_pct": round(cyc * 100, 1), "defensive_avg_pct": round(dfn * 100, 1),
            "commodity_avg_pct": round(com * 100, 1) if com is not None else None,
            "difference_pct": round(diff * 100, 1), "score": score, "regime": regime,
            "late_cycle_flag": late}


def estimate_cycle_phase(sectors):
    sb = sorted(sectors, key=lambda s: s.ratio, reverse=True)
    n = len(sb)
    top = {s.sector for s in sb[: n // 2 + 1]}
    bot = {s.sector for s in sb[n // 2:]}
    tmap = {s.sector: s.trend for s in sectors}
    scores = {}
    for ph, d in CYCLE_PHASES.items():
        ld = d["leaders"]; lg = d["laggards"]
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
    args = ap.parse_args()
    print("Computing India sector uptrend ratios (yfinance)...", file=sys.stderr)
    sectors = build_sector_data()
    result = {
        "as_of": str(date.today()),
        "ranking": rank_sectors(sectors),
        "regime": analyze_groups(sectors),
        "cycle_phase": estimate_cycle_phase(sectors),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        r = result["regime"]; p = result["cycle_phase"]
        print(f"\n=== India Sector Rotation — {result['as_of']} ===")
        print(f"Regime: {r['regime']} (score {r['score']}/100, cyc-def {r.get('difference_pct')}pp)")
        print(f"Cycle phase estimate: {p['phase'].upper()} (confidence {p['confidence']})")
        print("\nRank  Sector               Uptrend%  Trend  Status")
        for row in result["ranking"]:
            print(f"{row['rank']:>3}  {row['sector']:20s} {row['ratio_pct']:>6}  {row['trend']:5s}  {row['status']}")


if __name__ == "__main__":
    main()
