# Multi-Asset Backtesting

## Multiple Stocks

```python
import vectorbt as vbt
import yfinance as yf

tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS"]
prices = yf.download(tickers, period="5y")["Close"]

# Apply same strategy to all stocks
fast = vbt.MA.run(prices, window=10)
slow = vbt.MA.run(prices, window=50)
entries = fast.ma_crossed_above(slow)
exits = fast.ma_crossed_below(slow)

pf = vbt.Portfolio.from_signals(prices, entries, exits, init_cash=100000, fees=0.001)

# Per-stock performance
for ticker in tickers:
    print(f"{ticker}: Return={pf[ticker].total_return():.2%}, Sharpe={pf[ticker].sharpe_ratio():.2f}")
```

## Equal Weight Portfolio

```python
import numpy as np

# Equal allocation across stocks
n_stocks = len(tickers)
pf = vbt.Portfolio.from_signals(
    prices, entries, exits,
    init_cash=100000,
    size=1.0 / n_stocks,       # Equal weight
    size_type="targetpercent",
    fees=0.001,
)
print(pf.stats())
```

## Sector Rotation

Rotate between sectors based on momentum.

```python
# Sector ETFs / proxies
sectors = {
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "NTPC.NS"],
}

# Calculate sector momentum (3-month return)
import pandas as pd

all_tickers = [t for s in sectors.values() for t in s]
prices = yf.download(all_tickers, period="5y")["Close"]

sector_returns = {}
for name, tickers in sectors.items():
    sector_returns[name] = prices[tickers].pct_change(63).mean(axis=1)  # 63 days ~ 3 months

sector_df = pd.DataFrame(sector_returns)

# Pick top sector each quarter
top_sector = sector_df.idxmax(axis=1)
print(top_sector.tail(20))
```

## Rebalancing

```python
# Monthly rebalancing with equal weights
pf = vbt.Portfolio.from_signals(
    prices, entries, exits,
    init_cash=100000,
    size=1.0 / n_stocks,
    size_type="targetpercent",
    fees=0.001,
    freq="d",
    # Rebalance by generating entries on first trading day of month
)
```

## NIFTY 50 Components

```python
# Top 10 NIFTY stocks for portfolio backtesting
nifty_top10 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
]
prices = yf.download(nifty_top10, period="5y")["Close"]

# Benchmark: NIFTY 50 index
nifty = yf.download("^NSEI", period="5y")["Close"]
```
