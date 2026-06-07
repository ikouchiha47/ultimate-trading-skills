---
name: strategy-harness
description: >
  Backtest an India strategy against a null with realistic costs and report whether it has
  an EDGE (Sharpe over null), not just a pretty Sharpe. Use when asked "does <strategy> work",
  "backtest the 25-DMA reversion", "is there an edge", to compare a strategy to buy-and-hold,
  or to rank the strategy zoo. Drives framework/harness.py — the single evaluator. India-only.
tags: [india, backtest, edge, mean-reversion, null-model, vectorbt, bnf]
triggers: [backtest, does it work, edge over null, sharpe, walk-forward, mean reversion, 25-dma, strategy zoo]
---

# Strategy harness (India)

## Overview

`framework/harness.py` is the **single evaluator** every strategy is judged by (López de Prado
discipline: explicit costs, walk-forward OOS, and ALWAYS a null). The number that matters is
`sharpe_over_null`, not the raw Sharpe — a long-only basket strategy is exposed to the same beta
as buy-and-hold, so only the excess over the null isolates a real timing edge.

The harness is **generic**: it takes any `IStrategy` (the contract in `framework/interfaces.py`)
plus a point-in-time data dict, walks the timeline feeding the strategy only past bars (no
look-ahead — execution is shifted one bar), and marks P&L through `vectorbt` with the `CostModel`
(brokerage + STT + slippage). **You (the agent) pick the basket, the period and read the verdict**;
the engine computes.

## Workflow

### 1. Assemble the data dict (you pick the basket)

```python
from framework import data_api
from framework.interfaces import DataKind

members = data_api.index_members("NIFTY PSU BANK")        # valid names: data/index_catalog.md
frames = {s: data_api.history(s, "2021-01-01") for s in members}
frames = {s: df for s, df in frames.items() if len(df) > 250}   # need warm-up for the 200-DMA filter
data = {DataKind.OHLCV: frames}     # convention: OHLCV -> dict[symbol -> DataFrame]
```

### 2. Run vs a null

```python
from framework.harness import BacktestHarness
from framework.strategies.bnf_reversion import BnfReversion
from framework.strategies.nulls import BuyAndHoldBasket

res = BacktestHarness().run(BnfReversion(), data,
                            null=BuyAndHoldBasket(list(frames)), n_trials=1)
print(res.sharpe, res.null_sharpe, res.sharpe_over_null, res.notes)
```

`run(strategy, data, null=None, n_trials=1)` → `BacktestResult(cagr, sharpe, max_drawdown,
n_trades, null_sharpe, sharpe_over_null, deflated_sharpe, notes)`. If `null=None` it defaults to
equal-weight buy-and-hold of the same basket. `n_trials` = how many variants you tried (feeds the
deflated Sharpe — be honest, it penalises over-fitting). `BacktestHarness().rank(data)` backtests
every registered strategy in the zoo and sorts by `sharpe_over_null`.

### 3. Interpret (your job)

| field | read it as |
|---|---|
| `sharpe_over_null > 0` | the strategy's timing adds value beyond owning the basket — a candidate EDGE |
| `sharpe_over_null <= 0` | **no edge** — the rule loses to buy-and-hold; do not promote it |
| `deflated_sharpe` | P(Sharpe is real vs 0 after multiple-testing); want > ~0.95, and falls fast as `n_trials` rises |
| OOS-tail note | Sharpe on the held-out tail (`oos_fraction`, default 30%) — should not collapse vs full-sample |
| `n_trades` | too few ⇒ not enough evidence; too many ⇒ costs dominate |

## Discipline

- **Report the honest verdict, including failure.** A negative `sharpe_over_null` is a real
  result, not a bug to tune away — the price-only `BnfReversion` losing to a PSU-Bank bull-run
  null is the *expected* finding (manuals/03): indiscriminate fading has no edge; only fading
  *flow-driven* dips does. That is what the flow-vs-information filter is for (next edge item).
- Costs are never zero — `CostModel` (brokerage 3bps + STT 10bps + slippage 5bps). Oversold
  mean-reversion names are the least liquid; raise `slippage_bps` per liquidity bucket.
- No look-ahead: the harness shifts execution one bar after the signal. Never special-case it away.
- Survivorship: constituents come from the live index today. For a clean test use a point-in-time
  membership snapshot when available (cached CSVs in `data/constituents/`).

## Engine reference

- `framework/interfaces.py` — `IStrategy` (`meta()` + `generate_signals(data) -> list[Signal]`),
  `Signal`, `Side`, `DataKind`, `StrategyMeta`. Strategies are point-in-time pure functions.
- `framework/harness.py` — `BacktestHarness(costs=CostModel(), oos_fraction=0.3)`, `.run`, `.rank`;
  `CostModel`, `BacktestResult`.
- `framework/strategies/` — the zoo: `bnf_reversion.BnfReversion` (25-DMA snap-back),
  `nulls.BuyAndHoldBasket`. New strategies implement `IStrategy` and `register_strategy(...)`.
