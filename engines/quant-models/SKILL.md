---
name: quant-models
description: Quantitative finance models for signal generation, risk management, and portfolio construction. Includes Kalman filter (trend estimation), Hidden Markov Models (regime detection), GARCH (volatility forecasting), mean reversion (pairs trading), factor models (Fama-French), portfolio optimization (efficient frontier), and risk metrics (VaR, Sharpe, drawdown). Uses pykalman, hmmlearn, arch, pyportfolioopt, empyrical, and statsmodels.
license: MIT
metadata:
    skill-author: Iko Uchiha
---

# Quant Models — Quantitative Finance Toolkit

Statistical models for trading signal generation, risk management, and portfolio construction.

## Installation

```bash
uv pip install pykalman hmmlearn arch pyportfolioopt empyrical statsmodels yfinance pandas numpy scipy
```

## What's Included

| Model | Library | Use Case |
|-------|---------|----------|
| Kalman Filter | pykalman | Price smoothing, trend estimation |
| Hidden Markov Model | hmmlearn | Bull/bear regime detection |
| GARCH | arch | Volatility forecasting |
| Mean Reversion | statsmodels | Pairs trading, cointegration |
| Factor Models | statsmodels + numpy | Risk attribution, Fama-French |
| Portfolio Optimization | pyportfolioopt | Efficient frontier, risk parity |
| Risk Metrics | empyrical | VaR, Sharpe, drawdown |
| Feature Engineering | scikit-learn | Predictive feature extraction, walk-forward validation, ablation |

## Quick Examples

### Smooth noisy prices with Kalman filter
```python
from pykalman import KalmanFilter
import yfinance as yf

price = yf.download("RELIANCE.NS", period="1y")["Close"].values
kf = KalmanFilter(n_dim_obs=1, n_dim_state=1, initial_state_mean=price[0])
state_means, _ = kf.filter(price)
# state_means is the smoothed price series
```

### Detect market regimes
```python
from hmmlearn.hmm import GaussianHMM
import yfinance as yf
import numpy as np

returns = yf.download("^NSEI", period="5y")["Close"].pct_change().dropna().values.reshape(-1, 1)
model = GaussianHMM(n_components=2, covariance_type="full", n_iter=100)
model.fit(returns)
regimes = model.predict(returns)
# 0 = low-vol regime (bull), 1 = high-vol regime (bear) — or vice versa
```

### Forecast volatility
```python
from arch import arch_model
import yfinance as yf

returns = yf.download("RELIANCE.NS", period="5y")["Close"].pct_change().dropna() * 100
model = arch_model(returns, vol="Garch", p=1, q=1)
res = model.fit(disp="off")
forecast = res.forecast(horizon=5)
print(forecast.variance[-1:])
```

### Build predictive features for a sector
```bash
# Built-in sectors: mining, auto, it, banking
uv run python scripts/feature_engineer.py --sector mining

# Custom config
uv run python scripts/feature_engineer.py --config my_sector.json --output output/my_features
```

Outputs: tiered feature spec (JSON), feature matrices (CSV), ablation study, walk-forward validation results. See `references/feature-engineering.md` for the full framework and sector-specific feature selection guide.

See `references/` for detailed docs and worked examples for each model.
