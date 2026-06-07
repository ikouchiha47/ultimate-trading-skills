"""Flow-vs-information signals — separate a fadeable dislocation from a falling knife.

A deep drop below the 25-DMA (z-score) is necessary but NOT sufficient: the deepest
drops sit in the structurally weakest names (information-driven knives), not the
strong ones (flow-driven dips). To tell them apart you need price+VOLUME, not price:

  - ABSORPTION (per name): on the sell-off bar, is someone soaking up the supply?
    High volume + high DELIVERY% (real ownership transfer, not intraday churn — the
    India-specific signal) + a close in the upper part of the day's range = demand met
    supply. The opposite (low delivery, close on the low) is distribution — a knife.
  - REGIME / sector-wide-ness: did the WHOLE basket get dumped together (indiscriminate
    flow / risk-off — fadeable) or did ONE name fall alone (company news — information,
    a trap)? Measured as the breadth of dislocation across the basket.

Generic + thin: these functions compute scores from point-in-time OHLCV (+ delivery)
frames and return numbers. The strategy/agent decides the thresholds and what to do.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _clip01(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


def absorption_score(df: pd.DataFrame, window: int = 20) -> float | None:
    """0..1: is the latest bar an absorption bar (demand meeting panic supply)?

    Blends three point-in-time signals on the last completed bar:
      vol   — volume vs its rolling median (a spike means real participation)
      range — close position within the bar's high-low range (near high = buyers won)
      deliv — delivery% vs its rolling median (high = real owners taking stock, not churn)

    Returns None when there isn't enough history (or no volume), so the caller can
    treat "unknown" as "do not enter" rather than fabricate a score.
    """
    if df is None or len(df) < window + 1 or "volume" not in df:
        return None
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    vol = df["volume"].astype(float)
    if not np.isfinite(vol.iloc[-1]) or vol.iloc[-1] <= 0:
        return None

    vol_med = vol.iloc[-window:].median()
    s_vol = _clip01((vol.iloc[-1] / vol_med - 1.0) / 2.0) if vol_med > 0 else 0.0  # 1x->0, 3x->1

    rng = high.iloc[-1] - low.iloc[-1]
    range_pos = (close.iloc[-1] - low.iloc[-1]) / rng if rng > 0 else 0.5
    s_range = _clip01(range_pos)                                                   # near high -> 1

    deliv = df["delivery_pct"].astype(float).dropna() if "delivery_pct" in df else None
    if deliv is not None and len(deliv) >= 2:
        # delivery publishes with a ~1-day lag, so the latest bar is often NaN — use the
        # last SETTLED value, compared to its own recent median.
        deliv_med = deliv.iloc[-window:].median()
        s_deliv = _clip01((deliv.iloc[-1] / deliv_med - 1.0) / 0.5) if deliv_med > 0 else 0.0
    else:
        s_deliv = 0.5      # no delivery data (e.g. index/yfinance): neutral, don't reward or block

    return float(np.mean([s_vol, s_range, s_deliv]))


def dislocation_breadth(z_by_symbol: dict[str, float | None], entry_z: float) -> float:
    """Fraction of the basket that is also stretched below ``entry_z`` right now.

    High breadth ⇒ the whole sector was dumped together ⇒ indiscriminate flow (fadeable).
    Low breadth ⇒ this name fell alone ⇒ likely company-specific information (a trap).
    Names with no z (insufficient history) are excluded from the denominator.
    """
    vals = [z for z in z_by_symbol.values() if z is not None and np.isfinite(z)]
    if not vals:
        return 0.0
    stretched = sum(1 for z in vals if z < entry_z)
    return stretched / len(vals)
