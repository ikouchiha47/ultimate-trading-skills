# Kalman Filter

A recursive algorithm that estimates hidden state from noisy observations. In finance: extract the true trend from noisy price data.

## When to Use

- Smoothing price series (better than moving averages — no lag)
- Estimating dynamic hedge ratios for pairs trading
- Tracking time-varying betas

## Installation

```bash
uv pip install pykalman yfinance
```

## Price Smoothing

```python
from pykalman import KalmanFilter
import yfinance as yf
import numpy as np

price = yf.download("RELIANCE.NS", period="2y")["Close"]

kf = KalmanFilter(
    n_dim_obs=1,
    n_dim_state=1,
    initial_state_mean=price.values[0],
    initial_state_covariance=1.0,
    transition_matrices=[1],
    observation_matrices=[1],
    observation_covariance=1.0,
    transition_covariance=0.01,  # Lower = smoother
)

state_means, state_covs = kf.filter(price.values)

import pandas as pd
smoothed = pd.Series(state_means.flatten(), index=price.index, name="Kalman")
```

**Tuning**: `transition_covariance` controls smoothness. Lower = smoother (more lag). Higher = more responsive (more noise).

## Dynamic Hedge Ratio (Pairs Trading)

Track the time-varying relationship between two stocks:

```python
import yfinance as yf
import numpy as np
from pykalman import KalmanFilter

# Two cointegrated stocks
prices = yf.download(["HDFCBANK.NS", "ICICIBANK.NS"], period="3y")["Close"]
y = prices["HDFCBANK.NS"].values
x = prices["ICICIBANK.NS"].values

# State: [intercept, slope] — slope is the hedge ratio
delta = 1e-5
trans_cov = delta / (1 - delta) * np.eye(2)

kf = KalmanFilter(
    n_dim_obs=1,
    n_dim_state=2,
    initial_state_mean=np.zeros(2),
    initial_state_covariance=np.ones((2, 2)),
    transition_matrices=np.eye(2),
    observation_matrices=np.expand_dims(np.vstack([np.ones(len(x)), x]).T, axis=1),
    observation_covariance=1.0,
    transition_covariance=trans_cov,
)

state_means, _ = kf.filter(y)
hedge_ratio = state_means[:, 1]  # Time-varying hedge ratio
spread = y - hedge_ratio * x     # Mean-reverting spread
```

## Interpreting Results

- Kalman-smoothed price crossing raw price = potential signal
- Spread from pairs trading should be mean-reverting — trade when spread deviates >2 std from mean
- Widening state covariance = model uncertainty increasing = regime change possible
