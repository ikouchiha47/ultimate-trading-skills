# PSU Banks — Industry Analysis

*Sector: NIFTY PSU BANK. Date: 2026-06-06. Universe assembled: SBIN, BANKBARODA, PNB, CANBK
(4 of 12 — top by market cap; remaining 8 pending). All prices split-adjusted. Provenance is
marked on every figure: **(computed)** by our scripts, **(sourced)** from a dated disclosure,
or **`unknown`** where it cannot be honestly sourced.*

Template backbone: standard industry-analysis frameworks (Porter / PESTEL / life-cycle / value
chain / SWOT) — see `templates/industry-analysis.md`. A framework is a thoroughness checklist,
not a licence to speculate.

---

## 1. Industry life-cycle stage
**Mature / cyclical, mid-to-late upcycle.** PSU banking is a mature industry whose earnings ride
the credit + interest-rate cycle. The four names show the late-upcycle signature: P/E compressed
to **6.7–10.8** and the basket having delivered a strong multi-year run (5-yr stock CAGR
**18–33%** (sourced, screener)) now **consolidating** — every name sits within a few percent of
its 50- and 200-DMA (computed, see §8). This is the classic "earnings still good, price catching
its breath after a re-rating" mature-cycle posture, not an early-growth industry.

## 2. Porter's Five Forces
| Force | Read (India PSU banks) | Provenance |
|---|---|---|
| Threat of new entrants | **Low** — banking licence + capital + branch network are high barriers; new entrants are niche (SFBs, fintech), not full-scale rivals. | qualitative |
| Supplier power (cost of funds) | **Moderate-rising** — deposits are the raw material; deposit competition + CASA erosion lift cost of funds (CANBK cost of funds 5.18%, CASA 29.5% (sourced)). | sourced |
| Buyer power | **Moderate** — large corporate borrowers negotiate; retail borrowers are price-takers but mobile (repo-linked rates make switching easier). | qualitative |
| Substitutes | **Rising** — NBFCs, fintech lenders, capital markets disintermediate parts of the loan book. | qualitative |
| Rivalry | **High** — private banks (HDFC/ICICI) compete on NIM, tech, deposit franchise; PSU banks compete largely on reach + sovereign trust. | qualitative |

## 3. PESTEL — where India macro + policy lives
- **Political / Legal**: majority **Government of India ownership** (promoter holding 62.9% CANBK,
  and similar for peers (sourced, shareholding)) — drives capital-raising, dividend policy, and
  occasional directed-lending overhang. SEBI LODR governs disclosure. RBI is the prudential
  regulator (and active enforcer — see the **RBI ₹41.80 lakh KYC penalty on Canara Bank, 5 Jun
  2026** (sourced)).
- **Economic**: the dominant drivers are **the RBI repo rate, the credit cycle, and G-sec yields**
  (banks hold huge SLR investment books — §"Investments" below). PNB disclosed its **MCLR / repo-
  linked lending rate / base rate unchanged from 1 June 2026** (sourced) — a window into the rate
  environment. Current repo level / latest RBI policy stance: **`unknown`** (not sourced here;
  pull from RBI before asserting a number).
- **Social**: financial inclusion / PSL mandates shape the rural + priority-sector loan book.
- **Technological**: digital banking adoption; fintech substitution pressure.
- **Environmental**: BRSR sustainability reporting now mandatory (PNB filed FY26 BRSR (sourced)).

## 4. Value chain & related/adjacent sectors
PSU banks sit at the centre of the credit value chain: **deposits → lending → fee/treasury**.
Adjacent sectors that co-move or feed them: **NBFCs** (competitors + borrowers), **capex /
infrastructure** (corporate loan demand), **real estate / housing** (retail mortgage book),
**government borrowing** (G-sec holdings link bank P&L to fiscal/rate policy). Lead-lag structure
across the basket: **`unknown`** here — run `influence-graph` on the PSU-bank basket to compute it
(memory notes NIFTY50→PSU_BANK beta +0.85 dominates daily; macro transmits over weeks not days).

## 5. Market structure & the "markets they are invested in"
Two books matter: the **loan book** (who they lend to) and the **investment book** (G-secs etc.).
Balance-sheet scale, Mar 2026 (sourced, screener, ₹ Cr):

| Bank | Deposits | Borrowing | Investments (G-sec/SLR book) |
|---|---|---|---|
| SBIN | 60,43,097 | 7,77,302 | 23,59,502 |
| PNB | 17,24,795 | 1,07,558 | 5,23,515 |
| BANKBARODA | 16,75,895 | 1,70,297 | 4,35,778 |
| CANBK | 15,68,333 | 1,55,288 | 4,07,389 |

**Which markets they lend to — domestic advance mix (Q3 FY26, sourced: screener Key Points).**
Each bank's per-segment split (full breakdown + chart on the company page):

| Bank | Retail | Corporate | Agri | MSME/SME | Tilt |
|---|---|---|---|---|---|
| INDIANB | 23 | 34 | 25 | 18 | most RAM-tilted |
| IOB† | 30 | 28 | 34 | 18 | agri/retail-led |
| MAHABANK | 30 | 36 | 13 | 19 | retail-led |
| UCOBANK | 30 | 33 | 16 | 21 | retail/MSME |
| BANKBARODA | 31 | 38 | 16 | 15 | balanced |
| SBIN | 42 | 33 | 10 | 15‡ | retail-led |
| CANBK | 23 | 41 | 23 | 13 | corporate-heavy |
| BANKINDIA | 25 | 41 | 18 | 16 | corporate-heavy |
| PNB | 24 | 43 | 16 | 16 | corporate-heavy |
| UNIONBANK | 24 | 43 | 17 | 15 | corporate-heavy |

*% of domestic advances, sourced screener Q3 FY26 ("Corporate" includes corporate & others). †IOB's
screener buckets overlap (priority-sector Agri/MSME double-count with retail) and sum >100% — read as
share-per-segment, not a clean partition. ‡SBIN reports SME (not MSME). Canara is corporate-heavy with a
~third NBFC / ~third infrastructure corporate book (see CANBK page).*

For the **industry-wide** view — how system credit is deployed across sectors and what is growing fastest
(Services/NBFC, infrastructure, personal/housing) — see the RBI **"Sectoral Deployment of Bank Credit"**
release we sourced (`data/RBI_sectoral_deployment_apr2026.{md,json,xlsx}`) — the YoY-growth-by-sector
table is shown in [`00_comprehensive` §2a](00_comprehensive.md).

## 6. Structural drivers — why the sector re-rated
- **Asset-quality clean-up**: GNPA collapsed across the cycle (CANBK GNPA 2.08% / NNPA 0.45%,
  PCR 94.2% (sourced)) — the dominant re-rating driver, turning chronic loss-makers profitable.
- **Profit recovery**: all four swung from cyclical losses to record profits (5-yr profit CAGR
  30–73% (sourced); see per-bank reports).
- **Valuation still modest**: P/B 0.82–1.5 (sourced) — three of four below or near book.
- Cyclical caution: extrapolating 30%+ profit CAGR forward through a credit cycle is the classic
  mistake the CFA guidance flags. PSU bank earnings are cyclical; treat trailing growth as peak-ish.

## 7. SWOT (sector)
- **Strengths**: sovereign trust, deposit reach, cleaned-up balance sheets, cheap valuations.
- **Weaknesses**: lower NIM vs private banks (CANBK NIM 2.50% (sourced)), govt-ownership overhang,
  capital-raising dilution risk (CANBK approved FY26-27 capital plan (sourced)).
- **Opportunities**: credit growth, treasury gains if rates fall, re-rating toward book.
- **Threats**: rate cycle turning, fintech/NBFC substitution, directed lending, fresh slippage.

## 8. Signals to watch (the dashboard) — computed price-action, 2026-06-04
| Bank | Last ₹ | vs 50-DMA | vs 200-DMA | 1-yr ret | 20/120d vol | delivery% | absorption |
|---|---|---|---|---|---|---|---|
| SBIN | 977.7 | −4.6% | −0.8% | +20.7% | 1.35× | 43.6% | 0.15 |
| BANKBARODA | 263.7 | −1.7% | −4.5% | +4.0% | 1.32× | 37.4% | 0.19 |
| PNB | 106.8 | −0.6% | −7.5% | −2.4% | 1.10× | 30.4% | 0.13 |
| CANBK | 135.8 | +1.4% | −0.4% | +17.2% | 1.20× | 40.4% | 0.40 |

(computed from split-adjusted jugaad OHLCV + delivery%.) Read: the basket is **consolidating below
the 50-DMA** (BANKBARODA/PNB also below 200-DMA = weaker), volumes mildly elevated (1.1–1.35×) but
**no strong absorption signature** (all < 0.5 except CANBK at 0.40) — i.e. no decisive buyer
soaking up supply yet. CANBK is the relative leader (above 50-DMA, highest absorption, +17% 1-yr).

## 9. Strategy evidence (proving ground) — see `strategies/`
- **Anchor sweep (Sharpe-over-null, full 12-name basket, 2021–):** **50-DMA EARNED** Sharpe 1.32 /
  over-null **+0.23** / CAGR 32.4% / maxDD −19.5% / 18 trades. 25-DMA (−0.57), 100 (−0.76),
  200 (−0.40) all LOSE to buy-and-hold. The mean-reversion edge for this sector lives at the
  **50-DMA**, not the textbook 25-DMA. (computed)
- **Flow-gate on 50-DMA: NO EDGE** (over-null −0.40, only 5 trades) — the absorption/breadth gate
  over-filtered in a one-way bull window; it cannot out-Sharpe a permanent long here. Honest
  negative; revisit on a wider universe + a non-bull regime. (computed)

## 10. References
See `references.md`. Audit snapshots of every screener page in `filings/<sym>_screener_page.pdf`.

---
*Discipline: loan-book sector mix and current repo are marked `unknown` (not sourced) rather than
inferred. All price/strategy figures computed and split-adjusted; strategy figures are
Sharpe-OVER-NULL. Sourced figures carry a dated disclosure.*
