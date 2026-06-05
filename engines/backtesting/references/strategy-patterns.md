# Strategy Patterns

## RSI Mean Reversion

Buy when RSI drops below 30 (oversold), sell when it rises above 70 (overbought).

```python
import vectorbt as vbt
import yfinance as yf

price = yf.download("RELIANCE.NS", period="5y")["Close"]
rsi = vbt.RSI.run(price, window=14)

entries = rsi.rsi_crossed_below(30)
exits = rsi.rsi_crossed_above(70)

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)
print(pf.stats())
```

## MACD Crossover

Buy when MACD crosses above signal line, sell when it crosses below.

```python
macd = vbt.MACD.run(price, fast_window=12, slow_window=26, signal_window=9)

entries = macd.macd_crossed_above(macd.signal)
exits = macd.macd_crossed_below(macd.signal)

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)
print(pf.stats())
```

## Bollinger Band Breakout

Buy when price touches lower band, sell when it touches upper band.

```python
bb = vbt.BBANDS.run(price, window=20, alpha=2)

entries = price < bb.lower
exits = price > bb.upper

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)
print(pf.stats())
```

## Dual Moving Average

Classic trend-following: 10/50 day crossover.

```python
fast = vbt.MA.run(price, window=10)
slow = vbt.MA.run(price, window=50)

entries = fast.ma_crossed_above(slow)
exits = fast.ma_crossed_below(slow)

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)
print(pf.stats())
```

## Combined: MA + RSI Filter

Only take MA crossover entries when RSI confirms (not overbought).

```python
fast = vbt.MA.run(price, window=10)
slow = vbt.MA.run(price, window=50)
rsi = vbt.RSI.run(price, window=14)

# Buy: fast crosses above slow AND RSI < 60
entries = fast.ma_crossed_above(slow) & (rsi.rsi < 60)
# Sell: fast crosses below slow OR RSI > 80
exits = fast.ma_crossed_below(slow) | (rsi.rsi > 80)

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)
print(pf.stats())
```

## Buy and Hold Benchmark

Always compare your strategy against buy-and-hold:

```python
# Buy and hold
pf_bh = vbt.Portfolio.from_holding(price, init_cash=100000)

# Your strategy
pf_strat = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)

print(f"Buy & Hold Return: {pf_bh.total_return():.2%}")
print(f"Strategy Return:   {pf_strat.total_return():.2%}")
print(f"Buy & Hold Sharpe: {pf_bh.sharpe_ratio():.2f}")
print(f"Strategy Sharpe:   {pf_strat.sharpe_ratio():.2f}")
```
