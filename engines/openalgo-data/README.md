# OpenAlgo Data Adapter

OpenAlgo is the **data + forward-test backbone**. It is NOT a backtest compute engine.
Two jobs only:

1. **Historical OHLCV** -> feeds the backtest engine (replaces yfinance as primary; yfinance = fallback).
2. **Sandbox** (₹1cr paper engine) -> forward-tests the validated strategy before real capital.

OpenAlgo runs as a **separate local Flask server** (`http://127.0.0.1:5000`). This repo only *calls* it.

## Prerequisites
```bash
export OPENALGO_API_KEY="your_key"
export OPENALGO_HOST="http://127.0.0.1:5000"
```
Run OpenAlgo separately (see github.com/marketcalls/openalgo). Use its MCP server or REST `/api/v1/`.

## Job 1 — historical data for backtests

MCP tool / REST `history`:
```
get_historical_data(symbol, exchange, interval, start_date, end_date, source="api")
  exchange : NSE | BSE | NFO | ...
  interval : api -> 1m,3m,5m,10m,15m,30m,1h,D
             db  -> also 2m,4m,2h,3h, W,M,Q,Y (and 2W,3M ...)  # use db for weekly/monthly regime work
  dates    : YYYY-MM-DD
```
Returns OHLCV. The backtest engine (`engines/backtesting`, `skills/edge-pipeline/backtest-expert`)
consumes this instead of `yfinance.download(...)`. For sector/regime work pull `source="db"` weekly/monthly.

## Job 2 — sandbox forward-test (the new middle stage)

After a rule survives the historical backtest + null model, run it in OpenAlgo's sandbox engine
(₹1cr paper capital, IST-aligned, auto square-off) for N weeks of *unseen* live data. Only after
sandbox confirms do you consider real execution (deferred).

## What this adapter still owes
- A thin `client.py` wrapping the REST/MCP `history` call -> pandas DataFrame in the shape
  `backtest-expert` expects (Date index, OHLCV cols). Build when wiring the first backtest.
