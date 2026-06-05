# Walk-Forward Optimization

## Why Walk-Forward?

Optimizing strategy parameters on the full dataset leads to overfitting. Walk-forward splits data into train (optimize) and test (validate) windows, rolling forward over time.

## Basic Train/Test Split

```python
import vectorbt as vbt
import yfinance as yf

price = yf.download("RELIANCE.NS", period="5y")["Close"]

# Split: first 80% train, last 20% test
split = int(len(price) * 0.8)
train_price = price.iloc[:split]
test_price = price.iloc[split:]

# Optimize on train
windows = [5, 10, 15, 20, 25, 30]
best_sharpe = -999
best_window = None

for w in windows:
    fast = vbt.MA.run(train_price, window=w)
    slow = vbt.MA.run(train_price, window=w * 3)
    entries = fast.ma_crossed_above(slow)
    exits = fast.ma_crossed_below(slow)
    pf = vbt.Portfolio.from_signals(train_price, entries, exits, init_cash=100000, fees=0.001)
    sr = pf.sharpe_ratio()
    if sr > best_sharpe:
        best_sharpe = sr
        best_window = w

print(f"Best window: {best_window} (Sharpe: {best_sharpe:.2f})")

# Validate on test
fast = vbt.MA.run(test_price, window=best_window)
slow = vbt.MA.run(test_price, window=best_window * 3)
entries = fast.ma_crossed_above(slow)
exits = fast.ma_crossed_below(slow)
pf = vbt.Portfolio.from_signals(test_price, entries, exits, init_cash=100000, fees=0.001)
print(f"Out-of-sample Sharpe: {pf.sharpe_ratio():.2f}")
print(f"Out-of-sample Return: {pf.total_return():.2%}")
```

## Rolling Walk-Forward

```python
import pandas as pd
import numpy as np

price = yf.download("RELIANCE.NS", period="10y")["Close"]

train_days = 252 * 2  # 2 years train
test_days = 63         # 3 months test

results = []
for start in range(0, len(price) - train_days - test_days, test_days):
    train = price.iloc[start:start + train_days]
    test = price.iloc[start + train_days:start + train_days + test_days]

    # Optimize on train
    best_w, best_sr = 10, -999
    for w in [5, 10, 15, 20]:
        fast = vbt.MA.run(train, window=w)
        slow = vbt.MA.run(train, window=w * 3)
        e = fast.ma_crossed_above(slow)
        x = fast.ma_crossed_below(slow)
        pf = vbt.Portfolio.from_signals(train, e, x, init_cash=100000, fees=0.001)
        if pf.sharpe_ratio() > best_sr:
            best_sr = pf.sharpe_ratio()
            best_w = w

    # Test with best params
    fast = vbt.MA.run(test, window=best_w)
    slow = vbt.MA.run(test, window=best_w * 3)
    e = fast.ma_crossed_above(slow)
    x = fast.ma_crossed_below(slow)
    pf = vbt.Portfolio.from_signals(test, e, x, init_cash=100000, fees=0.001)

    results.append({
        "period": test.index[0],
        "best_window": best_w,
        "return": pf.total_return(),
        "sharpe": pf.sharpe_ratio(),
    })

df = pd.DataFrame(results)
print(df)
print(f"\nAverage OOS Return: {df['return'].mean():.2%}")
print(f"Average OOS Sharpe: {df['sharpe'].mean():.2f}")
```

## Rules of Thumb

- Train period should be 3-5x the test period
- If train Sharpe >> test Sharpe, you're overfitting
- Fewer parameters = less overfitting risk
- Test on multiple stocks, not just one
