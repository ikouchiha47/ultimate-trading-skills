"""BNF mean-reversion — the first StrategyProvider, as a reference implementation.

Source: Takashi Kotegawa ("BNF") — buy names that deviated sharply BELOW their
short moving average (forced/uninformed selling), expecting a snap-back. Formalized
as a deviation z-score (CONCEPTS_REFERENCES.md §1, §2).

Thesis (flow vs information): a large negative deviation from the local mean is
*sometimes* a forced seller, not news. Only then is it a trade. The quality filter
(ScreenerSource) and sector context (sector-analyst) are what separate the two —
this raw provider does NOT, by design, so the harness can measure how much the
filters actually add (the null = this, unfiltered).
"""

from __future__ import annotations

import pandas as pd

from framework.interfaces import DataKind, IStrategy, Side, Signal, StrategyMeta
from framework.registry import register_strategy


@register_strategy
class MeanReversionBNF(IStrategy):
    def __init__(self, lookback: int = 25, z_entry: float = -2.0):
        self.lookback = lookback
        self.z_entry = z_entry

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            name="mean_reversion_bnf",
            thesis="Large negative deviation from local mean = possible forced seller; fade for snap-back.",
            source="Takashi Kotegawa (BNF); Jegadeesh 1990 short-term reversal",
            required_data=(DataKind.OHLCV,),
            params={"lookback": self.lookback, "z_entry": self.z_entry},
        )

    def generate_signals(self, data: dict) -> list[Signal]:
        # data[DataKind.OHLCV]: {symbol: DataFrame[..., 'close']} as of current bar.
        ohlcv: dict[str, pd.DataFrame] = data[DataKind.OHLCV]
        signals: list[Signal] = []
        for symbol, df in ohlcv.items():
            close = df["close"]
            if len(close) < self.lookback:
                continue
            window = close.iloc[-self.lookback:]
            mean, std = window.mean(), window.std()
            if std == 0:
                continue
            z = (close.iloc[-1] - mean) / std
            if z <= self.z_entry:                      # stretched below mean -> fade
                signals.append(Signal(symbol, Side.LONG, strength=min(1.0, abs(z) / 3),
                                      meta={"z": round(float(z), 2)}))
        return signals
