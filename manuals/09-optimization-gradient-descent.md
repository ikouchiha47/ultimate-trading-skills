# 09 — Optimization: gradient descent

**The optimizer behind every fitted model** — not itself a finance idea. Calibrates LPPL params
(07), factor loadings (08), HMM (via EM, 06), and any ML signal.

## What it is
- **Gradient descent** — iteratively step parameters downhill along the loss gradient:
  `θ ← θ − η ∇L(θ)`. Variants: SGD, momentum, Adam.
- **Convex vs non-convex** — convex losses have one global minimum (clean); non-convex (LPPL fits,
  neural nets) have many local minima → results depend on initialization, need multistart /
  care. This is exactly why LPPL `t_c` estimates are unstable (07).
- **EM (Expectation–Maximization)** — the optimizer for latent-variable models like HMM
  (Baum–Welch is EM); alternates inferring hidden states and maximizing params.
- **Regularization** — L1/L2 to avoid overfitting (ties to manual 10's overfitting discipline).

## Primary sources
- 📕 **Boyd & Vandenberghe — *Convex Optimization*** (free PDF — the math of when optimization is well-behaved).
- 📕 Goodfellow, Bengio & Courville — *Deep Learning*, Ch. 4 & 8 (numerical optimization, SGD; free online).
- 📕 Nocedal & Wright — *Numerical Optimization* (the reference for NLS / quasi-Newton used in LPPL fits).

## Where it fits
Mechanical underpinning. Mostly relevant as a *warning*: non-convex fits (LPPL, ML) are fragile —
prefer convex/robust formulations, report stability, never trust a single fit.

## Notes
- _(expand: multistart for LPPL NLS; Adam defaults for any ML signal; why EM can get stuck.)_
