# Sector constituents — manual NSE download

This is the **live, authoritative** sector→stock mapping. There is no reliable programmatic
feed (the `niftystocks` package is frozen at pre-2022 members; `nsepython` has no constituents
function). NSE itself publishes the current list for every index as a CSV — so we download those
by hand and drop them here. This beats any scraper: it's the source of truth and never silently
goes stale.

## How to get the files

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
