# Mean Reversion & Pairs Trading

## When to Use

- Trading two correlated stocks that temporarily diverge
- Statistical arbitrage strategies
- Market-neutral portfolios

## Cointegration Test

Two stocks are cointegrated if their linear combination is stationary (mean-reverting).

```python
import yfinance as yf
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint, adfuller

# Fetch pair
prices = yf.download(["HDFCBANK.NS", "ICICIBANK.NS"], period="5y")["Close"]
y = prices["HDFCBANK.NS"]
x = prices["ICICIBANK.NS"]

# Engle-Granger cointegration test
score, pvalue, _ = coint(y, x)
print(f"Cointegration p-value: {pvalue:.4f}")
# p < 0.05 = cointegrated (good for pairs trading)
```

## Spread Construction

```python
import numpy as np

# OLS hedge ratio
X = sm.add_constant(x)
model = sm.OLS(y, X).fit()
hedge_ratio = model.params.iloc[1]
intercept = model.params.iloc[0]

spread = y - hedge_ratio * x - intercept

# Verify spread is stationary
adf_stat, adf_pval, _, _, _, _ = adfuller(spread)
print(f"ADF p-value: {adf_pval:.4f}")
# p < 0.05 = stationary (mean-reverting)
```

## Half-Life of Mean Reversion

How quickly the spread reverts to its mean. Determines holding period.

```python
from statsmodels.regression.linear_model import OLS

spread_lag = spread.shift(1).dropna()
spread_diff = spread.diff().dropna()
spread_lag = spread_lag.iloc[1:]  # Align

model = OLS(spread_diff, sm.add_constant(spread_lag)).fit()
half_life = -np.log(2) / model.params.iloc[1]
print(f"Half-life: {half_life:.0f} days")
# Shorter half-life = faster reversion = better for trading
```

## Trading Strategy

```python
import pandas as pd

# Z-score of spread
lookback = int(half_life)
spread_mean = spread.rolling(lookback).mean()
spread_std = spread.rolling(lookback).std()
zscore = (spread - spread_mean) / spread_std

# Signals
entry_threshold = 2.0
exit_threshold = 0.0

long_entry = zscore < -entry_threshold    # Spread too low: buy y, sell x
long_exit = zscore >= exit_threshold
short_entry = zscore > entry_threshold     # Spread too high: sell y, buy x
short_exit = zscore <= exit_threshold

# Position: +1 = long spread, -1 = short spread, 0 = flat
position = pd.Series(0, index=zscore.index)
position[long_entry] = 1
position[short_entry] = -1
position[long_exit | short_exit] = 0
position = position.ffill()

# Returns
spread_returns = spread.pct_change()
strategy_returns = position.shift(1) * spread_returns
cum_returns = (1 + strategy_returns).cumprod()
print(f"Total return: {cum_returns.iloc[-1] - 1:.2%}")
```

## Finding Pairs

```python
# Screen all NIFTY bank stocks for cointegrated pairs
from itertools import combinations

tickers = ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"]
prices = yf.download(tickers, period="3y")["Close"]

pairs = []
for t1, t2 in combinations(tickers, 2):
    score, pval, _ = coint(prices[t1], prices[t2])
    if pval < 0.05:
        pairs.append((t1, t2, pval))
        print(f"{t1} + {t2}: p={pval:.4f} (cointegrated)")

if not pairs:
    print("No cointegrated pairs found")
```
