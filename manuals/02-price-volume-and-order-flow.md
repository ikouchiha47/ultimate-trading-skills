# 02 — Price–volume & order flow

**Price alone is misleading. Every signal must be confirmed by volume.** A move on thin volume
is noise; the same move on heavy volume is participation. This manual is cross-cutting — it
qualifies the entry engine (03), the setup overlay (05), and the "uninformed selling" test (01).

## What it is
- **Volume confirms price.** Up-moves on rising volume = real demand; up-moves on falling volume
  = exhaustion. Down-moves on climactic volume = capitulation (often the reversion point we want).
- **Wyckoff** — accumulation/distribution phases read from price *and* volume: selling climax,
  automatic rally, secondary test, spring. The vocabulary for "smart money quietly buying a
  forced-sold name."
- **Volume Spread Analysis (VSA)** — relationship between bar spread, close position, and volume
  to infer effort vs result (e.g. high volume + narrow spread + close up = absorption).
- **VWAP** — institutional benchmark; price vs VWAP says who is in control intraday/over a window.
- **OBV / accumulation-distribution** — cumulative volume-flow oscillators.

### India-specific: delivery %
NSE reports **delivery quantity / %** (in jugaad `stock_df`: `DELIVERY QTY`, `DELIVERY %`). High
delivery % = buyers taking actual delivery (conviction), not intraday churn. A sell-off on **low**
delivery % is more likely flow/speculative (fadeable); high delivery % on a drop signals real
distribution (don't fade). This is a near-unique edge in Indian data — use it.

## Primary sources
- 📕 Richard Wyckoff — *The Richard D. Wyckoff Method of Trading and Investing in Stocks* (and the modern Wyckoff literature, e.g. Pruden — *The Three Skills of Top Trading*).
- 📕 Anna Coulling — *A Complete Guide to Volume Price Analysis* (practitioner VSA).
- 📕 Tom Williams — *Master the Markets* (VSA origin).
- 📄 Karpoff (1987), *"The Relation Between Price Changes and Trading Volume: A Survey,"* J. Financial & Quantitative Analysis — the academic price–volume relationship.
- 📄 Llorente, Michaely, Saar & Wang (2002), *"Dynamic Volume-Return Relation,"* Review of Financial Studies — volume helps distinguish informed vs liquidity-driven moves (directly relevant to 01).

## Where it fits
- **01 (why edge exists):** volume + delivery % is how we *operationalize* "uninformed selling."
  Llorente et al. is the formal hook: liquidity-driven (high-volume, low-information) moves revert;
  informed moves continue.
- **03 (mean reversion):** require a volume/delivery filter on the oversold signal — fade
  capitulation, not quiet bleed.
- **05 (VCP):** volume *contraction* is half the pattern definition.

## Local implementation
- 🛠 `data/sources.py` `JugaadData` — already returns `volume` + (raw) `DELIVERY %`.
- TODO: surface delivery % through the normalized OHLCV schema (currently dropped to OHLCV cols).

## Notes
- _(expand: exact volume/delivery filters for the BNF entry; backtest whether delivery % adds
  edge over volume alone; Llorente illiquidity-interaction term as a feature.)_
