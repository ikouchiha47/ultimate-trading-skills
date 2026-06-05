# Ultimate Trading Skills (India)

Consolidated Claude skill stack for **Indian-market** systematic trading. One decision chain:

> **regime → sector rotation → quality filter → edge experiment → backtest → (sandbox execute)**

Built by vendoring four sources into four layers. Provenance and India-port status tracked below.

## The 4-layer stack

| Layer | Dir | Does | Vendored from | India status |
|---|---|---|---|---|
| **1 Data + forward-test** | `engines/openalgo-data/` | historical OHLCV (broker-quality) + ₹1cr sandbox paper-test; live execution deferred | [OpenAlgo](https://github.com/marketcalls/openalgo) (run separately) | native India ✅ |
| **2 Regime brain** | `skills/regime/` | macro regime, sector rotation, breadth, bubble risk | tradermonty (US) | **needs port** ⚠️ |
| **3 Screeners** | `skills/screeners/` | breadth, FII/DII, VCP, F&O, news, stock analysis | ajeesh (India) | native India ✅ |
| **4 Fundamentals** | `skills/fundamentals/` | screener.in, concalls, DRHP, fundamentals = quality filter | your equity-research | native India ✅ |
| **Edge pipeline** | `skills/edge-pipeline/` | hypothesis → strategy → review → backtest (the experiment harness) | tradermonty | market-agnostic ✅ |
| **Engines** | `engines/` | OU mean-reversion, HMM regime, vectorbt, yfinance, stats | claude-scientific-skills | agnostic ✅ |

### The backbone (this is the real product, not any single strategy)

```sh
framework/                   # the contracts everything plugs into
├── interfaces.py            #   IDataSource, IStrategy, Signal, StrategyMeta
├── registry.py              #   register/enumerate providers
└── harness.py               #   BacktestHarness — ONE evaluator: walk-forward + costs + null
data/
└── sources.py               # your data table as IDataSource adapters (jugaad/openalgo/screener/macro/...)
strategies/                  # the zoo — each a StrategyProvider implementing IStrategy
└── mean_reversion_bnf.py    # first reference provider (Kotegawa/BNF)
```

Stance: **no strategy is privileged or dropped a priori.** Each is reproduced from a
paper/recorded trader, registered as a provider, and ranked by the harness against a
null on Indian data. "First know what works."

`CONCEPTS_REFERENCES.md` — theory + source map (mean-reversion, Grossman-Stiglitz, LPPL/HLPPL, VCP, gradient descent). Crash-timing (LPPL/HLPPL) is **just another `CrashTiming` provider on the backlog** — competes via backtest like everything else, not a dependency, not on the critical path. `DEPLOYMENT.md` — data tiers + OpenAlgo Docker.

## The core thesis (why this stack exists)

A sector gets force-sold (rotation / FII risk-off, not earnings). Fundamentally-strong names inside it get sold **indiscriminately** and revert. The edge = telling **flow-driven** dislocation (fadeable) from **information-driven** (not). Sector context + quality filter is the separator. See `CONCEPTS_REFERENCES.md`.

## Run order (daily)

1. `regime/macro-regime-detector` + `regime/sector-analyst` → which cycle phase, which sectors lead/lag *(PORT NEEDED — see PORT_PLAN.md)*
2. `screeners/india-market-breadth` + `fii-dii-flow-tracker` → is breadth / institutional flow confirming?
3. `regime/exposure-coach` → given the regime, how much risk is allowed? (often: none — wait)
4. `screeners/nse-vcp-screener` → candidates inside the favoured sectors
5. `fundamentals/equity-research` → quality gate: did it fall but *shouldn't have*?
6. `edge-pipeline/*` → formalize as a falsifiable strategy + `backtest-expert` (fed **OpenAlgo historical data**, not yfinance) with costs + a no-filter null
7. **OpenAlgo sandbox** → forward-test the survivor on unseen live data (₹1cr paper) before any real capital. Live execution deferred.

## Backtesting note
OpenAlgo provides **data + sandbox forward-testing**, not a historical backtest *engine*. Historical
backtest compute stays in `engines/backtesting` (vectorbt) + `edge-pipeline/backtest-expert`, but
re-sourced to OpenAlgo data. See `engines/openalgo-data/README.md`.

## Sources
- tradermonty/claude-trading-skills (US) — regime + edge brains
- ajeeshworkspace/indian-trading-skills — India screeners (itself adapted from tradermonty)
- claude-scientific-skills/equity-research — India fundamentals
- marketcalls/openalgo + openalgo-claude-plugin — execution / live data

> Not financial advice. Educational/research. Past performance ≠ future results.
