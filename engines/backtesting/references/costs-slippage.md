# Transaction Costs & Slippage

## Adding Fees

```python
import vectorbt as vbt

pf = vbt.Portfolio.from_signals(
    price, entries, exits,
    init_cash=100000,
    fees=0.001,          # 0.1% per trade (both entry and exit)
)
```

## Typical Fee Structures

| Market | Brokerage | STT | Total (approx) |
|--------|-----------|-----|-----------------|
| NSE (Zerodha) | 0.03% or ₹20 | 0.1% sell | ~0.15% round trip |
| NSE (Delivery) | 0 | 0.1% sell | ~0.1% round trip |
| US (IBKR) | $0.005/share | 0 | ~0.01-0.05% |

```python
# Indian market realistic costs
pf = vbt.Portfolio.from_signals(
    price, entries, exits,
    init_cash=100000,
    fees=0.0015,  # ~0.15% round trip for Indian intraday
)
```

## Slippage

Slippage = difference between the price you see and the price you get. Matters for illiquid stocks and large orders.

```python
pf = vbt.Portfolio.from_signals(
    price, entries, exits,
    init_cash=100000,
    fees=0.001,
    slippage=0.001,   # 0.1% slippage per trade
)
```

## Impact on Returns

```python
# Compare: no costs vs realistic costs
pf_ideal = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000)
pf_real = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.0015, slippage=0.001)

print(f"Ideal Return:    {pf_ideal.total_return():.2%}")
print(f"Realistic Return: {pf_real.total_return():.2%}")
print(f"Cost Drag:        {pf_ideal.total_return() - pf_real.total_return():.2%}")
print(f"Trades: {pf_real.total_trades()}")
```

A strategy that trades 200 times/year with 0.15% cost per trade loses ~30% to costs alone. High-frequency strategies need very high win rates to overcome costs.
