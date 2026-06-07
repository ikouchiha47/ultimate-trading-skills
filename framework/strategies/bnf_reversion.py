"""BNF / Kotegawa 25-DMA mean-reversion — the first edge under test.

Thesis (manuals/03): in a flow-driven dislocation, a fundamentally-fine name gets
sold *with* its basket and snaps back toward its 25-day moving average. The marker
is a deep, anomalous deviation below the 25-DMA (z-scored), entered only while the
name is still structurally in an uptrend so we fade a *dip*, not a *breakdown*.

This is the price-only v1. The flow-vs-information filter (fadeable vs trap — FII
flow, delivery%, sector mode) is the *next* edge item and plugs in as an entry gate
via ``meta().required_data`` once built; here the strategy is deliberately naive so
the harness measures the raw 25-DMA effect before any enrichment.

Stateless target-position semantics (the harness walks bars in order and shifts
execution forward one bar): LONG while the z-deviation sits below ``entry_z``; FLAT
once it recovers past ``exit_z``. The band gives hysteresis without internal state.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..interfaces import DataKind, IStrategy, Side, Signal, StrategyMeta


class BnfReversion(IStrategy):
    def __init__(self, *, ma: int = 25, entry_z: float = -1.5, exit_z: float = -0.25,
                 z_window: int = 120, uptrend_ma: int = 200):
        # entry_z: how many std-devs below typical the 25-DMA gap must be to fade.
        # exit_z:  band edge to flatten on recovery. uptrend_ma: structural filter.
        self.ma = ma
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.z_window = z_window
        self.uptrend_ma = uptrend_ma

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            name="bnf-25dma-reversion",
            thesis="fade flow-driven dips below the 25-DMA in structurally-uptrending names",
            source="BNF / Kotegawa 25-DMA snap-back (manuals/03)",
            required_data=(DataKind.OHLCV,),
            params={"ma": self.ma, "entry_z": self.entry_z, "exit_z": self.exit_z,
                    "z_window": self.z_window, "uptrend_ma": self.uptrend_ma},
        )

    def _dev_z(self, close: pd.Series) -> float | None:
        if len(close) < max(self.ma, self.uptrend_ma):
            return None
        ma = close.rolling(self.ma).mean()
        dev = ((close - ma) / ma).dropna()
        if len(dev) < self.z_window:
            return None
        recent = dev.iloc[-self.z_window:]
        sd = recent.std()
        if not sd or not np.isfinite(sd):
            return None
        return float((dev.iloc[-1] - recent.mean()) / sd)

    def _in_uptrend(self, close: pd.Series) -> bool:
        if not self.uptrend_ma:            # 0/None => no structural gate
            return True
        if len(close) < self.uptrend_ma:
            return False
        return float(close.iloc[-1]) > float(close.rolling(self.uptrend_ma).mean().iloc[-1])

    def generate_signals(self, data: dict[DataKind, object]) -> list[Signal]:
        frames: dict = data.get(DataKind.OHLCV, {})
        out: list[Signal] = []
        for sym, df in frames.items():
            close = df["close"].astype(float).dropna()
            z = self._dev_z(close)
            if z is None:
                continue
            if z < self.entry_z and self._in_uptrend(close):
                # deeper below the band => stronger conviction, capped at 1.
                strength = min(1.0, abs(z - self.entry_z) / 1.5 + 0.5)
                out.append(Signal(sym, Side.LONG, strength, meta={"z": round(z, 2)}))
            elif z >= self.exit_z:
                out.append(Signal(sym, Side.FLAT, 0.0, meta={"z": round(z, 2)}))
            # in the band between exit_z and entry_z: emit nothing -> hold prior.
        return out
