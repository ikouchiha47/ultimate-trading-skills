# Market Data

## OHLCV Data

```python
import yfinance as yf

# Basic download
df = yf.download("RELIANCE.NS", period="1y")
# Columns: Open, High, Low, Close, Adj Close, Volume

# Specific date range
df = yf.download("RELIANCE.NS", start="2020-01-01", end="2025-12-31")

# Intraday (max 60 days for 1m, 730 days for 1h)
df = yf.download("RELIANCE.NS", period="5d", interval="5m")

# Weekly/monthly
df = yf.download("RELIANCE.NS", period="5y", interval="1wk")
df = yf.download("RELIANCE.NS", period="max", interval="1mo")
```

## Multiple Tickers

```python
# Download multiple at once
tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
df = yf.download(tickers, period="1y")

# Access individual stock
df["Close"]["RELIANCE.NS"]

# Compare returns
returns = df["Close"].pct_change()
```

## Dividends and Splits

```python
ticker = yf.Ticker("RELIANCE.NS")

# Dividend history
divs = ticker.dividends
print(divs.tail(10))

# Stock splits
splits = ticker.splits
print(splits)

# Include in download
df = yf.download("RELIANCE.NS", period="5y", actions=True)
# Adds Dividends and Stock Splits columns
```

## Periods and Intervals

**Periods:** `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

**Intervals:**
| Interval | Max Period |
|----------|-----------|
| 1m | 7 days |
| 2m, 5m, 15m, 30m | 60 days |
| 60m, 90m, 1h | 730 days |
| 1d, 5d, 1wk, 1mo, 3mo | unlimited |
