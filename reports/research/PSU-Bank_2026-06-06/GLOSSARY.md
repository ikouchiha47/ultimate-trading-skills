# Glossary — what every header & line item means

Reference for the tables and charts in this report. **(computed)** = our scripts (split-adjusted
prices / backtests); **(sourced)** = from a dated disclosure (screener / filings / RBI).

## Dashboard table headers (00_comprehensive §3)
| Header | Meaning | How to read |
|---|---|---|
| **P/B** | Price-to-Book = price ÷ book value per share (sourced) | <1 = trading below net worth; banks valued on P/B |
| **ROE %** | Return on Equity = net profit ÷ shareholder equity (sourced) | how profitably the bank uses capital; >15% strong for a bank |
| **5y profit CAGR** | annualised net-profit growth over 5 yrs (sourced) | trailing — off a cyclical-loss base for PSU banks, NOT a forward guide |
| **TTM profit** | trailing-twelve-month profit growth YoY (sourced) | recent momentum; +ve = still growing |
| **1-yr ret** | price return over 1 year (computed, split-adjusted) | momentum |
| **vs 50-DMA %** | price distance from its **50-day** moving average = (price ÷ 50DMA − 1)×100 (computed) | medium-term trend; −ve = below/pulled back |
| **vs 200-DMA %** | price distance from its **200-day** moving average (computed) | long-term trend; above = uptrend, below = downtrend |
| **vol(20/120)** | recent volume vs base = avg 20-day volume ÷ avg 120-day volume (computed) | >1 = elevated activity |
| **delivery %** | % of traded shares actually delivered (not intraday) (computed) | high = investor (not trader) participation = conviction |
| **absorption** | 0–1 flow score: volume spike + delivery + close-in-range (computed) | high on a dip = a buyer soaking up supply (fadeable) |

**Structure read:** above both DMAs = uptrend · below both = downtrend · below 50 but at/above 200
= pullback within an uptrend (the EARNED 50-DMA buy-the-dip zone).

## Strategy terms (strategies/)
| Term | Meaning |
|---|---|
| **null** | the benchmark a strategy must beat — here buy-and-hold the basket |
| **Sharpe** | risk-adjusted return (return ÷ volatility) |
| **Sharpe-over-null** | strategy Sharpe **minus** the null's Sharpe — isolates timing skill from market beta; **>0 = real edge** |
| **maxDD** | maximum drawdown (worst peak-to-trough loss) |
| **EARNED / NO EDGE** | verdict: did Sharpe-over-null clear 0 on out-of-sample-aware testing |

## Financial line items (data/*.csv & financial charts)
| Line item | Meaning (banking) |
|---|---|
| **Revenue** | total income (interest + other income) (sourced) |
| **Interest** | interest earned on loans/investments |
| **Financing Profit / Margin %** | income minus interest expense+ops (bank's core spread; often −ve as screener defines it) |
| **Net Profit** | bottom-line profit after tax |
| **EPS (₹)** | earnings per share |
| **Deposits** | customer money the bank holds (its funding) |
| **Borrowing** | wholesale/market borrowing (other funding) |
| **Investments** | the bank's securities book — mostly **G-secs / SLR** ("where money is invested" beyond loans) |
| **CASA** | Current+Savings deposits ÷ total — cheap funding; higher = better |
| **NIM** | Net Interest Margin = net interest income ÷ assets — the lending spread |
| **GNPA / NNPA** | Gross / Net Non-Performing Assets % — bad-loan ratio (lower = healthier) |
| **PCR** | Provision Coverage Ratio — % of bad loans provided for (higher = safer) |

## Graph diagrams
*(`charts/dependency_*.png`)*
Node colour: green = listed company (has a price) · yellow = unlisted group entity · purple = foreign
JV partner. Edge: **green = price-validated co-move / high-confidence** · blue = leads · dotted =
unvalidated. `group_entity` = subsidiary/associate; `partners_with` = JV partner. Edge "strength" =
the parent's stake %. Listed subs annotated with correlation to the parent (corroboration, not proof).

## Credit ratings (what the grades mean)
Indian **long-term** scale (CRISIL / ICRA / CARE / India Ratings–Fitch / Brickwork), best → worst:

- **AAA** — highest safety, lowest credit risk (the big PSU banks' senior debt).
- **AA** (AA+/AA/AA−) — high safety, marginally more risk than AAA (typical for PSU **AT1 / Tier-I**
  bonds, and the *senior* debt of weaker PSU banks).
- **A** (A+/A/A−) — adequate safety. **BBB** — moderate (lowest investment grade); below **BBB−** = speculative.

**Modifiers/terms:** `+`/`−` = standing within a band · **Outlook** (Stable / Positive / Negative) =
likely medium-term direction · **Rating Watch** = a near-term event may move it. **Short-term scale:**
**A1+** (highest) … A4 — used for Certificates of Deposit / CP. **Actions:** Assigned (new) ·
Reaffirmed/Affirmed (unchanged) · Upgraded/Downgraded · Withdrawn.

**Important:** one rationale doc rates MANY instruments at different grades — e.g. a bank's
Tier-II/FD at **AAA** but its **AT1 (Tier-I)** a notch lower at **AA+**. The "senior" rating we cite is
the *highest* (issuer / FD / Tier-II). Prefixes (`CRISIL` / `[ICRA]` / `IND` / `CARE`) denote the agency.
