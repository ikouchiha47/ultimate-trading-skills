---
name: influence-graph
description: >
  Build and empirically validate an influence graph for an Indian sector — which macro drivers
  (USD, US yields, VIX), the broad market, and which constituents actually move/lead it, EARNED
  from data by lead-lag (not asserted). Use when asked "what drives <sector>", "who leads the
  basket", "is <driver> really moving <sector>", for scenario impact-ranking, or to scope the
  causes behind a sector-deep-dive divergence. India-only.
tags: [india, causal, influence-graph, lead-lag, flow-vs-information, scenario]
triggers: [what drives, who leads, bellwether, causal, influence, lead-lag, transmission, why did, what moved]
---

# Influence graph (India)

## Overview

A typed graph of NODES (macro drivers · broad market · sector · constituents) and hypothesis
EDGES ("X moves Y, expected sign + mechanism"). The engine `framework/influence_graph.py` is
**generic** — it makes no claim about which sector or which hypotheses. **You (the agent) decide
what to analyse**; the script earns each edge from data and hands back structured results + a
plot, which you interpret. It is a **hypothesis generator + search scoper, NOT a truth oracle**
(manuals/12): every empirical edge is validated by lead-lag; untestable ones (e.g. repo rate —
macro source `MISSING`) are marked, never asserted.

Two directions:
- **Forward** (scenario-analyzer): event -> ranked impacts (follow edges out of a driver).
- **Backward** (sector-deep-dive stage 6): a divergence -> candidate causes (edges into the sector),
  then corroborate with dated news (`data_api.news`, `sourced`) + fundamentals.

## Workflow

### 1. Build + validate the graph (you pick the sector and, optionally, the drivers)

```python
from framework.influence_graph import build_sector_graph, company_sector_graph, format_report, plot_graph

# Default drivers (USD/US10Y/VIX/Nifty50) + constituents -> the sector, all validated:
nodes, edges = build_sector_graph("PSU Bank", since="2023-01-01")
print(format_report(edges))
plot_graph(nodes, edges, title="PSU Bank influence graph")   # -> reports/influence_graph/*.png
```

Override the drivers for a custom hypothesis (e.g. test crude + China for Metal). Driver spec is
`(id, "driver:<name>"|"index:<name>", expected_sign, mechanism)`; valid index names are in
`data/index_catalog.md`:

```python
metal_drivers = [("NIFTY50","index:Nifty 50",+1,"market beta"),
                 ("USDINR","driver:USDINR",-1,"INR/import cost")]   # add crude when audited
build_sector_graph("Metal", drivers=metal_drivers)
```

### 2. Bellwethers — who moves/leads the basket

```python
for e in company_sector_graph("PSU Bank"):        # ranked by |corr|
    print(e.src, e.corr0, e.verdict)
```

### 3. Interpret (this is your job, not the script's)

| verdict | meaning | how to use |
|---|---|---|
| `supported (co-move)` | strong same-bar corr in expected sign | a real driver; size impact by `corr0` |
| `supported (leads Nd)` | directionally-correct corr at +N days | **predictive** edge — the valuable kind |
| `weak` | small/ambiguous | keep as a maybe; retest weekly |
| `no daily link …` | ~0 at daily freq | NOT false — flow channels act over weeks; check via flow/weekly |
| `wrong sign` | opposite to hypothesis | the mechanism is wrong — revise or drop |
| `untested (… MISSING)` | no audited source yet (repo, G-sec) | structural only; do not assert |

Read `corr0` as effect size, `lead_lag` as how many days of warning. A high market-beta + low
idiosyncratic spread ⇒ cyclical/top-down sector; low beta + high constituent dispersion ⇒
bottom-up (manuals/12) — which sets the flow-vs-information prior for the fade edge.

## Discipline

- Every claimed edge must be EARNED (a verdict from data) — never narrate a link from memory.
- Prefer near nodes; treat far/multi-hop links (e.g. datacenter->private-banks) as low-confidence
  until lead-lag confirms them (manuals/12 worked example).
- `no daily link` ≠ false. Macro->sector often transmits through FLOW over weeks; say so, and
  retest at weekly frequency or once the FPI-flow time series is richer.
- Names/mappings come from the single sources (`data/index_targets.toml`, `data/index_catalog.md`).
  Do not hardcode index names in prompts — reference the catalog.

## Engine reference (generic primitives in `framework/influence_graph.py`)

- `node_returns(spec, since)` — return series for `index:/driver:/stock:` specs.
- `lead_lag(x, y)` — causal-direction cross-correlation (x leads y).
- `build_sector_graph(sector, drivers=…, with_constituents=…, extra_edges=…)` — assemble + validate.
- `company_sector_graph(sector)` — constituent->sector edges, ranked.
- `plot_graph(nodes, edges)` — auto-laid-out PNG (green=co-move, blue=leads, dotted=untested, faint=no link).
