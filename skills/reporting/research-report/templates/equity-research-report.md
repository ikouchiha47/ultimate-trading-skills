<!--
TEMPLATE: company equity research report.
Backbone = CFA Institute "Equity Research Report Essentials" (Sept 2020), the de-facto standard
section set used in the CFA Research Challenge. Sources:
  - https://www.cfainstitute.org/sites/default/files/-/media/documents/support/research-challenge/challenge/rc-equity-research-report-essentials.pdf
  - https://analystprep.com/cfa-level-1-exam/equity/elements-of-company-research-report/
  - https://corporatefinanceinstitute.com/resources/valuation/equity-research-report/
Adapted for India (NSE/BSE) + this repo's flow-vs-information edge and IRON DISCIPLINE:
every figure is computed-by-us OR a dated sourced link; unsourceable = `unknown`; computed and
sourced numbers are kept visibly separate; strategy claims report Sharpe-OVER-NULL, not bare Sharpe.
Delete bracketed guidance when filling. Fields marked (sourced)/(computed) MUST carry provenance.
-->

# <Company> (<TICKER>) — Equity Research

## 1. Basic information  *(the header — CFA "Basic Information")*
| Field | Value | Provenance |
|---|---|---|
| Ticker / exchange | <SYMBOL> / NSE·BSE | sourced |
| Sector / industry | <sector> | sourced |
| Recommendation | <Buy/Hold/Avoid — or `unknown` if not derived> | computed/`unknown` |
| Current price | ₹<x> | sourced (screener, dated) |
| **Tally check** | jugaad close ₹<x> vs screener ₹<y> = <z>% | computed — must be < a few % |
| Market cap | ₹<x> Cr | sourced |
| Target price | <₹x or `unknown`> | computed/`unknown` |
| Float / major shareholders | promoter <x>%, FII <x>%, DII <x>% | sourced (shareholding) |

## 2. Business description  *(CFA "Business Description")*
- What the company does; products/services; **economics** — key drivers of revenue & expense.
- For a bank: loan book mix, NIM, GNPA/NNPA, CASA, PCR, branch network, market share (sourced
  from `fetch_company_about` key-points — keep citation links).
- Source: company filings (annual report / concall via equity-research readers), screener About.

## 3. Industry overview & competitive positioning  *(CFA — uses Porter's Five Forces)*
- Industry dynamics; peer group for competitive analysis.
- **Porter's Five Forces**: new entrants · supplier power · buyer power · substitutes · rivalry.
- Production/capacity, pricing, distribution, **stability of market share**.
- The **moat** — brand / cost leadership / protected tech or resources.
- Source: `sector-deep-dive` + `influence-graph` + peers' filings. (See industry-analysis.md for
  the full sector lens if this is a sector-level report.)

## 4. Investment summary  *(CFA "Investment Summary")*
- Brief description + significant recent developments (sourced — e.g. RBI penalties, board outcomes
  from `fetch_company_signals` announcements, dated + linked).
- Earnings trajectory, valuation summary, recommended action.
- **The mispricing thesis**: why is the market not pricing this correctly, and what re-rates it?
  (If no defensible thesis, say so — do NOT invent one.)

## 5. Valuation  *(CFA "Valuation" — use MORE THAN ONE model)*
- Relative: P/E, P/B, P/Sales, dividend yield vs peers + own history (computed from screener data).
- Absolute: DCF / residual-income where applicable (`unknown` if inputs not sourced — do not fabricate).
- State every assumption; flag where a number is sourced vs computed.

## 6. Financial analysis  *(CFA "Financial Analysis")*
- Historical P&L / balance sheet / cash flow / **quarterly** trajectory (tables → `data/` json+csv).
- Earnings QUALITY: footnotes, nonrecurring items, off-balance-sheet, reserve/depreciation policy.
- Caution extrapolating through a cycle (esp. cyclical/PSU banks at a credit-cycle top/bottom).
- Industry-specific ratios (banks: NIM, GNPA, cost-to-income, credit cost, slippage).

## 7. Price & flow (this repo's addition — the edge layer)
- Split-adjusted price + 25/50/200-DMA + volume + delivery% chart (`charts/<sym>_price_volume.png`).
- Absorption / dislocation-breadth read (flow-vs-information): is a dip flow-driven (fadeable) or
  information-driven (trap)? Sourced from `framework.flow_classifier`.
- Any strategy result → see `strategies/`; report **Sharpe-over-null**, never a bare Sharpe.

## 8. Investment risks  *(CFA "Investment Risks")*
- Operational / financial / regulatory / legal. Auditor qualified opinions & "material weakness in
  internal control" = automatic red flags. Quantify where possible; else label the risk qualitatively.

## 9. ESG  *(CFA "Environmental, Social & Governance")*
- E: emissions/energy. S: community, labour, customer. G: board composition, audit committee,
  exec compensation, succession, bribery/corruption policy. Sourced or `unknown`.

## 10. References
- Every link used (filings, screener page PDF in `filings/`, RBI, news), dated. A claim without a
  reference here is a bug. See `references.md`.

---
*Discipline gate (run before done): every figure computed-by-us OR dated-sourced; unknowns marked;
prices split-adjusted; strategy claims report Sharpe-over-null; tables saved json+csv; audit PDF saved.*
