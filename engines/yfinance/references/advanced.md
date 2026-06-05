# Advanced Usage

## Batch Downloads

```python
import yfinance as yf

# Download many tickers efficiently
tickers = "RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS ICICIBANK.NS"
df = yf.download(tickers, period="1y", group_by="ticker", threads=True)

# Access per ticker
df["RELIANCE.NS"]["Close"]
```

## Caching

yfinance caches requests in the current session. For persistent caching:

```python
import yfinance as yf
import requests_cache

# Cache responses for 1 hour
session = requests_cache.CachedSession("yfinance_cache", expire_after=3600)
session.headers["User-agent"] = "my-program/1.0"

ticker = yf.Ticker("RELIANCE.NS", session=session)
df = ticker.history(period="1y")
```

Install: `uv pip install requests-cache`

## Computing Technical Indicators

yfinance doesn't provide built-in indicators (unlike Alpha Vantage). Compute them with pandas:

```python
import yfinance as yf
import pandas as pd

df = yf.download("RELIANCE.NS", period="2y")

# SMA
df["SMA_20"] = df["Close"].rolling(20).mean()
df["SMA_50"] = df["Close"].rolling(50).mean()

# EMA
df["EMA_12"] = df["Close"].ewm(span=12).mean()
df["EMA_26"] = df["Close"].ewm(span=26).mean()

# MACD
df["MACD"] = df["EMA_12"] - df["EMA_26"]
df["Signal"] = df["MACD"].ewm(span=9).mean()

# RSI
delta = df["Close"].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
df["RSI"] = 100 - (100 / (1 + gain / loss))

# Bollinger Bands
df["BB_mid"] = df["Close"].rolling(20).mean()
df["BB_std"] = df["Close"].rolling(20).std()
df["BB_upper"] = df["BB_mid"] + 2 * df["BB_std"]
df["BB_lower"] = df["BB_mid"] - 2 * df["BB_std"]
```

Or use `ta` library: `uv pip install ta`

```python
import ta
df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
df["MACD"] = ta.trend.MACD(df["Close"]).macd()
```

## Pandas Integration

```python
# Returns
df["Returns"] = df["Close"].pct_change()
df["Cumulative"] = (1 + df["Returns"]).cumprod()

# Resampling
monthly = df["Close"].resample("M").last()
weekly = df["Close"].resample("W").last()

# Rolling statistics
df["Volatility_30d"] = df["Returns"].rolling(30).std() * (252 ** 0.5)  # Annualized

# Correlation matrix
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
prices = yf.download(tickers, period="1y")["Close"]
corr = prices.pct_change().corr()
```

## yfinance vs Alpha Vantage

Use **yfinance** when:
- Fetching bulk historical data for backtesting
- No API key setup needed
- Need fundamentals + price data together
- Doing portfolio analysis across many stocks

Use **Alpha Vantage** when:
- Need pre-computed technical indicators (RSI, MACD, etc.)
- Need economic indicators (GDP, CPI, treasury yields)
- Need news/sentiment data
- Need commodity prices (gold, oil)
