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

from pathlib import Path

# NSE index name per sector — the index whose official constituent CSV to download.
SECTOR_INDEX = {
    "PSU Bank": "NIFTY PSU BANK", "Private Bank": "NIFTY PRIVATE BANK",
    "Financial Services": "NIFTY FINANCIAL SERVICES", "Auto": "NIFTY AUTO",
    "IT": "NIFTY IT", "Pharma": "NIFTY PHARMA", "FMCG": "NIFTY FMCG",
    "Metal": "NIFTY METAL", "Energy": "NIFTY ENERGY", "Realty": "NIFTY REALTY",
    "Infra": "NIFTY INFRASTRUCTURE",
}

# Directory of manually-downloaded NSE/niftyindices constituent CSVs (the live input).
# One file per sector, named "<Sector>.csv" (the SEED_SECTORS keys), in NSE's native
# format (a "Symbol" column). See data/constituents/README.md for how to fetch them.
CONSTITUENTS_DIR = Path(__file__).resolve().parents[1] / "data" / "constituents"

# Cyclical/defensive classification — domain judgment, a legit steering guardrail.
# Overridable by callers, but stable enough to keep as default.
CYCLICAL_SECTORS = ["PSU Bank", "Private Bank", "Financial Services", "Auto", "Realty", "Infra"]
DEFENSIVE_SECTORS = ["IT", "Pharma", "FMCG"]   # IT defensive in India (USD export / INR hedge)
COMMODITY_SECTORS = ["Metal", "Energy"]


def _read_nse_csv_symbols(path: Path) -> list[str]:
    """Extract symbols from one NSE/niftyindices constituent CSV (has a 'Symbol' column)."""
    import csv as _csv
    with path.open(newline="") as fh:
        rows = list(_csv.DictReader(fh))
    if not rows:
        return []
    # NSE header is "Symbol"; be lenient about case/whitespace.
    key = next((k for k in rows[0] if k and k.strip().lower() == "symbol"), None)
    if key is None:
        return []
    return [r[key].strip() for r in rows if r.get(key) and r[key].strip()]


def load_sector_constituents(source: str = "seed", csv_path: str | None = None) -> dict[str, list[str]]:
    """Return the sector→constituents map. THIS is the real input.

    source:
      "seed"     — hardcoded fallback (offline / guardrail). CURRENTLY PRIMARY until
                   constituent CSVs are dropped in data/constituents/ (no reliable
                   programmatic live feed: niftystocks is stale, nsepython has none).
      "nse_csv"  — read manually-downloaded NSE constituent CSVs from CONSTITUENTS_DIR,
                   one file per sector named "<Sector>.csv". This is the recommended
                   live path — see data/constituents/README.md. Any sector without a
                   file falls back to its SEED entry.
      "csv"      — single user file at csv_path with columns: sector,symbol.

    Anything missing falls back to SEED_SECTORS so the pipeline never hard-stops.
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

    if source == "nse_csv":
        out = dict(SEED_SECTORS)  # start from seed; override per-sector where a file exists
        if CONSTITUENTS_DIR.is_dir():
            for sector in SEED_SECTORS:
                f = CONSTITUENTS_DIR / f"{sector}.csv"
                if f.exists():
                    syms = _read_nse_csv_symbols(f)
                    if syms:
                        out[sector] = syms
        return out

    # unknown source → safest default
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
