# 08 — Factor models

**The alpha-isolation layer.** Before claiming an edge, strip out the returns explained by known
risk factors (market, size, value, momentum). What's left — if anything — is the real alpha.

## What it is
- **CAPM** — one factor (market beta). The baseline.
- **Fama–French 3-factor** — market + size (SMB) + value (HML). The standard control.
- **Carhart 4-factor** — adds momentum (UMD/WML) — important for us since we must show our
  reversion edge isn't just a short momentum bet in disguise.
- **Fama–French 5-factor** — adds profitability (RMW) + investment (CMA).
- Use: regress strategy returns on the factors; a significant **alpha intercept** after controls
  is the claim worth making. A "strategy" that's just loaded size + value beta is not an edge.

## Primary sources
- 📄 **Fama & French (1993), *"Common Risk Factors in the Returns on Stocks and Bonds,"* J. Financial Economics.**
- 📄 Carhart (1997), *"On Persistence in Mutual Fund Performance,"* J. Finance — momentum factor.
- 📄 Fama & French (2015), *"A Five-Factor Asset Pricing Model,"* J. Financial Economics.
- 📕 Ang — *Asset Management: A Systematic Approach to Factor Investing*.

## Where it fits
The **honesty check** at the end of the pipeline (with manual 10): decompose the backtested
returns and report the residual alpha + factor loadings, not just the raw Sharpe.
**India note:** use India factor data (e.g. IIM-A / NSE factor returns) — not US FF factors.

## Local implementation
- 🛠 `engines/quant-models/references/factor-models.md`.

## Notes
- _(expand: source India FF/Carhart factor series; regress BNF returns, report alpha t-stat;
  ensure not a short-momentum proxy.)_
