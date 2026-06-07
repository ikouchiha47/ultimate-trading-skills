<!--
TEMPLATE: sector / industry analysis.
Backbone = the standard industry-analysis frameworks (Porter's Five Forces, PESTEL, SWOT, industry
life-cycle, value chain, strategic groups, BCG). Sources:
  - https://creately.com/guides/industry-analysis-templates/        (framework catalogue)
  - https://www.appinio.com/en/blog/market-research/industry-analysis (process: data → metrics →
    competitive intel → interpretation → entry/risk; Porter / PESTEL / SWOT / value chain / life-cycle)
  - CFA "Equity Research Report Essentials" §"Industry Overview & Competitive Positioning"
Adapted for India sector investigation + this repo's IRON DISCIPLINE (every claim = computed number
OR dated sourced link; else `unknown`; computed vs sourced kept separate). A framework is a
checklist to be thorough, NOT a licence to speculate — fill only what you can anchor.
Delete bracketed guidance when filling.
-->

# <Sector> — Industry Analysis

## 1. Industry life-cycle stage
- Introduction / growth / maturity / decline — with the evidence (credit growth, capex, penetration).
- Sets the lens; ties to `framework.india_sectors.sector_mode` (top-down cyclical / bottom-up / thematic).

## 2. Porter's Five Forces
| Force | Read (India specifics) | Provenance |
|---|---|---|
| Threat of new entrants | <licensing/regulatory moat, capital intensity> | sourced/`unknown` |
| Supplier power | <e.g. cost of funds / deposit competition for banks> | |
| Buyer power | <borrower/customer concentration, switching cost> | |
| Substitutes | <fintech / NBFC / alt channels> | |
| Rivalry | <NIM pressure, market-share stability> | |

## 3. PESTEL  *(where India macro + policy lives)*
- **Political/Legal**: RBI regulation, govt ownership (PSU), SEBI/LODR, sectoral policy.
- **Economic**: repo rate, G-sec yields, CPI, credit cycle, capex, FII/DII flow.
- **Social / Technological / Environmental**: as relevant (digital adoption, financial inclusion).
- Source: RBI (`xlsx_reader` for Sectoral Deployment), macro series, dated news (`sourced`).

## 4. Value chain & related/adjacent sectors
- Up/downstream linkages (e.g. banks ↔ NBFCs, capex, real estate, infra).
- Who leads/lags whom — from `influence-graph` (lead-lag validated, computed).

## 5. Market structure & strategic groups
- Size, growth, concentration; the strategic groups (PSU vs private banks, large vs mid-cap).
- Relative strength / breadth ranking — from `sector-deep-dive` (computed).

## 6. Structural drivers — why growing / declining
- Each driver sourced. Separate cyclical (rate cycle) from structural (financial deepening).

## 7. SWOT (sector level)
- Strengths / Weaknesses (internal to the sector's firms) · Opportunities / Threats (external).

## 8. Defining signals to watch (the dashboard)
- The handful of numbers that actually move this sector (rates, RBI actions, FII flow, commodity,
  delivery%/absorption breadth). Each with where it's sourced and at what frequency.

## 9. Constituents & companies
- Index members (computed via nselib), then per-company write-ups (see equity-research-report.md).

## 10. References
- Every link, dated. See `references.md`.

---
*Discipline gate: framework cells filled ONLY where anchored to a computed number or dated source;
everything else `unknown`. Computed (our scripts) and sourced (disclosures/news) kept visibly separate.*
