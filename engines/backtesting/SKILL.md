---
name: backtesting
description: Backtest trading strategies on historical stock data using vectorbt and yfinance. Test RSI, MACD, moving average crossover, Bollinger Band, and custom strategies with transaction costs, slippage, and walk-forward optimization. Includes performance analysis (Sharpe, drawdown, equity curves) and portfolio-level backtesting. Indian and global market support.
license: MIT
metadata:
    skill-author: Iko Uchiha
---

# Backtesting — Test Trading Strategies on Historical Data

Backtest any trading strategy against historical data. Uses vectorbt for fast vectorized backtesting and yfinance for free market data.

## Installation

```bash
uv pip install vectorbt yfinance
```

## Quick Start — MA Crossover on RELIANCE

```python
import vectorbt as vbt
import yfinance as yf

# Fetch data
price = yf.download("RELIANCE.NS", period="5y")["Close"]

# Moving average crossover: buy when fast > slow, sell when fast < slow
fast_ma = vbt.MA.run(price, window=10)
slow_ma = vbt.MA.run(price, window=50)

entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)

# Run backtest
pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)

# Results
print(f"Total Return: {pf.total_return():.2%}")
print(f"Sharpe Ratio: {pf.sharpe_ratio():.2f}")
print(f"Max Drawdown: {pf.max_drawdown():.2%}")
print(pf.stats())
```

## Strategy Patterns

| Strategy | Signal | Best For |
|----------|--------|----------|
| MA Crossover | Fast MA crosses slow MA | Trend following |
| RSI | Buy < 30, Sell > 70 | Mean reversion |
| MACD | MACD crosses signal line | Momentum |
| Bollinger Bands | Price touches lower/upper band | Volatility |
| Dual MA + RSI | Combined signals | Filtered entries |

See `references/strategy-patterns.md` for implementations.

## Key Concepts

- **Entries/Exits**: Boolean arrays marking buy/sell signals
- **Portfolio**: Simulates trades with cash, position sizing, fees
- **Walk-forward**: Train on past data, test on unseen data to avoid overfitting
- **Slippage**: Difference between expected and actual execution price

## Common Pitfalls

1. **Overfitting**: Strategy works on historical data but fails live — use walk-forward testing
2. **Survivorship bias**: Only testing stocks that exist today — include delisted stocks
3. **Look-ahead bias**: Using future data in signals — ensure indicators use only past data
4. **Ignoring costs**: Transaction fees and slippage eat returns — always include them
5. **Data snooping**: Testing too many strategies on the same data — use out-of-sample validation
