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
from pathlib import Path

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

    def history(self, symbol, start, end, interval="D", exchange="NSE",
                adjust=True) -> pd.DataFrame:
        from jugaad_data.nse import stock_df
        df = stock_df(symbol=symbol, from_date=start, to_date=end, series="EQ")
        df = df.rename(columns={k: v for k, v in self._MAP.items() if k in df.columns})
        df = _finalize(df, date_col="date")
        # jugaad returns RAW, unadjusted prices: a stock split shows up as a fake cliff
        # (e.g. CANBK 5:1 on 2024-05-14, 566 -> 119) that wrecks CAGR/maxDD/25-DMA-z over any
        # window crossing it. Back-adjust for splits by default so metrics are honest.
        return back_adjust_splits(df, symbol, exchange) if adjust else df


_CA_DIR = Path(__file__).resolve().parent / "corporate_actions"
_CA_TTL_DAYS = 30
_YF_SPLIT_TIMEOUT_S = 8


def _detect_split_gaps(close: pd.Series) -> list[tuple]:
    """Find split-shaped single-day jumps in THIS series — fast, offline, no network.

    A forward split makes close[t-1]/close[t] ~ an integer R (2..20) within tolerance; the
    price then trades normally (unlike a crash, which rarely lands on a clean ratio). Returns
    [(ex_date, ratio)]; empty for the vast majority of stocks, so the common path costs nothing.
    """
    ratios = (close.shift(1) / close).dropna()
    out: list[tuple] = []
    for dt, rr in ratios.items():
        if not (rr > 1.4):                       # only big single-day drops are split-shaped
            continue
        nearest = round(float(rr))
        if 2 <= nearest <= 20 and abs(rr - nearest) / nearest < 0.06:
            out.append((dt, nearest))
    return out


def _confirm_splits_yf(symbol: str, exchange: str) -> set[int]:
    """Authoritative split ratios from yfinance — DISK-CACHED + hard TIMEOUT (never hangs).

    Only called when _detect_split_gaps already found a candidate, so we pay the network cost
    at most once per split stock (then cache). On any timeout/error returns empty -> caller
    falls back to the data-detected ratio (a clean integer gap is almost certainly a split).
    """
    import json
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FTimeout

    _CA_DIR.mkdir(parents=True, exist_ok=True)
    cache = _CA_DIR / f"{symbol}_{exchange}.json"
    if cache.exists():
        try:
            blob = json.loads(cache.read_text())
            ts = date.fromisoformat(blob.get("fetched", "1970-01-01"))
            if (date.today() - ts).days < _CA_TTL_DAYS:
                return {int(r) for r in blob.get("ratios", [])}
        except Exception:  # noqa: BLE001
            pass
    suffix = ".BO" if exchange.upper() == "BSE" else ".NS"

    def _pull():
        import yfinance as yf
        s = yf.Ticker(f"{symbol}{suffix}").splits
        return {int(round(float(r))) for r in s.values if r and r > 0}

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            ratios = ex.submit(_pull).result(timeout=_YF_SPLIT_TIMEOUT_S)
    except (_FTimeout, Exception):  # noqa: BLE001
        return set()
    try:
        cache.write_text(json.dumps({"fetched": date.today().isoformat(),
                                     "ratios": sorted(ratios)}))
    except Exception:  # noqa: BLE001
        pass
    return ratios


def back_adjust_splits(df: pd.DataFrame, symbol: str, exchange: str = "NSE") -> pd.DataFrame:
    """Split-only back-adjust raw OHLCV (matches screener; not dividend-adjusted).

    Gap-detect FIRST (offline) so no-split stocks cost zero network. When a split-shaped gap
    is found, confirm the ratio against yfinance (cached + timeout); if confirmation is
    unavailable, trust the clean integer gap. Divides bars BEFORE each ex-date by the
    cumulative factor (located by the gap, so a record/ex-date offset can't mis-shift it);
    scales volume + deliverable_qty up.
    """
    if df is None or df.empty or "close" not in df.columns:
        return df
    gaps = _detect_split_gaps(df["close"].astype(float))
    if not gaps:
        return df                                # common case: instant, offline
    confirmed = _confirm_splits_yf(symbol, exchange)   # may be empty (timeout) -> trust the gap
    factor = pd.Series(1.0, index=df.index)
    for ex_date, ratio in gaps:
        if confirmed and ratio not in confirmed:
            continue                             # yfinance knows the splits and this isn't one
        factor.loc[df.index < ex_date] *= ratio
    if bool((factor == 1.0).all()):
        return df
    out = df.copy()
    for c in ("open", "high", "low", "close", "vwap"):
        if c in out.columns:
            out[c] = out[c].astype(float) / factor
    for c in ("volume", "deliverable_qty"):
        if c in out.columns:
            out[c] = out[c].astype(float) * factor
    return out


@register_data_source
class NseIndexSource:
    """Sector / broad index daily OHLC via nsepython index_history (no volume).

    `symbol` is the NSE index name, e.g. "NIFTY PSU BANK" (validate against
    nsepython.nse_get_index_list). Used for sector relative-strength.
    """
    name = "nse_index"
    kinds = (DataKind.OHLCV,)
    needs_auth = False

    # niftyindices.com (via nsepython) sets NO socket timeout — when the host is flaky it
    # blocks forever and wedges the calling skill. Cap it so it raises instead of hanging.
    _TIMEOUT_S = 20

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FTimeout

        from nsepython import index_history
        s, e = start.strftime("%d-%b-%Y"), end.strftime("%d-%b-%Y")
        with ThreadPoolExecutor(max_workers=1) as ex:
            try:
                df = ex.submit(index_history, symbol, s, e).result(timeout=self._TIMEOUT_S)
            except _FTimeout:
                raise TimeoutError(
                    f"niftyindices index_history({symbol!r}) timed out after "
                    f"{self._TIMEOUT_S}s (host unresponsive)") from None
        # raw cols: RequestNumber, Index Name, INDEX_NAME, HistoricalDate, OPEN, HIGH, LOW, CLOSE
        keep = {"HistoricalDate": "date", "OPEN": "open", "HIGH": "high",
                "LOW": "low", "CLOSE": "close"}
        df = df[[c for c in keep if c in df.columns]].rename(columns=keep)
        for c in ("open", "high", "low", "close"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return _finalize(df, date_col="date")


# Canonical NSE index name -> yfinance ticker. niftyindices.com (used by nsepython AND
# jugaad index_df) is Akamai bot-gated: the data POST is silently dropped (read-timeout)
# even with cookie warm-up + browser headers, exactly like nse_eq. yfinance carries these
# index series reliably, so it is the PRIMARY index source. Verified 13/13 sectors 2026-06.
INDEX_YF_TICKERS = {
    "NIFTY 50": "^NSEI", "NIFTY BANK": "^NSEBANK", "NIFTY IT": "^CNXIT",
    "NIFTY PSU BANK": "^CNXPSUBANK", "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY AUTO": "^CNXAUTO", "NIFTY FMCG": "^CNXFMCG", "NIFTY METAL": "^CNXMETAL",
    "NIFTY REALTY": "^CNXREALTY", "NIFTY ENERGY": "^CNXENERGY",
    "NIFTY INFRASTRUCTURE": "^CNXINFRA", "NIFTY PRIVATE BANK": "NIFTY_PVT_BANK.NS",
    "NIFTY FINANCIAL SERVICES": "NIFTY_FIN_SERVICE.NS",
}


@register_data_source
class NselibIndexSource:
    """Sector / broad index daily OHLC via nselib (PRIMARY index source).

    `symbol` is the canonical NSE index name (e.g. "NIFTY PSU BANK", "NIFTY 50") — the
    same names as framework.india_sectors.SECTOR_INDEX, no ticker translation. Returns
    OFFICIAL NSE values + real traded quantity (volume), and bypasses the Akamai gate that
    breaks niftyindices. Verified 13/13 sectors 2026-06.
    """
    name = "nselib_index"
    kinds = (DataKind.OHLCV,)
    needs_auth = False

    _MAP = {
        "OPEN_INDEX_VAL": "open", "HIGH_INDEX_VAL": "high", "LOW_INDEX_VAL": "low",
        "CLOSE_INDEX_VAL": "close", "TRADED_QTY": "volume", "TIMESTAMP": "date",
    }

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        from nselib import capital_market
        df = capital_market.index_data(
            index=symbol, from_date=start.strftime("%d-%m-%Y"), to_date=end.strftime("%d-%m-%Y"))
        df = df.rename(columns={k: v for k, v in self._MAP.items() if k in df.columns})
        for c in ("open", "high", "low", "close", "volume"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        # nselib TIMESTAMP is "%d-%b-%Y" (e.g. "10-JAN-2024"); parse explicitly so the
        # schema is deterministic (no dateutil per-element inference).
        df["date"] = pd.to_datetime(df["date"], format="%d-%b-%Y", errors="coerce")
        return _finalize(df, date_col="date")


@register_data_source
class YfIndexSource:
    """Sector / broad index daily OHLC via yfinance (PRIMARY index source).

    `symbol` is the canonical NSE index name (e.g. "NIFTY PSU BANK", "NIFTY 50"); it is
    mapped to the yfinance ticker via INDEX_YF_TICKERS. Use this for relative strength —
    niftyindices (NseIndexSource) is unreliable (Akamai-gated), kept only as opt-in.
    """
    name = "yf_index"
    kinds = (DataKind.OHLCV,)
    needs_auth = False

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        ticker = INDEX_YF_TICKERS.get(symbol)
        if ticker is None:
            raise KeyError(
                f"no yfinance ticker for index {symbol!r}; known: {sorted(INDEX_YF_TICKERS)}")
        # exchange="US" => YFinanceSource uses the ticker raw (^-prefixed / already .NS)
        return YFinanceSource().history(ticker, start, end, exchange="US")


@register_data_source
class YFinanceSource:
    """Fallback only. yfinance has gaps/bad adjustments for India. Needs .NS/.BO suffix."""
    name = "yfinance"
    kinds = (DataKind.OHLCV,)
    needs_auth = False

    def history(self, symbol, start, end, interval="D", exchange="NSE") -> pd.DataFrame:
        import yfinance as yf
        if exchange in ("NSE", "BSE"):
            suffix = ".NS" if exchange == "NSE" else ".BO"
            sym = symbol if symbol.endswith((".NS", ".BO")) else symbol + suffix
        else:
            sym = symbol  # US / FX / index ticker already in yfinance form (USDINR=X, ^TNX, SPY)
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
class NsdlFpiSource:
    """Official NSDL FPI custody flow via nselib.nsdl_fpi. Verified-working 2026-06 (no auth).

    Richer than nse_fiidii: splits Equity / Debt / Hybrid by investment route, with net in
    BOTH ₹Cr and USD Mn + the USD/INR conversion — so FPI flow ties directly to the dollar
    (the US-driver -> FII-outflow thesis, manuals/01, /12). `trade_date=None` => latest report.
    """
    name = "nsdl_fpi"
    kinds = (DataKind.INSTITUTIONAL_FLOW,)
    needs_auth = False

    _MAP = {
        "REPORT_DATE": "report_date", "ASSET_CLASS": "asset_class",
        "INVESTMENT_ROUTE": "investment_route",
        "GROSS_PURCHASES_RS_CR": "gross_purchases_rs_cr", "GROSS_SALES_RS_CR": "gross_sales_rs_cr",
        "NET_INVESTMENT_RS_CR": "net_rs_cr", "NET_INVESTMENT_USD_MN": "net_usd_mn",
        "USD_INR_CONVERSION": "usd_inr",
    }

    def fetch(self, trade_date=None) -> pd.DataFrame:
        from nselib import nsdl_fpi
        if trade_date is None:
            df = nsdl_fpi.fetch_nsdl_fpi_latest_investment_activity()
        else:
            df = nsdl_fpi.fetch_nsdl_fpi_investment_activity(trade_date)
        df = df.rename(columns={k: v for k, v in self._MAP.items() if k in df.columns})
        if "report_date" in df.columns:
            df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
        for c in ("gross_purchases_rs_cr", "gross_sales_rs_cr", "net_rs_cr", "net_usd_mn", "usd_inr"):
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
