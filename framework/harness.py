"""BacktestHarness — the single evaluator every strategy is judged by.

The discipline (López de Prado): walk-forward, transaction costs, and ALWAYS a
null model. A strategy that does not beat its null has no edge, regardless of
how good its Sharpe looks in isolation.

This is a skeleton: the orchestration contract is fixed; the compute can be
backed by vectorbt (engines/backtesting) or a simple vectorized loop. Forward
testing happens separately in OpenAlgo's sandbox, not here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .interfaces import DataKind, IStrategy, Side


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

    # -- data convention -----------------------------------------------------
    # data[DataKind.OHLCV] is a dict[symbol -> DataFrame] (lowercase OHLCV cols,
    # ascending DatetimeIndex). Every other DataKind a strategy declares is passed
    # through untouched; the harness only needs prices to mark P&L.

    @staticmethod
    def _close_wide(data: dict) -> pd.DataFrame:
        frames = data[DataKind.OHLCV]
        if not isinstance(frames, dict):
            raise TypeError("data[OHLCV] must be a dict[symbol -> DataFrame] for backtesting")
        cols = {sym: df["close"].astype(float) for sym, df in frames.items() if len(df)}
        wide = pd.DataFrame(cols).sort_index()
        return wide.loc[~wide.index.duplicated(keep="last")]

    def _simulate_positions(self, strategy: IStrategy, data: dict, close: pd.DataFrame) -> pd.DataFrame:
        """Walk the timeline, feeding the strategy only point-in-time data.

        At each bar t the strategy sees frames sliced to ``.loc[:t]`` (last row =
        the just-completed bar), and emits a target Side per symbol. No look-ahead:
        execution of those targets is shifted one bar by the portfolio layer.
        """
        frames = data[DataKind.OHLCV]
        passthrough = {k: v for k, v in data.items() if k != DataKind.OHLCV}
        pos = pd.DataFrame(0.0, index=close.index, columns=close.columns)
        sign = {Side.LONG: 1.0, Side.SHORT: -1.0, Side.FLAT: 0.0}
        held = dict.fromkeys(close.columns, 0.0)   # carry-forward state for hysteresis
        for t in close.index:
            pit = {sym: df.loc[:t] for sym, df in frames.items()}
            pit = {sym: f for sym, f in pit.items() if len(f)}
            signals = strategy.generate_signals({DataKind.OHLCV: pit, **passthrough})
            # A symbol with no signal this bar HOLDS its prior position (the band
            # between entry_z and exit_z); only an explicit Signal changes it.
            for s in signals:
                if s.symbol in held:
                    held[s.symbol] = sign[s.side] * float(s.strength)
            for sym, v in held.items():
                pos.at[t, sym] = v
        return pos

    def _portfolio(self, positions: pd.DataFrame, close: pd.DataFrame):
        import vectorbt as vbt

        # Decide on bar t, execute on t+1 — shift targets forward to kill look-ahead.
        target = positions.shift(1).fillna(0.0)
        long_only = target.clip(lower=0.0)            # v1 strategies are long-only baskets
        entries = (long_only > 0) & (long_only.shift(1).fillna(0.0) <= 0)
        exits = (long_only <= 0) & (long_only.shift(1).fillna(0.0) > 0)
        fees = (self.costs.brokerage_bps + self.costs.stt_bps) / 1e4
        slippage = self.costs.slippage_bps / 1e4
        return vbt.Portfolio.from_signals(
            close, entries, exits,
            fees=fees, slippage=slippage,
            freq="1D", group_by=True, cash_sharing=True,
        )

    @staticmethod
    def _sharpe(pf) -> float | None:
        try:
            s = pf.sharpe_ratio()
            return float(s) if np.isfinite(s) else None
        except Exception:
            return None

    @staticmethod
    def _deflated_sharpe(observed: float | None, n_trials: int, n_obs: int) -> float | None:
        """Probability the observed Sharpe is real after multiple-testing inflation.

        López de Prado's Deflated Sharpe Ratio with a Bonferroni-style expected-max
        benchmark for the null Sharpe (skew/kurtosis assumed Normal at v1).
        """
        if observed is None or n_trials < 1 or n_obs < 3:
            return None
        from scipy.stats import norm

        if n_trials == 1:
            sr_star = 0.0                         # single trial: no selection inflation
        else:
            e_max = (1 - np.euler_gamma) * norm.ppf(1 - 1 / n_trials) + \
                np.euler_gamma * norm.ppf(1 - 1 / (n_trials * np.e))
            sr_star = e_max / math.sqrt(n_obs - 1)   # expected-max Sharpe under the null
        denom = math.sqrt(1 - 0 * observed + (observed ** 2) / 2) / math.sqrt(n_obs - 1)
        if denom == 0:
            return None
        return float(norm.cdf((observed - sr_star) / denom))

    def run(self, strategy: IStrategy, data: dict, null: IStrategy | None = None,
            n_trials: int = 1) -> BacktestResult:
        """Walk-forward backtest with explicit costs + a null comparison.

        Same data, same costs for strategy and null. ``sharpe_over_null`` is the
        number that matters; the OOS-tail Sharpe is reported in notes. ``n_trials``
        is how many strategy variants were tried (for the deflated Sharpe).
        """
        close = self._close_wide(data)
        if close.empty:
            raise ValueError("no priceable OHLCV in data — cannot backtest")

        pos = self._simulate_positions(strategy, data, close)
        pf = self._portfolio(pos, close)
        res = BacktestResult(strategy=strategy.meta().name)
        res.n_trades = int(pf.trades.count()) if hasattr(pf.trades, "count") else 0
        res.sharpe = self._sharpe(pf)
        try:
            res.cagr = float(pf.annualized_return())
            res.max_drawdown = float(pf.max_drawdown())
        except Exception:
            pass

        if null is None:
            from .strategies.nulls import BuyAndHoldBasket
            null = BuyAndHoldBasket(list(close.columns))
        null_pos = self._simulate_positions(null, data, close)
        null_pf = self._portfolio(null_pos, close)
        res.null_sharpe = self._sharpe(null_pf)
        if res.sharpe is not None and res.null_sharpe is not None:
            res.sharpe_over_null = res.sharpe - res.null_sharpe

        res.deflated_sharpe = self._deflated_sharpe(res.sharpe, n_trials, len(close))

        # Out-of-sample tail check (no re-fit at v1 — strategies are parameter-fixed).
        split = int(len(close) * (1 - self.oos_fraction))
        if 3 < split < len(close):
            oos_idx = close.index[split:]
            oos_pf = self._portfolio(pos.loc[oos_idx], close.loc[oos_idx])
            oos_sh = self._sharpe(oos_pf)
            res.notes.append(f"OOS-tail Sharpe ({int(self.oos_fraction*100)}%): "
                             + (f"{oos_sh:.2f}" if oos_sh is not None else "n/a"))
        if res.sharpe_over_null is not None:
            verdict = "EDGE" if res.sharpe_over_null > 0 else "no edge over null"
            res.notes.append(f"{verdict}: Sharpe {res.sharpe:.2f} vs null {res.null_sharpe:.2f}")
        return res

    def rank(self, data: dict) -> list[BacktestResult]:
        """Backtest every registered strategy and rank by sharpe_over_null."""
        from .registry import strategies
        results = [self.run(s, data) for s in strategies().values()]
        return sorted(
            results,
            key=lambda r: (r.sharpe_over_null if r.sharpe_over_null is not None else -1),
            reverse=True,
        )
