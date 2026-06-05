# 06 — Regime detection (incl. Hidden Markov Models)

**The trap-avoidance layer.** Distinguish a transient *rotation* sell-off (tradeable — reverts)
from a *structural* decline (a trap — keeps falling). Everything in our thesis ("fell but
shouldn't have") depends on being right about which regime we're in.

## What it is
Markets switch between unobservable states (bull / bear / high-vol / low-vol). We can't see the
state directly — only emissions (returns, volatility, breadth). The job is to infer the hidden
state and condition the strategy on it.

### Hidden Markov Models (HMM) — the workhorse
- **Structure:** a small set of hidden states; each emits observations from its own distribution
  (e.g. Gaussian returns with state-specific mean/variance). State transitions follow a Markov
  matrix (next state depends only on current).
- **Three classic problems (Rabiner):**
  1. *Evaluation* — likelihood of an observation sequence (forward algorithm).
  2. *Decoding* — most likely hidden-state path (**Viterbi**) → "we are in the high-vol regime."
  3. *Learning* — fit transition + emission params (**Baum–Welch**, an EM algorithm).
- **Why it fits us:** a 2–3 state Gaussian HMM on index returns/volatility cleanly separates
  "calm risk-on" from "stress/risk-off." We only take mean-reversion longs when the regime says
  the sell-off is a rotation within a non-broken market — not a structural bear state.
- **Caveats:** states are statistical, not labelled (you assign meaning post-hoc); regimes are
  detected with lag; prone to look-ahead if fit on the full sample — fit walk-forward only
  (see manual 10).

### Related approaches
- **Markov regime-switching** (Hamilton) — the econometric origin; HMM is the same idea
  generalized.
- **Change-point detection**, **clustering on features (vol, breadth, credit spreads)**, and
  rule-based regime flags (e.g. price vs 200DMA, India VIX level) as simpler robust baselines.

## Primary sources
- 📄 **Hamilton (1989), *"A New Approach to the Economic Analysis of Nonstationary Time Series
  and the Business Cycle,"* Econometrica** — Markov regime-switching origin.
- 📄 **Rabiner (1989), *"A Tutorial on Hidden Markov Models...,"* Proceedings of the IEEE** — the
  canonical HMM tutorial (forward / Viterbi / Baum–Welch).
- 📕 Hamilton — *Time Series Analysis*, Ch. 22 (regime switching).
- 📕 Bishop — *Pattern Recognition and Machine Learning*, Ch. 13 (HMM, EM) — the ML treatment.
- 📕 Marcos López de Prado — *Advances in Financial Machine Learning* (regime / structural breaks done without look-ahead).

## Where it fits
The **gate** between "dislocation detected" (01, 03) and "take the trade." Feeds the
exposure decision: in a stress regime, the answer is often *no position — wait*.

## Local implementation
- 🛠 `engines/quant-models/references/regime-detection.md` (HMM, implemented — `hmmlearn` `GaussianHMM`).
- 🛠 `skills/regime/macro-regime-detector` (port pending) — cross-asset regime read for India.

## Notes
- _(expand: choose # states by BIC; features = index return + realized vol + India VIX + breadth;
  strict walk-forward fitting; compare HMM gate vs simple 200DMA rule in the backtest.)_
