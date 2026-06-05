---
name: yfinance
description: Free Yahoo Finance market data library. Fetch historical OHLCV, dividends, splits, financials, options chains, and company info for any global stock. No API key required. Supports NSE/BSE Indian equities, US markets, and 50+ global exchanges. Returns pandas DataFrames.
license: MIT
metadata:
    skill-author: Iko Uchiha
---

# yfinance — Free Market Data

Fetch stock market data from Yahoo Finance. No API key, no rate limits (reasonable usage), returns pandas DataFrames.

## Installation

```bash
uv pip install yfinance pandas
```

## Quick Start

```python
import yfinance as yf

# Download historical data
df = yf.download("RELIANCE.NS", period="1y")
print(df.tail())

# Multiple stocks — returns MultiIndex DataFrame
df = yf.download(["RELIANCE.NS", "TCS.NS", "INFY.NS"], period="5y")
closes = df["Close"]           # DataFrame with tickers as columns
returns = closes.pct_change()  # Returns for each ticker

# WRONG — do NOT use group_by="ticker" then access df["Close"]
# That creates a different MultiIndex where Close is nested under each ticker

# Company info and fundamentals
ticker = yf.Ticker("RELIANCE.NS")
print(ticker.info["marketCap"])
print(ticker.info["trailingPE"])

# Financial statements
print(ticker.financials)       # Income statement
print(ticker.balance_sheet)    # Balance sheet
print(ticker.cashflow)         # Cash flow

# Dividends and splits
print(ticker.dividends)
print(ticker.splits)
```

## Symbol Formats

| Market | Format | Example |
|--------|--------|---------|
| NSE (India) | `SYMBOL.NS` | `RELIANCE.NS`, `TCS.NS` |
| BSE (India) | `SYMBOL.BO` | `RELIANCE.BO`, `TCS.BO` |
| US (NASDAQ/NYSE) | `SYMBOL` | `AAPL`, `MSFT` |
| London | `SYMBOL.L` | `HSBA.L` |
| Tokyo | `SYMBOL.T` | `7203.T` |

## Download Parameters

```python
yf.download(
    tickers="RELIANCE.NS",   # Single or list
    period="1y",              # 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    interval="1d",            # 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    start="2020-01-01",       # Alternative to period
    end="2024-01-01",
    auto_adjust=True,         # Adjust for splits/dividends
    actions=True,             # Include dividends/splits columns
)
```

## Indian Market Indices

```python
# NIFTY 50
nifty = yf.download("^NSEI", period="5y")

# SENSEX
sensex = yf.download("^BSESN", period="5y")

# NIFTY Bank
bank_nifty = yf.download("^NSEBANK", period="5y")
```

## Environment Variables

None required. yfinance is completely free with no API key.

## Comparison with Alpha Vantage

| Feature | yfinance | Alpha Vantage |
|---------|----------|---------------|
| API Key | Not needed | Required (free tier) |
| Rate Limit | Reasonable use | 25/day (free) |
| Historical Data | 20+ years | 20+ years |
| Fundamentals | Yes | Yes |
| Technical Indicators | No (compute yourself) | 50+ built-in |
| Options | Yes | Yes |
| Real-time | 15-min delayed | 15-min delayed (free) |
| Best For | Backtesting, bulk data | Technical indicators |
