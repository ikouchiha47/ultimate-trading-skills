# Portfolio Optimization

## Installation

```bash
uv pip install pyportfolioopt yfinance
```

## Efficient Frontier (Mean-Variance)

```python
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models, expected_returns
import yfinance as yf

tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS",
           "SBIN.NS", "BHARTIARTL.NS", "LT.NS", "SUNPHARMA.NS", "TITAN.NS"]
prices = yf.download(tickers, period="5y")["Close"]

# Expected returns and risk model
mu = expected_returns.mean_historical_return(prices)
S = risk_models.sample_cov(prices)

# Optimize for max Sharpe ratio
ef = EfficientFrontier(mu, S)
weights = ef.max_sharpe(risk_free_rate=0.06)  # India ~6% risk-free
cleaned = ef.clean_weights()
print("Max Sharpe Portfolio:")
for k, v in cleaned.items():
    if v > 0:
        print(f"  {k}: {v:.1%}")
ef.portfolio_performance(verbose=True, risk_free_rate=0.06)
```

## Minimum Volatility

```python
ef = EfficientFrontier(mu, S)
weights = ef.min_volatility()
cleaned = ef.clean_weights()
print("Min Volatility Portfolio:")
for k, v in cleaned.items():
    if v > 0:
        print(f"  {k}: {v:.1%}")
ef.portfolio_performance(verbose=True)
```

## Risk Parity

Equal risk contribution from each asset.

```python
from pypfopt import HRPOpt

# Hierarchical Risk Parity (doesn't need expected returns)
returns = prices.pct_change().dropna()
hrp = HRPOpt(returns)
weights = hrp.optimize()
print("Risk Parity Portfolio:")
for k, v in weights.items():
    if v > 0.01:
        print(f"  {k}: {v:.1%}")
hrp.portfolio_performance(verbose=True)
```

## Black-Litterman

Combine market equilibrium with your views.

```python
from pypfopt.black_litterman import BlackLittermanModel
from pypfopt import risk_models

S = risk_models.sample_cov(prices)
market_caps = {}
for t in tickers:
    info = yf.Ticker(t).info
    market_caps[t] = info.get("marketCap", 1e10)

# Your views: RELIANCE will return 15%, TCS will outperform INFY by 5%
viewdict = {"RELIANCE.NS": 0.15, "TCS.NS": 0.05}
bl = BlackLittermanModel(S, pi="market", market_caps=market_caps, absolute_views=viewdict)
ret_bl = bl.bl_returns()

ef = EfficientFrontier(ret_bl, S)
ef.max_sharpe(risk_free_rate=0.06)
print(ef.clean_weights())
```

## Constraints

```python
ef = EfficientFrontier(mu, S)

# No single stock > 25%
ef.add_constraint(lambda w: w <= 0.25)

# Minimum 5% in each stock
ef.add_constraint(lambda w: w >= 0.05)

# Sector constraints (e.g., max 40% in banking)
banking = ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"]
banking_idx = [tickers.index(t) for t in banking if t in tickers]
# ef.add_constraint(lambda w: sum(w[i] for i in banking_idx) <= 0.40)

weights = ef.max_sharpe(risk_free_rate=0.06)
ef.portfolio_performance(verbose=True)
```

## Discrete Allocation

Convert weights to actual share counts given a budget.

```python
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices

latest_prices = get_latest_prices(prices)
da = DiscreteAllocation(cleaned, latest_prices, total_portfolio_value=500000)
allocation, leftover = da.greedy_portfolio()
print(f"\nDiscrete allocation (₹5L budget):")
for k, v in allocation.items():
    print(f"  {k}: {v} shares")
print(f"Leftover: ₹{leftover:.0f}")
```
