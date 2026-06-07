"""Universe builder — get a list, then filter it. Script + agent driven.

The reusable screening core: `build_universe(base, **filters)` resolves a base list (any NSE
index via the seam, or an explicit symbol list), computes per-symbol metrics ONCE, applies the
composable filters you pass, and returns both the surviving symbols AND a transparent table
(so you can see why each name passed/failed — no black box).

  - The SCRIPT decides HOW (deterministic metric math; no fabrication — a name that fails to
    fetch is dropped, never guessed).
  - The AGENT decides WHAT (which filters + thresholds, translated from a plain-English ask),
    then feeds the result to a screener (nse-vcp), sector-deep-dive, etc.

Every filter is optional (None = skip). Price filters run off one history() fetch per symbol;
fundamental filters (slower, Playwright) run only on the price-survivors. Valid base index
names are catalogued in data/index_catalog.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from framework import data_api, indicators


@dataclass
class UniverseResult:
    symbols: list[str]        # names passing ALL applied filters
    table: pd.DataFrame       # per-symbol metrics + per-filter pass flags (transparency)

    def __len__(self) -> int:
        return len(self.symbols)


def _resolve_base(base: str | list[str]) -> list[str]:
    """A base is either an explicit symbol list or an NSE index name (-> its members)."""
    if isinstance(base, (list, tuple, set)):
        return [str(s).strip() for s in base if str(s).strip()]
    return data_api.index_members(base)


def _price_metrics(symbol: str, since: date, source: str) -> dict | None:
    """Per-symbol price metrics from one history() fetch. None if it can't be read."""
    try:
        df = data_api.history(symbol, since, source=source)
    except Exception:  # noqa: BLE001 — a bad symbol is dropped, never faked
        return None
    if df is None or df.empty or "close" not in df.columns:
        return None
    snap = indicators.indicator_snapshot(df)
    close = df["close"].astype(float).dropna()  # drop trailing-NaN bar (yfinance)
    if close.empty:
        return None
    turnover_cr = None
    if "volume" in df.columns:
        turnover_cr = float((close.tail(20) * df["volume"].astype(float).reindex(close.index).tail(20)).mean()) / 1e7
    return {
        "close": snap.get("close"),
        "above_50": (snap.get("sma_50") is not None and snap["close"] > snap["sma_50"]),
        "above_200": (snap.get("sma_200") is not None and snap["close"] > snap["sma_200"]),
        "rsi_14": snap.get("rsi_14"),
        "ret_window": float(close.iloc[-1] / close.iloc[0] - 1) if len(close) > 1 else None,
        "turnover_cr": turnover_cr,
        "avg_delivery_pct": (float(df["delivery_pct"].astype(float).mean())
                             if "delivery_pct" in df.columns else None),
    }


def _fundamental_metrics(symbol: str) -> dict:
    """ROCE / debt-to-equity / 5y sales growth via fundamentals() (slow; Playwright)."""
    try:
        f = data_api.fundamentals(symbol)
    except Exception:  # noqa: BLE001
        return {"roce_pct": None, "debt_to_equity": None, "sales_growth_5y": None}
    num = f.get("numeric", {})
    growth = f.get("growth", {}).get("sales_growth", {})
    return {
        "roce_pct": num.get("roce_pct"),
        "debt_to_equity": num.get("debt_to_equity"),
        "sales_growth_5y": growth.get("5y"),
    }


def build_universe(
    base: str | list[str],
    since: str | date | None = None,
    *,
    # price filters (one history() fetch each)
    liquidity_min_cr: float | None = None,   # avg 20d turnover (close*vol) in ₹ crore
    above_ma: int | None = None,             # 50 or 200 — require close above that DMA
    momentum_min: float | None = None,       # window return >= this (e.g. 0.10 = +10%)
    delivery_min: float | None = None,       # avg delivery % >= this (needs source="jugaad")
    # fundamental filters (slower; run only on price-survivors)
    roce_min: float | None = None,
    debt_max: float | None = None,
    sales_growth_min: float | None = None,
    price_source: str = "yfinance",
    lookback_days: int = 400,
) -> UniverseResult:
    """Resolve `base`, compute metrics, apply the given filters, return survivors + table."""
    if delivery_min is not None and price_source != "jugaad":
        raise ValueError("delivery_min requires price_source='jugaad' (yfinance has no delivery%)")
    start = (date.today() - timedelta(days=lookback_days)) if since is None else \
        (since if isinstance(since, date) else date.fromisoformat(str(since)))

    rows: dict[str, dict] = {}
    for sym in _resolve_base(base):
        m = _price_metrics(sym, start, price_source)
        if m is not None:
            rows[sym] = m
    table = pd.DataFrame.from_dict(rows, orient="index")
    if table.empty:
        return UniverseResult([], table)

    passes = pd.Series(True, index=table.index)
    if liquidity_min_cr is not None:
        passes &= table["turnover_cr"].fillna(-1) >= liquidity_min_cr
    if above_ma is not None:
        col = {50: "above_50", 200: "above_200"}[above_ma]
        passes &= table[col].fillna(False)
    if momentum_min is not None:
        passes &= table["ret_window"].fillna(-1e9) >= momentum_min
    if delivery_min is not None:
        passes &= table["avg_delivery_pct"].fillna(-1) >= delivery_min

    # Fundamental filters: only fetch for names still passing (Playwright is slow).
    if any(v is not None for v in (roce_min, debt_max, sales_growth_min)):
        fund = {s: _fundamental_metrics(s) for s in table.index[passes]}
        fdf = pd.DataFrame.from_dict(fund, orient="index")
        for c in ("roce_pct", "debt_to_equity", "sales_growth_5y"):
            table[c] = fdf[c] if c in fdf.columns else None
        if roce_min is not None:
            passes &= table["roce_pct"].fillna(-1e9) >= roce_min
        if debt_max is not None:
            passes &= table["debt_to_equity"].fillna(1e9) <= debt_max
        if sales_growth_min is not None:
            passes &= table["sales_growth_5y"].fillna(-1e9) >= sales_growth_min

    table["passes"] = passes
    return UniverseResult(sorted(table.index[passes]), table)
