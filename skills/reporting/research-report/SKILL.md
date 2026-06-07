---
name: research-report
description: >
  Orchestrate a full India sector/company investigation into ONE structured report folder:
  sector context -> companies (about, filings, fundamentals, charts, tables) -> other research
  -> references -> strategies. Use when asked to "research <sector>", "deep-dive <company>",
  "build a report on ...", "investigate <stock> for swing/position". This skill ROUTES to the
  other skills and assembles their structured output; it does not re-compute. India-only.
tags: [india, report, orchestrator, sector, company, equity-research, investigation]
triggers: [research, report on, deep dive, investigate, build a report, write up, dossier]
---

# Research report (India) — the orchestrator

## What this is

You (the agent) are the report writer. This skill is the **conductor**: it tells you how to
decompose an investigation, which skill produces each piece, the folder layout to assemble them
into, and the discipline every claim must meet. The other skills are the thin compute; the report
is their assembled, sourced output. Long steps (filings, calibration) run in the background so the
session never blocks.

**Iron discipline (non-negotiable):** every claim is anchored to a NUMBER (computed by our skills)
or a SOURCED disclosure (dated link). Anything you cannot source is written **`unknown`** — never
inferred from price, never fabricated. Keep computed-vs-sourced separate (a web figure is never a
computed number). Mark provenance on every figure.

## The workflow (see `WORKFLOW.md` for the diagram)
**gather → structure → unify → review**, with the hard boundary: **scripted core only gathers +
computes; YOU (the agent) plan, author the prose/structure, unify and review.** NEVER write a Python
program that emits the report markdown — pages are authored from the template, not generated.

**TODO IS THE HEART — do this FIRST and keep it live.** Before any work, build the plan with the
task tools (`TaskCreate`) — a task per stage and per sub-step (e.g. one per company to author/review)
— and maintain it throughout (`TaskUpdate` in_progress→completed; `TaskList` to see what's left).
Every gap found in review goes back in as a task. The todo is the single source of truth for progress;
don't run the flow from memory. **If the task tools aren't available**, fall back to a `_todo.md` in
the report folder — ONE per unique research query — updated the same way; persist it until the context
changes (user pivots to a different search), and on a context change **confirm before** replacing it.

1. **Plan & scope** — build the TODO; resolve sector→index→constituents; decide universe/depth; create the folder.
2. **Gather (scripted)** — data + charts + graphs + backtests + filings (the inputs you embed).
3. **Structure (you)** — author each page from `templates/` (company + sector), filling sections
   from the gathered data; embed charts as images with caption cards.
   - **Header = stance card (tables, not a paragraph):** an emoji-stance HEADING + two metric tables
     (valuation + price-action) + a tight Why + Links — per the template. Pull the metric cells from
     the gathered digest so they tally; never hand-type or script-format them. Formatting is your job
     as the author (instructions/template), NOT a Python post-processor.
   - **Currency:** use the market's appropriate currency + local digit grouping (India ₹ with
     lakh/crore, e.g. ₹1,36,369 Cr; US $ with thousands). State the unit once, stay consistent.
   - **Prose → charts:** when a section is compositional/percentage data (loan-book mix, sector/
     corporate exposure = "markets they lend to", shareholding, geographic split, revenue mix) or a
     trajectory, render it as a chart via `framework.charts.composition_chart({label: pct}, ...)` /
     `financial_charts` and embed it (keep a one-line read) — don't leave a long comma-list in prose.
4. **Unify (you)** — make the N pages ONE report: (a) identical section structure/order/colours so
   pages are comparable; (b) cross-link Overview↔company↔Industry↔Glossary↔strategies; (c) reconcile
   — the same number/Stance is identical everywhere (no contradictions); (d) one narrative thread
   from Overview→Industry→Observations→each stance.
5. **Review step-by-step (you, supervisor)** — FIRST **apply the sector analysis to EACH company and
   seed it**: how Porter/PESTEL forces, RBI credit-deployment mix, the influence-graph bellwether/
   beta role, and the EARNED strategy anchor hit THAT name → **update the company page** (its "Sector
   forces → this company" mapping + refresh stance/risks). THEN run the **verification pass** (below)
   and the discipline checklist. Gaps route back to gather or re-author. Then publish.

### Verification pass — every claim, against its source-of-truth (whole report, not piecemeal)
Verification is **holistic**: go claim-class by claim-class for each company, confirm each figure
against the source that owns it, and stamp a status. **Price never implies a fact.** Render the result
as one **`## Verification`** section per company page (near the end, before the closing stance) — a
table of claim-class · source-of-truth · status, listing any ⚠️ disputes explicitly.

| Claim class | Where in report | Source of truth | How to verify |
|---|---|---|---|
| Header metrics (price, mcap, P/E, P/B, ROE, div, 1-yr) | stance card | `_digest_all10.json` / `<sym>_fundamentals.json` | equal to digest |
| Price-action (vs 50/200-DMA, delivery, RelVol, absorption) | stance card, price§ | computed digest | equal to digest |
| Financial trajectory (net profit, EPS, deposits, advances, investments) | §Financial | `<sym>_profit_loss.csv` / `_balance_sheet.csv` | equal to CSV; flag concall-vs-screener diffs |
| Quality ratios (NIM, GNPA, NNPA, CASA, PCR, CRAR, cost/income) | About, §3 | screener `key_points` (dated) or concall | present + dated in panel/concall |
| Loan/advance mix | About chart | screener `key_points` advance mix | equals chart data |
| Dividend (₹/share, %) | §Financial | `<sym>_fundamentals` payout% + FV | recompute ₹/share from EPS×payout |
| Shareholding (GoI/FII/DII) | §Financial/§3 | `<sym>_shareholding.csv` | equal to CSV |
| Corporate actions (merger/QIP/split/rights) | About | `signals.json` `corporate_actions` tabs | present in tabs |
| Subsidiary stakes | About / graph | screener related-party / AR AOC-1 / WebSearch | dated source link; else `unknown` |
| Concall **STT `(call: …)`** figures | concall STT | `data/` + AI summary (MATCHED quarter) | within tolerance → ✅; mismatch → fix/drop |
| Credit ratings (level + outlook + action) | refs / ratings | agency rationale docs (CRISIL/ICRA/Fitch) — `_ratings.py` | parse {agency,instrument,rating,outlook,action,date} |
| RBI / macro | comprehensive §3b | RBI sectoral-deployment xlsx | equal to release |

**Status vocabulary:** ✅ verified · ⚠️ disputed (show BOTH values + which source wins) · 🔢 computed ·
📄 sourced (dated link) · ❓ unknown (not sourceable — never inferred). On any sourced-vs-computed
disagreement, `data/` + dated disclosure win over a paraphrase; correct the prose, don't average.

## Output layout — one folder per investigation

```
reports/research/<SECTOR-or-COMPANY>_<YYYY-MM-DD>/
  00_comprehensive.md          # sector SCREENER listing + dashboard + strategy + graphs (the deliverable)
  00_industry.md               # sector frameworks (Porter/PESTEL/life-cycle/value-chain/SWOT)
  01_observations.md           # price-action/volume/profit -> buy/sell stance per name + why
  <SYMBOL>_equity_research.md  # one per company (CFA structure) — MUST embed its charts
  GLOSSARY.md                  # every header / line item / chart colour explained (link from each report)
  data/                        # every table as .json AND .csv + RBI xlsx
  charts/                      # PNGs: <sym>_price_volume.png, <sym>_financials.png,
                               #       dependency_<sym>.png, dependency_<sector>_network.png, influence_graph.png
  graph/                       # influence + dependency graph json/verdict
  filings/                     # audit page PDFs; ar/ (annual-report extracts, gitignored — large)
  strategies/<strategy>_<sector>/   # backtest result, params, EARNED/NO-EDGE verdict
  references.md                # ALL source links, for testing/audit
```

**VISUALS ARE MANDATORY (this is where reports fail).** Charts MUST be embedded as real markdown
images `![alt](charts/x.png)` — NEVER referenced as inline code `` `charts/x.png` `` (that renders as
text, shows nothing). Every per-company report has a **## Visuals** block near the top with: the
price/volume/DMA chart, the financial chart (`framework.charts.financial_charts` — revenue/profit,
the Deposits/Investments/Borrowing book, quarterly profit, EPS), and the group/dependency graph if
built. The sector report leads with a **TradingView-style screener listing** (one row per name:
price, mkt cap, P/E, P/B, ROE, div, growth, 1y ret, vs50/vs200, RelVol, deliv, **Stance** = our
analyst-rating analog) and embeds the influence graph + group-network gallery. Link `GLOSSARY.md`
from every report so headers/line-items/chart-colours are self-explanatory.

## Templates (credible backbones — START from these, don't invent structure)

`templates/` holds two attributed templates; copy the right one into `00_report.md` and fill it:
- **`templates/equity-research-report.md`** — a COMPANY report. Backbone = CFA Institute "Equity
  Research Report Essentials" (the CFA Research Challenge section set): Basic info → Business
  description → Industry & competitive positioning (Porter) → Investment summary → Valuation
  (≥1 model) → Financial analysis → Investment risks → ESG. Adapted with our Price & flow layer.
- **`templates/industry-analysis.md`** — a SECTOR report. Backbone = the standard industry-analysis
  frameworks: industry life-cycle, Porter's Five Forces, PESTEL (where India macro/RBI lives),
  value chain, strategic groups, SWOT. Each cell filled only where anchored; else `unknown`.

A sector investigation usually = one `industry-analysis.md` + one `equity-research-report.md` per
constituent. The frameworks are CHECKLISTS for thoroughness, never licence to speculate.

## Report structure (fill in this order)

### 1. Sector context — structured via the industry-analysis frameworks
Cover the sector through these standard lenses (use the ones that fit; each claim still anchored
to a number or a dated sourced link — a framework is a checklist, not a licence to speculate):
- **Industry life-cycle stage** — introduction / growth / maturity / decline (sets the lens;
  ties to `framework.india_sectors.sector_mode` top-down-cyclical / bottom-up / thematic).
- **Porter's Five Forces** — new-entrant threat, supplier power, buyer power, substitutes, rivalry
  (for banks: deposit competition, regulatory moat, fintech substitution, NIM pressure).
- **PESTEL** — Political/Economic/Social/Technological/Environmental/Legal; for India this is where
  **RBI policy, repo, capex cycle, FII flow** live (the defining factors/signals/policies).
- **Value chain & related/adjacent sectors** — up/down stream (banks ↔ NBFCs, capex, real estate).
- **Why it's growing/declining** — the structural drivers, each sourced.
- Source: `sector-deep-dive` (quant ranking, rel-strength, breadth) + `influence-graph`
  (what actually moves it, who leads) + `scenario-analyzer` (forward cascades).

### 2. Companies (repeat per company)
- **About** — `equity-research` `screener_reader.fetch_company_about(symbol)` (the screener
  ABOUT + KEY POINTS panel: business, NIM/GNPA, market share, branch network, loan book). This
  is narrative+sourced; keep its citation links.
- **Filings** — pull and extract into `filings/`:
  - Annual report → `annual_report_reader.py`
  - DRHP (if recent IPO) → `drhp_reader.py` / `drhp_vision.py`
  - Concall (latest) → `concall_reader.py`
  Run these in the background (minutes each). They emit `.md` + `.json`.
- **Data tables** — `fetch_company_fundamentals` (incl. **quarters**) / `fetch_company_ratios` →
  write each to `data/<symbol>_*.json` AND `.csv` (P&L, balance sheet, cash flow, **quarters**,
  shareholding). Tables in the report carry a header note or link to `GLOSSARY.md`.
- **Charts (BOTH, embedded as images)** —
  1. `framework.charts.price_volume_chart` → `charts/<sym>_price_volume.png` (price + 25/50/200-DMA
     + volume + delivery)
  2. `framework.charts.financial_charts(symbol, data_dir, charts_dir)` → `charts/<sym>_financials.png`
     (revenue & profit, the Deposits/Investments/Borrowing **book**, quarterly profit, EPS — screener-style)
  3. group/dependency graph (see dependency-graph skill) → `charts/dependency_<sym>.png`
  Put all in the report's **## Visuals** block as `![...](charts/...)` — embedded, not inline-code.
- **Other research** — anything else gathered, each with its source.

### 3. RBI policy + news (per company/stock)
- Relevant **RBI policy** events (repo, sectoral credit) and **dated news links** that bear on
  the name. Sourced via date-scoped WebSearch, labelled `sourced` — these contextualise, they
  are NOT computed numbers. Cite every link.

### 4. References
- `references.md` — every link used (filings, screener, RBI, news), so the report is auditable
  and re-testable. A claim without a reference here is a bug.

### 5. Strategies (own folder each)
- For each strategy tested on this sector/name, a subfolder under `strategies/` with: the
  backtest result (Sharpe, **over-null**, maxDD, trades, deflated Sharpe, OOS note), the params
  used, and the EARNED verdict. Drive via `strategy-harness` + `framework.calibrate` (per-sector
  reversion anchor — calibrate if `sector_params.reversion_anchor` raises `NotCalibrated`).

## Batch the gather phase (don't get rate-limited)

Screener/filing scrapes and per-name backtests hit external hosts — run them through the
resumable batch runner so you pace requests and can resume after a throttle/stall. The tracker
JSON lives in the report folder; re-running the same call picks up only what's left.

```python
from framework.batch import run_batch

symbols = ["SBIN", "BANKBARODA", "PNB", "CANBK"]
tracker = "reports/research/<name>_<date>/_tracker.json"

def gather(sym):
    from skills... import fetch_company_about, fetch_company_fundamentals   # equity-research
    about = fetch_company_about(sym)
    fund  = fetch_company_fundamentals(sym)
    # ...write data/<sym>_*.json+csv, charts/, queue filings...
    return f"data/{sym}_fundamentals.json"          # json-able result recorded in the tracker

run_batch(symbols, gather, tracker, delay=3.0, jitter=2.0, max_retries=2, backoff=8.0)
```

- `delay`+`jitter` = polite spacing (raise for screener; it throttles). `max_retries`+`backoff`
  ride out transient 429s. The tracker persists after EVERY item (atomic write).
- Already-`done` symbols are skipped on re-run; `failed` ones retried. Check `tracker.summary()`.
- For the SLOW filing reads (AR/DRHP/concall, minutes each), run the batch in the harness
  background so the session isn't blocked; poll the tracker for progress.

## Data sources — jugaad vs screener are COMPLEMENTARY (neither alone is enough)

They cover disjoint data; capture from BOTH, then cross-check the one field they share.

| Signal | Source | Notes |
|---|---|---|
| daily OHLCV, **volume, delivery %** | `data.sources.JugaadData.history` | screener has NO daily series; this is the backtest engine |
| split/dividend ratios | jugaad+yfinance (default) OR screener **Corporate Actions** modal | screener's modal is authoritative — prefer it to confirm a split |
| P&L / Balance Sheet / Cash Flow / **Quarters** (12y) | screener `fetch_company_fundamentals` | jugaad has ZERO fundamentals; `tables` now includes `quarters` |
| shareholding (promoter/FII/DII trend) | screener (same call) | the ownership-flow signal |
| growth CAGRs, ratios (P/E, NIM, GNPA, div yield) | screener `fetch_company_fundamentals` / `fetch_company_ratios` | — |
| segments (Retail/Wholesale/Treasury/Life Ins) | screener (premium-GATED) | row NAMES present, VALUES blank → write `unknown`, NOT a bug |
| announcements / RBI penalties / concalls / ARs | screener Documents + `get_documents` | sourced narrative + filing URLs |

**Return shapes (don't re-derive — they bit us once):**
- `JugaadData.history(sym, start, end, adjust=True)` → DataFrame indexed by **`date`** (already the
  index, do NOT `set_index("date")`); columns `open/high/low/close/volume/vwap/trades/deliverable_qty/delivery_pct`.
- `fetch_company_fundamentals(sym)` → `{symbol,url,numeric,ratios,growth,tables,documents_note}` where
  `tables[section] = {"periods":[...], "rows": {line_item: [floats]}}` for section in
  `quarters/profit_loss/balance_sheet/cash_flow/shareholding`. (CSV = header `line_item,*periods`.)
- `fetch_company_about(sym)` → `{about, key_points{raw,sections}, links, website, bse, nse}` (SOURCED).
  Bank key_points OFTEN carry the **segment/revenue mix** (e.g. Retail/Corporate/Treasury %) — use it.
- `fetch_company_ratios(sym)` → `{ratios{label:str}, numeric{key:float}}`.
- `fetch_company_signals(sym)` → announcements / credit_ratings / annual_reports / concalls / corp-actions.
- `fetch_related_party(sym)` → related entities (corroboration; **transaction TYPES for banks**, not
  entities — for a bank group graph use sourced subsidiary disclosures instead, see dependency-graph skill).
- `framework.charts.financial_charts(sym, data_dir, charts_dir)` → screener-style financial PNG.

**Data tally check (do this once per name):** jugaad latest `close` must ≈ screener `numeric.price`
(only field both carry). Verified CANBK ₹135.81 (jugaad 4-Jun) ≈ ₹136 (screener) ✓. A mismatch > a
few % means a split the adjuster missed — investigate before trusting any multi-year metric.

**Audit capture:** save the whole screener company page as PDF (`save_company_page_pdf`) into
`filings/<sym>_screener_page.pdf` so every scraped figure is verifiable against the source snapshot.

## Routing table (query part -> skill)

| You need | Call |
|---|---|
| sector quant + rel-strength + 25-DMA/absorption flags | `skills/regime/sector-deep-dive` |
| what drives the sector / who leads | `skills/regime/influence-graph` |
| company about / key points | `equity-research` `screener_reader.fetch_company_about` |
| announcements / RBI penalties / credit ratings / AR + concall links / corp actions | `equity-research` `screener_reader.fetch_company_signals` (all SOURCED) |
| whole-page audit snapshot PDF | `equity-research` `screener_reader.save_company_page_pdf` -> `filings/` |
| annual report / DRHP / concall text + tables | `equity-research` readers (background) |
| fundamentals ratios (P/E,P/B,div yield,NIM,GNPA) | `equity-research` `fetch_company_fundamentals` |
| price+volume+DMA chart, ratio charts | `framework.charts` |
| RBI tables / xlsx | `equity-research` `xlsx_reader.py` (see utility) |
| forward thematic cascade | `skills/screeners/scenario-analyzer` |
| backtest / edge over null / anchor calibration | `skills/edge-pipeline/strategy-harness` |

## Required assembly steps (NOT optional — these are easy to skip and leave `unknown` holes)
The routing table lists what's *available*; these MUST actually be RUN and their output folded in,
or the report ships with unfilled gaps (this bit us once — the influence graph was documented but
never executed, so lead-lag shipped as `unknown`). For every sector report, the driver runs:
1. gather (fundamentals/about/signals/quarters/chart/audit PDF) — `framework.batch`
2. **financial charts** — `framework.charts.financial_charts(sym, …)` per name → `charts/<sym>_financials.png`
3. **influence graph** — `framework.influence_graph.build_sector_graph(sector)` → `graph/` +
   `charts/influence_graph.png` (drives "what moves it / who leads / bellwethers"; never leave
   lead-lag `unknown` without trying this)
4. **group/dependency graphs** — per name + combined network → `charts/dependency_*.png`
   (for banks: SOURCED subsidiary disclosures, NOT screener related-party — it returns txn types)
5. strategy proving-ground — anchor sweep + flow-gate → `strategies/`
6. loan-book sourcing — RBI Sectoral Deployment (`xlsx_reader`, Akamai-proof) + AR segment notes
7. **assemble**: screener-style sector listing (with Stance), per-name reports with EMBEDDED
   `## Visuals`, `GLOSSARY.md`, references. Then `tools/build_pages.py` to publish.
Each is a concrete script call; if you write a custom driver, include ALL of these, don't just
reference them in prose.

## Discipline checklist (run before declaring the report done — the trade-supervisor pass)
- [ ] Every figure is computed-by-us OR has a dated source link in `references.md`.
- [ ] Every unsourceable item says `unknown` (no price-inferred exposures, no fabricated ₹).
- [ ] Prices are split-adjusted (jugaad `adjust=True` default — verify no fake cliffs).
- [ ] Every strategy claim reports **Sharpe-over-null**, not a bare Sharpe.
- [ ] Tables saved as both `.json` and `.csv`; charts saved as PNG; folder layout followed.
- [ ] Compositional/% data (loan mix, sector/corporate exposure, shareholding, geography) rendered as
      **charts** (`composition_chart`), not left as long comma-lists — reviewer decides what's chart-worthy.
