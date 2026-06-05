# Factor Models

Decompose stock returns into systematic factors (market, size, value, momentum) and idiosyncratic risk.

## When to Use

- Understanding what drives a stock's returns
- Building factor-neutral portfolios
- Risk attribution
- Alpha generation (returns unexplained by factors)

## Single Factor (CAPM Beta)

```python
import yfinance as yf
import statsmodels.api as sm

# Stock and market
stock = yf.download("RELIANCE.NS", period="3y")["Close"].pct_change().dropna()
market = yf.download("^NSEI", period="3y")["Close"].pct_change().dropna()

# Align dates
aligned = stock.to_frame("stock").join(market.to_frame("market")).dropna()

# Regression: stock = alpha + beta * market
X = sm.add_constant(aligned["market"])
model = sm.OLS(aligned["stock"], X).fit()
print(f"Alpha (daily): {model.params['const']:.6f}")
print(f"Beta: {model.params['market']:.2f}")
print(f"R²: {model.rsquared:.2f}")
```

## Multi-Factor (Fama-French Style)

```python
import numpy as np
import pandas as pd

# For Indian markets, construct simple factors from NIFTY stocks
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS",
           "SBIN.NS", "LT.NS", "MARUTI.NS", "SUNPHARMA.NS", "TATAMOTORS.NS"]
prices = yf.download(tickers, period="3y")["Close"]
returns = prices.pct_change().dropna()

market_ret = yf.download("^NSEI", period="3y")["Close"].pct_change().dropna()

# Simple SMB (small minus big) proxy: equal-weight bottom 5 minus top 5 by market cap
# In practice, sort by market cap — here simplified
smb = returns[tickers[5:]].mean(axis=1) - returns[tickers[:5]].mean(axis=1)

# HML (high minus low book-to-market) proxy
# Simplified: value stocks minus growth stocks
hml = returns[["ITC.NS", "SBIN.NS", "TATAMOTORS.NS"]].mean(axis=1) - \
      returns[["TCS.NS", "INFY.NS"]].mean(axis=1)

# Regress a stock on factors
stock = returns["RELIANCE.NS"]
factors = pd.DataFrame({"market": market_ret, "smb": smb, "hml": hml}).dropna()
aligned = stock.to_frame("stock").join(factors).dropna()

X = sm.add_constant(aligned[["market", "smb", "hml"]])
model = sm.OLS(aligned["stock"], X).fit()
print(model.summary())
```

## PCA-Based Factor Decomposition

Let the data tell you what the factors are.

```python
from sklearn.decomposition import PCA

# Returns matrix: rows=dates, cols=stocks
returns_matrix = returns.dropna()

pca = PCA(n_components=5)
pca.fit(returns_matrix)

print("Explained variance ratios:")
for i, var in enumerate(pca.explained_variance_ratio_):
    print(f"  PC{i+1}: {var:.2%}")

# Factor loadings
loadings = pd.DataFrame(
    pca.components_[:3].T,
    index=returns_matrix.columns,
    columns=["PC1 (Market)", "PC2", "PC3"]
)
print("\nFactor loadings:")
print(loadings)
```

## Interpreting Results

- **Alpha > 0**: Stock outperforms after accounting for factor exposure
- **Beta > 1**: More volatile than market, < 1 = less volatile
- **R² high**: Returns mostly explained by factors (less stock-specific risk)
- **R² low**: Returns driven by idiosyncratic factors (harder to hedge)
- **PC1** is almost always the market factor (explains 40-60% of returns)
