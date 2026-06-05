"""Shared India sector/uptrend computation.

ONE place computes per-sector uptrend ratios + momentum from NSE constituents.
Both skills import this so the data math is not duplicated, yet each skill stays
its own thin, separately-runnable tool:

    skills/regime/sector-analyst   → rotation read + cycle phase
    skills/regime/uptrend-analyzer → 5-component breadth health score

Sector→constituent map from the ajeesh sector_mapping.md. IT is DEFENSIVE in India.
Data via yfinance (.NS) by default; swap to data/sources.py adapters later.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

# --- SEED ONLY ---------------------------------------------------------------
# Hardcoded maps are SEED / FALLBACK / GUARDRAIL, not the source of truth.
# Index constituents drift (rebalances, additions); the live map should be
# LOADED from a source (NSE official index constituents / niftystocks).
# Use these only when offline or to sanity-bound a fetched map.
SEED_SECTORS: dict[str, list[str]] = {
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

# NSE index name per sector — used to FETCH live constituents (the real input).
SECTOR_INDEX = {
    "PSU Bank": "NIFTY PSU BANK", "Private Bank": "NIFTY PRIVATE BANK",
    "Financial Services": "NIFTY FINANCIAL SERVICES", "Auto": "NIFTY AUTO",
    "IT": "NIFTY IT", "Pharma": "NIFTY PHARMA", "FMCG": "NIFTY FMCG",
    "Metal": "NIFTY METAL", "Energy": "NIFTY ENERGY", "Realty": "NIFTY REALTY",
    "Infra": "NIFTY INFRASTRUCTURE",
}

# Cyclical/defensive classification — domain judgment, a legit steering guardrail.
# Overridable by callers, but stable enough to keep as default.
CYCLICAL_SECTORS = ["PSU Bank", "Private Bank", "Financial Services", "Auto", "Realty", "Infra"]
DEFENSIVE_SECTORS = ["IT", "Pharma", "FMCG"]   # IT defensive in India (USD export / INR hedge)
COMMODITY_SECTORS = ["Metal", "Energy"]


def load_sector_constituents(source: str = "seed", csv_path: str | None = None) -> dict[str, list[str]]:
    """Return the sector→constituents map. THIS is the real input.

    source:
      "seed"        — hardcoded fallback (offline / guardrail). CURRENTLY PRIMARY:
                      see audit note below — no reliable live constituent feed yet.
      "niftystocks" — DO NOT TRUST: audited 2026-06, returns STALE pre-2022 members
                      (e.g. LTI/MINDTREE pre-merger). Kept only as a code path.
      "nse"         — NSE official index constituents (nsepython). nsepython has no
                      constituents fn; proper source is NSE/niftyindices CSV (TODO).
      "csv"         — user-supplied csv_path with columns: sector,symbol.

    Any fetch failure falls back to SEED_SECTORS so the pipeline never hard-stops.
    """
    if source == "seed":
        return dict(SEED_SECTORS)
    if source == "csv" and csv_path:
        import csv as _csv
        out: dict[str, list[str]] = {}
        with open(csv_path) as fh:
            for row in _csv.DictReader(fh):
                out.setdefault(row["sector"], []).append(row["symbol"])
        return out or dict(SEED_SECTORS)
    if source == "niftystocks":
        try:
            from niftystocks import ns
            getter = {  # niftystocks exposes per-index getters
                "NIFTY IT": ns.get_nifty_it, "NIFTY BANK": ns.get_nifty_bank,
                "NIFTY AUTO": ns.get_nifty_auto, "NIFTY FMCG": ns.get_nifty_fmcg,
                "NIFTY PHARMA": ns.get_nifty_pharma, "NIFTY METAL": ns.get_nifty_metal,
                "NIFTY REALTY": ns.get_nifty_realty, "NIFTY ENERGY": ns.get_nifty_energy,
            }
            out = {sec: getter[idx]() for sec, idx in SECTOR_INDEX.items() if idx in getter}
            return out or dict(SEED_SECTORS)
        except Exception:  # noqa: BLE001
            return dict(SEED_SECTORS)
    # "nse" or unknown → fetch via nsepython, fallback to seed
    try:
        from nsepython import nse_get_index_constituents  # type: ignore
        return {sec: nse_get_index_constituents(idx) for sec, idx in SECTOR_INDEX.items()} or dict(SEED_SECTORS)
    except Exception:  # noqa: BLE001
        return dict(SEED_SECTORS)


# Back-compat alias (do not rely on it as the live map).
INDIAN_SECTORS = SEED_SECTORS

OVERBOUGHT_THRESHOLD = 0.80
OVERSOLD_THRESHOLD = 0.20


@dataclass
class SectorData:
    sector: str
    ratio: float                 # fraction of constituents in uptrend (0..1)
    trend: str                   # "up" / "down"
    momentum_20d: float | None   # mean 20-day return of constituents
    n: int                       # constituents counted
    status: str = ""


def _compute_one(symbols: list[str]) -> tuple[float, float, int]:
    """Return (uptrend_ratio, mean_20d_return, n_counted) for a sector's constituents."""
    import yfinance as yf

    end = date.today()
    start = end - timedelta(days=400)
    up = counted = 0
    rets: list[float] = []
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
            if len(close) > 20:
                rets.append(float(close.iloc[-1] / close.iloc[-21] - 1))
        except Exception:  # noqa: BLE001
            continue
    ratio = up / counted if counted else 0.0
    mom = sum(rets) / len(rets) if rets else None
    return ratio, mom, counted


def compute_sector_data(
    sectors: dict[str, list[str]] | None = None, source: str = "seed"
) -> list[SectorData]:
    """Compute SectorData for every Indian sector. Shared by both skills.

    sectors : explicit sector→constituents map (highest precedence — pass a
              fetched/curated map here in a workflow).
    source  : if sectors is None, load via load_sector_constituents(source).
              Defaults to "seed" so it runs offline; pass "niftystocks"/"nse"
              in production to use the live map.
    """
    if sectors is None:
        sectors = load_sector_constituents(source)
    out: list[SectorData] = []
    for sector, syms in sectors.items():
        ratio, mom, n = _compute_one(syms)
        status = ("overbought" if ratio > OVERBOUGHT_THRESHOLD
                  else "oversold" if ratio < OVERSOLD_THRESHOLD else "neutral")
        out.append(SectorData(sector, round(ratio, 4), "up" if ratio >= 0.5 else "down",
                              round(mom, 4) if mom is not None else None, n, status))
    return out
