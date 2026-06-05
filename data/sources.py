"""Indian-market data adapters — your source table, codified as IDataSource providers.

Priority for backtesting (offline, no auth):  JugaadData > YFinance
Priority for live / recent / forward-test:     OpenAlgo (needs broker session)
Fundamentals (quality filter):                 ScreenerSource (equity-research)
Macro (regime inputs):                         MacroSource (RBI/MOSPI/CMIE)

Each adapter declares needs_auth so the harness can pick the frictionless path
for bulk historical pulls. Implementations are thin; heavy ones are stubbed with
the exact library/endpoint to use, so wiring is mechanical.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from framework.interfaces import DataKind, IDataSource
from framework.registry import register_data_source

_OHLCV_COLS = ["open", "high", "low", "close", "volume"]


@register_data_source
class JugaadData:
    """FREE, no auth. Best for bulk historical backtests (NSE/BSE bhavcopy, indices, F&O).

    pip install jugaad-data
    from jugaad_data.nse import stock_df
    """
    name = "jugaad"
    kinds = (DataKind.OHLCV,)
    needs_auth = False

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        from jugaad_data.nse import stock_df
        df = stock_df(symbol=symbol, from_date=start, to_date=end, series="EQ")
        df = df.rename(columns=str.lower).set_index("date").sort_index()
        return df[[c for c in _OHLCV_COLS if c in df.columns]]


@register_data_source
class OpenAlgoSource:
    """Broker-quality OHLCV via self-hosted OpenAlgo (Docker). Needs a live broker session.

    Env: OPENALGO_API_KEY, OPENALGO_HOST (default http://127.0.0.1:5000)
    Use for live/recent data + sandbox forward-test, not bulk history (daily re-auth).
    """
    name = "openalgo"
    kinds = (DataKind.OHLCV,)
    needs_auth = True

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        import os, requests
        host = os.environ.get("OPENALGO_HOST", "http://127.0.0.1:5000")
        key = os.environ["OPENALGO_API_KEY"]
        r = requests.post(f"{host}/api/v1/history", json={
            "apikey": key, "symbol": symbol, "exchange": exchange,
            "interval": interval, "start_date": str(start), "end_date": str(end),
        }, timeout=30)
        r.raise_for_status()
        df = pd.DataFrame(r.json()["data"])
        df = df.rename(columns=str.lower).set_index("timestamp").sort_index()
        df.index = pd.to_datetime(df.index)
        return df[[c for c in _OHLCV_COLS if c in df.columns]]


@register_data_source
class YFinanceSource:
    """Fallback only. yfinance has gaps/bad adjustments for India. Symbol needs .NS suffix."""
    name = "yfinance"
    kinds = (DataKind.OHLCV,)
    needs_auth = False

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        import yfinance as yf
        suffix = ".NS" if exchange == "NSE" else ".BO"
        sym = symbol if symbol.endswith((".NS", ".BO")) else symbol + suffix
        iv = {"D": "1d"}.get(interval, interval)
        df = yf.download(sym, start=start, end=end, interval=iv, progress=False)
        # yfinance returns a 2-level column MultiIndex (field, ticker) — flatten to field.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        return df[[c for c in _OHLCV_COLS if c in df.columns]].sort_index()


@register_data_source
class ScreenerSource:
    """Fundamentals (quality filter). Wraps skills/fundamentals/equity-research scraper.

    Provides the 'shouldn't have fallen' test: ROCE, debt, earnings growth, FCF.
    """
    name = "screener"
    kinds = (DataKind.FUNDAMENTALS,)
    needs_auth = True  # saved screener.in session

    def history(self, *a, **k):
        raise NotImplementedError("Use skills/fundamentals/equity-research/screener_reader.py")


@register_data_source
class TrendlyneSource:
    """Sector breadth / momentum from Trendlyne CSV export (the heatmap screenshots)."""
    name = "trendlyne"
    kinds = (DataKind.SECTOR_BREADTH,)
    needs_auth = False

    def history(self, *a, **k):
        raise NotImplementedError("Load exported CSV from data/trendlyne/*.csv")


@register_data_source
class MacroSource:
    """Regime inputs NOT in any price feed: credit growth, G-Sec yields, CPI.

    RBI DBIE (dbie.rbi.org.in), MOSPI, CMIE. Feeds macro-regime-detector port.
    """
    name = "macro"
    kinds = (DataKind.MACRO,)
    needs_auth = False

    def history(self, *a, **k):
        raise NotImplementedError("Pull RBI/MOSPI series; cache to data/macro/*.csv")


@register_data_source
class NSEPythonSource:
    """FREE NSE official endpoints (quotes, option chain, indices). Live-ish, not bulk history."""
    name = "nsepython"
    kinds = (DataKind.OHLCV, DataKind.INSTITUTIONAL_FLOW)
    needs_auth = False

    def history(self, *a, **k):
        raise NotImplementedError("from nsepython import ... ; use for option chain / indices")
