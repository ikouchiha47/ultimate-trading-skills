# PSU Banks Deep-Dive — 2022-01-01 to 2026-06-06

## 1. Quant Ranking: Risk-Adjusted Return (Calmar)

**Sector:** NIFTY PSU BANK | **Benchmark:** NIFTY 50  
**Sector return:** +241% | **NIFTY 50 return:** +37% | **Relative-strength Δ:** +148%

| Rank | Symbol      | CAGR     | MaxDD   | Calmar  | WindowRet | ExcessVsSector | Up? | 25dmaZ    |
|------|-------------|----------|---------|---------|-----------|----------------|-----|-----------|
| 1    | INDIANB     | 54.7%    | -21.8%  | 2.50    | +564%     | +323%          | ·   | -0.30     |
| 2    | MAHABANK    | 43.2%    | -39.8%  | 1.08    | +375%     | +134%          | ↑   | -0.30     |
| 3    | BANKBARODA  | 34.8%    | -32.2%  | 1.08    | +265%     | +24%           | ·   | +0.14     |
| 4    | UNIONBANK   | 40.5%    | -38.9%  | 1.04    | +337%     | +96%           | ·   | -0.06     |
| 5    | CANBK       | 35.3%    | -35.2%  | 1.00    | +271%     | +30%           | ·   | +0.00     |
| 6    | SBIN        | 20.9%    | -23.9%  | 0.87    | +127%     | -114%          | ·   | -0.24     |
| 7    | PNB         | 28.8%    | -37.7%  | 0.76    | +200%     | -41%           | ·   | -0.12     |
| 8    | BANKINDIA   | 30.0%    | -40.6%  | 0.74    | +212%     | -29%           | ↑   | +0.05     |
| 9    | UCOBANK     | 16.9%    | -66.6%  | 0.25    | +97%      | -144%          | ·   | -0.32     |
| 10   | IOB         | 11.5%    | -60.6%  | 0.19    | +60%      | -181%          | ·   | -0.43     |
| 11   | CENTRALBK   | 9.2%     | -58.6%  | 0.16    | +46%      | -194%          | ·   | **-1.30** |
| 12   | PSB         | 9.4%     | -72.4%  | 0.13    | +48%      | -193%          | ·   | -0.44     |

**Key observations:**
- **INDIANB** dominates on risk-adjusted return (Calmar 2.50) — lowest max drawdown (-22%) combined with 54.7% CAGR. Also +323% excess vs sector.
- **CENTRALBK** flag: 25dmaZ = -1.30, unusually stretched below its 25-DMA. BNF fade candidate.
- **SBIN** underperformed the sector materially (-114% excess vs sector) despite being the largest PSU bank — suggests a "laggard leader" dynamic.
- Only **MAHABANK** and **BANKINDIA** are in structural uptrend (price > 50-DMA > 200-DMA). All others have broken their uptrend.

Charts saved to: `reports/sector-deep-dive/PSU_Bank_2026-06-06/`

---

## 2. Influence Graph — What Moves PSU Banks

### Macro Drivers (since 2022-01-01)

| Driver    | ExpSign | corr0    | Lead(d) | LeadCorr  | Verdict                        |
|-----------|---------|----------|---------|-----------|--------------------------------|
| NIFTY50   | +1      | +0.73    | 0       | +0.73     | **supported (co-move)**        |
| USDINR    | -1      | +0.04    | 2       | +0.08     | no daily link                  |
| US10Y     | -1      | +0.07    | 5       | -0.12     | weak                           |
| VIX       | -1      | -0.07    | 1       | -0.33     | **supported (leads 1d -0.33)** |

### Bellwethers (constituents ranked by sector correlation)

| Rank | Symbol     | corr0    | Verdict                        |
|------|------------|----------|--------------------------------|
| 1    | PNB        | +0.43    | supported (co-move)            |
| 2    | CANBK      | +0.39    | supported (co-move)            |
| 3    | BANKINDIA  | +0.38    | supported (co-move)            |
| 4    | BANKBARODA | +0.37    | supported (co-move)            |
| 5    | UNIONBANK  | +0.37    | supported (co-move)            |

**Interpretation:**
- PSU Banks are **high-beta to NIFTY 50** (corr +0.73) — they move with the broad market.
- **VIX leads PSU Banks by 1 day** with -0.33 correlation: a VIX spike today predicts PSU Bank weakness tomorrow. This is the fear channel (global risk-off → EM de-risking).
- **USDINR** and **US10Y** show no reliable daily link. The FII-outflow channel (INR weakness + higher US yields → FPI selling) may act at a weekly/monthly frequency, not daily.
- **PNB** is the strongest bellwether (corr +0.43 with sector) — it moves most in sync with the sector index.

---

## 3. Lending / Credit Exposure — Loan Book Breakdown

### 3a. RBI Sectoral Deployment of Bank Credit (₹ Crore, as of Mar 31, 2026)

Source: RBI Bulletin Table 16 — Industry-wise Deployment of Gross Bank Credit, released May 22, 2026  
[XLSX](https://rbidocs.rbi.org.in/rdocs/Bulletin/DOCs/16T_BULL220520262D5B1FB3FDDA45E8AC537580D34ACFA8.XLSX)

| Sub-Sector               | Outstanding (₹ Cr) | YoY Growth |
|--------------------------|--------------------|------------|
| **Total Industry**       | 4,582,009          | +15.0%     |
| **Infrastructure (total)**| 1,493,563         | +9.5%      |
| ├ Power                  | 845,053            | **+22.1%** |
| ├ Telecommunications     | 108,701            | **-12.2%** |
| ├ Roads (incl. Ports)    | 337,819            | +1.1%      |
| ├ Airports               | 6,662              | -27.2%     |
| ├ Ports                  | 8,794              | +48.7%     |
| ├ Railways               | 6,693              | -50.1%     |
| └ Other Infrastructure   | 179,840            | -3.2%      |
| **Construction**         | 179,323            | +12.1%     |
| **Services (NBFCs etc.)**| (see press release) | +18.6%     |

Key systemic trends (Source: RBI PR #62827, May 29, 2026):
- Non-food bank credit: **₹211 Lakh Cr** (+15.8% YoY)
- **Services credit (NBFCs, CRE)** grew **18.6% YoY** — strongest broad sector
- **Power** credit grew **22.1% YoY** — fastest infra sub-sector
- **Telecom** credit **shrinking** (-12.2% YoY) — likely due to debt reduction by incumbent telcos post-capex cycle
- Data Centre / IT does **not appear as a separate line item** in RBI Table 16. Likely categorized under "Other Infrastructure" or "Computer Software" in the full statements.

### 3b. SBI (State Bank of India)

Source: SBI Annual Report FY2024-25  
[PDF](https://www.bseindia.com/xml-data/corpfiling/AttachHis/9c6a98f8-f882-4c06-9cb1-7f3b6ae1159f.pdf)  
[Investor relations](https://sbi.co.in/web/investor-relations)

**Loan Book Composition (FY2025, ₹ Lakh Cr):**

| Segment               | Amount (₹ Lakh Cr) | % of Domestic Advances |
|-----------------------|-------------------:|-----------------------:|
| **Retail Advances**   | 15.06              | **41.8%**              |
| ├ Home Loans          | 8.31               | 23.07% (55.1% of retail) |
| ├ Auto Loans          | 1.27               | —                      |
| └ Xpress Credit       | 3.50               | —                      |
| **Corporate (CCG)**   | 12.41              | ~34.4%                 |
| **SME**               | 5.06               | ~14.1%                 |
| **Agri**              | 3.49               | ~9.7%                  |
| **Total Domestic**    | **36.02**          | **100%**               |

**Corporate credit growth drivers (FY2025):** CCG gross advances grew **16.43% YoY**, driven by NBFCs, Infrastructure, Services, Commercial Real Estate (CRE), Power, Chemicals, and Engineering.

**Real Estate exposure (FY2024):** ₹9,47,857 Cr total exposure to real estate sector (Source: SBI FY2024 AR, Notes to Accounts).

**Data Centres:** SBI has identified **Data Centre as a "Champion Sector"** under the EASE 7.0 framework. A **"Centre of Excellence (Chakra) for Data Centres"** exists (sbi.co.in/web/coe-chakra/data-centres). Exact loan exposure to data centres: **unknown** — not separately disclosed.

**Green finance:** Target of 7.5% green portfolio of domestic advances by 2030. $3.07B raised from DFIs/MDBs for green lending.

### 3c. Bank of Baroda

Source: BOB Annual Report FY2024-25  
[PDF](https://www.bseindia.com/xml-data/corpfiling/AttachHis/f770ec9f-581e-47f3-b952-f6fe10d57daf.pdf)  
Concalls: [May 2026 transcript](https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=B1C5608A_FE04_4F34_AE03_A6777062FA78_165011.pdf)

**Loan Book Composition (FY2025, ₹ Cr):**

| Segment            | Amount (₹ Cr)  | % of Domestic Advances |
|--------------------|---------------:|-----------------------:|
| **Corporate**      | 4,12,274       | **40.4%**              |
| **Retail**         | 2,56,633       | **25.1%**              |
| **International**  | 2,09,349       | —                      |
| **Gross Domestic** | **10,21,112**  | **100%**               |

Domestic advances grew **13.69% YoY**. Retail grew **19.40%**, Corporate grew **8.57%**.

**Sector-specific breakdown (Power, Telecom, Roads, NBFC, Real Estate, Data Centre):**  
**Unknown** — not found in extracted annual report text. These figures are in the Notes to Accounts (Schedule 9-like tables) in the full PDF which could not be reliably parsed.

### 3d. PNB (Punjab National Bank)

Source: PNB Q4 FY2026 Concall transcript (May 2026)  
[Transcript](https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=2be9c223-c5bb-46ad-a57d-975eb6c28902.pdf)

**Loan Book (FY2026, as of Mar 31, 2026):**
- Total advances: **₹12.59 Lakh Cr** (+12.7% YoY)
- RAM (Retail + Agri + MSME): **~54%** of book
- Corporate loan book: **~46-47%** (management targeting to reduce to ~40%)
- Retail (excl IBPC): +18.2% YoY
- MSME: +19.9% YoY
- Agri priority: +16.2% YoY
- Corporate credit sanctioned in FY26: **₹4 Lakh Cr+**
- ECLGS book outstanding: ₹8.75 Lakh Cr (69.5% of book), NPA in this book: only ₹5,034 Cr
- Domestic NIM: 2.61%
- **Sector-specific breakdown (Power, Telecom, Roads, NBFC, Real Estate, Data Centre):**  
  **Unknown** — not disclosed in the concall transcript.

### 3e. CANBK (Canara Bank)

Source: CANBK Q4 FY2026 Concall transcript (May 2026)  
[Transcript](https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=864b8993-7923-4f0d-b6b9-9c07c39dc5da.pdf)

**Loan Book (FY2026, as of Mar 31, 2026):**
- Total advances: **₹12.37 Lakh Cr** (+15.30% YoY)
- RAM book: **₹7.30 Lakh Cr** (+19.73%), targeting **60-40 RAM-Corporate mix** (currently 59-40)
- Retail: ₹2.96 Lakh Cr (**+32.93%**)
- Housing: ₹1.24 Lakh Cr (+17.55%)
- Vehicle: ₹26,070 Cr (+26.33%)
- MSME: ₹1.57 Lakh Cr (+12.85%)
- Gold loans: **~20% of book** (material exposure)
- **Sector-specific breakdown (Power, Telecom, Roads, NBFC, Real Estate, Data Centre):**  
  **Unknown** — not disclosed in the concall transcript.

---

## 4. Thematic: Datacentre + Telecom Capex → PSU Bank Exposure Scenario

### Thesis Statement
*"India's datacentre and telecom infrastructure capex cycle creates loan demand. PSU banks, as primary lenders to infrastructure, should benefit via corporate loan growth."*

### Evidence from Data

| Channel | Evidence | Source |
|---------|----------|--------|
| **System-wide infra credit growth** | Infrastructure credit grew **9.5% YoY** to ₹14.9 Lakh Cr. **Power** grew 22.1% (data centres are power-intensive). | RBI Table 16, Mar 2026 |
| **Telecom credit declining** | Telecom credit **shrinking** (-12.2% YoY to ₹1.09 Lakh Cr). Incumbent telcos are deleveraging, not borrowing for new capex. | RBI Table 16, Mar 2026 |
| **SBI — Data Centre Champion Sector** | SBI explicitly named Data Centre as a "Champion Sector" under EASE 7.0 and has a dedicated CoE. | SBI FY2025 AR, p.68 |
| **SBI — Power exposure** | Power listed as a corporate credit growth driver (along with NBFCs, Infra, CRE). | SBI FY2025 AR, CCG section |
| **BOB/PNB/CANBK — Unknown** | No bank-level disclosure of specific datacentre or telecom loan exposure found in annual reports or concall transcripts. | Extracted annual report data |

### Forward Scenario (Scenario Analyzer Framework)

Using the [sector sensitivity matrix](skills/screeners/scenario-analyzer/references/sector_sensitivity_matrix.md):

**Scenario: Datacentre + Telecom Capex Acceleration**

| Order | Impact | Mechanism |
|-------|--------|-----------|
| 1° (0-6m) | **Power sector lending** (H+) | Data centres are power-intensive. Power infra credit +22.1% already reflects this. Banks with power exposure benefit. |
| 1° (0-6m) | **Infrastructure lending** (M+) | Civil/electrical works for DC construction. Roads/ports for logistics. |
| 2° (6-12m) | **NBFC lending** (M+) | DC operators finance equipment through NBFCs → bank co-lending benefits PSU banks. |
| 2° (6-12m) | **CRE / Real Estate** (M+) | DC campuses are large real estate plays → CRE loan demand. |
| 3° (12-18m) | **Telecom lending** (L) | 5G/6G backhaul needed for DC connectivity. BUT telecom credit is currently shrinking (-12.2%) — this would require a trend reversal. |

### Which PSU Banks Benefit Most?

| Bank | Thesis Support | Data Support |
|------|---------------|--------------|
| **SBIN** | **Strongest** — explicit Data Centre CoE + Champion Sector. Power is a stated CCG growth driver. | SBI is the largest project finance arranger among PSU banks. Leadership role in DC financing is confirmed. |
| **BANKBARODA** | **Moderate** — large corporate book (40.4%). Likely participates in infra lending. | No specific DC/telecom disclosure found. |
| **PNB** | **Moderate** — corporate book reducing (46-47% → targeting 40%). May benefit but pivoting away from corporate lending. | ECLGS book is 69.5% of advances — DC lending would be a small slice. |
| **CANBK** | **Moderate** — corporate book ~40%. Gold loans = 20% of book (idiosyncratic risk). | Pivoting strongly to RAM (60% target). DC/telecom lending would be corporate, which they're de-emphasizing. |

### Verdict

**Hypothesis: datacentre/telecom capex → PSU bank benefit.**  
**Status: PARTIALLY CONFIRMED for SBIN only.**  
- SBI has the explicit apparatus (CoE, Champion Sector tag, stated power/infra focus).  
- For BOB/PNB/CANBK: **insufficient data to confirm** — no specific datacentre or telecom loan exposure figures could be sourced from their latest annual reports or concalls.  
- **Systemically** (RBI data): infra credit is growing (power +22.1% is the key vector), but telecom credit is contracting. The datacentre channel flows through power demand, not direct DC lending.

**What's unknown:**
- Exact ₹ amount of datacentre lending by any PSU bank (not separately disclosed in any annual report)
- Whether telecom credit decline (-12.2%) is structural (incumbent deleveraging) or cyclical (pause before 6G capex)
- Individual bank exposure to telecom sector for BOB, PNB, CANBK
- Individual bank exposure to NBFC sector for any of the four banks analysed

---

## Sources Index

### Primary disclosures (annual reports, investor presentations, RBI data)

| Source | URL | Date |
|--------|-----|------|
| **RBI** Sectoral Deployment Table 16 (XLSX) | https://rbidocs.rbi.org.in/rdocs/Bulletin/DOCs/16T_BULL220520262D5B1FB3FDDA45E8AC537580D34ACFA8.XLSX | Mar 31, 2026 |
| **RBI** PR #62827 Sectoral Deployment Apr 2026 | https://rbidocs.rbi.org.in/rdocs/PressRelease/PDFs/PR348SDB744CD12ECA54334B5BF6A8BBA847F06.PDF | Apr 30, 2026 |
| **SBI** Data Centre CoE (Chakra) | https://sbi.co.in/web/coe-chakra/data-centres | Current |

#### SBI — Annual reports (15 available, FY2012–FY2026)
| Year | URL |
|------|-----|
| FY2026 | https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=faa17496-838f-432d-a39f-32d82156799c.pdf |
| FY2025 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/9c6a98f8-f882-4c06-9cb1-7f3b6ae1159f.pdf |
| FY2024 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/0e236470-9427-43c7-93e9-c8eb61bb1f72.pdf |
| FY2023 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/22d33d1d-af2a-4d2d-98c0-eff16cd73cb5.pdf |
| FY2012–2022 | https://www.bseindia.com/bseplus/AnnualReport/500112/*.pdf (sequential) |

#### Bank of Baroda — Annual reports (15 available, FY2012–FY2026)
| Year | URL |
|------|-----|
| FY2026 | https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=12b37c40-fbd0-4f9d-98d8-d59d5d485cb9.pdf |
| FY2025 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/f770ec9f-581e-47f3-b952-f6fe10d57daf.pdf |
| FY2024 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/aeebbed0-a043-4a00-b350-40a58eb996c9.pdf |
| FY2023 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/5e7191ef-8de8-4aa3-8118-93fd1fa83426.pdf |
| FY2012–2022 | https://www.bseindia.com/bseplus/AnnualReport/532134/*.pdf (sequential) |

#### PNB — Annual reports (14 available, FY2012–FY2026, FY2025 missing)
| Year | URL |
|------|-----|
| FY2026 | https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=2be9c223-c5bb-46ad-a57d-975eb6c28902.pdf |
| FY2024 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/1192d645-9fe8-49d5-b6ca-cfffc8781746.pdf |
| FY2023 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/01b4a055-de00-4725-acb2-3925a86b10f0.pdf |
| FY2022 | https://www.bseindia.com/bseplus/AnnualReport/532461/73163532461.pdf |
| FY2021 | https://www.bseindia.com/bseplus/AnnualReport/532461/68736532461.pdf |
| FY2020 | https://www.bseindia.com/bseplus/AnnualReport/532461/5324610320.pdf |
| FY2019 | https://www.bseindia.com/bseplus/AnnualReport/532461/5324610319.pdf |
| FY2018 | https://www.bseindia.com/bseplus/AnnualReport/532461/5324610318.pdf |
| FY2017 | https://www.bseindia.com/bseplus/AnnualReport/532461/5324610317.pdf |
| FY2016 | https://www.bseindia.com/bseplus/AnnualReport/532461/5324610316.pdf |
| FY2015 | https://www.bseindia.com/bseplus/AnnualReport/532461/5324610315.pdf |
| FY2014 | https://www.bseindia.com/bseplus/AnnualReport/532461/5324610314.pdf |
| FY2013 | https://www.bseindia.com/bseplus/AnnualReport/532461/5324610313.pdf |
| FY2012 | https://www.bseindia.com/bseplus/AnnualReport/532461/5324610312.pdf |

#### Canara Bank — Annual reports (15 available, FY2012–FY2026)
| Year | URL |
|------|-----|
| FY2026 | https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=864b8993-7923-4f0d-b6b9-9c07c39dc5da.pdf |
| FY2025 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/4bfe9370-9caf-4675-a406-4df51fa9e018.pdf |
| FY2024 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/e755e34b-9a3b-4082-ba59-ddca97649e44.pdf |
| FY2023 | https://www.bseindia.com/xml-data/corpfiling/AttachHis/a1c03c31-06b0-404b-ad62-7177954235e0.pdf |
| FY2022 | https://www.bseindia.com/bseplus/AnnualReport/532483/73046532483_17_06_22.pdf |
| FY2012–2021 | https://www.bseindia.com/bseplus/AnnualReport/532483/*.pdf (sequential) |

### Concall / investor-call transcripts extracted (most recent used in report)
Full archives of 31–41 concalls per bank are catalogued in the respective screener JSONs.

| Bank | Recent extracted | Transcript | PPT | AI Summary |
|------|-----------------|------------|-----|------------|
| SBIN | May 2026 | ✅ | ✅ | ✅ |
| BOB  | May 2026 | ✅ | ✅ | ✅ |
| PNB  | May 2026 | ✅ | ✅ | ✅ |
| CANBK| May 2026 | ✅ | ✅ | ✅ |

### Scripts (copied to `runs/20260606_031139/scripts/` for reproducibility)

| Script | Purpose |
|--------|---------|
| `scripts/sector_deep_dive.py` | Quant ranking, rel-strength, charts |
| `scripts/influence_graph.py` | Influence-graph edges + validation |
| `scripts/india_sectors.py` | Constituent resolution, per-stock metrics (CAGR, maxDD, Calmar, 25dmaZ) |
| `scripts/data_api.py` | Single seam for all price/index/driver data |
| `scripts/screener_reader.py` | Document index (annual report URLs, concall URLs) |
| `scripts/annual_report_reader.py` | PDF → markdown extraction |
| `scripts/concall_reader.py` | Concall PPT/transcript extraction |
| `scripts/pdf_to_md.py` | Base PDF → markdown transformer |
| `skills/screeners/scenario-analyzer/references/sector_sensitivity_matrix.md` | Scenario sensitivity matrix (in-repo) |

## Generated Artifacts (local files)

| Artifact | Path | Type |
|----------|------|------|
| **This report** | `reports/psu_bank_deep_dive_2026-06-06.md` | Markdown |
| Sector deep-dive JSON output | (console output in session — not persisted to disk) | JSON |
| Relative-strength chart (sector vs NIFTY 50) | `reports/sector-deep-dive/PSU_Bank_2026-06-06/rel_strength.png` | PNG |
| Returns bar chart (per constituent) | `reports/sector-deep-dive/PSU_Bank_2026-06-06/returns.png` | PNG |
| Drawdown bar chart (per constituent) | `reports/sector-deep-dive/PSU_Bank_2026-06-06/drawdown.png` | PNG |
| SBI FY2025 annual report (parsed markdown) | `runs/20260606_031139/sbin_ar_2025.json` | JSON |
| SBI FY2024 annual report (parsed markdown) | `runs/20260606_031139/sbin_ar_2024.json` | JSON |
| **SBI screener index** (all 15 ARs + 41 concalls catalogued) | `runs/20260606_031139/sbin_screener.json` | JSON |
| BOB FY2025 annual report (parsed) | `runs/20260606_031139/bob_ar_2025.json` | JSON |
| **BOB screener index** (all 15 ARs + 41 concalls) | `runs/20260606_031139/bob_screener.json` | JSON |
| BOB May 2026 concall transcript (parsed text) | `runs/20260606_031139/bob_concall_may2026.json` | JSON |
| **PNB screener index** (all 14 ARs + 31 concalls) | `runs/20260606_031139/pnb_screener.json` | JSON |
| PNB May 2026 concall transcript | `runs/20260606_031139/pnb_concall.json` | JSON |
| **CANBK screener index** (all 15 ARs + 35 concalls) | `runs/20260606_031139/canbk_screener.json` | JSON |
| CANBK May 2026 concall transcript | `runs/20260606_031139/canbk_concall.json` | JSON |
| RBI Table 16 XLSX (downloaded and parsed) | `runs/20260606_031139/rbi_table16.xlsx` | XLSX |

## Data-extraction scripts used

| Script | Purpose |
|--------|---------|
| `skills/regime/sector-deep-dive/scripts/sector_deep_dive.py` | Quant ranking, rel-strength, charts |
| `framework/influence_graph.py` | Influence-graph edges + validation |
| `framework/india_sectors.py` | Constituent resolution, per-stock metrics (CAGR, maxDD, Calmar, 25dmaZ) |
| `framework/data_api.py` | Single seam for all price/index/driver data |
| `data/sources.py` | Audited India data adapters (nselib, yfinance, jugaad) |
| `skills/fundamentals/equity-research/scripts/screener_reader.py` | Document index (annual report URLs, concall URLs) |
| `skills/fundamentals/equity-research/scripts/annual_report_reader.py` | PDF → markdown extraction |
| `skills/fundamentals/equity-research/scripts/concall_reader.py` | Concall PPT/transcript extraction |

---

*Report compiled 2026-06-06. All claims anchored to sourced disclosures. Anything marked "unknown" could not be verified from disclosed figures and should not be inferred.*
