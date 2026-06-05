# Indian Markets

## Symbol Formats

| Exchange | Suffix | Example |
|----------|--------|---------|
| NSE | `.NS` | `RELIANCE.NS` |
| BSE | `.BO` | `RELIANCE.BO` |

## Popular NSE Tickers

```python
nifty50_sample = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "HCLTECH.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TATAMOTORS.NS", "TITAN.NS", "WIPRO.NS", "ULTRACEMCO.NS",
    "BAJFINANCE.NS", "NESTLEIND.NS", "TATASTEEL.NS", "POWERGRID.NS", "NTPC.NS",
    "M&M.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "ONGC.NS",
]
```

## Indian Indices

```python
import yfinance as yf

# NIFTY 50
nifty = yf.download("^NSEI", period="5y")

# SENSEX (BSE 30)
sensex = yf.download("^BSESN", period="5y")

# NIFTY Bank
bank_nifty = yf.download("^NSEBANK", period="5y")

# NIFTY IT
nifty_it = yf.download("^CNXIT", period="5y")

# NIFTY Pharma
nifty_pharma = yf.download("^CNXPHARMA", period="5y")

# India VIX
india_vix = yf.download("^INDIAVIX", period="1y")
```

## Quirks and Gotchas

1. **Symbol lookup**: If unsure of the exact ticker, use `yf.Ticker("SYMBOL.NS").info["shortName"]` to verify
2. **Missing data**: Some smaller BSE-only stocks may not have data on Yahoo Finance
3. **Adjusted prices**: Use `auto_adjust=True` (default) to get split/dividend-adjusted prices
4. **Currency**: All Indian stock prices are in INR
5. **Trading hours**: NSE/BSE trade 9:15 AM - 3:30 PM IST (no pre/after market in yfinance)
6. **Holidays**: Indian market holidays differ from US — missing dates in data are normal
7. **M&M ticker**: Mahindra & Mahindra is `M&M.NS` — the ampersand can cause issues in some contexts, use URL encoding if needed

## Sector-wise Screening

```python
import yfinance as yf
import pandas as pd

banking = ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"]
data = []
for sym in banking:
    info = yf.Ticker(sym).info
    data.append({
        "Symbol": sym.replace(".NS", ""),
        "Price": info.get("currentPrice"),
        "P/E": info.get("trailingPE"),
        "P/B": info.get("priceToBook"),
        "ROE": info.get("returnOnEquity"),
        "NPA": info.get("debtToEquity"),
    })
print(pd.DataFrame(data).to_string(index=False))
```
