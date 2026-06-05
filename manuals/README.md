# Manuals — theory & source reference

One file per concept. Each is a living reference: **what it is**, its **primary sources**
(books/papers), **where it fits** in our experiment, the **local implementation**, and a
**Notes** section to expand as we read.

Legend: 📕 book · 📄 paper · 🛠 local skill/engine in this repo · 🔗 online resource

## Index

| # | Manual | Role in the experiment |
|---|---|---|
| 01 | [Why an edge can exist](01-why-edge-exists.md) | EMH vs Grossman–Stiglitz vs Adaptive Markets — *the foundation* |
| 02 | [Price–volume & order flow](02-price-volume-and-order-flow.md) | volume + delivery % confirm price — *price alone misleads* |
| 03 | [Mean reversion](03-mean-reversion.md) | the entry engine (OU, cointegration, BNF snap-back) |
| 04 | [Momentum & trend](04-momentum-trend.md) | the opposite leg — know it to avoid fighting it |
| 05 | [Setup quality — VCP / SEPA](05-setup-quality-vcp.md) | optional entry-timing / setup-quality overlay |
| 06 | [Regime detection (incl. HMM)](06-regime-detection.md) | rotation (tradeable) vs structural break (trap) |
| 07 | [Bubbles — LPPL / HLPPL](07-bubbles-lppl.md) | crashes + negative bubbles (rebounds); backlog provider |
| 08 | [Factor models](08-factor-models.md) | strip sector/size/value beta, isolate alpha |
| 09 | [Optimization — gradient descent](09-optimization-gradient-descent.md) | calibrate every fitted model |
| 10 | [Backtesting discipline](10-backtesting-discipline.md) | prove it survives costs + walk-forward vs a null |
| 11 | [Risk & position sizing](11-risk-position-sizing.md) | Kelly, drawdown control |

## How they connect (the experiment)

```
01 Why edge exists   →  why the dislocation exists (forced / uninformed sector selling)
02 Price–volume      →  confirm it: is the selling flow-driven (low delivery%) or informed?
06 Regime detection  →  is it a rotation (tradeable) or a break (trap)?   [HMM]
03 Mean reversion    →  the entry signal (oversold vs sector)   ┐
07 LPPLS neg. bubble →  formal "fell but shouldn't" (optional)  ┘
   quality filter    →  the "shouldn't have" — excludes weak names (fundamentals skill)
05 VCP / 04 momentum →  optional setup-quality / timing overlay
08 Factor models     →  strip out sector beta, isolate the alpha
10 López de Prado    →  prove it survives costs + walk-forward (vs a null)
09 Gradient descent / 11 risk → calibrate & size
```

Core thesis lives in the repo `README.md`; this directory is the *why-it-should-work* backing.
