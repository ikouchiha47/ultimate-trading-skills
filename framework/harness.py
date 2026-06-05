"""BacktestHarness — the single evaluator every strategy is judged by.

The discipline (López de Prado): walk-forward, transaction costs, and ALWAYS a
null model. A strategy that does not beat its null has no edge, regardless of
how good its Sharpe looks in isolation.

This is a skeleton: the orchestration contract is fixed; the compute can be
backed by vectorbt (engines/backtesting) or a simple vectorized loop. Forward
testing happens separately in OpenAlgo's sandbox, not here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .interfaces import IStrategy


# Indian market frictions — make costs explicit, never zero.
@dataclass
class CostModel:
    brokerage_bps: float = 3.0     # ~0.03% discount broker
    stt_bps: float = 10.0          # securities transaction tax (delivery, sell side)
    slippage_bps: float = 5.0      # impact — worse for illiquid oversold names
    # NOTE: oversold mean-reversion names are often the least liquid; slippage
    # is the single biggest killer of this style. Tune per liquidity bucket.


@dataclass
class BacktestResult:
    strategy: str
    cagr: float | None = None
    sharpe: float | None = None
    max_drawdown: float | None = None
    n_trades: int = 0
    # The number that actually matters: edge over the null.
    null_sharpe: float | None = None
    sharpe_over_null: float | None = None
    deflated_sharpe: float | None = None
    notes: list[str] = field(default_factory=list)


class BacktestHarness:
    """Runs a strategy and its null on the SAME data, SAME costs, walk-forward."""

    def __init__(self, costs: CostModel | None = None, oos_fraction: float = 0.3):
        self.costs = costs or CostModel()
        self.oos_fraction = oos_fraction  # held-out tail for out-of-sample check

    def run(self, strategy: IStrategy, data: dict, null: IStrategy | None = None) -> BacktestResult:
        """Execute walk-forward backtest with costs + null comparison.

        TODO(impl): wire to engines/backtesting (vectorbt) or a vectorized loop.
        Contract is intentionally fixed first so every provider plugs in the same
        way. Implementation lands when the first provider (BNF) is registered.
        """
        raise NotImplementedError(
            "Harness contract defined; compute backend wired with first provider."
        )

    def rank(self, data: dict) -> list[BacktestResult]:
        """Backtest every registered strategy and rank by sharpe_over_null."""
        from .registry import strategies
        results = [self.run(s, data) for s in strategies().values()]
        return sorted(
            results,
            key=lambda r: (r.sharpe_over_null if r.sharpe_over_null is not None else -1),
            reverse=True,
        )
