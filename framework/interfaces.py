"""Core contracts for the strategy zoo.

Two pluggable abstractions, evaluated empirically:

    IDataSource  — where data comes from (OpenAlgo, jugaad-data, screener, macro, ...)
    IStrategy    — a documented strategy, sourced from a paper or a recorded trader,
                   that turns data into positions. Nothing privileged; every provider
                   earns its place via the BacktestHarness against a null.

Design stance: "first know what works." A strategy is *registered and tested*,
not believed. See README and manuals/.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Protocol, runtime_checkable

import pandas as pd


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

class DataKind(str, Enum):
    OHLCV = "ohlcv"            # price bars (stocks AND indices)
    FUNDAMENTALS = "fundamentals"
    SECTOR_BREADTH = "sector_breadth"
    INSTITUTIONAL_FLOW = "institutional_flow"  # FII/DII
    MACRO = "macro"           # credit growth, G-Sec yields, CPI (RBI/MOSPI/CMIE)
    FUND_NAV = "fund_nav"     # mutual-fund scheme NAV (AMFI via mftool)


# Canonical normalized schema for any OHLCV source. Adapters MUST return these as
# lowercase columns on an ascending DatetimeIndex.
OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")
# Sources MAY append extra columns beyond OHLCV (consumers ignore unknown ones). India
# stock feeds add delivery data — valuable for flow-vs-information (manuals/02).
OHLCV_EXTRA_COLUMNS = ("delivery_pct", "deliverable_qty", "vwap", "trades")


@runtime_checkable
class IDataSource(Protocol):
    """Every data adapter implements this. Keeps strategies source-agnostic."""

    name: str
    kinds: tuple[DataKind, ...]
    needs_auth: bool

    def history(
        self, symbol: str, start: date, end: date, interval: str = "D", exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Return a price-bar frame on an ascending DatetimeIndex.

        Guarantees lowercase OHLC columns (open, high, low, close); `volume` is present
        for stocks (NaN/absent for index sources, which have no volume). Sources MAY add
        extra columns from OHLCV_EXTRA_COLUMNS (e.g. delivery_pct). No look-ahead: the
        last row is the most recent COMPLETED bar.
        """
        ...


# ---------------------------------------------------------------------------
# Strategy layer
# ---------------------------------------------------------------------------

class Side(str, Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


@dataclass
class Signal:
    """One positioning decision for one symbol on one bar."""

    symbol: str
    side: Side
    strength: float = 1.0          # 0..1, used for sizing / conviction
    meta: dict = field(default_factory=dict)


@dataclass
class StrategyMeta:
    """Provenance — the academic part. Where did this strategy come from?"""

    name: str
    thesis: str                    # one-line edge hypothesis (flow vs information)
    source: str                    # paper / trader / book it is reproduced from
    required_data: tuple[DataKind, ...]
    params: dict = field(default_factory=dict)


class IStrategy(ABC):
    """The contract every StrategyProvider implements."""

    @abstractmethod
    def meta(self) -> StrategyMeta: ...

    @abstractmethod
    def generate_signals(self, data: dict[DataKind, object]) -> list[Signal]:
        """Given the data it declared in required_data, emit target positions.

        Pure function of *point-in-time* data — no look-ahead. The harness is
        responsible for feeding only data available as of each bar.
        """
        ...
