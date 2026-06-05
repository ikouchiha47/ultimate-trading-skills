# 05 — Setup quality: VCP / SEPA

**An optional entry-timing / setup-quality overlay.** Not the engine — a way to time entries and
filter low-quality setups, built explicitly on price *and volume* (manual 02).

## What it is
- **Volatility Contraction Pattern (VCP)** — price contracts in a series of progressively
  *tightening* pullbacks on **declining volume** before a breakout. The volume dry-up is the tell:
  supply is exhausted. Then a breakout on a volume expansion.
- **SEPA** (Specific Entry Point Analysis) — Minervini's full framework: trend template
  (price above rising 50/150/200 DMAs) + fundamentals + VCP timing + risk control.
- Lineage: **CAN SLIM** (O'Neil) — the precursor combining fundamentals (earnings/sales
  acceleration) with technicals (base breakouts on volume).

## Primary sources
- 📕 **Mark Minervini — *Trade Like a Stock Market Wizard*** (SEPA + VCP, the source).
- 📕 Mark Minervini — *Think & Trade Like a Champion* (risk / position sizing follow-up).
- 📕 William O'Neil — *How to Make Money in Stocks* (CAN SLIM, the precursor).

## Where it fits
For a mean-reversion book this is **secondary**: after a forced-sold quality name stops falling,
a VCP-style tightening on drying volume is a cleaner entry trigger than catching the falling knife.
Combines our reversion thesis (03) with volume confirmation (02) for timing.

## Local implementation
- 🛠 `skills/screeners/nse-vcp-screener` (ajeesh, India-native) — candidate scanner inside favoured sectors.

## Notes
- _(expand: codify the trend-template + contraction-count as a filter on reversion candidates;
  measure whether VCP timing improves the BNF entry vs entering on z-score alone.)_
