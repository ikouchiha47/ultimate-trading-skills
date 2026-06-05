# Options Data

## Options Chain

```python
import yfinance as yf

ticker = yf.Ticker("AAPL")  # Options most liquid for US stocks

# Available expiry dates
ticker.options
# ('2024-01-19', '2024-01-26', '2024-02-02', ...)

# Get chain for specific expiry
chain = ticker.option_chain("2024-01-19")

# Calls
chain.calls
# Columns: contractSymbol, lastTradeDate, strike, lastPrice, bid, ask,
#          change, percentChange, volume, openInterest, impliedVolatility

# Puts
chain.puts
```

## Filtering Options

```python
calls = chain.calls

# ATM options (near current price)
current_price = ticker.info["currentPrice"]
atm = calls[abs(calls["strike"] - current_price) < 5]

# High open interest
liquid = calls[calls["openInterest"] > 1000]

# ITM calls
itm = calls[calls["strike"] < current_price]
```

## All Expiries

```python
import pandas as pd

all_calls = []
for exp in ticker.options[:5]:  # First 5 expiries
    chain = ticker.option_chain(exp)
    c = chain.calls.copy()
    c["expiry"] = exp
    all_calls.append(c)

all_calls_df = pd.concat(all_calls)
```

## Note on Indian Markets

NSE options data through yfinance can be limited or unavailable. For Indian options, consider using the NSE website directly or broker APIs.
