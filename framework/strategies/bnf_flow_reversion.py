"""BNF 25-DMA reversion, flow-gated — the edge hypothesis with the trap filter.

Same snap-back thesis as the price-only ``BnfReversion``, but it only fades a deep
dip when the dip carries a FLOW signature, not an INFORMATION one (manuals/02, /03).
Three gates must ALL agree, on point-in-time data:

  1. dislocation — dist_25dma z below ``entry_z`` (same as the naive version)
  2. absorption  — `flow_classifier.absorption_score` >= ``absorption_min`` (volume +
                   delivery% + close-in-range say a buyer is soaking up the selling)
  3. sector-wide — `flow_classifier.dislocation_breadth` >= ``breadth_min`` (the whole
                   basket fell together = indiscriminate flow, not a lone-name news hit)

The bet: separating absorption-fades from falling-knives is what turns z-score depth
from a trap-finder into an edge. The harness decides if it worked (vs the price-only
version and the null) — nothing here is believed, only tested.
"""
from __future__ import annotations

from ..flow_classifier import absorption_score, dislocation_breadth
from ..interfaces import DataKind, Side, Signal, StrategyMeta
from .bnf_reversion import BnfReversion


class BnfFlowReversion(BnfReversion):
    def __init__(self, *, absorption_min: float = 0.5, breadth_min: float = 0.3,
                 vol_window: int = 20, uptrend_ma: int = 200, **kw):
        super().__init__(uptrend_ma=uptrend_ma, **kw)
        self.absorption_min = absorption_min
        self.breadth_min = breadth_min
        self.vol_window = vol_window

    def meta(self) -> StrategyMeta:
        m = super().meta()
        return StrategyMeta(
            name="bnf-flow-reversion",
            thesis="fade 25-DMA dips ONLY when absorption + sector-wide flow say it's fadeable, not a knife",
            source="BNF/Kotegawa snap-back + flow-vs-information filter (manuals/02,/03)",
            required_data=m.required_data,
            params={**m.params, "absorption_min": self.absorption_min,
                    "breadth_min": self.breadth_min, "vol_window": self.vol_window},
        )

    def generate_signals(self, data: dict[DataKind, object]) -> list[Signal]:
        frames: dict = data.get(DataKind.OHLCV, {})
        z_by = {s: self._dev_z(df["close"].astype(float).dropna()) for s, df in frames.items()}
        breadth = dislocation_breadth(z_by, self.entry_z)   # one regime number for the bar
        sector_wide = breadth >= self.breadth_min

        out: list[Signal] = []
        for sym, df in frames.items():
            close = df["close"].astype(float).dropna()
            z = z_by.get(sym)
            if z is None:
                continue
            if z >= self.exit_z:
                out.append(Signal(sym, Side.FLAT, 0.0, meta={"z": round(z, 2)}))
                continue
            if z < self.entry_z and self._in_uptrend(close):
                absorp = absorption_score(df, window=self.vol_window)
                if absorp is not None and absorp >= self.absorption_min and sector_wide:
                    strength = min(1.0, abs(z - self.entry_z) / 1.5 + 0.5)
                    out.append(Signal(sym, Side.LONG, strength,
                                      meta={"z": round(z, 2), "absorption": round(absorp, 2),
                                            "breadth": round(breadth, 2)}))
            # otherwise: emit nothing -> hold prior (band hysteresis)
        return out
