"""Shared India sector/uptrend computation.

ONE place computes per-sector uptrend ratios + momentum from NSE constituents.
Both skills import this so the data math is not duplicated, yet each skill stays
its own thin, separately-runnable tool:

    skills/regime/sector-analyst   -> rotation read + cycle phase
    skills/regime/uptrend-analyzer -> 5-component breadth health score

Sector->constituent SEED map (fallback; live membership loads from nselib). IT is DEFENSIVE
in India. Data via the seam adapters (data/sources.py).
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

# --- Analysis mode (manuals/12) -------------------------------------------------
# The dominant driver of a sector dictates the analysis MODE and — load-bearing — the
# PRIOR on whether a sector-wide move is flow-driven (fadeable, our edge) or
# information-driven (a trap). SEED from judgment (guardrail); each tag carries a NAMED
# falsifiable test (seed + empirical-validation discipline — manuals/10). Not yet wired
# into pipelines; this is the taxonomy the wiring will consume.
#
#   mode               : top_down_cyclical | bottom_up_idiosyncratic | thematic_cascade
#   drivers            : the dominant return drivers to measure beta against
#   flow_vs_info_prior : "high" => sector-wide move likely indiscriminate flow (fade edge);
#                        "low"  => likely shared-driver information (trap)
#   validation         : the falsifiable test that must confirm/refute this tag
TOP_DOWN, BOTTOM_UP, THEMATIC = "top_down_cyclical", "bottom_up_idiosyncratic", "thematic_cascade"

SECTOR_MODE: dict[str, dict] = {
    "Metal":     {"mode": TOP_DOWN, "drivers": ["LME", "China demand", "USDINR"],
                  "flow_vs_info_prior": "low",
                  "validation": "high beta to LME/China; fade-the-dip expectancy ≈0 or <0"},
    "Energy":    {"mode": TOP_DOWN, "drivers": ["crude", "rates", "USDINR"],
                  "flow_vs_info_prior": "low",
                  "validation": "high beta to crude; fade expectancy not positive"},
    "Auto":      {"mode": TOP_DOWN, "drivers": ["rates", "fuel", "consumer cycle"],
                  "flow_vs_info_prior": "low",
                  "validation": "beta to rates/consumption confirms cyclical"},
    "Pharma":    {"mode": BOTTOM_UP, "drivers": ["USFDA approvals", "US generic pricing", "USDINR"],
                  "flow_vs_info_prior": "high",
                  "validation": "high within-sector dispersion; fade expectancy >0"},
    "IT":        {"mode": BOTTOM_UP, "drivers": ["US client tech-spend", "USDINR"],
                  "flow_vs_info_prior": "high",
                  "validation": "tier-1 vs midcap dispersion; USDINR beta; fade expectancy >0"},
    "FMCG":      {"mode": BOTTOM_UP, "drivers": ["rural demand", "input costs", "pricing power"],
                  "flow_vs_info_prior": "high",
                  "validation": "low macro beta; idiosyncratic dispersion"},
    "PSU Bank":  {"mode": TOP_DOWN, "drivers": ["rates", "credit cycle", "govt policy"],
                  "flow_vs_info_prior": "low",
                  "validation": "credit-growth/rate beta; but check asset-quality dispersion"},
    "Private Bank": {"mode": TOP_DOWN, "drivers": ["rates", "credit cycle", "capex cycle"],
                  "flow_vs_info_prior": "low",
                  "validation": "rate/credit beta; high name-level dispersion ⇒ partial bottom-up"},
    "Financial Services": {"mode": TOP_DOWN, "drivers": ["rates", "credit cycle"],
                  "flow_vs_info_prior": "low", "validation": "rate beta confirms cyclical"},
    "Realty":    {"mode": TOP_DOWN, "drivers": ["rates", "capex cycle"],
                  "flow_vs_info_prior": "low", "validation": "rate-sensitivity beta"},
    "Infra":     {"mode": THEMATIC, "drivers": ["govt capex", "order book", "rates"],
                  "flow_vs_info_prior": "low",
                  "validation": "lead-lag vs capex/order announcements; cascade reach"},
}

# Cyclical/defensive classification — DERIVED from SECTOR_MODE (back-compat steering guardrail).
CYCLICAL_SECTORS = [s for s, m in SECTOR_MODE.items() if m["mode"] == TOP_DOWN]
DEFENSIVE_SECTORS = ["IT", "Pharma", "FMCG"]   # IT defensive in India (USD export / INR hedge)
COMMODITY_SECTORS = ["Metal", "Energy"]


def sector_mode(sector: str) -> dict | None:
    """Return the analysis-mode tag for a sector (manuals/12), or None if unclassified."""
    return SECTOR_MODE.get(sector)


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
    """Return the sector->constituents map. THIS is the real input.

    source:
      "seed"      — hardcoded fallback (offline / guardrail).
      "nse_fetch" — fetch LIVE from niftyindices.com (requests+cookie-warmup, Playwright
                    fallback), caching to data/constituents/. The recommended live path.
                    See data/nse_constituents.py. Per-sector fallback to SEED.
      "nse_csv"   — read already-downloaded/cached NSE CSVs from CONSTITUENTS_DIR, one file
                    per sector "<Sector>.csv". Offline-reproducible; per-sector SEED fallback.
      "csv"       — single user file at csv_path with columns: sector,symbol.

    Anything missing falls back to SEED_SECTORS so the pipeline never hard-stops.
    """
    if source == "seed":
        return dict(SEED_SECTORS)

    if source == "nselib":
        # PRIMARY: live via nselib (Akamai-free). Layer: seed -> cached CSV -> live nselib,
        # so each sector ends up with the best available (live > cached > seed).
        out = dict(SEED_SECTORS)
        if CONSTITUENTS_DIR.is_dir():
            for sector in SEED_SECTORS:
                f = CONSTITUENTS_DIR / f"{sector}.csv"
                if f.exists():
                    syms = _read_nse_csv_symbols(f)
                    if syms:
                        out[sector] = syms
        try:
            from data.nse_constituents import fetch_sector_constituents_nselib
            out.update(fetch_sector_constituents_nselib())  # only successful sectors override
        except Exception:  # noqa: BLE001
            pass
        return out

    if source == "nse_fetch":
        out = dict(SEED_SECTORS)
        try:
            from data.nse_constituents import fetch_sector_constituents
            out.update(fetch_sector_constituents())  # only successful sectors override seed
        except Exception:  # noqa: BLE001
            pass
        return out

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

    # unknown source -> safest default
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
    n: int                       # constituents counted (>= MIN_BARS of data)
    status: str = ""


MIN_BARS = 200  # need 200 bars for a valid 200DMA / trend read

# Type of the injectable per-symbol fetcher: (symbol, start, end) -> normalized OHLCV df.
HistoryFn = "Callable[[str, date, date], pd.DataFrame]"


def _default_history(symbol: str, start: date, end: date):
    """Default fetcher: normalized yfinance OHLCV (fast enough for breadth scans).

    yfinance is our documented FALLBACK source, used here for breadth because it is
    fast across ~hundreds of symbols. Pass JugaadData().history as history_fn for the
    deep-dive (it adds delivery_pct — see manuals/02).
    """
    from data.sources import YFinanceSource
    return YFinanceSource().history(symbol, start, end)


def _metrics_from_ohlcv(df) -> dict | None:
    """Per-stock metrics from one normalized OHLCV frame. None if too few bars."""
    import numpy as np

    if df is None or df.empty or "close" not in df.columns:
        return None
    close = df["close"].astype(float).dropna()
    n = len(close)
    if n < MIN_BARS:
        return None
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]
    last = close.iloc[-1]
    uptrend = bool(last > ma50 and ma50 > ma200)
    ret_20d = float(last / close.iloc[-21] - 1) if n > 21 else np.nan
    ret_window = float(last / close.iloc[0] - 1)
    years = n / 252.0
    cagr = float((last / close.iloc[0]) ** (1 / years) - 1) if years > 0 else np.nan
    max_dd = float((close / close.cummax() - 1).min())
    avg_delivery = (float(df["delivery_pct"].astype(float).mean())
                    if "delivery_pct" in df.columns else np.nan)
    # 25-DMA deviation — the BNF / Kotegawa snap-back marker (manuals/03). dist_25dma is the
    # current % deviation from the 25-DMA; dist_25dma_z z-scores it over the window so a large
    # negative z = unusually stretched BELOW its mean — the fade candidate.
    ma25_series = close.rolling(25).mean()
    dev = ((close - ma25_series) / ma25_series).dropna()
    dist_25dma = float(dev.iloc[-1]) if len(dev) else np.nan
    dist_25dma_z = (float((dev.iloc[-1] - dev.mean()) / dev.std())
                    if len(dev) > 1 and dev.std() > 0 else np.nan)
    return {
        "n_bars": n, "last": float(last), "ma50": float(ma50), "ma200": float(ma200),
        "uptrend": uptrend, "ret_20d": ret_20d, "ret_window": ret_window,
        "cagr": cagr, "max_drawdown": max_dd, "avg_delivery_pct": avg_delivery,
        "dist_25dma": dist_25dma, "dist_25dma_z": dist_25dma_z,
    }


def compute_constituent_metrics(
    symbols: list[str], history_fn=None, lookback_days: int = 400
) -> "pd.DataFrame":
    """Per-stock metric table for a list of symbols (indexed by symbol).

    This is the building block both the breadth read and the sector deep-dive use — it
    keeps the per-symbol numbers (cagr, drawdown, delivery, 20d return) instead of
    averaging them away. Symbols that fail to fetch or have < MIN_BARS are dropped.
    """
    import pandas as pd

    fetch = history_fn or _default_history
    end = date.today()
    start = end - timedelta(days=lookback_days)
    rows: dict[str, dict] = {}
    for s in symbols:
        try:
            m = _metrics_from_ohlcv(fetch(s, start, end))
        except Exception:  # noqa: BLE001
            m = None
        if m is not None:
            rows[s] = m
    df = pd.DataFrame.from_dict(rows, orient="index")
    df.index.name = "symbol"
    return df


def compute_sector_data(
    sectors: dict[str, list[str]] | None = None, source: str = "seed", history_fn=None
) -> list[SectorData]:
    """Aggregate SectorData for every Indian sector from the per-stock table.

    sectors    : explicit sector->constituents map (highest precedence).
    source     : if sectors is None, load via load_sector_constituents(source)
                 ("seed" offline default, "nse_csv" for the live map).
    history_fn : optional injected fetcher (e.g. JugaadData().history); default yfinance.
    """
    if sectors is None:
        sectors = load_sector_constituents(source)
    out: list[SectorData] = []
    for sector, syms in sectors.items():
        m = compute_constituent_metrics(syms, history_fn=history_fn)
        n = len(m)
        if n:
            ratio = float(m["uptrend"].mean())
            mom = float(m["ret_20d"].mean()) if m["ret_20d"].notna().any() else None
        else:
            ratio, mom = 0.0, None
        status = ("overbought" if ratio > OVERBOUGHT_THRESHOLD
                  else "oversold" if ratio < OVERSOLD_THRESHOLD else "neutral")
        out.append(SectorData(sector, round(ratio, 4), "up" if ratio >= 0.5 else "down",
                              round(mom, 4) if mom is not None else None, n, status))
    return out
