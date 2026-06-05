# 10 — Backtesting discipline

**The thing that makes a result real instead of a story.** Most "edges" are overfitting, look-ahead,
or survivorship artifacts. This manual is the standard every strategy in `strategies/` must pass.

## What it is
- **Look-ahead bias** — using data not yet available at decision time (the #1 silent killer; e.g.
  fitting a regime/HMM on the full sample, using restated fundamentals, same-bar close signals).
- **Survivorship bias** — testing only on names that still exist (delisted losers excluded).
  India-relevant: handle delisted/merged tickers in the universe.
- **Overfitting / multiple testing** — try enough parameters and something looks great by chance.
  Counter: **walk-forward** (rolling out-of-sample), **deflated Sharpe** (penalize for #trials),
  **CPCV** (combinatorial purged cross-validation), purging + embargo around test folds.
- **Costs** — brokerage, **STT** (India securities transaction tax), slippage, impact. A pre-cost
  edge that dies post-cost is not an edge. Our harness models these.
- **The null** — every strategy is ranked against a no-filter / random baseline. Beating nothing
  is the bar.

## Primary sources
- 📕 **Marcos López de Prado — *Advances in Financial Machine Learning*** ← the discipline bible (purging, embargo, CPCV, deflated Sharpe).
- 📄 Bailey & López de Prado (2014), *"The Deflated Sharpe Ratio,"* J. Portfolio Management.
- 📄 Bailey, Borwein, López de Prado & Zhu (2014), *"Pseudo-Mathematics and Financial Charlatanism,"* Notices of the AMS — backtest overfitting.
- 📕 Robert Pardo — *The Evaluation and Optimization of Trading Strategies* (walk-forward).

## Where it fits
The **gate to belief.** Implemented as the single shared evaluator so no strategy is judged by a
different, friendlier yardstick.

## Local implementation
- 🛠 `framework/harness.py` — `BacktestHarness` (walk-forward + `CostModel` + null; `deflated_sharpe`,
  `sharpe_over_null`). `run()` is a stub pending the vectorbt backend.
- 🛠 `engines/backtesting/` references (walk-forward, costs-slippage, performance-analysis).

## Notes
- _(expand: wire vectorbt backend; encode STT/brokerage/slippage for NSE; purge+embargo; report
  deflated Sharpe with trial count; survivorship-safe NSE universe with delisted names.)_
