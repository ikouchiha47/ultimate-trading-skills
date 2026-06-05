# Sector constituents — live NSE source (auto-fetched, cached here)

This is the **live, authoritative** sector→stock mapping from niftyindices.com. Files here are
normally written automatically by `data/nse_constituents.py` (`source="nse_fetch"`); they can also
be downloaded by hand if the fetch is ever blocked. The `niftystocks` package is NOT used (frozen
at pre-2022 members).

## Automatic (preferred)

```python
from framework.india_sectors import load_sector_constituents
m = load_sector_constituents(source="nse_fetch")  # live fetch + cache to this dir
m = load_sector_constituents(source="nse_csv")     # read the cache offline
```
`nse_fetch` uses `requests`+cookie-warmup with retries, and falls back to **Playwright headless**
(install: `uv pip install -e ".[scrape]" && uv run playwright install chromium`). Per-sector
fallback to `SEED_SECTORS` if a sector fails.

## Manual fallback — how to get the files by hand

1. Go to **https://www.niftyindices.com** → *Indices* → pick the sectoral index.
2. On the index page, use **Download (.csv)** for the constituent list
   (or directly: `https://www.niftyindices.com/IndexConstituent/ind_nifty<...>list.csv`).
3. Save it here, **renamed to the sector key** (exact, including the space):

   | Save as | NSE index |
   |---|---|
   | `PSU Bank.csv` | NIFTY PSU BANK |
   | `Private Bank.csv` | NIFTY PRIVATE BANK |
   | `Financial Services.csv` | NIFTY FINANCIAL SERVICES |
   | `Auto.csv` | NIFTY AUTO |
   | `IT.csv` | NIFTY IT |
   | `Pharma.csv` | NIFTY PHARMA |
   | `FMCG.csv` | NIFTY FMCG |
   | `Metal.csv` | NIFTY METAL |
   | `Energy.csv` | NIFTY ENERGY |
   | `Realty.csv` | NIFTY REALTY |
   | `Infra.csv` | NIFTY INFRASTRUCTURE |

Keep NSE's native format — the loader only needs the **`Symbol`** column (the file also has
Company Name / Industry / Series / ISIN, which is fine to leave in).

## How it's used

```python
from framework.india_sectors import load_sector_constituents
m = load_sector_constituents(source="nse_csv")   # reads this dir; per-sector fallback to seed
```

Or via the skills: `--source nse_csv`. Any sector **without** a file here falls back to the
hardcoded `SEED_SECTORS` guardrail, so a partial download still works.

## Refresh cadence

NSE rebalances sectoral indices periodically (additions/removals, mergers). Re-download after a
rebalance. Commit the CSVs so backtests are reproducible against a known constituent set
(survivorship matters — see `manuals/10-backtesting-discipline.md`).
