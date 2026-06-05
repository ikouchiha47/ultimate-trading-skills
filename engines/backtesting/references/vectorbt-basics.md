# vectorbt Basics

## Installation

```bash
uv pip install vectorbt yfinance
```

## Core Workflow

```python
import vectorbt as vbt
import yfinance as yf

# 1. Get data
price = yf.download("RELIANCE.NS", period="5y")["Close"]

# 2. Generate signals (boolean arrays)
entries = ...  # True where you want to buy
exits = ...    # True where you want to sell

# 3. Simulate portfolio
pf = vbt.Portfolio.from_signals(
    price, entries, exits,
    init_cash=100000,
    fees=0.001,        # 0.1% per trade
    slippage=0.001,    # 0.1% slippage
)

# 4. Analyze
print(pf.stats())
pf.plot().show()
```

## Built-in Indicators

```python
# Moving averages
ma = vbt.MA.run(price, window=[10, 20, 50])

# RSI
rsi = vbt.RSI.run(price, window=14)

# Bollinger Bands
bb = vbt.BBANDS.run(price, window=20, alpha=2)

# MACD
macd = vbt.MACD.run(price, fast_window=12, slow_window=26, signal_window=9)
```

## Signal Generation

```python
# MA crossover
fast = vbt.MA.run(price, window=10)
slow = vbt.MA.run(price, window=50)
entries = fast.ma_crossed_above(slow)
exits = fast.ma_crossed_below(slow)

# RSI threshold
rsi = vbt.RSI.run(price, window=14)
entries = rsi.rsi_crossed_below(30)  # Oversold
exits = rsi.rsi_crossed_above(70)    # Overbought
```

## Portfolio Stats

```python
pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000)

pf.total_return()      # Total return
pf.sharpe_ratio()      # Annualized Sharpe
pf.sortino_ratio()     # Sortino ratio
pf.max_drawdown()      # Maximum drawdown
pf.win_rate()          # Percentage of winning trades
pf.profit_factor()     # Gross profit / gross loss
pf.total_trades()      # Number of trades
pf.avg_winning_trade() # Average winning trade return
pf.avg_losing_trade()  # Average losing trade return

# Full stats
print(pf.stats())
```

## Parameter Optimization

```python
# Test multiple MA windows at once
fast_windows = [5, 10, 15, 20]
slow_windows = [30, 40, 50, 60]

fast_ma, slow_ma = vbt.MA.run_combs(price, window=fast_windows + slow_windows, r=2, short_names=["fast", "slow"])

entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)

# Find best combination
print(pf.sharpe_ratio().sort_values(ascending=False).head(10))
```
