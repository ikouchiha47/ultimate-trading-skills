# 03 — Mean reversion (the entry engine)

**The core mechanism of our strategy.** Prices deviate from a long-run mean and snap back. We
fade *flow-driven* deviations (confirmed by volume, manual 02), not informed ones.

## What it is
- **Ornstein–Uhlenbeck (OU) process** — continuous-time mean reversion: `dx = θ(μ − x)dt + σ dW`.
  θ = speed of reversion, μ = long-run mean, half-life = ln(2)/θ. Fit it to estimate *how fast*
  and *how far* a name reverts.
- **Cointegration / pairs** — two non-stationary prices whose *spread* is stationary
  (mean-reverting). Trade the spread, market-neutral. Engle–Granger / Johansen tests.
- **Short-term reversal factor** — the cross-sectional academic analog: last week's/month's losers
  outperform winners over the next period (Jegadeesh 1990). This is the documented version of BNF.

### The "BNF" snap-back (Takashi Kotegawa)
Japanese day-trader who bought names that deviated violently below their **25-day MA**, expecting
reversion. No formal text — folklore. We formalize it AS mean reversion: a deviation-from-MA
**z-score** entry, volume/delivery-confirmed (02), quality-filtered (excludes broken names).

## Primary sources
- 📕 **Ernest Chan — *Algorithmic Trading: Winning Strategies and Their Rationale*** (mean-reversion & pairs chapters — canonical practitioner text).
- 📕 Ernest Chan — *Quantitative Trading* (intro companion).
- 📕 Vidyamurthy — *Pairs Trading: Quantitative Methods and Analysis*.
- 📄 **Avellaneda & Lee (2010), *"Statistical Arbitrage in the U.S. Equities Market,"* Quantitative Finance** — sector-residual mean reversion (very close to our design).
- 📄 Jegadeesh (1990), *"Evidence of Predictable Behavior of Security Returns,"* J. Finance — short-term reversal.
- 📄 Poterba & Summers (1988), *"Mean Reversion in Stock Prices,"* J. Financial Economics.

## Where it fits
The **entry signal**. Avellaneda–Lee is the most direct template: regress a name on its sector,
mean-revert the *residual* — exactly "fell relative to its sector but shouldn't have."

## Local implementation
- 🛠 `engines/quant-models/references/mean-reversion.md` (OU + cointegration).
- 🛠 `strategies/mean_reversion_bnf.py` — reference provider (z-score, `z_entry=-2.0`, `lookback=25`).

## Notes
- _(expand: half-life estimation per name to set holding period; sector-residual version per
  Avellaneda–Lee; interaction with volume filter from 02.)_
