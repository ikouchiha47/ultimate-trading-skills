"""Deterministic technical indicators computed from normalized OHLCV (the seam's history()).

The vendored `technical-analyst` skill is VISION-only (it reads chart images), so it is NOT
an indicator engine. The numeric skills (india-stock-analysis, weekly-fno, nse-vcp) need
actual indicator *values* — this module is that shared engine, replacing the broker-MCP
`get_historical_technical_indicators`. Pure pandas, no extra dependency, no look-ahead
(every value at bar t uses only data up to t).

Input: a frame with lowercase `close` (and `high`/`low` for ATR/ADX), ascending DatetimeIndex
— exactly what data_api.history()/index() return. All functions return pandas Series aligned
to the input index; `indicator_snapshot()` returns the latest scalar values for a report.
"""

from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window, min_periods=window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    # Wilder's smoothing
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({"macd": macd_line, "signal": signal_line,
                         "hist": macd_line - signal_line})


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat([high - low, (high - prev_close).abs(),
                      (low - prev_close).abs()], axis=1).max(axis=1)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = _true_range(high, low, close)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def bollinger(close: pd.Series, window: int = 20, n_std: float = 2.0) -> pd.DataFrame:
    mid = sma(close, window)
    sd = close.rolling(window, min_periods=window).std()
    return pd.DataFrame({"mid": mid, "upper": mid + n_std * sd, "lower": mid - n_std * sd})


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    up = high.diff()
    down = -low.diff()
    plus_dm = ((up > down) & (up > 0)) * up
    minus_dm = ((down > up) & (down > 0)) * down
    tr = _true_range(high, low, close)
    atr_ = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def indicator_snapshot(df: pd.DataFrame) -> dict:
    """Latest-bar scalar values for a report. Needs lowercase close (+ high/low for ATR/ADX).

    Uses the last VALID close — some feeds (yfinance) append a trailing NaN row for the current
    incomplete bar, which would otherwise NaN-poison every reading.
    """
    close = df["close"].astype(float).dropna()
    if close.empty:
        return {"close": None}
    out: dict = {
        "close": float(close.iloc[-1]),
        "sma_20": _last(sma(close, 20)), "sma_50": _last(sma(close, 50)),
        "sma_200": _last(sma(close, 200)), "ema_20": _last(ema(close, 20)),
        "rsi_14": _last(rsi(close)),
    }
    m = macd(close).iloc[-1]
    out |= {"macd": _f(m["macd"]), "macd_signal": _f(m["signal"]), "macd_hist": _f(m["hist"])}
    b = bollinger(close).iloc[-1]
    out |= {"bb_upper": _f(b["upper"]), "bb_mid": _f(b["mid"]), "bb_lower": _f(b["lower"])}
    if {"high", "low"} <= set(df.columns):
        high, low = df["high"].astype(float), df["low"].astype(float)
        out["atr_14"] = _last(atr(high, low, close))
        out["adx_14"] = _last(adx(high, low, close))
    # convenience flags
    if out["sma_50"] and out["sma_200"]:
        out["golden_cross"] = out["sma_50"] > out["sma_200"]
    return out


def _last(s: pd.Series):
    v = s.dropna()
    return float(v.iloc[-1]) if len(v) else None


def _f(x):
    return float(x) if pd.notna(x) else None
