# Advanced: Event-Driven Backtesting

## When vectorbt Isn't Enough

vectorbt is fast but signal-based (boolean arrays). For complex logic like:
- Dynamic position sizing based on portfolio value
- Multiple order types (limit, stop-loss, trailing stop)
- Inter-stock dependencies (pairs trading)
- Custom execution logic

Use **zipline-reloaded** or **backtesting.py**.

## backtesting.py (simpler alternative)

```bash
uv pip install backtesting
```

```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import yfinance as yf
import pandas as pd

# Fetch data (backtesting.py needs specific column names)
df = yf.download("RELIANCE.NS", period="5y")
df = df[["Open", "High", "Low", "Close", "Volume"]]

class SmaCross(Strategy):
    n1 = 10  # Fast MA
    n2 = 50  # Slow MA

    def init(self):
        self.sma1 = self.I(lambda x: pd.Series(x).rolling(self.n1).mean(), self.data.Close)
        self.sma2 = self.I(lambda x: pd.Series(x).rolling(self.n2).mean(), self.data.Close)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()

bt = Backtest(df, SmaCross, cash=100000, commission=0.001)
stats = bt.run()
print(stats)

# Optimize
stats = bt.optimize(n1=range(5, 30, 5), n2=range(20, 80, 10), maximize="Sharpe Ratio")
print(stats._strategy)
```

## Stop-Loss and Take-Profit

```python
class StopLossStrategy(Strategy):
    def init(self):
        self.rsi = self.I(lambda x: pd.Series(x).rolling(14).apply(
            lambda r: 100 - 100 / (1 + r[r > 0].mean() / abs(r[r < 0].mean()))
        ), self.data.Close)

    def next(self):
        if not self.position:
            if self.rsi[-1] < 30:
                self.buy(sl=self.data.Close[-1] * 0.95,   # 5% stop loss
                         tp=self.data.Close[-1] * 1.10)    # 10% take profit
```

## zipline-reloaded (full framework)

```bash
uv pip install zipline-reloaded
```

zipline is the most realistic backtesting engine (used by Quantopian). It handles:
- Minute-level data
- Commission models
- Slippage models
- Multiple order types
- Calendar-aware (market holidays)
- Pipeline API for factor analysis

However, it requires data bundles and more setup. Use it only when vectorbt or backtesting.py aren't sufficient for your needs.

## Choosing a Framework

| Feature | vectorbt | backtesting.py | zipline |
|---------|----------|----------------|---------|
| Speed | Fastest | Fast | Slow |
| Complexity | Signal-based | Class-based | Event-driven |
| Stop-loss/TP | Manual | Built-in | Built-in |
| Optimization | Built-in | Built-in | Manual |
| Learning curve | Low | Low | High |
| Best for | Quick testing | Strategy dev | Production |
