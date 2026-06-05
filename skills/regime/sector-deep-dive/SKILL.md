---
name: sector-deep-dive
description: >
  Deep-dive one Indian sector (NSE): rank its constituents by risk-adjusted return,
  measure the sector's relative strength vs NIFTY 50, render charts, and tee up a
  numbers-anchored narrative on which names led/lagged. Use when asked to "analyse
  / deep-dive / report on" a sector (e.g. "look into PSU banks", "which IT names
  held up", "PSU Bank report with charts"). India-only.
---

# Sector deep-dive (India)

Turns a vague "tell me about sector X" into a structured, falsifiable report. The script
does the **quantitative** stages; Claude does the **narrative** stage on top of the verified
numbers — never freestanding (see `manuals/01`, repo CLAUDE.md).

## Pipeline

| Stage | What | Where |
|---|---|---|
| 1 | resolve constituents | `load_sector_constituents` (live `nse_fetch` / cached `nse_csv`) |
| 2 | per-stock performance | CAGR, max drawdown, **Calmar** (risk-adj), 20d return, avg delivery %, excess-vs-sector |
| 3 | sector vs market | sector NSE index vs NIFTY 50 relative strength |
| 5 | charts (`--report`) | matplotlib PNGs → `reports/sector-deep-dive/<sector>_<date>/` |
| 4 | event overlay | mark RBI/policy dates on the timeline — **TODO** |
| 6 | narrative | Claude reads stages 2–4 + fundamentals/news skills → "who pivoted, who didn't" |

## Run

```sh
# quant report + charts (jugaad gives delivery %; yfinance is faster, no delivery)
uv run --extra data python skills/regime/sector-deep-dive/scripts/sector_deep_dive.py \
    "PSU Bank" --since 2020-01-01 --report

uv run --extra data python .../sector_deep_dive.py IT --since 2022-01-01 \
    --price-source yfinance --json
```

Flags: `--since YYYY-MM-DD` (default 5y), `--source seed|nse_fetch|nse_csv` (default
`nse_csv`), `--price-source jugaad|yfinance`, `--report` (charts), `--json`.

## How to prompt it (the trick)

A good prompt mirrors the stages 1:1, e.g.:

> "Deep-dive PSU Bank since 2020. Rank constituents by risk-adjusted return, show relative
> strength vs NIFTY 50 with charts, then — anchored to those numbers — tell me which banks
> pivoted well on the rule changes (PSL norms, HDFC merger, PCA exits) and which didn't."

Each clause maps to a stage. Run the script for 1–3/5, then read its JSON to write stage 6.

## Discipline

- Stage 6 (causal "who pivoted") MUST cite the stage-2/3 numbers; no freestanding hindsight.
- Constituent counts come from the live NSE source, not stale guesses (`manuals/10` —
  survivorship matters; commit the `data/constituents/*.csv` used).
