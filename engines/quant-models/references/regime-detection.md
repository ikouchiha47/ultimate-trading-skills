# Regime Detection with Hidden Markov Models

Detect hidden market states (bull/bear/sideways) from return data. The model learns the regimes automatically from the data.

## When to Use

- Adapting strategy to market conditions (trend-follow in bull, mean-revert in bear)
- Risk management (reduce exposure in high-vol regimes)
- Timing entries/exits based on regime transitions

## Installation

```bash
uv pip install hmmlearn yfinance
```

## Two-Regime Model (Bull/Bear)

```python
from hmmlearn.hmm import GaussianHMM
import yfinance as yf
import numpy as np
import pandas as pd

# Fetch data
price = yf.download("^NSEI", period="10y")["Close"]
returns = price.pct_change().dropna()

# Fit 2-state HMM
X = returns.values.reshape(-1, 1)
model = GaussianHMM(n_components=2, covariance_type="full", n_iter=1000, random_state=42)
model.fit(X)

# Predict regimes
regimes = model.predict(X)

# Identify which regime is bull vs bear
means = model.means_.flatten()
bull_regime = np.argmax(means)  # Higher mean return = bull
bear_regime = np.argmin(means)

regime_labels = pd.Series(
    ["Bull" if r == bull_regime else "Bear" for r in regimes],
    index=returns.index
)

# Stats per regime
for label in ["Bull", "Bear"]:
    mask = regime_labels == label
    r = returns[mask]
    print(f"{label}: mean={r.mean():.4f}, vol={r.std():.4f}, days={mask.sum()}")
```

## Three-Regime Model (Bull/Sideways/Bear)

```python
model = GaussianHMM(n_components=3, covariance_type="full", n_iter=1000, random_state=42)
model.fit(X)
regimes = model.predict(X)

# Sort regimes by mean return
means = model.means_.flatten()
order = np.argsort(means)
labels = {order[0]: "Bear", order[1]: "Sideways", order[2]: "Bull"}
regime_labels = pd.Series([labels[r] for r in regimes], index=returns.index)
```

## Using Regimes for Trading

```python
# Only go long in bull regime
signal = (regime_labels == "Bull").astype(int)

# Strategy returns: market return when in bull, 0 otherwise
strategy_returns = returns * signal.shift(1)  # Shift to avoid look-ahead

# Compare
cum_market = (1 + returns).cumprod()
cum_strategy = (1 + strategy_returns).cumprod()
print(f"Market: {cum_market.iloc[-1]:.2f}x")
print(f"Regime Strategy: {cum_strategy.iloc[-1]:.2f}x")
```

## Transition Probabilities

```python
print("Transition matrix:")
print(model.transmat_)
# transmat_[i][j] = probability of going from regime i to regime j
# High diagonal = regimes are sticky (persistent)
```

## Caveats

- HMM results can vary between runs — set `random_state` for reproducibility
- Regime labels are arbitrary (0, 1, 2) — identify them by mean/variance
- In-sample regime detection is much easier than real-time prediction
- The model sees the full dataset — for live use, refit periodically on trailing window
