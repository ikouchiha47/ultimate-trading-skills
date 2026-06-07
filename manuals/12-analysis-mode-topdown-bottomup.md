# 12 — Analysis mode: top-down vs bottom-up (and what it does to our edge)

Legend: 📕 book · 📄 paper · 🛠 local · 🔗 online

## What it is

Not every sector should be analysed the same way. The **dominant driver** of a sector's
returns dictates the analysis *mode*, and — critically for us — the **prior on whether a
sector-wide move is flow-driven (fadeable) or information-driven (a trap)**. Mode is not
cosmetic; it gates where our mean-reversion edge (manuals/01, /03) even applies.

Three modes:

| Mode | Dominant drivers | Read of a *sector-wide* selloff | Our edge here |
|---|---|---|---|
| **top_down_cyclical** | global macro -> local macro -> sector (LME/crude/China, USD, rates) | often **information** — the cycle turned; "fair value" anchor itself moved | **weak / trap.** Fading a real regime change. |
| **bottom_up_idiosyncratic** | per-name fundamentals (USFDA approvals, molecule pipeline, client wins) | almost definitionally **indiscriminate flow** — one event can't be information about *every* name | **strongest.** Good names sold with the bad -> the BNF "fell but shouldn't have." |
| **thematic_cascade** | a capex/demand theme propagating down a supply chain | depends on the theme's persistence; near-supply-chain nodes move first | edge is in *mispriced cascade reach*, validated by lead-lag |

The chain length differs by mode:
- cyclical: **top-down** — `global macro -> local macro -> sector -> names -> portfolio`.
- idiosyncratic: **bottom-up** — skip macro; go to per-name dispersion + the quality/fade screen.
- thematic: **forward cascade** — theme node -> ranked beneficiary nodes (the influence graph).

## Why mode sets the flow-vs-information prior

This is the load-bearing insight (Grossman–Stiglitz, manuals/01). A sector-wide drawdown is
the *same observable* in every sector, but it means different things:

- In a **bottom-up** sector, fundamentals are idiosyncratic, so a move that hits *all* names
  at once cannot be information about each one — it is overwhelmingly likely to be flow
  (FII risk-off, rotation, index selling). High prior that it's fadeable. **Our edge lives here.**
- In a **cyclical** sector, the names share one macro driver, so a sector-wide move *can* be a
  single piece of information (the cycle turned) hitting the shared driver. Low prior that
  it's noise. **Fade with caution / not at all.**

Corollary (a falsifiable, sector-conditional claim, not an assumption): **fade-the-dip
expectancy should be positive in bottom-up sectors and ≈0 or negative in cyclicals.** That is
a backtest, not a belief (manuals/10).

## India specifics

- **Pharma = bottom-up dominant, USD-overlaid.** Value is per-molecule / USFDA
  inspection-and-approval / US generic-price-erosion / India branded formulations — company
  specific. One macro overlay: USD/INR + the US generics pricing cycle (it's an export sector).
- **Metals, Energy, Cement = top-down cyclical.** LME / crude / China demand / USD / rates.
- **IT = bottom-up-ish, heavily USD-overlaid** (US client tech-spend cycle, USD/INR). Defensive
  in India for the INR-hedge reason, but dispersion is real (tier-1 vs mid-cap divergence).
- **Banks / Financials = rate + credit-cycle + capex-cycle cyclical**, but with large
  idiosyncratic dispersion (asset quality, PSU vs private). Mixed.

## The thematic-cascade trap (datacenter -> private banks)

Worked example of mode = thematic. "Datacenter capex boom -> bet the industries that build
them" is the influence graph run forward (🛠 `scenario-analyzer`):

```
datacenter capex boom
  -> power/transmission (NTPC, Power Grid), transformers/switchgear (ABB, Siemens)   [near]
  -> cooling, EPC/construction (L&T), land/REITs (realty)                            [mid]
  -> financing the capex cycle -> private banks                                       [far, lagged, weak edge]
```

Private banks is a **far node** — multi-hop, lagged, second/third-order. The cascade is a
**hypothesis generator, not a truth oracle** (manuals/01, repo CLAUDE.md): edges are earned
**structurally OR by empirical lead-lag validation**, never by narrative alone. Rank candidate
beneficiaries by *directness* and *measured lead-lag*; prefer near nodes; require the far ones
to clear a higher empirical bar (does private-bank credit growth actually lead/lag
datacenter-capex announcements in the data?).

## Local implementation 🛠

- `framework/india_sectors.py` — `SECTOR_MODE`: per-sector `{mode, dominant_drivers,
  flow_vs_info_prior, validation}`. Seed from judgment (guardrail), but **every tag carries a
  named falsifiable test** (seed + empirical-validation discipline). `CYCLICAL/DEFENSIVE/
  COMMODITY` lists are the crude precursor, now derivable from `SECTOR_MODE`.
- Mode then **gates the pipeline**: cyclicals route through the top-down `driver()` chain
  (manuals/08, the US-driver nodes -> FII -> sector); bottom-up sectors skip macro and go to
  per-name dispersion + the fade/quality screen; thematic runs the forward influence graph.
- Not yet wired into the pipelines — captured as taxonomy + theory first (per build order).

## Primary sources

- 📄 Grossman & Stiglitz (1980), *On the Impossibility of Informationally Efficient Markets* — why
  a sector-wide uninformed move is fadeable (the prior). (see manuals/01)
- 📕 Andrew Lo, *Adaptive Markets* — edge is context-dependent; mode is one context axis.
- 📕 Grinold & Kahn, *Active Portfolio Management* — factor/driver decomposition (manuals/08);
  the cyclical "shared driver" is a factor exposure.
- 🔗 Practitioner framing (top-down for cyclicals, bottom-up for idiosyncratic sectors) — to be
  pinned to specific writeups as we read.

## Notes

- Mode can be **regime-dependent**: a normally-idiosyncratic sector can temporarily go
  top-down in a liquidity crisis (everything correlates to 1). The flow-vs-info prior should
  be conditioned on the broad regime (manuals/06).
- Validation tests to run when wiring: (a) fade-the-dip expectancy by sector; (b) each sector's
  measured beta to its claimed dominant driver (LME/USD/rates/credit-growth) — confirms or
  refutes the `mode` tag; (c) within-sector return dispersion (high ⇒ bottom-up).
