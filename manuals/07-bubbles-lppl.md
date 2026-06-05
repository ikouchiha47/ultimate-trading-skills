# 07 — Bubbles: LPPL / LPPLS / HLPPL

**Backlog, not critical path.** A formal model of crashes (positive bubbles) *and* over-selling
set to rebound (negative bubbles) — the latter is a rigorous version of "fell but shouldn't."
Competes as a `CrashTiming` / rebound-timing provider via backtest like everything else; it is
**not a dependency.**

## What it is
- **LPPL (Log-Periodic Power Law)** — bubbles grow *super-exponentially* via positive feedback /
  herding, with **log-periodic oscillations** (accelerating wobbles) toward a critical time `t_c`
  where the regime ends (crash or sharp reversal).
- **LPPLS** — the "S" = adds a confidence/trust calibration over multiple scales.
- **Negative bubbles** — the same math inverted: a panic/forced sell-off that accelerates
  downward and is primed to snap back. *This* is the part relevant to our long mean-reversion book.
- **HLPPL ("Hyped LPPL", 2025)** — augments LPPL with sentiment/hype signals + transformer; the
  current research frontier. (We carry it only because it's the latest variant — no fixation.)
- Fit by **gradient descent / nonlinear least squares** (manual 09) — notoriously unstable;
  many local minima.

## Primary sources
- 📕 **Didier Sornette — *Why Stock Markets Crash: Critical Events in Complex Financial Systems*** (Princeton) ← the book.
- 📄 Johansen, Ledoit & Sornette (2000) — the original **JLS model**.
- 📄 Lin, Ren & Sornette (2014) — volatility-confined LPPL (residuals = OU mean-reverting; ties to manual 03).
- 📄 Demirer, Demos, Gupta & Sornette (2019), *"...LPPLS confidence multi-scale indicators,"* Quantitative Finance 19(5).
- 📄 Shu & Song (2024), *"Detection of financial bubbles using a LPPLS model,"* WIREs Computational Statistics.
- 📄 Filippopoulou et al. — *"Hyped LPPL"* (HLPPL, 2025), arXiv:2510.10878.
- 🔗 Sornette's ETH "Financial Crisis Observatory" — DS LPPLS Confidence™/Trust™.

## Where it fits
*Optional* timing overlay for the reversion entry (negative-bubble → rebound) and a separate
crash-risk read for the bubble detector. Must earn its place against the null in the harness.

## Local implementation
- (none) — backlog `CrashTiming` provider implementing `IStrategy`.

## Notes
- _(expand: only pursue after the core BNF + regime stack is validated; start with negative-bubble
  detection on NSE sector indices; beware fit instability — report confidence, not point t_c.)_
