# 11 — Risk & position sizing

**Surviving to compound.** A positive edge with bad sizing still blows up. How much to bet, and how
to cap downside, is as important as the entry.

## What it is
- **Kelly criterion** — the bet fraction maximizing long-run log growth: `f* = edge / odds`.
  Full Kelly is too aggressive in practice (estimation error, fat tails) -> use **fractional Kelly**
  (¼–½).
- **Volatility targeting / risk parity** — size inversely to volatility so each position contributes
  comparable risk; scale exposure to a target portfolio vol.
- **Drawdown control** — max-drawdown limits, per-trade stop = fixed fraction of capital
  (Minervini-style), de-gross in stress regimes (ties to manual 06).
- **Position limits** — concentration caps; correlation-aware (a "diversified" basket of forced-sold
  names in one sector is one bet).

## Primary sources
- 📄 **Kelly (1956), *"A New Interpretation of Information Rate,"* Bell System Technical Journal.**
- 📕 Ralph Vince — *The Mathematics of Money Management* (practical f, optimal-f).
- 📕 Edward Thorp — *A Man for All Markets* / his Kelly papers (applied Kelly in markets).
- 📕 Mark Minervini — *Think & Trade Like a Champion* (stop discipline, risk-first sizing).

## Where it fits
The **last stage** before execution: given the validated edge (10) and the regime (06), decide
exposure — frequently *zero* (wait for alignment). Correlation matters: our forced-sold candidates
cluster by sector, so size at the *sector* level, not per name.

## Local implementation
- 🛠 `engines/quant-models/references/risk-metrics.md` (VaR, Sharpe, drawdown).
- 🛠 `skills/regime/exposure-coach` (port pending) — regime -> allowed risk.

## Notes
- _(expand: fractional-Kelly with shrunk edge estimate; sector-level correlation cap; vol-target
  the book; de-gross rule keyed to HMM stress state.)_
