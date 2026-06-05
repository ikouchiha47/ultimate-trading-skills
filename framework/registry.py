"""Registries so providers are discoverable and interchangeable.

Register a data source or strategy once; the harness can then enumerate and
rank everything uniformly. This is what makes "the strategy zoo" a zoo.
"""

from __future__ import annotations

from .interfaces import IDataSource, IStrategy

_DATA_SOURCES: dict[str, IDataSource] = {}
_STRATEGIES: dict[str, IStrategy] = {}


def register_data_source(src: IDataSource) -> IDataSource:
    _DATA_SOURCES[src.name] = src
    return src


def register_strategy(strat: IStrategy) -> IStrategy:
    _STRATEGIES[strat.meta().name] = strat
    return strat


def data_sources() -> dict[str, IDataSource]:
    return dict(_DATA_SOURCES)


def strategies() -> dict[str, IStrategy]:
    return dict(_STRATEGIES)
