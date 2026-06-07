# PORTING_PLAN.md — integrating the vendored skills into the audited stack

**Goal.** Make all 28 vendored skills draw data **only** through one audited seam, run on
**India (NSE/BSE)** data, instruct the agent (in their `SKILL.md` prose) to use that path, cite
theory from `manuals/`, and reconcile their numbers with the framework's own. No US feeds, no
broker-MCP taps, no silent fallbacks, no placeholder numbers posing as real.

This is **wiring + porting + connecting**, not copying — everything is already vendored.

---

## 0. Corrected status (supersedes earlier claims)

Earlier notes (CLAUDE.md, memory) called `sector-analyst` and `uptrend-analyzer`
"India-ported + verified." **That was wrong** — both still fetch TraderMonty's US
`uptrend-dashboard` GitHub CSV. Verified plumbing per skill:

| Skill | Today's data tap | On our seam? |
|---|---|---|
| `regime/sector-deep-dive` | `data.sources` + `framework.india_sectors` | ✅ yes (the only one) |
| `screeners/nse-vcp-screener` | `yfinance` `.NS` tickers | ⚠️ India data, off-seam (no jugaad/delivery%) |
| `screeners/india-news-tracker` | RSS (recent) verified; WebSearch (historical) verified | ⚠️ runs, not seam-routed |
| `screeners/*` (fii-dii, india-stock-analysis, technical-analyst, scenario-analyzer, india-market-breadth, options-strategy-advisor, weekly-fno) | **broker-MCP** tool calls + web-search/yfinance fallback (prose-driven) | ❌ no |
| `regime/sector-analyst`, `regime/uptrend-analyzer`, `regime/market-breadth-analyzer`, `regime/breadth-chart-analyst`, `regime/macro-regime-detector`, `regime/us-market-bubble-detector`, `regime/exposure-coach` | **US feeds** (TraderMonty CSV / FMP / FRED / yfinance) | ❌ no, and US universe |
| `edge-pipeline/*` (10) | mostly LLM-agent/orchestration; data touchpoints in `backtest-expert`, `signal-postmortem`, `edge-signal-aggregator` | ❌ no |

---

## 1. The seam — `framework/data_api.py` (Step 0, build first)

One stable façade every skill imports. Wraps the already-audited adapters in `data/sources.py`
and `data/nse_constituents.py`. Skills never import yfinance/FMP/FRED/MCP again.

```
history(symbol, since, source="jugaad")   -> OHLCV + delivery%      (JugaadData / YFinance)
index(name, since)                        -> sector/benchmark OHLC   (NseIndexSource)
fii_dii(since)                            -> FII/DII daily cash flow (FiiDiiSource)
constituents(sector, source="nse_csv")    -> live membership         (nse_constituents)
nav(scheme=None, category=None)           -> MF NAV history          (MutualFundSource)
breadth(sector_or_universe, since)        -> % >50/200DMA, A/D, NH/NL (Step 2 India source)
driver(name, since)                       -> USDINR/^TNX/SPY/QQQ/^VIX/FPI (exogenous only)
news(query, since=None)                   -> recent(RSS) | historical(WebSearch) contract
```

### MISSING registry + fallback policy (decided)
- Numeric data we have **not** audited for India -> `raise NotImplementedError("MISSING: <gap>")`.
  **Hard fail.** No US fallback, no web-search number substituted for a computed one. A skill that
  needs a missing source stays partially dark until the source is built — that is acceptable; a
  fake number is not.
- **Exception — flagged WebSearch for narrative/news only.** `news()` and stage-6-style causal
  narrative may use date-scoped WebSearch, returned **clearly labelled `sourced` (dated URL), never
  `computed`**. It may never stand in for a price/flow/breadth number.

---

## 2. Data-layer gaps to close before consumers wire (Step 1)

These are what the seam's `breadth()`/`driver()`/fundamentals will otherwise hard-fail on:

- [x] **India breadth source** — `data/breadth.py` (% above 50/200-DMA, advance/decline line,
      new 52w highs/lows) computed from constituent OHLCV via the seam's `history()`, with a
      200-DMA warm-up buffer so rolling stats are valid from the first bar. Wired to
      `data_api.breadth()`. Verified live (PSU Bank). Replaces the TraderMonty US CSV.
- [x] **US-driver nodes** — `data_api.driver()` (USDINR, ^TNX, SPY/QQQ/^VIX via yfinance, raw
      ticker, verified) as **exogenous inputs**; NOT a tradeable universe.
- [x] **NSDL FPI custody flow** — `data_api.fpi_flow()` via `nselib.nsdl_fpi` (Equity/Debt split,
      net ₹Cr + USD Mn + USD/INR; no auth, ~0.9s). Verified. Authoritative FPI flow vs fii_dii().
- [x] **India fundamentals** — `data_api.fundamentals()` via the vendored equity-research
      screener.in Playwright reader (`fetch_company_fundamentals`): header ratios (P/E, ROCE,
      ROE, book value, debt) + growth 3/5/10y (sales, profit, RoE, stock CAGR) + P&L/BS/CF
      tables (OPM, Borrowings trajectory, Free Cash Flow). Concall/DRHP/AR *reading* deferred to
      the skill (agentic; pointer only). Saved session; [scrape] extra. Verified (SBIN, RELIANCE).
      **Step 1 COMPLETE.**

---

## 3. Wiring waves — by plumbing type & dependency order (NOT by size)

**Foundation — universe builder** (`framework/universe.py`, ✅ verified): `build_universe(base,
**filters)` resolves any index via `index_members` -> composable price filters (liquidity,
above-MA, momentum, delivery%) + fundamental filters (ROCE/debt/sales-growth, only on
price-survivors) -> survivors + transparent table. PSU Bank 5/12 pass. Hardened `indicators.py`
vs yfinance trailing-NaN. nse-vcp now screens the **real Nifty 500** via `index_members`.
Constituent layer switched to nselib primary (Akamai-free); targets in `data/index_targets.toml`,
catalog in `data/index_catalog.md`.

### Wave A — native-India broker-MCP skills -> seam
Already India; only the data tap is wrong. Per skill: rewrite the SKILL.md data section
(MCP tool -> `data_api` call), remove/redirect the fallback table, run live, verify numbers.
Order = thesis dependency (what feeds what):

1. [x] `fii-dii-flow-tracker` -> `fii_dii()` + `fpi_flow()` + `index()` + `driver()`. SKILL.md
       data steps rewritten (was WebSearch + Groww MCP); trailing trend loops NSDL anchored to
       latest report; WebSearch demoted to narrative-only. Verified live. **Acceptance gate passed.**
2. [x] `india-stock-analysis` -> `history()` (+delivery%) + `fundamentals()` (ratios/growth/
       P&L-BS-CF + **shareholding** added to screener reader) + `index()`. Data Sources section
       rewritten (was Groww/Zerodha MCP); indicators defer to `technical-analyst`; WebSearch
       narrative-only. Verified live (RELIANCE). **Acceptance gate passed.**
3. [x] `technical-analyst` -> **no data wiring needed**: it's a VISION skill (reads chart
       *images*), zero MCP/US deps. Built the real numeric engine `framework/indicators.py`
       (SMA/EMA/RSI/MACD/ATR/Bollinger/ADX from `history()`, verified on SBIN) for the skills
       that need indicator *values* (corrected `india-stock-analysis` to point here, not at this
       vision skill). Optional config-gated local-VLM fallback added (`framework/local_model.py`
       + `config/local_models.toml`, `[local]` extra) — qwen2.5vl:3b **validated** for chart
       number-OCR + colour (SBIN:33,PNB:24,CANBK:30). Extraction-only; agent does compute.
4. [x] `nse-vcp-screener` -> `history()` (+delivery% option) + `index()` benchmark (selectable,
       any NSE index) + universe via `index_members`/constituents (real Nifty 500). niftystocks
       removed. Calculators fed Capitalized cols; verified (trend/RS scores real).
5. [x] `scenario-analyzer` -> price via `history()`, news via `news()`; prose marks it the
       influence-graph FORWARD pass (hypothesis generator; rank by directness, validate far nodes).
6. [x] `india-market-breadth` -> `breadth()` (A/D, %>50/200DMA, NH/NL) + `index()` divergence +
       sector participation loop. Data Sources + Steps 1/3/4 rewritten (was WebSearch + Groww MCP).
7. [~] `options-strategy-advisor` -> underlying via `index()`/`history()` (+realized vol). **Live
       option chain / OI / Greeks = `MISSING`** (OpenAlgo-deferred) — skill honestly partial, no fabrication.
8. [~] `weekly-fno-trade-planner` -> movers via `build_universe` (rank by momentum) + `breadth()` +
       `fii_dii`/`fpi_flow`; underlying via `index()`. **Live F&O list/OI = `MISSING`** (deferred).
9. [x] `india-news-tracker` -> cross-ref section rewritten to `news()` + `history()` (+delivery as
       flow-vs-info tell) + `fundamentals()`; broker MCP removed. RSS/WebSearch modes verified earlier.

### Wave B — US-feed regime skills -> India port + seam
Bigger: tickers, breadth definitions, feeds all change.

10. [ ] `macro-regime-detector` -> seam + `driver()` nodes (where US->FII drivers legitimately live)
11. [ ] `market-breadth-analyzer` -> `breadth()` (depends on Step-2 India breadth)
12. [ ] `breadth-chart-analyst` -> `breadth()` + chart layer
13. [ ] `uptrend-analyzer` -> **re-port for real** off `history()`/`breadth()`
14. [ ] `sector-analyst` -> **re-port for real** off `index()`/`constituents()` (de-dupe vs sector-deep-dive)
15. [ ] `exposure-coach` -> consumes 10–14, position-sizing on India regime
16. [ ] `us-market-bubble-detector` -> LPPL math is universe-agnostic; retarget to NIFTY indices

### Wave C — edge-pipeline (10 skills)
Mostly orchestration/LLM-agent flows; retarget examples to India, references -> `manuals/`.
Real data touchpoints:

17. [ ] `backtest-expert` -> wire to `framework.harness.BacktestHarness` + vectorbt
18. [ ] `signal-postmortem` -> seam
19. [ ] `edge-signal-aggregator` -> seam
20–26. [ ] remaining edge-pipeline (candidate/concept/hint/orchestrator/designer/reviewer/ideator)
        -> prose + examples retargeted to India; no direct data taps

---

## 3b. EDGE TRACK — the actual research goal (outranks finishing B/C plumbing)

The differentiated work: prove the flow-vs-information mean-reversion edge on real data. The
vendored skills are plumbing; this is the point.

- [x] **Influence-graph backbone** — generic engine (`framework/influence_graph.py`) + skill;
      lead-lag-validated; bellwether + driver verdicts; plot. PSU Bank + IT verified.
- [ ] **BacktestHarness -> vectorbt** — wire `framework/harness.py` so a strategy + a null produce
      real, cost-aware, walk-forward numbers (manuals/10). The proving ground.
- [ ] **BNF mean-reversion strategy** — code as an `IStrategy` (25-DMA deviation snap-back on
      flow-driven dislocations), run vs a null through the harness. We have theory + data, no strategy yet.
- [ ] **Flow-vs-information classifier** — combine `fii_dii`/`fpi_flow` + delivery% + driver()
      + sector mode (manuals/12) into a per-dislocation "fadeable vs trap" score. The edge's heart.
- [ ] **Influence graph at WEEKLY freq + via flow series** — daily test showed macro->sector as
      "no daily link"; retest weekly + with a richer FPI-flow time series.
- [ ] **Macro source** (RBI repo, G-sec yields, CPI) — `MacroSource` stub -> real; unblocks the
      graph's structural edges + macro-regime.
- [ ] **HMM regime detection** — code the manuals/06 theory (rotation vs structural break).

### sector-deep-dive completion (now unblocked)
- [ ] Stage 4 — RBI/policy **event overlay** on the timeline.
- [ ] Stage 6 — numbers-anchored **narrative join** (measured inflection + influence-graph causes
      + dated `news()` + fundamentals; never from memory).
- [ ] Add `dist_from_25dma` (z-scored) + `uptrend` to the per-stock table (the BNF marker).
- [ ] Refactor to **generic core + agent-driven skill** (the influence-graph pattern); same for
      `scenario-analyzer` — don't embed specifics in the core.

### Backlog (separate tracks)
- [ ] OpenAlgo live layer (option chain / live quotes / execution) — unblocks the 2 F&O skills.
- [ ] IPO pipeline + unlisted/pre-IPO tracking (liquidity-flow node).

---

## 4. Connect (Step 3) — wiring is the precondition, not the goal
- `scenario-analyzer` (forward) + `sector-deep-dive` stage 6 (backward) share the influence-graph backbone
- `technical-analyst` = MA/markers provider others import (don't reinvent indicators)
- `india-news-tracker` = the `news()` seam for stage 6
- `fii-dii` + `driver()` = the flow-vs-information classifier feeding everything

---

## 5. Per-skill acceptance gate (Step 4 — the meticulous bar)
A skill is **done** only when all hold:
1. Zero imports of yfinance/FMP/FRED/MCP outside `framework/data_api.py`.
2. `SKILL.md` prose instructs the seam path (no stale MCP/US instructions).
3. Runs live on India data; numbers reconcile with the framework's own (no two paths disagreeing).
4. Any unavailable input hard-fails as `MISSING` (narrative-only WebSearch allowed, labelled `sourced`).
5. References point at `manuals/`.
6. Committed (no `Co-Authored-By` trailer).

---

## 6. Build order summary
**Step 0** seam + MISSING registry -> **Step 1** breadth/driver/fundamentals gaps ->
**Wave A** (1–9) -> **Wave B** (10–16) -> **Wave C** (17–26) -> **Connect** -> gate every skill.
