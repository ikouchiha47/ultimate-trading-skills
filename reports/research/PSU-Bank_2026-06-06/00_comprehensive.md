# Top-10 PSU Banks — Comprehensive Report

*Date: 2026-06-06. Universe: top 10 of the 12 NIFTY PSU BANK constituents by market cap (dropped
CENTRALBK #11, PSB #12). All prices split-adjusted (jugaad `adjust=True`). Provenance marked:
**(computed)** = our scripts · **(sourced)** = dated disclosure · **`unknown`** = not honestly
sourceable. Companion files: `00_industry.md` (sector frameworks), `<BANK>_equity_research.md`
(per name), `01_observations.md` (price-action/volume/profit → buy-sell), `strategies/`, `data/`,
`charts/`, `filings/`, `references.md`.*

---

## 1. The 10 banks (ranked by market cap, sourced)
| # | Bank | Mcap ₹Cr | Price ₹ | P/E | P/B | Div% | ROE% |
|---|---|---|---|---|---|---|---|
| 1 | SBIN | 9,02,477 | 978 | 10.8 | 1.51 | 1.77 | 15.4 |
| 2 | BANKBARODA | 1,36,369 | 264 | 6.88 | 0.82 | 3.22 | 12.7 |
| 3 | UNIONBANK | 1,27,481 | 167 | 6.56 | 0.95 | 2.84 | 15.7 |
| 4 | CANBK | 1,23,189 | 136 | 6.87 | 1.05 | 3.09 | 16.1 |
| 5 | PNB | 1,22,802 | 107 | 6.68 | 0.82 | 2.81 | 13.0 |
| 6 | INDIANB | 1,13,421 | 842 | 9.69 | 1.42 | 2.17 | 15.4 |
| 7 | BANKINDIA | 64,402 | 141 | 6.08 | 0.71 | 3.29 | 12.4 |
| 8 | IOB | 63,412 | 32.9 | 11.7 | 1.71 | 0.00 | 15.6 |
| 9 | MAHABANK | 60,909 | 79.2 | 8.68 | 1.83 | 2.78 | 22.7 |
| 10 | UCOBANK | 31,675 | 25.3 | 12.8 | 1.03 | 1.74 | 8.5 |

All fundamentals sourced (screener, 2026-06-06). Price tally check (jugaad vs screener) passed
< 0.2% for every name (computed).

## 2. The markets they are invested in (loan-book / credit deployment)

**Two books per bank:** the **loan book** (credit by sector) and the **investment book** (mostly
G-secs/SLR). The per-bank loan-book SECTOR split is **premium-gated on screener** (segment table
blank), so it is sourced two ways instead:

### 2a. System-wide — RBI Sectoral Deployment of Bank Credit (April 2026, sourced)
Authoritative RBI release (all scheduled commercial banks, ~95% of non-food credit; system-wide,
not PSU-specific). Full table: `data/RBI_sectoral_deployment_apr2026.{xlsx,json,md}`. **YoY credit
growth (Apr 2026 vs Apr 2025), sourced:**

| Sector | YoY growth | (prior yr) | Note |
|---|---|---|---|
| **Non-food credit (total)** | **15.8%** | 9.8% | broad acceleration |
| Services | **18.6%** | 10.1% | **fastest** — driven by NBFCs **+27.7%**, commercial real estate, trade |
| Personal loans | 16.0% | 11.9% | housing +11.4%, vehicle robust, credit-card moderating |
| Industry | 15.1% | 7.0% | infra/basic metals/engineering strong; construction/textiles weak |
| Agriculture & allied | 13.7% | 9.2% | slowest, still improved |

**Read:** bank credit is being deployed fastest into **Services (esp. lending to NBFCs)** and
**Personal/housing** — i.e. the PSU banks' growth markets are NBFC wholesale funding, real estate,
infra and retail mortgages, not classical agri/industry. This is the system picture; per-bank mix
follows in 2b.

### 2b. Per-bank — annual-report segment notes (in progress)
Each bank's FY2025 annual report is being downloaded + text-extracted into `filings/ar/` (background
batch). The segment/business-ratio note (retail vs corporate vs treasury, sector exposure) is read
from there per bank. Where a bank's segment split is not yet extracted it is marked **`unknown`** in
its per-bank report — never inferred from price. Investment-book SIZE is sourced now from each
balance sheet (`data/<sym>_balance_sheet.csv`).

## 3. Full dashboard — fundamentals × price-action (computed, 2026-06-04)
| Bank | P/B | ROE% | 5y profit CAGR | TTM profit | 1-yr ret | vs50 | vs200 | vol(20/120) | deliv% | absorp |
|---|---|---|---|---|---|---|---|---|---|---|
| SBIN | 1.51 | 15.4 | 30% | +7% | +20.7% | −4.6 | −0.8 | 1.35 | 43.6 | 0.15 |
| BANKBARODA | 0.82 | 12.7 | 73% | −4% | +4.0% | −1.7 | −4.5 | 1.32 | 37.4 | 0.19 |
| UNIONBANK | 0.95 | 15.7 | 47% | +8% | +10.1% | −2.8 | **+4.3** | 0.77 | 39.2 | 0.13 |
| CANBK | 1.05 | 16.1 | 44% | +2% | +17.2% | **+1.4** | −0.4 | 1.20 | 40.4 | **0.40** |
| PNB | 0.82 | 13.0 | 48% | 0% | −2.4% | −0.6 | −7.5 | 1.10 | 30.4 | 0.13 |
| INDIANB | 1.42 | 15.4 | 30% | +4% | **+33.2%** | −3.3 | **+1.5** | 1.62 | 34.8 | 0.17 |
| BANKINDIA | **0.71** | 12.4 | 39% | +13% | +13.5% | −1.3 | −0.3 | 0.99 | 40.5 | 0.20 |
| IOB | 1.71 | 15.6 | 48% | +60% | **−18.8%** | −2.9 | −9.5 | 0.42 | 44.2 | 0.28 |
| MAHABANK | 1.83 | **22.7** | 65% | +27% | **+39.8%** | **+5.1** | **+23.7** | 0.60 | 38.0 | 0.04 |
| UCOBANK | 1.03 | 8.5 | 0% | +48% | **−25.6%** | −0.9 | −11.5 | 0.59 | 39.3 | 0.19 |

(P/B, ROE, growth = sourced screener; returns/DMA/volume/delivery/absorption = computed split-adjusted.)

## 4. What the table says (groupings)
- **Momentum leaders (above 200-DMA, strong 1-yr):** MAHABANK (+39.8%, ROE 22.7% — best operator,
  but P/B 1.83 richest & price **+23.7% above 200-DMA = extended**), INDIANB (+33.2%, above 200-DMA),
  UNIONBANK (+10.1%, above 200-DMA, ROE 15.7%, cheap P/B 0.95). CANBK (+17.2%, above 50-DMA, highest
  absorption 0.40).
- **Cheap & basing (near DMAs):** BANKINDIA (cheapest P/B 0.71, +13% TTM, at its DMAs),
  BANKBARODA (P/B 0.82, but below both DMAs, −4% TTM).
- **Weak price-action laggards:** PNB (−2.4% 1-yr, −7.5% below 200-DMA), and the two clear losers
  **IOB (−18.8%) and UCOBANK (−25.6%)** — both far below their 200-DMA yet carry the **richest P/E
  (11.7, 12.8)** and huge TTM growth (60%, 48%). That combination = base-effect earnings on
  collapsing prices; the market is de-rating them despite the optics. Treat their TTM growth as a
  low-base artefact, not momentum.
- **SBIN:** the quality anchor — pulling back to its 200-DMA on the highest volume (1.35×) and
  highest-but-one delivery (43.6%); investor accumulation into weakness.

## 5. Strategy evidence (see `strategies/`)
- **EARNED: 50-DMA mean-reversion** on the PSU-bank basket (2021–): Sharpe 1.32 / **over-null
  +0.23** / CAGR 32.4% / maxDD −19.5% / 18 trades. The 25-DMA (textbook), 100, 200 all LOSE to
  buy-and-hold. The sector's reversion edge lives at the **50-DMA**. (computed)
- **Flow-gate stacked on 50-DMA: NO EDGE** here (over-null −0.40, 5 trades) — over-filtered in a
  one-way bull. Honest negative; needs a wider universe + non-bull regime. (computed)

## 5b. What drives the sector / who leads — influence graph (computed)
Lead-lag-validated graph (2023–, daily; `graph/influence_report.txt`, `charts/influence_graph.png`):
- **NIFTY50 → PSU_BANK +0.90** — daily moves are **dominated by market beta**, not bank-specific
  news. (i.e. on any given day the basket mostly does what the market does.)
- **Bellwethers** (constituents most representative of the basket, by co-move): **PNB +0.44,
  CANBK +0.42, BANKBARODA +0.41**, UNIONBANK +0.39, SBIN +0.38 — watch the large caps to read the
  cohort. The small caps **IOB +0.30, UCOBANK +0.31** are the least representative (they march to
  their own, weaker, drum — consistent with their laggard price-action).
- **VIX leads PSU_BANK by 1 day −0.34** (risk-off hits with a lag) — the one usable daily signal.
- **US10Y / USDINR: no daily link** (corr ≈ +0.06) — macro transmits to PSU banks **via flow over
  weeks**, not daily price. Don't trade these banks off daily yield/FX ticks.

## 6. Caveats (discipline)
- RBI sectoral data is **system-wide**, not PSU-only; per-bank loan mix is being sourced from ARs
  (some `unknown` until extracted). Repo/policy current level: pull from RBI before quoting a number.
- Trailing 5-yr profit CAGRs (39–73%) are off cyclical-loss bases — **not** forward guides.
- The 50-DMA edge is one basket / one bull window; modest. Not investment advice.

## 7. References — `references.md` + audit PDFs in `filings/`.
