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
MARKDOWN HYGIENE: leave a BLANK LINE before every list, table and heading (MkDocs won't start a
list/table that directly follows a prose line — it renders the -/| as literal text); keep headings
on one line (no hard-wrap).
-->

# <Company> (<TICKER>) — Equity Research

*<date>. Prices split-adjusted (jugaad `adjust=True`). Provenance on every figure:
**(computed)** = our scripts · **(sourced)** = dated disclosure · **`unknown`** = not sourceable.
[GLOSSARY](GLOSSARY.md) explains every header, term and chart colour.*

<!-- HEADER = a scannable stance card: an emoji-stance HEADING (so it appears in the mobile TOC),
two metric TABLES, a short Why, and Links. NEVER a run-on blockquote paragraph, and NEVER hand-typed
numbers — the metric cells are the gathered values (data/_digest_all10.json or <sym>_fundamentals.json
+ the computed price-action digest), so the header always tallies with the body. Emoji: 🟢 constructive
· 🟡 neutral/watch · 🔴 avoid. Use the market's APPROPRIATE CURRENCY and local digit grouping —
India: ₹ with lakh/crore grouping (₹1,36,369 Cr); US: $ with thousands grouping ($1,363.69M / $B).
State the unit once and stay consistent. -->

## <emoji> Stance — <one-line call, e.g. "Buy on dips" / "Hold — don't chase" / "Wait for 200-DMA reclaim">

| Price | M-cap | P/E | P/B | ROE | Div yield | 1-yr |
|---|---|---|---|---|---|---|
| ₹<x> | ₹<x,xx,xxx> Cr | <x> | <x> | <x>% | <x>% | <±x>% |

| Trend | vs 50-DMA | vs 200-DMA | Delivery | RelVol | Absorption |
|---|---|---|---|---|---|
| <emoji> <trend> | <±x>% | <±x>% | <x>% | <x>× | <x> |

**Why <emoji>:** 2–4 sentences tying valuation (P/B vs ROE) + price-action (vs DMAs, absorption) +
the EARNED strategy read into the one-line call. Keep it tight; detail lives in the sections below.

**Links:** [Screener](<url>) · [TradingView](<url>) · [BSE](<url>) · [NSE](<url>)

*(Tally check — jugaad close vs screener within a few % — is a gather-step computed assertion; keep it
in `data/`/logs, not the header.)*

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
