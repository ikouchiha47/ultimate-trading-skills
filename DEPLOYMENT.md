# Deployment & Data Setup

## You can build + backtest the WHOLE framework without OpenAlgo running.
Offline backtests use **jugaad-data** (free, no auth). OpenAlgo is only needed for
live/recent data and sandbox forward-testing. Don't block on it.

## Tiers

| When | Data source | Setup |
|---|---|---|
| Bulk historical backtest | `jugaad-data` | `pip install jugaad-data` — done. |
| Fundamentals / quality gate | `equity-research` (screener.in) | one-time screener.in login (saved session) |
| Macro / regime inputs | RBI DBIE, MOSPI | manual CSV pull → `data/macro/` |
| Sector breadth | Trendlyne CSV export | drop exports in `data/trendlyne/` |
| Live / recent + forward-test | **OpenAlgo (Docker)** | below |

## OpenAlgo via Docker (only when you reach forward-testing)

The two-key sandwich:
1. **Broker → OpenAlgo**: connect your broker (Zerodha/Upstox/...) with *that broker's*
   API key+secret inside OpenAlgo. This gives OpenAlgo real data + execution.
2. **OpenAlgo → this repo**: OpenAlgo exposes its OWN app key + host. The Claude plugin
   / our `OpenAlgoSource` adapter use these.

```bash
# follow docs.openalgo.in/installation-guidelines/getting-started/docker-development
git clone https://github.com/marketcalls/openalgo
cd openalgo && docker compose up -d        # serves http://127.0.0.1:5000
# then in OpenAlgo web UI: connect broker, generate the OpenAlgo API key
```

Wire this repo to it:
```bash
export OPENALGO_HOST="http://127.0.0.1:5000"
export OPENALGO_API_KEY="<openalgo_app_key>"   # NOT your broker key
```

Caveat: OpenAlgo historical data needs a live broker session (most Indian brokers
require daily re-auth) — fine for live/sandbox, painful for years of history. That's
why bulk backtests use jugaad-data instead.

## Python deps
```bash
pip install jugaad-data pandas numpy yfinance vectorbt requests nsepython
# fundamentals scraper: playwright pdfplumber  (see skills/fundamentals/equity-research)
```
