# Trading & Quant Concepts — Source Reference

One place. Each concept → its **primary source** (book/paper) + a one-line "what it is" + where it
fits in the sector-rotation mean-reversion experiment ("fell but shouldn't have").

Legend: 📕 book · 📄 paper · 🛠 local skill in `claude-scientific-skills/`

---

## 1. Mean reversion (the engine)
*Prices deviate from a long-run mean and snap back. Modeled as Ornstein–Uhlenbeck / cointegration.*
- 📕 Ernest Chan — *Algorithmic Trading: Winning Strategies and Their Rationale* (mean-reversion & pairs chapters — canonical practitioner text)
- 📕 Ernest Chan — *Quantitative Trading* (intro-level companion)
- 📕 Vidyamurthy — *Pairs Trading: Quantitative Methods and Analysis*
- 📄 Avellaneda & Lee (2010), *"Statistical Arbitrage in the U.S. Equities Market,"* Quantitative Finance
- 🛠 `quant-models/references/mean-reversion.md` (OU + cointegration, implemented)

## 2. The "BNF" contrarian snap-back
*Takashi Kotegawa ("BNF"): buy names that deviated violently below their 25-day MA, expecting reversion.*
- 📕 No formal text; folklore. Formalize it AS mean reversion (#1) with a deviation-from-MA z-score.
- Closest documented analog: short-term reversal factor — Jegadeesh (1990), *"Evidence of Predictable Behavior of Security Returns,"* Journal of Finance.

## 3. Momentum / trend (the opposite leg — know it to avoid fighting it)
- 📄 Jegadeesh & Titman (1993), *"Returns to Buying Winners and Selling Losers,"* Journal of Finance
- 📕 Andreas Clenow — *Stocks on the Move* (practitioner momentum)

## 4. Mark Minervini — Volatility Contraction Pattern (VCP) / SEPA
*Price contracts in tightening swings on falling volume before a breakout; a setup-quality framework.*
- 📕 Mark Minervini — *Trade Like a Stock Market Wizard* (SEPA + VCP, the source)
- 📕 Mark Minervini — *Think & Trade Like a Champion* (risk/position-sizing follow-up)
- Lineage: William O'Neil — *How to Make Money in Stocks* (CAN SLIM, the precursor)

## 5. Grossman–Stiglitz paradox (WHY any edge can exist)
*Perfectly efficient markets are impossible — no one would pay to gather info. Forced/uninformed selling leaves exploitable dislocations.*
- 📄 Grossman & Stiglitz (1980), *"On the Impossibility of Informationally Efficient Markets,"* American Economic Review 70(3)
- 📕 O'Hara — *Market Microstructure Theory*
- 📕 Bouchaud, Bonart, Donier & Gould — *Trades, Quotes and Prices* (modern price-impact / forced-selling view)

## 6. Efficient Market Hypothesis (the thing #5 pushes against)
- 📄 Fama (1970), *"Efficient Capital Markets: A Review of Theory and Empirical Work,"* Journal of Finance
- 📕 Andrew Lo — *Adaptive Markets* (the reconciling modern view)

## 7. LPPL / LPPLS / HLPPL (bubbles AND negative bubbles = rebounds)
*Super-exponential growth + log-periodic oscillations from herding. Detects crashes (positive bubbles) and over-selling set to rebound (negative bubbles) — a formal model of "fell but shouldn't."*
- 📕 **Didier Sornette — *Why Stock Markets Crash: Critical Events in Complex Financial Systems* (Princeton)** ← the book
- 📄 Johansen, Ledoit & Sornette (2000) — the original **JLS model**
- 📄 Lin, Ren & Sornette (2014) — volatility-confined LPPL (residuals = **OU mean-reverting**; ties to #1)
- 📄 Demirer, Demos, Gupta & Sornette (2019), *"On the predictability of stock market bubbles: LPPLS confidence multi-scale indicators,"* Quantitative Finance 19(5)
- 📄 Shu & Song (2024), *"Detection of financial bubbles using a LPPLS model,"* WIREs Computational Statistics
- 📄 Filippopoulou et al. — *"Hyped LPPL"* (HLPPL, 2025), arXiv:2510.10878 (adds sentiment/hype + transformer)
- 🔗 Sornette's ETH "Financial Crisis Observatory" — DS LPPLS Confidence™/Trust™ indicators

## 8. Gradient descent (the optimizer, not a finance idea)
*How you calibrate every fitted model — LPPL params, factor loadings, ML signals.*
- 📕 Goodfellow, Bengio & Courville — *Deep Learning*, Ch. 4 & 8 (free online)
- 📕 Boyd & Vandenberghe — *Convex Optimization* (free PDF — the math)

## 9. Regime detection (is the sector risk-off or broken?)
*Distinguish a transient rotation sell-off from structural decline.*
- 📄 Hamilton (1989) — Markov regime-switching (the origin)
- 🛠 `quant-models/references/regime-detection.md` (HMM, implemented)

## 10. Factor models (control for sector/size/value beta)
- 📄 Fama & French (1993), *"Common Risk Factors in the Returns on Stocks and Bonds,"* J. Financial Economics
- 📄 Carhart (1997) — adds momentum factor
- 🛠 `quant-models/references/factor-models.md`

## 11. Backtesting discipline (so the result is real)
*Avoid overfitting, look-ahead, survivorship; walk-forward; deflated Sharpe.*
- 📕 **Marcos López de Prado — *Advances in Financial Machine Learning*** ← the discipline bible
- 📕 Robert Pardo — *The Evaluation and Optimization of Trading Strategies*
- 🛠 `backtesting/` skill (vectorbt: walk-forward, costs, slippage, Sharpe/drawdown)

## 12. Risk & position sizing
- 📄 Kelly (1956) — the Kelly criterion
- 📕 Ralph Vince — *The Mathematics of Money Management*
- 🛠 `quant-models/references/risk-metrics.md` (VaR, Sharpe, drawdown)

---

### How they connect in the experiment
```
#5 Grossman-Stiglitz   →  why the dislocation exists (forced/uninformed sector selling)
#9 Regime detection    →  is it a rotation (tradeable) or a break (trap)?
#1 Mean reversion /     ┐
#2 BNF deviation        ├→  the entry signal (oversold vs sector)
#7 LPPLS negative bubble┘
quality filter (equity-research) → the "shouldn't have" — excludes weak names
#4 VCP / #3 momentum   →  optional setup-quality / timing overlay
#10 Factor models      →  strip out sector beta, isolate the alpha
#11 López de Prado     →  prove it survives costs + walk-forward (vs a no-filter null)
#8 Gradient descent / #12 risk → calibrate & size
```
