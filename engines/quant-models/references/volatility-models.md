# Volatility Models (GARCH)

GARCH models capture volatility clustering — the tendency of large moves to follow large moves. Essential for risk management and options pricing.

## When to Use

- Forecasting future volatility (next day, next week)
- VaR estimation using conditional volatility
- Comparing current volatility to historical norms
- Options pricing (implied vs realized vol)

## Installation

```bash
uv pip install arch yfinance
```

## GARCH(1,1)

The workhorse model — good enough for most applications.

```python
from arch import arch_model
import yfinance as yf

price = yf.download("RELIANCE.NS", period="5y")["Close"]
returns = price.pct_change().dropna() * 100  # Scale to percentage

# Fit GARCH(1,1)
model = arch_model(returns, vol="Garch", p=1, q=1, mean="constant")
res = model.fit(disp="off")
print(res.summary())

# Conditional volatility (fitted)
cond_vol = res.conditional_volatility

# Forecast next 5 days
forecast = res.forecast(horizon=5)
print("Variance forecast (next 5 days):")
print(forecast.variance.iloc[-1])
```

## EGARCH (Asymmetric)

Captures the leverage effect: negative returns increase volatility more than positive returns.

```python
model = arch_model(returns, vol="EGARCH", p=1, q=1, o=1)
res = model.fit(disp="off")

# Check leverage effect
print(res.params)
# gamma (o[1]) < 0 means negative returns increase vol more
```

## Volatility Forecasting

```python
# 1-day ahead rolling forecast
from arch import arch_model
import pandas as pd

rolling_vol = []
window = 252 * 2  # 2 years

for i in range(window, len(returns)):
    train = returns.iloc[i - window:i]
    model = arch_model(train, vol="Garch", p=1, q=1, mean="constant")
    res = model.fit(disp="off")
    fcast = res.forecast(horizon=1)
    rolling_vol.append({
        "date": returns.index[i],
        "forecast_vol": fcast.variance.values[-1, 0] ** 0.5,
        "realized_vol": abs(returns.iloc[i]),
    })

vol_df = pd.DataFrame(rolling_vol).set_index("date")
```

## VaR from GARCH

```python
import numpy as np
from scipy.stats import norm

# 1-day 95% VaR
res = model.fit(disp="off")
fcast = res.forecast(horizon=1)
mean_fcast = fcast.mean.values[-1, 0]
vol_fcast = fcast.variance.values[-1, 0] ** 0.5

VaR_95 = mean_fcast - 1.645 * vol_fcast
print(f"1-day 95% VaR: {VaR_95:.2f}%")
# Interpretation: 95% confident the loss won't exceed this
```

## Comparing Current vs Historical Volatility

```python
current_vol = cond_vol.iloc[-1]
mean_vol = cond_vol.mean()
percentile = (cond_vol < current_vol).mean() * 100

print(f"Current vol: {current_vol:.2f}")
print(f"Historical mean: {mean_vol:.2f}")
print(f"Percentile: {percentile:.0f}th")
# Above 80th = elevated volatility, consider reducing position size
```
