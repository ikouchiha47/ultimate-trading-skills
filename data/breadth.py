"""India market breadth — computed from constituent OHLCV (NOT the retired US CSV).

Breadth = how broadly a move is shared across a universe's members. The classic internals:
  - % of members above their 50-DMA / 200-DMA   (participation / trend health)
  - advance/decline line                         (cumulative net advancers)
  - new 52w highs vs lows                        (leadership vs deterioration)

All derived from the same audited per-stock OHLCV the rest of the stack uses (the seam's
history()), so there is ONE data path and no silent US fallback. This closes the `breadth`
MISSING gap in framework/data_api.py (Step 1 of PORTING_PLAN.md).

Why this matters to the thesis (manuals/12, /06): breadth tells you whether a sector-wide
move is broad (flow/rotation — everything moving together) or narrow (idiosyncratic). A
broad, indiscriminate drop in a bottom-up sector is exactly the fadeable dislocation.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

# 252 ≈ 1 trading year; need ~200 bars before %>200DMA is meaningful.
_HIGH_LOW_WINDOW = 252


def _close_panel(symbols: list[str], start: date, end: date, source: str) -> pd.DataFrame:
    """date x symbol panel of close prices, via the seam's history(). Drops empties."""
    from framework import data_api

    cols: dict[str, pd.Series] = {}
    for s in symbols:
        try:
            df = data_api.history(s, start, end, source=source)
        except Exception:  # noqa: BLE001 — one bad symbol must not sink the scan
            continue
        if df is not None and not df.empty and "close" in df.columns:
            cols[s] = df["close"].astype(float)
    if not cols:
        return pd.DataFrame()
    return pd.DataFrame(cols).sort_index()


# Warm-up so the 200-DMA / 52w-high are valid from the FIRST requested bar (else
# pct_above_200 reads a false 0). ~200 trading days ≈ 300 cal; pad to 420 for holidays.
_WARMUP_DAYS = 420


def breadth_series(
    symbols: list[str], start: date, end: date, source: str = "yfinance"
) -> pd.DataFrame:
    """Breadth internals time series for an explicit symbol list.

    source defaults to yfinance — fast across many names for a breadth scan (documented
    fallback). Pass source="jugaad" for delivery-aware single-name precision elsewhere.

    Fetches a 200-DMA warm-up buffer BEFORE `start` so the rolling stats are valid from the
    first returned bar, then trims output to [start, end]. Returns a DataFrame indexed by
    date: pct_above_50, pct_above_200, advancers, decliners, ad_line, new_highs, new_lows, n.
    """
    panel = _close_panel(symbols, start - timedelta(days=_WARMUP_DAYS), end, source)
    if panel.empty:
        return pd.DataFrame()

    ma50 = panel.rolling(50, min_periods=50).mean()
    ma200 = panel.rolling(200, min_periods=200).mean()
    above50 = panel > ma50
    above200 = panel > ma200

    daily_ret = panel.pct_change()
    advancers = (daily_ret > 0).sum(axis=1)
    decliners = (daily_ret < 0).sum(axis=1)

    roll_max = panel.rolling(_HIGH_LOW_WINDOW, min_periods=20).max()
    roll_min = panel.rolling(_HIGH_LOW_WINDOW, min_periods=20).min()
    new_highs = (panel >= roll_max).sum(axis=1)
    new_lows = (panel <= roll_min).sum(axis=1)

    n_present = panel.notna().sum(axis=1)  # members with data on each date
    out = pd.DataFrame({
        "pct_above_50": (above50.sum(axis=1) / n_present).where(n_present > 0),
        "pct_above_200": (above200.sum(axis=1) / n_present).where(n_present > 0),
        "advancers": advancers,
        "decliners": decliners,
        "ad_line": (advancers - decliners).cumsum(),
        "new_highs": new_highs,
        "new_lows": new_lows,
        "n": n_present,
    })
    out.index.name = "date"
    # Trim the warm-up buffer: only return the requested window, now with valid MAs.
    return out[out.index >= pd.Timestamp(start)]


def sector_breadth(
    universe: str, start: date, end: date, source: str = "yfinance",
    constituents_source: str = "nse_csv",
) -> pd.DataFrame:
    """Breadth internals for a named universe — a sector ("PSU Bank") or "NIFTY 50".

    Resolves members via the seam's constituents() then delegates to breadth_series().
    """
    from framework import data_api

    members = data_api.constituents(source=constituents_source)
    if universe in members:
        symbols = members[universe]
    elif universe.upper() in {"NIFTY 50", "NIFTY50", "MARKET"}:
        # broad-market breadth = union of all sector constituents we track
        symbols = sorted({s for syms in members.values() for s in syms})
    else:
        raise KeyError(f"unknown breadth universe {universe!r}; "
                       f"known sectors: {sorted(members)} or 'NIFTY 50'")
    return breadth_series(symbols, start, end, source=source)
