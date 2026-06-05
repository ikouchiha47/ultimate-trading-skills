# 04 — Momentum & trend

**The opposite leg.** Know it precisely so we don't fade a genuine informed trend (which would be
fighting momentum — the fast way to lose on a mean-reversion book).

## What it is
- **Cross-sectional momentum** — past winners (3–12 month) keep winning over the next 3–12 months.
  The single most robust anomaly in the literature.
- **Time-series / absolute momentum** — an asset's own past return predicts its future sign.
- **The reversal/momentum boundary** — *short* horizon (days–weeks) = reversal (our edge, manual 03);
  *intermediate* horizon (months) = momentum. Knowing which regime a move is in tells us whether to
  fade or stand aside.

## Primary sources
- 📄 **Jegadeesh & Titman (1993), *"Returns to Buying Winners and Selling Losers,"* J. Finance** — the momentum paper.
- 📄 Moskowitz, Ooi & Pedersen (2012), *"Time Series Momentum,"* J. Financial Economics.
- 📄 Asness, Moskowitz & Pedersen (2013), *"Value and Momentum Everywhere,"* J. Finance.
- 📕 Andreas Clenow — *Stocks on the Move* (practitioner momentum, implementable).

## Where it fits
A **guardrail / filter**. If a name's intermediate-term momentum is strongly negative on real
volume and information, the "oversold" reading is a value trap, not a reversion setup — skip it.

## Local implementation
- (none yet) — candidate for a momentum `StrategyProvider` to (a) backtest as a comparison and
  (b) serve as a veto filter on the mean-reversion entries.

## Notes
- _(expand: use 6–12m momentum sign as a veto on BNF entries; test reversal-vs-momentum horizon
  split on NSE names.)_
