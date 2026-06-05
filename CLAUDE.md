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

## One-time host fixes for the data libs (verified 2026-06)

```sh
# jugaad-data: stock_df spawns threads that race on os.makedirs (no exist_ok) for its
# cache dir → FileExistsError. Pre-create so the branch never fires.
mkdir -p ~/Library/Caches/nsehistory-stock ~/Library/Caches/nsehistory-index

# mftool imports Pillow; the installed wheel can ship without libopenjp2 dylib. Reinstall.
uv pip install --reinstall pillow
```

## Data sources — audited status (see data/_audit.py, data/_audit2.py)

| Source | Use for | Status |
|---|---|---|
| `jugaad-data` `stock_df` | per-stock historical OHLCV + DELIVERY% (primary backtest) | ✅ works (after cache fix); descending order, 15 cols → normalize |
| `nsepython` `index_history` | sector-index daily OHLC (rel-strength) | ✅ works; dup cols + string dates → clean |
| `nsepython` `nse_fiidii` | FII/FPI + DII daily cash flow (thesis input) | ✅ works |
| `nsepython` `nse_get_index_list` | validate index names (213) | ✅ works |
| `mftool` | mutual-fund scheme NAV + category filter (the "schemes" question) | ✅ works (after Pillow fix) |
| `yfinance` | fallback OHLCV | ✅ works; multi-index cols → flatten in adapter |
| niftyindices.com CSV | live sector constituents | ✅ works via `requests`+headers; Playwright fallback wired |
| `nsepython` `nse_eq` | live single-stock quote | ❌ Akamai-blocked (403/HTTP2) even via headless Playwright — NOT needed |
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
| Vendored + India-ported + verified | `regime/sector-analyst`, `regime/uptrend-analyzer`; new `regime/sector-deep-dive` |
| Vendored but STILL US content (unported) | `regime/`: macro-regime-detector, us-market-bubble-detector, market-breadth-analyzer, breadth-chart-analyst, exposure-coach |
| Verified to run | `india-news-tracker` RSS fetcher (recent); historical via date-scoped WebSearch (agentic) |
| NOT done for any vendored skill | wired to framework data layer · run/verified · connected to each other + influence graph |

Key reused mappings: `scenario-analyzer` = forward causal cascade (event→impacts) + event taxonomy
= the influence graph run forward; `sector-deep-dive` stage 6 = same graph backward; `technical-analyst`
= the MA/markers framework (don't reinvent indicators); `india-news-tracker` = the news CLI agent.

## Conventions

- Git commits: **no `Co-Authored-By` trailer.**
- Hardcoded maps (sectors→constituents, cyclical/defensive) are SEED / guardrail only; real
  inputs are loaded. Don't promote a hardcode to source-of-truth.
- Separate quantitative (scriptable, chartable) from causal/narrative ("who pivoted on policy")
  analysis — narrative must be anchored to verified numbers, never freestanding.
