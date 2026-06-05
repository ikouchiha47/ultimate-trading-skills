# Performance Analysis

## Key Metrics

```python
import vectorbt as vbt

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)

# Returns
pf.total_return()          # Total return
pf.annualized_return()     # Annualized return

# Risk
pf.max_drawdown()          # Maximum peak-to-trough decline
pf.annualized_volatility() # Annualized volatility

# Risk-adjusted
pf.sharpe_ratio()          # (Return - Rf) / Volatility
pf.sortino_ratio()         # Like Sharpe but only downside vol
pf.calmar_ratio()          # Return / Max Drawdown

# Trade quality
pf.win_rate()              # % of winning trades
pf.profit_factor()         # Gross profit / Gross loss
pf.expectancy()            # Average P&L per trade
pf.total_trades()          # Number of trades
```

## Full Stats

```python
print(pf.stats())
# Prints everything: returns, drawdown, Sharpe, trades, etc.
```

## Benchmark Comparison

```python
# Compare strategy vs buy-and-hold
pf_bh = vbt.Portfolio.from_holding(price, init_cash=100000)
pf_strat = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.001)

metrics = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate"]
for m in metrics:
    bh_val = getattr(pf_bh, m)()
    st_val = getattr(pf_strat, m)()
    print(f"{m:25s}  B&H: {bh_val:>10.4f}  Strategy: {st_val:>10.4f}")
```

## Drawdown Analysis

```python
# Drawdown series
dd = pf.drawdown()

# Top 5 drawdowns
print(pf.drawdowns.records_readable.sort_values("max_drawdown").head())
```

## Trade Log

```python
# All trades
trades = pf.trades.records_readable
print(trades[["entry_idx", "exit_idx", "pnl", "return"]].head(20))

# Winning vs losing
winners = trades[trades["pnl"] > 0]
losers = trades[trades["pnl"] < 0]
print(f"Winners: {len(winners)}, Avg: {winners['pnl'].mean():.0f}")
print(f"Losers:  {len(losers)}, Avg: {losers['pnl'].mean():.0f}")
```

## Using empyrical (standalone)

```python
import empyrical as ep
import yfinance as yf

price = yf.download("RELIANCE.NS", period="5y")["Close"]
returns = price.pct_change().dropna()

ep.annual_return(returns)
ep.annual_volatility(returns)
ep.sharpe_ratio(returns)
ep.max_drawdown(returns)
ep.sortino_ratio(returns)
ep.calmar_ratio(returns)
ep.value_at_risk(returns)  # VaR
```
