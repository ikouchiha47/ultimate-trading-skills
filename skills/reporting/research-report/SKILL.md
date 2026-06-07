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

## Output layout — one folder per investigation

```
reports/research/<SECTOR-or-COMPANY>_<YYYY-MM-DD>/
  00_report.md                 # the assembled narrative (this is the deliverable)
  data/                        # every table as .json AND .csv (the raw numbers)
  charts/                      # generated PNGs (price+vol+DMA, rel-strength, ratios)
  filings/                     # extracted AR / DRHP / concall .md + .json per company
  strategies/                  # one subfolder per strategy run (see §6)
    <strategy>_<sector>/       #   backtest result, equity curve, params, verdict
  references.md                # ALL source links, for testing/audit
```

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
- **Data tables** — `fetch_company_fundamentals` / `fetch_company_ratios` → write each to
  `data/<symbol>_ratios.json` AND `.csv` (P&L, balance sheet, cash flow, growth, shareholding).
- **Charts** — `framework.charts.price_volume_chart` (price + 25/50/200-DMA + volume + delivery)
  into `charts/`; plus ratio charts (P/E, P/B, dividend yield over time, like screener).
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
| P&L / Balance Sheet / Cash Flow (12y) | screener `fetch_company_fundamentals` | jugaad has ZERO fundamentals |
| shareholding (promoter/FII/DII trend) | screener (same call) | the ownership-flow signal |
| growth CAGRs, ratios (P/E, NIM, GNPA, div yield) | screener `fetch_company_fundamentals` / `fetch_company_ratios` | — |
| segments (Retail/Wholesale/Treasury/Life Ins) | screener (premium-GATED) | row NAMES present, VALUES blank → write `unknown`, NOT a bug |
| announcements / RBI penalties / concalls / ARs | screener Documents + `get_documents` | sourced narrative + filing URLs |

**Return shapes (don't re-derive — they bit us once):**
- `JugaadData.history(sym, start, end, adjust=True)` → DataFrame indexed by **`date`** (already the
  index, do NOT `set_index("date")`); columns `open/high/low/close/volume/vwap/trades/deliverable_qty/delivery_pct`.
- `fetch_company_fundamentals(sym)` → `{symbol,url,numeric,ratios,growth,tables,documents_note}` where
  `tables[section] = {"periods":[...], "rows": {line_item: [floats]}}` for section in
  `profit_loss/balance_sheet/cash_flow/shareholding`. (CSV = header `line_item,*periods`, one row per line_item.)
- `fetch_company_about(sym)` → `{about, key_points{raw,sections}, links, website, bse, nse}` (SOURCED).
- `fetch_company_ratios(sym)` → `{ratios{label:str}, numeric{key:float}}`.

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
2. **influence graph** — `framework.influence_graph.build_sector_graph(sector)` → `graph/` +
   `charts/influence_graph.png` (drives the "what moves it / who leads / bellwethers" section;
   never leave lead-lag as `unknown` without having tried this)
3. strategy proving-ground — anchor sweep + flow-gate → `strategies/`
4. loan-book sourcing — RBI Sectoral Deployment (`xlsx_reader`, Akamai-proof) + AR segment notes
Each is a concrete script call; if you write a custom driver, include ALL of these, don't just
reference them in prose.

## Discipline checklist (run before declaring the report done — the trade-supervisor pass)
- [ ] Every figure is computed-by-us OR has a dated source link in `references.md`.
- [ ] Every unsourceable item says `unknown` (no price-inferred exposures, no fabricated ₹).
- [ ] Prices are split-adjusted (jugaad `adjust=True` default — verify no fake cliffs).
- [ ] Every strategy claim reports **Sharpe-over-null**, not a bare Sharpe.
- [ ] Tables saved as both `.json` and `.csv`; charts saved as PNG; folder layout followed.
