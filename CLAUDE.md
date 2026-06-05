# CLAUDE.md — working notes for this repo

Systematic trading research for **Indian markets only** (NSE/BSE). Serious project — be
meticulous, no placeholder numbers posing as real, every strategy competes via backtest
against a null. Architecture + thesis live in `README.md`; theory sources in
`CONCEPTS_REFERENCES.md`.

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
| `nsepython` `nse_eq` | live single-stock quote | ❌ blocked by NSE anti-bot — not needed |
| `niftystocks` | live sector constituents | ❌ STALE (pre-2022, e.g. LTI/MINDTREE) — do NOT use |

**Open gap:** no reliable *live* sector-constituent feed (niftystocks is frozen; nsepython has
no constituents fn). Proper source = NSE/niftyindices index-constituent CSVs. Until wired,
`framework/india_sectors.SEED_SECTORS` stays the primary map (it's a loaded input, fallback-only
by design — see `load_sector_constituents`).

## Conventions

- Git commits: **no `Co-Authored-By` trailer.**
- Hardcoded maps (sectors→constituents, cyclical/defensive) are SEED / guardrail only; real
  inputs are loaded. Don't promote a hardcode to source-of-truth.
- Separate quantitative (scriptable, chartable) from causal/narrative ("who pivoted on policy")
  analysis — narrative must be anchored to verified numbers, never freestanding.
