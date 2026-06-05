# Fundamentals

## Company Info

```python
import yfinance as yf

ticker = yf.Ticker("RELIANCE.NS")
info = ticker.info

# Key metrics
info["marketCap"]         # Market capitalization
info["trailingPE"]        # P/E ratio (trailing)
info["forwardPE"]         # P/E ratio (forward)
info["dividendYield"]     # Dividend yield
info["bookValue"]         # Book value per share
info["priceToBook"]       # P/B ratio
info["debtToEquity"]      # D/E ratio
info["returnOnEquity"]    # ROE
info["revenueGrowth"]     # Revenue growth
info["sector"]            # Sector
info["industry"]          # Industry
```

## Financial Statements

```python
ticker = yf.Ticker("RELIANCE.NS")

# Income Statement (annual)
ticker.financials
# Quarterly
ticker.quarterly_financials

# Balance Sheet
ticker.balance_sheet
ticker.quarterly_balance_sheet

# Cash Flow
ticker.cashflow
ticker.quarterly_cashflow
```

## Earnings

```python
# Earnings history
ticker.earnings_history

# Earnings dates (upcoming/recent)
ticker.earnings_dates

# Earnings estimates
ticker.earnings_estimate
ticker.revenue_estimate
```

## Analyst Recommendations

```python
# Current recommendations
ticker.recommendations
# Columns: period, strongBuy, buy, hold, sell, strongSell

# Recommendation summary
ticker.recommendations_summary

# Price targets
info["targetHighPrice"]
info["targetLowPrice"]
info["targetMeanPrice"]
```

## Holders

```python
# Major holders
ticker.major_holders

# Institutional holders
ticker.institutional_holders

# Mutual fund holders
ticker.mutualfund_holders
```

## Comparing Fundamentals

```python
tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
data = []
for t in tickers:
    info = yf.Ticker(t).info
    data.append({
        "Symbol": t,
        "Market Cap": info.get("marketCap"),
        "P/E": info.get("trailingPE"),
        "P/B": info.get("priceToBook"),
        "ROE": info.get("returnOnEquity"),
        "Debt/Equity": info.get("debtToEquity"),
    })

import pandas as pd
df = pd.DataFrame(data)
print(df)
```
