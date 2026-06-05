# Risk Metrics

## Installation

```bash
uv pip install empyrical yfinance
```

## Quick Metrics with empyrical

```python
import empyrical as ep
import yfinance as yf

price = yf.download("RELIANCE.NS", period="5y")["Close"]
returns = price.pct_change().dropna()

print(f"Annual Return:     {ep.annual_return(returns):.2%}")
print(f"Annual Volatility: {ep.annual_volatility(returns):.2%}")
print(f"Sharpe Ratio:      {ep.sharpe_ratio(returns, risk_free=0.06/252):.2f}")
print(f"Sortino Ratio:     {ep.sortino_ratio(returns, required_return=0.06/252):.2f}")
print(f"Calmar Ratio:      {ep.calmar_ratio(returns):.2f}")
print(f"Max Drawdown:      {ep.max_drawdown(returns):.2%}")
print(f"Daily VaR (95%):   {ep.value_at_risk(returns, cutoff=0.05):.2%}")
```

## Value at Risk (VaR)

Maximum expected loss at a given confidence level.

```python
import numpy as np

# Historical VaR
var_95 = np.percentile(returns, 5)
var_99 = np.percentile(returns, 1)
print(f"1-day 95% VaR: {var_95:.2%}")
print(f"1-day 99% VaR: {var_99:.2%}")

# For ₹10L portfolio
portfolio_value = 1000000
print(f"95% VaR (₹): ₹{abs(var_95 * portfolio_value):,.0f}")
```

## Conditional VaR (CVaR / Expected Shortfall)

Average loss beyond VaR — answers "when things go bad, how bad?"

```python
var_95 = np.percentile(returns, 5)
cvar_95 = returns[returns <= var_95].mean()
print(f"95% CVaR: {cvar_95:.2%}")
```

## Drawdown Analysis

```python
import pandas as pd

# Drawdown series
cumulative = (1 + returns).cumprod()
running_max = cumulative.cummax()
drawdown = (cumulative - running_max) / running_max

print(f"Max Drawdown: {drawdown.min():.2%}")
print(f"Current Drawdown: {drawdown.iloc[-1]:.2%}")

# Top 5 drawdown periods
dd_groups = (drawdown == 0).cumsum()
worst = drawdown.groupby(dd_groups).min().sort_values().head(5)
print("\nWorst drawdowns:")
print(worst)
```

## Sharpe vs Sortino

```python
# Sharpe: penalizes all volatility (up and down)
sharpe = ep.sharpe_ratio(returns, risk_free=0.06/252)

# Sortino: only penalizes downside volatility (more fair for skewed returns)
sortino = ep.sortino_ratio(returns, required_return=0.06/252)

print(f"Sharpe:  {sharpe:.2f}")
print(f"Sortino: {sortino:.2f}")
# Sortino > Sharpe means positive skew (more upside than downside volatility)
```

## Portfolio Risk

```python
import numpy as np

tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS"]
prices = yf.download(tickers, period="3y")["Close"]
returns = prices.pct_change().dropna()

weights = np.array([0.25, 0.20, 0.20, 0.20, 0.15])

# Portfolio return and vol
port_return = (returns.mean() * weights).sum() * 252
cov_matrix = returns.cov() * 252
port_vol = np.sqrt(weights @ cov_matrix @ weights)

print(f"Portfolio Return: {port_return:.2%}")
print(f"Portfolio Vol:    {port_vol:.2%}")
print(f"Sharpe (Rf=6%):   {(port_return - 0.06) / port_vol:.2f}")

# Marginal risk contribution
mrc = cov_matrix @ weights / port_vol
print("\nMarginal Risk Contribution:")
for t, m in zip(tickers, mrc):
    print(f"  {t}: {m:.4f}")
```

## Metric Interpretation Guide

| Metric | Good | Mediocre | Bad |
|--------|------|----------|-----|
| Sharpe | > 1.5 | 0.5-1.5 | < 0.5 |
| Sortino | > 2.0 | 1.0-2.0 | < 1.0 |
| Max Drawdown | < 15% | 15-30% | > 30% |
| Calmar | > 1.0 | 0.5-1.0 | < 0.5 |
| Win Rate | > 55% | 45-55% | < 45% |
