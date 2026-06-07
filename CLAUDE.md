# CLAUDE.md — working notes for this repo

Systematic trading research for **Indian markets only** (NSE/BSE). Serious project — be
meticulous, no placeholder numbers posing as real, every strategy competes via backtest
against a null. Architecture + thesis live in `README.md`; theory sources in `manuals/`.

## Environment (uv, isolated — do NOT touch system Python)

Pinned to **Python 3.12** (`<3.13`); India-market libs lag on 3.13.

```sh
uv venv --python 3.12          # creates .venv (already pinned via .python-version)
uv pip install -e .            # core: pandas, requests
uv pip install -e ".[data]"    # data sources: jugaad-data, nsepython, yfinance, mftool, niftystocks
uv pip install -e ".[backtest]"  # vectorbt (later)
```

Run anything via uv. **`uv run` re-syncs to base deps and DROPS optional extras**, so always
pass the extra you need:

```sh
uv run --extra data python -m data._audit     # data-source verification harness
```

(uv 0.5.9 here — `uv run` has no `--active`; that flag is `uv pip` only.)

## Configuration — dotenv, single seam (ENFORCED)

All host/secret/endpoint/model settings go through **`framework/config.py`** via dotenv. **Do
NOT hardcode** endpoints, API keys, model ids, or host paths in code — read them from config.

```sh
cp .env.example .env      # then edit; .env is gitignored (secrets never committed)
```

- `config.ensure_env()` — locates and loads `.env`, looping candidate paths (repo root -> cwd ->
  `$HOME`), idempotent. Call it at an entrypoint; `ensure_env(required=True)` to hard-fail if no
  `.env` exists. It also runs once on import so plain `config.env(...)` works.
- `config.env(key, default, required=)`, `env_bool`, `env_int` wrap `os.getenv` with
  required-enforcement; `ollama_endpoint()` / `vision_model()` are convenience accessors.
- Recognized vars are documented in `.env.example` (local-vision toggle/endpoint/model/policy,
  OpenAlgo key/host, screener session path).

**The rule:** new code that needs an endpoint/secret/model adds it to `.env.example` and reads it
via `framework.config` — never inline literals.

## One-time host fixes for the data libs (verified 2026-06)

```sh
# jugaad-data: stock_df spawns threads that race on os.makedirs (no exist_ok) for its
# cache dir -> FileExistsError. Pre-create so the branch never fires.
mkdir -p ~/Library/Caches/nsehistory-stock ~/Library/Caches/nsehistory-index

# mftool imports Pillow; the installed wheel can ship without libopenjp2 dylib. Reinstall.
uv pip install --reinstall pillow
```

## Data sources — audited status (see data/_audit.py, data/_audit2.py)

| Source | Use for | Status |
|---|---|---|
| `jugaad-data` `stock_df` | per-stock historical OHLCV + DELIVERY% (primary backtest) | ✅ works (after cache fix); ~0.1s; descending, 15 cols -> normalize |
| `nselib` `capital_market.index_data` | **sector/broad index OHLC + volume (PRIMARY index source)** | ✅ works; 13/13 sectors, ~0.8s, official NSE values, bypasses Akamai; TIMESTAMP `%d-%b-%Y` |
| `yfinance` index tickers (`^NSEI`,`^CNX*`) | index OHLC FALLBACK | ✅ works 13/13; adjusted/approx, no volume; map in `INDEX_YF_TICKERS` |
| `nsepython`/`jugaad` `index_history`/`index_df` (niftyindices.com) | sector-index OHLC | ❌ Akamai-gated: data POST silently dropped (read-timeout) even w/ cookie warm-up. Opt-in only, has 20s timeout |
| `nselib` `price_volume_and_deliverable_position_data` | per-stock OHLCV + delivery (jugaad alt/cross-check) | ✅ works (15 cols incl DeliverableQty) |
| `nsepython` `nse_fiidii` | FII/DII daily provisional cash flow (fast pulse) | ✅ works |
| `nselib` `nsdl_fpi` | official NSDL FPI custody flow (Equity/Debt, net ₹Cr+USD Mn+USDINR) | ✅ works; no auth, ~0.9s; `fpi_flow()` — authoritative flow + dollar tie-in |
| `nsepython` `nse_get_index_list` | validate index names (213) | ✅ works |
| `mftool` | mutual-fund scheme NAV + category filter (the "schemes" question) | ✅ works (after Pillow fix) |
| screener.in (Playwright) | fundamentals: header ratios + growth(3/5/10y) + P&L/BS/CF tables (OPM, Borrowings, FCF) — "shouldn't have fallen" test | ✅ `equity-research/screener_reader.fetch_company_fundamentals`; saved session, [scrape]; `fundamentals()`. Concall/DRHP reading stays the skill's agentic job (pointer only) |
| `yfinance` US drivers (`USDINR=X`,`^TNX`,`SPY`,`^VIX`) | exogenous FII-flow drivers (NOT tradeable) | ✅ works; adapter must NOT suffix `.NS` (exchange≠NSE/BSE -> raw) |
| `nselib` `indices.constituent_stock_list` | **index constituents (PRIMARY)** — any index (sector/broad/thematic), Akamai-free | ✅ works ~0.5s; `index_members(name)` + `constituents(source="nselib")`; targets in `data/index_targets.toml`, full list in `data/index_catalog.md` |
| niftyindices.com CSV | sector constituents (FALLBACK) | ⚠️ works via `requests`+headers + Playwright fallback, but Akamai-prone — demoted under nselib; cached in `data/constituents/` |
| `nseindia.com` `/api/*` (`nse_eq`) | live quote / equity-master | ❌ Akamai-gated; only via Playwright cookie-mint (`_abck`/`bm_sz` need JS) — fragile, deferred |
| `niftystocks` | live sector constituents | ❌ STALE (pre-2022) — REMOVED |

**Sector constituents — SOLVED.** `data/nse_constituents.py` fetches live from niftyindices.com:
`requests` + cookie-warmup + retry (primary), **Playwright headless fallback** (`scrape` extra +
`playwright install chromium`). Use `source="nse_fetch"` (live, caches to `data/constituents/`) or
`source="nse_csv"` (read the cache offline). `SEED_SECTORS` is per-sector fallback. Commit the
cached CSVs for reproducible (survivorship-aware) backtests. Live counts differ a lot from the old
seed (e.g. NIFTY ENERGY = 40 names, not 9) — always prefer `nse_fetch`/`nse_csv`.

**Why `nse_eq` can't be cracked but the CSV can:** niftyindices is a static file host (any
browser-like client works); nseindia.com's API runs Akamai Bot Manager — headless Chromium is
fingerprinted and rejected at the HTTP/2 layer. We don't need live quotes (backtest-first); real-time
is OpenAlgo's job (deferred execution), not scraping.

## Porting status — VENDORED ≠ WIRED

All upstream skills are physically copied in. The work remaining is wiring to the verified data
layer + running/verifying + connecting them — NOT copying.

| State | Skills |
|---|---|
| Vendored, native India (ajeesh) | `screeners/`: fii-dii-flow-tracker, india-market-breadth, india-news-tracker, india-stock-analysis, nse-vcp-screener, options-strategy-advisor, scenario-analyzer, technical-analyst, weekly-fno-trade-planner; `edge-pipeline/backtest-expert`; `fundamentals/equity-research` |
| Vendored + India-ported + verified | `regime/sector-deep-dive` ONLY (genuinely on `data.sources`/`framework`) |
| Vendored but STILL US content (unported) | `regime/`: macro-regime-detector, us-market-bubble-detector, market-breadth-analyzer, breadth-chart-analyst, exposure-coach, **sector-analyst** + **uptrend-analyzer** (both still read TraderMonty US CSV — earlier "ported" claim was WRONG) |
| Off-seam India data | `nse-vcp-screener` (yfinance `.NS`, no jugaad/delivery%); `india-news-tracker` (RSS/WebSearch, not seam-routed) |
| Verified to run | `india-news-tracker` RSS fetcher (recent); historical via date-scoped WebSearch (agentic) |
| NOT done for any vendored skill | wired to framework data layer · run/verified · connected to each other + influence graph |

Key reused mappings: `scenario-analyzer` = forward causal cascade (event->impacts) + event taxonomy
= the influence graph run forward; `sector-deep-dive` stage 6 = same graph backward; `technical-analyst`
= the MA/markers framework (don't reinvent indicators); `india-news-tracker` = the news CLI agent.

## Reporting + fundamentals + document pipeline

- **`skills/reporting/research-report`** — the ORCHESTRATOR for a sector/company investigation.
  Has **credible report templates** in `research-report/templates/`: `equity-research-report.md`
  (company; CFA Institute "Equity Research Report Essentials" section set + our price/flow layer)
  and `industry-analysis.md` (sector; Porter's Five Forces / PESTEL / life-cycle / value chain /
  SWOT). Start a report by copying the right template — don't invent structure. Frameworks are
  thoroughness checklists, never licence to speculate (every cell anchored or `unknown`).
  Routes to the other skills and assembles one folder `reports/research/<name>_<date>/`
  (`00_report.md` + `data/` json&csv + `charts/` + `filings/` + `strategies/<one folder each>` +
  `references.md`). Structure: sector context -> companies (about/filings/fundamentals/charts) ->
  RBI+news -> references -> strategies. Iron rule: every claim anchored to a computed number or a
  dated sourced link; unsourceable = `unknown`. Long steps (filings, calibration) run via the
  harness's background execution — there is NO separate worker (a missing timeout, not a missing
  worker, caused the earlier hang; fixed in the data layer). Multi-name gathering (screener/filing
  scrapes, per-name backtests) goes through **`framework/batch.py`** `run_batch(items, work_fn,
  tracker_path, delay=, jitter=, max_retries=, backoff=)` — paced + retried + a resumable tracker
  JSON persisted after every item, so a throttle/stall resumes where it left off (re-run skips
  `done`, retries `failed`). Avoids rate limits; check `BatchTracker.summary()`.
- **`skills/fundamentals/equity-research`** — THE fundamentals + document provider (vendored from
  the scientific-skills `equity-research`, PLUS our India additions; thin gatherers, agent is the
  analyst). Use as-is; do not reinvent. Scripts:
  - `screener_reader.py` — `fetch_company_about` (ABOUT + KEY POINTS warehouse: NIM/GNPA/market
    share/branch network/loan-book — SOURCED, keep its citation links), `fetch_company_ratios`
    (P/E,P/B,div yield,ROCE,ROE), `fetch_company_fundamentals` (+ P&L/BS/CF/growth/shareholding,
    document URLs). Needs Playwright + saved screener session (`screener_login.py`).
  - Document pipeline (PDF/PPT/XLSX -> Markdown+JSON; agent reads): `pdf_to_md.py` (base) ->
    `annual_report_reader.py`, `drhp_reader.py`/`drhp_vision.py` (qwen2.5vl), `concall_reader.py`
    (transcript>AI-summary>PPT), `xlsx_reader.py` (RBI Sectoral-Deployment tables — **Akamai-proof**:
    `_fetch` auto-falls back to a headless-chromium context for rbidocs/nseindia/bseindia or any
    HTML-challenge response, so RBI's bot wall never returns the HTML block; `--referer` warms cookies).
    Chart-image
    OCR = `framework.local_model` vision (config-gated).
- **`framework/charts.py`** `price_volume_chart` — the swing/position chart (close + 25/50/200-DMA
  + volume + delivery overlay; 200-DMA label is a BAND, not a knife-edge flip).
- **Data integrity — split adjustment (DEFAULT ON):** jugaad prices are RAW; a split shows as a
  fake cliff (CANBK 5:1 2024-05-14, 566->119 => fake -87% DD, ranked worst; truth +30% CAGR,
  rank 3). `JugaadData.history(adjust=True)` back-adjusts via `data.sources.back_adjust_splits`:
  gap-detect FIRST (offline, zero network for no-split names), confirm ratio against yfinance
  (`data/corporate_actions/` disk cache + 8s timeout, never hangs). Split-only (matches screener),
  not dividend-adjusted. Any pre-fix multi-year metric is suspect.

## Dependency / social graph (business ecosystem) — core + agent-driven SKILL

Who depends on a company, who it depends on, partners/competitors, group entities, plus the social
layer (board interlocks, promoter group). **Country-polymorphic.**
- **Core (generic, thin):** `framework/dependency_graph.py` — Entity/Edge model, `build_graph(seed,
  country, ...)` BFS engine, `derive_social_edges` (board/promoter), `validate_with_prices`
  (corroboration overlay via `influence_graph` — NEVER creates edges). `Entity.listed` distinguishes
  listed (filings backbone) from PRIVATE (e.g. Razorpay → MCA/RBI/news).
- **Providers (thin gatherers, per country):** `framework/dependency_providers/{india,us}.py`,
  registered by country. **US = SEC EDGAR** (submissions + full-text reverse-lookup "who names X",
  free/structured). **IN** = screener related-party (corroboration) + LODR/AR/MCA/RBI (agent-driven).
  Add a country = new provider module + `register_provider`.
- **Driver:** `skills/regime/dependency-graph/SKILL.md` — the agent REASONS the discovery strategy
  (not a fixed recipe): characterise entity → pick from source ARCHETYPES (regulator/registrar/
  domain-licence/self-disclosure/counterparty/news/aggregator/technical) → write a `discovery_plan.md`
  → gather → typed+directional+SOURCED edges (price never implies a relationship; EDGAR low-confidence
  reverse hits must be refined). Private seeds: domain via RBI register, customers via case-studies/
  news, then sector-peers via `data_api.constituents()`.

## Publishing research to GitHub Pages (`tools/build_pages.py`)

Turns `reports/research/*` into a MkDocs Material site, **excluding code** (driver scripts `_*.py`,
trackers `*_tracker.json`, logs). Generic — auto-discovers every report folder; re-run any time.

```sh
uv run python tools/build_pages.py            # assembles docs/ + mkdocs.yml; PASS/FAIL self-audit
uvx --with mkdocs-material mkdocs serve        # preview at http://127.0.0.1:8000
uvx --with mkdocs-material mkdocs build --strict   # render to site/ (what the Action runs)
```

- **Validate no code is published (fail-closed):** `build_pages.py` ends with `validate_no_code(docs/)`
  and **exits 1** if any `_*.py` / `*_tracker.json` / `*.log` / `.py` slips in — prints
  `PASS: no code/driver/tracker/log files in docs/`. The same gate runs in CI, so a leak fails the build.
- Manual re-check anytime: `find site -name '_*.py' -o -name '*_tracker.json' -o -name '*.log'`
  must return nothing. Data (csv/json) + audit PDFs ARE published (research output, auditable);
  only the executable pipeline is withheld.
- `docs/` and `site/` are generated and gitignored. Deploy: `.github/workflows/pages.yml` builds +
  publishes on push to `main` (needs the repo's Pages source set to "GitHub Actions").

## Conventions

- Git commits: **no `Co-Authored-By` trailer.**
- Hardcoded maps (sectors->constituents, cyclical/defensive) are SEED / guardrail only; real
  inputs are loaded. Don't promote a hardcode to source-of-truth.
- Separate quantitative (scriptable, chartable) from causal/narrative ("who pivoted on policy")
  analysis — narrative must be anchored to verified numbers, never freestanding.
