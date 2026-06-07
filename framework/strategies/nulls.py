"""Null models — the bar every strategy must clear.

A strategy with no edge is one that does not beat a *naive* alternative on the same
data and costs. The default null is equal-weight buy-and-hold of the same basket:
if a clever entry/exit rule cannot beat simply owning the names, it has no edge.
"""
from __future__ import annotations

from ..interfaces import DataKind, IStrategy, Side, Signal, StrategyMeta


class BuyAndHoldBasket(IStrategy):
    """Hold every symbol in the basket, equal weight, always long.

    The honest baseline for a long-only mean-reversion basket: it captures the
    market beta the strategy is also exposed to, so ``sharpe_over_null`` isolates
    the timing edge from the beta.
    """

    def __init__(self, symbols: list[str]):
        self._symbols = list(symbols)

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            name="null:buy-and-hold",
            thesis="own the basket; no timing — the beta-only baseline",
            source="null model (López de Prado discipline)",
            required_data=(DataKind.OHLCV,),
        )

    def generate_signals(self, data: dict[DataKind, object]) -> list[Signal]:
        frames = data.get(DataKind.OHLCV, {})
        syms = self._symbols or list(frames)
        return [Signal(symbol=s, side=Side.LONG, strength=1.0) for s in syms]
