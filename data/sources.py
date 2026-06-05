"""Indian-market data adapters — the source table codified as IDataSource providers.

Priority for backtesting (offline, no auth):  JugaadData > YFinance
Sector-index price series (rel-strength):      NseIndexSource (nsepython)
Live / recent / forward-test:                  OpenAlgo (needs broker session)
Fundamentals (quality filter):                 ScreenerSource (equity-research)
Macro (regime inputs):                         MacroSource (RBI/MOSPI/CMIE)

Every OHLCV adapter returns the SAME normalized frame (see _finalize): lowercase
columns, ascending DatetimeIndex, OHLC guaranteed. Audited against live feeds
2026-06 (see data/_audit.py); host fixes in CLAUDE.md.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from framework.interfaces import OHLCV_COLUMNS, DataKind, IDataSource
from framework.registry import register_data_source

# Order normalized output: OHLCV core first, then any recognized extras present.
_EXTRA_ORDER = ["vwap", "trades", "deliverable_qty", "delivery_pct"]


def _finalize(df: pd.DataFrame, date_col: str | None = None) -> pd.DataFrame:
    """Normalize any price frame to the canonical schema.

    - lowercase column names
    - set an ascending DatetimeIndex (from `date_col`, else assume already indexed)
    - keep OHLC(V) core + recognized extras, in a stable order
    """
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if date_col is not None:
        dc = date_col.strip().lower()
        df[dc] = pd.to_datetime(df[dc], errors="coerce")
        df = df.dropna(subset=[dc]).set_index(dc)
    df.index = pd.to_datetime(df.index)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df.index.name = "date"
    core = [c for c in OHLCV_COLUMNS if c in df.columns]
    extras = [c for c in _EXTRA_ORDER if c in df.columns]
    return df[core + extras]


@register_data_source
class JugaadData:
    """FREE, no auth. Primary bulk historical backtest source (NSE/BSE bhavcopy).

    pip install jugaad-data ; needs ~/Library/Caches/nsehistory-stock to pre-exist
    (threaded makedirs race — see CLAUDE.md). Surfaces India delivery % / deliverable
    qty (manuals/02 — flow-vs-information signal) alongside OHLCV.
    """
    name = "jugaad"
    kinds = (DataKind.OHLCV,)
    needs_auth = False

    # jugaad raw column -> normalized name
    _MAP = {
        "OPEN": "open", "HIGH": "high", "LOW": "low", "CLOSE": "close",
        "VOLUME": "volume", "VWAP": "vwap", "NO OF TRADES": "trades",
        "DELIVERY QTY": "deliverable_qty", "DELIVERY %": "delivery_pct", "DATE": "date",
    }

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        from jugaad_data.nse import stock_df
        df = stock_df(symbol=symbol, from_date=start, to_date=end, series="EQ")
        df = df.rename(columns={k: v for k, v in self._MAP.items() if k in df.columns})
        return _finalize(df, date_col="date")


@register_data_source
class NseIndexSource:
    """Sector / broad index daily OHLC via nsepython index_history (no volume).

    `symbol` is the NSE index name, e.g. "NIFTY PSU BANK" (validate against
    nsepython.nse_get_index_list). Used for sector relative-strength.
    """
    name = "nse_index"
    kinds = (DataKind.OHLCV,)
    needs_auth = False

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        from nsepython import index_history
        df = index_history(symbol, start.strftime("%d-%b-%Y"), end.strftime("%d-%b-%Y"))
        # raw cols: RequestNumber, Index Name, INDEX_NAME, HistoricalDate, OPEN, HIGH, LOW, CLOSE
        keep = {"HistoricalDate": "date", "OPEN": "open", "HIGH": "high",
                "LOW": "low", "CLOSE": "close"}
        df = df[[c for c in keep if c in df.columns]].rename(columns=keep)
        for c in ("open", "high", "low", "close"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return _finalize(df, date_col="date")


@register_data_source
class YFinanceSource:
    """Fallback only. yfinance has gaps/bad adjustments for India. Needs .NS/.BO suffix."""
    name = "yfinance"
    kinds = (DataKind.OHLCV,)
    needs_auth = False

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        import yfinance as yf
        suffix = ".NS" if exchange == "NSE" else ".BO"
        sym = symbol if symbol.endswith((".NS", ".BO")) else symbol + suffix
        iv = {"D": "1d"}.get(interval, interval)
        df = yf.download(sym, start=start, end=end, interval=iv, progress=False)
        if isinstance(df.columns, pd.MultiIndex):  # (field, ticker) -> field
            df.columns = df.columns.get_level_values(0)
        return _finalize(df)


@register_data_source
class OpenAlgoSource:
    """Broker-quality OHLCV via self-hosted OpenAlgo (Docker). Needs a live broker session.

    Env: OPENALGO_API_KEY, OPENALGO_HOST (default http://127.0.0.1:5000).
    For live/recent + sandbox forward-test, not bulk history (daily re-auth).
    """
    name = "openalgo"
    kinds = (DataKind.OHLCV,)
    needs_auth = True

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        import os
        import requests
        host = os.environ.get("OPENALGO_HOST", "http://127.0.0.1:5000")
        key = os.environ["OPENALGO_API_KEY"]
        r = requests.post(f"{host}/api/v1/history", json={
            "apikey": key, "symbol": symbol, "exchange": exchange,
            "interval": interval, "start_date": str(start), "end_date": str(end),
        }, timeout=30)
        r.raise_for_status()
        df = pd.DataFrame(r.json()["data"])
        return _finalize(df, date_col="timestamp" if "timestamp" in df.columns else "date")


@register_data_source
class FiiDiiSource:
    """FII/FPI + DII daily cash flow (nsepython nse_fiidii). Verified-working 2026-06.

    Daily snapshot, not a long history — so history() returns the latest available rows
    (buy/sell/net by category). Core 'who is force-selling' input (manuals/01).
    """
    name = "fii_dii"
    kinds = (DataKind.INSTITUTIONAL_FLOW,)
    needs_auth = False

    def history(self, symbol="", start=None, end=None, interval="D", exchange="NSE") -> pd.DataFrame:
        from nsepython import nse_fiidii
        df = pd.DataFrame(nse_fiidii())
        for c in ("buyValue", "sellValue", "netValue"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df


@register_data_source
class MutualFundSource:
    """AMFI scheme NAV history via mftool. Verified-working 2026-06 (needs Pillow fix).

    `symbol` is the scheme code. Use mftool.get_scheme_codes() / scheme_category to
    find schemes (e.g. 'Banking and PSU Fund') — answers 'which schemes did better'.
    """
    name = "mutual_fund"
    kinds = (DataKind.FUND_NAV,)
    needs_auth = False

    def history(self, symbol, start=None, end=None, interval="D", exchange="NSE") -> pd.DataFrame:
        from mftool import Mftool
        data = Mftool().get_scheme_historical_nav(symbol)
        df = pd.DataFrame(data["data"])  # [{date, nav}, ...]
        df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
        return df.dropna(subset=["date"]).set_index("date").sort_index()


@register_data_source
class ScreenerSource:
    """Fundamentals (quality filter). Wraps skills/fundamentals/equity-research scraper.

    The 'shouldn't have fallen' test: ROCE, debt, earnings growth, FCF.
    """
    name = "screener"
    kinds = (DataKind.FUNDAMENTALS,)
    needs_auth = True  # saved screener.in session

    def history(self, *a, **k):
        raise NotImplementedError("Use skills/fundamentals/equity-research/screener_reader.py")


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
