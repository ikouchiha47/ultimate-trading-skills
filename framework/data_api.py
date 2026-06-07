"""The single data seam every skill imports.

Skills MUST get data through this façade — never by importing yfinance / FMP / FRED /
broker-MCP / a GitHub CSV directly. That keeps ONE audited path, so two skills can't
silently disagree, and a missing India source fails loudly instead of quietly serving
US data or a fabricated number.

Policy (see PORTING_PLAN.md, decided):
  - Numeric data we have NOT audited for India -> raise MissingDataSource("MISSING: ...").
    Hard fail. No US fallback, no web-search number standing in for a computed one.
  - Narrative/news MAY use date-scoped WebSearch, but only via news(..., since=...), which
    returns an agent directive labelled provenance="sourced" (dated URL) — never "computed".

Every record this module returns carries a `provenance` tag: "computed" (from an audited
numeric feed) or "sourced" (a dated external citation the agent fetched).

Audited adapters wrapped here live in data/sources.py and data/nse_constituents.py
(status table in CLAUDE.md). Verified 2026-06.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd

# ---------------------------------------------------------------------------
# Failure + provenance primitives
# ---------------------------------------------------------------------------

class MissingDataSource(NotImplementedError):
    """Raised when a skill asks for India data we have not audited/built yet.

    The message always starts with 'MISSING: ' and names the concrete gap, so the
    skill (and the human) see exactly which source must be built — never a silent
    US fallback or a placeholder number.
    """


PROVENANCE_COMPUTED = "computed"   # from an audited numeric feed
PROVENANCE_SOURCED = "sourced"     # a dated external citation the agent fetched


def _as_date(d: str | date | None, default: date | None = None) -> date | None:
    if d is None:
        return default
    if isinstance(d, date):
        return d
    return datetime.strptime(str(d), "%Y-%m-%d").date()


# ---------------------------------------------------------------------------
# Price / index
# ---------------------------------------------------------------------------

# What `source=` may be for history(). jugaad is primary (adds delivery%); yfinance
# is the documented fallback (must be asked for explicitly — no silent fallback).
_PRICE_SOURCES = {"jugaad", "yfinance"}


def history(symbol: str, since: str | date, until: str | date | None = None,
            source: str = "jugaad", exchange: str = "NSE") -> pd.DataFrame:
    """Per-stock OHLCV (+ delivery% from jugaad) on an ascending DatetimeIndex.

    source: "jugaad" (primary, adds delivery_pct/deliverable_qty) | "yfinance" (fallback).
    Raises on fetch failure — does NOT silently fall back to another source.
    """
    if source not in _PRICE_SOURCES:
        raise ValueError(f"history source must be one of {_PRICE_SOURCES}, got {source!r}")
    start = _as_date(since)
    end = _as_date(until, date.today())
    if source == "jugaad":
        from data.sources import JugaadData
        return JugaadData().history(symbol, start, end, exchange=exchange)
    from data.sources import YFinanceSource
    return YFinanceSource().history(symbol, start, end, exchange=exchange)


def index(name: str, since: str | date, until: str | date | None = None,
          source: str = "nselib") -> pd.DataFrame:
    """Sector / broad-market index daily OHLC, e.g. "NIFTY PSU BANK", "NIFTY 50".

    source: "nselib" (PRIMARY — official NSE OHLC + volume, bypasses Akamai) |
    "yfinance" (fallback, adjusted, no volume) | "niftyindices" (opt-in; Akamai-gated,
    may time out — see CLAUDE.md). Used for relative strength.
    """
    start, end = _as_date(since), _as_date(until, date.today())
    if source == "nselib":
        from data.sources import NselibIndexSource
        return NselibIndexSource().history(name, start, end)
    if source == "yfinance":
        from data.sources import INDEX_YF_TICKERS, YfIndexSource
        if name not in INDEX_YF_TICKERS:
            raise MissingDataSource(
                f"MISSING: no yfinance index ticker for {name!r}; "
                f"known: {sorted(INDEX_YF_TICKERS)}")
        return YfIndexSource().history(name, start, end)
    if source == "niftyindices":
        from data.sources import NseIndexSource
        return NseIndexSource().history(name, start, end)
    raise ValueError(f"index source must be nselib/yfinance/niftyindices, got {source!r}")


# ---------------------------------------------------------------------------
# Flow (the thesis input)
# ---------------------------------------------------------------------------

def fii_dii(since: str | date | None = None) -> pd.DataFrame:
    """FII/FPI + DII daily cash flow (buy/sell/net by category).

    NOTE: nse_fiidii is a latest-snapshot endpoint, not a long history — `since` is
    accepted for interface symmetry but the source returns only recent rows. A longer
    FII/DII history is a known gap (NSDL/Bloomberg) -> tracked, not faked.
    """
    from data.sources import FiiDiiSource
    return FiiDiiSource().history()


def fpi_flow(trade_date: str | date | None = None) -> pd.DataFrame:
    """Official NSDL FPI custody flow — Equity/Debt split, net in ₹Cr AND USD Mn + USD/INR.

    Authoritative FPI flow (vs fii_dii()'s provisional daily cash pulse). trade_date=None
    => latest report. Ties foreign flow to the dollar (US-driver thesis, manuals/12).
    """
    from data.sources import NsdlFpiSource
    return NsdlFpiSource().fetch(_as_date(trade_date) if trade_date else None)


# ---------------------------------------------------------------------------
# Constituents
# ---------------------------------------------------------------------------

def constituents(sector: str | None = None, source: str = "nselib") -> dict[str, list[str]] | list[str]:
    """Sector membership. source: "nselib" (live, PRIMARY, Akamai-free) | "nse_csv" (cached
    offline) | "nse_fetch" (niftyindices live) | "seed". Layered fallback to seed.

    Returns the full sector->symbols map, or just one sector's list if `sector` is given.
    """
    from framework.india_sectors import load_sector_constituents
    full = load_sector_constituents(source)
    if sector is None:
        return full
    if sector not in full:
        raise MissingDataSource(f"MISSING: no constituent list for sector {sector!r}")
    return full[sector]


def index_members(index_name: str) -> list[str]:
    """Symbols of ANY NSE index via nselib (Akamai-free), e.g. "Nifty 500", "Nifty PSU Bank",
    "Nifty Midcap 150". Valid names are catalogued in data/index_catalog.md.
    """
    from data.nse_constituents import fetch_index_members
    return fetch_index_members(index_name)


# ---------------------------------------------------------------------------
# Mutual-fund NAV
# ---------------------------------------------------------------------------

def nav(scheme_code: str | None = None, category: str | None = None) -> pd.DataFrame:
    """Mutual-fund scheme NAV history (AMFI via mftool). Pass a scheme_code.

    `category` lookup (e.g. "Banking and PSU Fund") is not wired yet -> MISSING until
    the scheme-code resolver is added.
    """
    if scheme_code is None:
        raise MissingDataSource(
            "MISSING: scheme-code resolver for category lookups; pass an explicit scheme_code")
    from data.sources import MutualFundSource
    return MutualFundSource().history(scheme_code)


# ---------------------------------------------------------------------------
# US drivers of FII flow (EXOGENOUS inputs — NOT a tradeable universe)
# ---------------------------------------------------------------------------

# Drivers fetchable via yfinance today. NSDL/CDSL FPI flow is a separate gap (MISSING).
_DRIVER_TICKERS = {
    "USDINR": "USDINR=X", "DXY": "DX-Y.NYB", "US10Y": "^TNX",
    "SPY": "SPY", "QQQ": "QQQ", "VIX": "^VIX",
}


def driver(name: str, since: str | date, until: str | date | None = None) -> pd.DataFrame:
    """Exogenous US/global driver of FII flow (dollar, US yields, US equity, vol).

    These contextualize flow-vs-information (manuals/01); they are NEVER a universe we
    trade. FPI custody flow (NSDL/CDSL) is a known gap -> MISSING.
    """
    key = name.upper()
    if key in {"FPI", "NSDL", "FPI_FLOW"}:
        raise ValueError("FPI flow is an institutional-flow input, not a market driver — "
                         "use data_api.fpi_flow()")
    if key not in _DRIVER_TICKERS:
        raise MissingDataSource(
            f"MISSING: driver {name!r}; known drivers: {sorted(_DRIVER_TICKERS)}")
    from data.sources import YFinanceSource
    df = YFinanceSource().history(_DRIVER_TICKERS[key], _as_date(since),
                                  _as_date(until, date.today()), exchange="US")
    return df


# ---------------------------------------------------------------------------
# Breadth (Step 1 — not built yet; hard-fail loudly)
# ---------------------------------------------------------------------------

def breadth(universe: str, since: str | date, until: str | date | None = None,
            source: str = "yfinance") -> pd.DataFrame:
    """Market/sector breadth time series: % above 50/200-DMA, advance/decline, new highs/lows.

    Computed from constituent OHLCV via history() (not a pre-built US breadth CSV).
    `universe` is a sector name ("PSU Bank") or "NIFTY 50". source defaults to yfinance
    (fast across many names for a scan). See data/breadth.py.
    """
    from data.breadth import sector_breadth
    return sector_breadth(universe, _as_date(since), _as_date(until, date.today()), source=source)


# ---------------------------------------------------------------------------
# Fundamentals (Step 1 — audit pending)
# ---------------------------------------------------------------------------

def fundamentals(symbol: str) -> dict:
    """Quality metrics (P/E, ROCE, ROE, book value, debt) — the 'shouldn't have fallen' test.

    Scrapes screener.in via the vendored equity-research Playwright reader (uses the saved
    session if present; public ratios need no login). Returns {symbol, url, ratios, numeric}.
    Needs the [scrape] extra + `playwright install chromium` -> else MISSING with that hint.
    """
    import importlib.util
    from pathlib import Path

    reader_path = (Path(__file__).resolve().parents[1] / "skills" / "fundamentals" /
                   "equity-research" / "scripts" / "screener_reader.py")
    spec = importlib.util.spec_from_file_location("screener_reader", reader_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except ImportError as e:  # playwright not installed
        raise MissingDataSource(
            f"MISSING: screener.in needs the [scrape] extra + `playwright install chromium` ({e})"
        ) from None
    return mod.fetch_company_fundamentals(symbol)


# ---------------------------------------------------------------------------
# Option chain (no audited free India source)
# ---------------------------------------------------------------------------

def option_chain(symbol: str) -> pd.DataFrame:
    """NSE option chain. nse_eq-class endpoints are Akamai-blocked (CLAUDE.md) -> MISSING.

    Real-time options are OpenAlgo's job (live broker session), deferred.
    """
    raise MissingDataSource(
        "MISSING: audited India option-chain source (nseindia API is Akamai-blocked; "
        "use OpenAlgo with a live broker session — deferred)")


# ---------------------------------------------------------------------------
# News — recent (RSS, computed-ish) vs historical (agent WebSearch, sourced)
# ---------------------------------------------------------------------------

@dataclass
class WebSearchDirective:
    """Returned for point-in-time news. A python lib can't call WebSearch — the AGENT must.

    The skill's SKILL.md instructs the agent to run `suggested_query`, then attach each
    result as a record with provenance="sourced" and its dated URL. NEVER let a sourced
    item stand in for a computed number.
    """
    query: str
    suggested_query: str
    since: date
    until: date | None
    provenance: str = PROVENANCE_SOURCED
    note: str = ("Run this as a date-scoped WebSearch; cite dated URLs; label provenance="
                 "'sourced'. Do not use for any numeric (price/flow/breadth) value.")


def news(query: str, since: str | date | None = None,
         until: str | date | None = None) -> list[dict] | WebSearchDirective:
    """Recent news via RSS (since=None); point-in-time via an agent WebSearch directive.

    since=None  -> live RSS items (india-news-tracker fetcher), each tagged provenance.
    since set    -> WebSearchDirective the agent must fulfill (historical RSS doesn't exist).
    """
    if since is None:
        try:
            from skills.screeners.india_news_tracker.scripts import news_fetcher  # type: ignore
        except Exception:  # noqa: BLE001
            raise MissingDataSource(
                "MISSING: news RSS fetcher import (skills/screeners/india-news-tracker); "
                "install the [news] extra (feedparser)")
        items = news_fetcher.fetch(query) if hasattr(news_fetcher, "fetch") else []
        for it in items:
            it.setdefault("provenance", PROVENANCE_SOURCED)
        return items
    s = _as_date(since)
    u = _as_date(until, None)
    window = f"{s:%B %Y}" + (f" to {u:%B %Y}" if u else "")
    return WebSearchDirective(query=query, suggested_query=f"{query} India {window}",
                              since=s, until=u)
