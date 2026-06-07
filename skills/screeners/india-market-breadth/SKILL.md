---
name: india-market-breadth
description: >
  Analyze Indian market breadth health using advance/decline data, stocks above moving averages,
  new highs/lows, and sector participation. Use when assessing rally quality, market participation
  width, or equity exposure levels for NSE/BSE.
---

# India Market Breadth Analyzer

## Purpose

Market breadth measures how broadly a rally or decline is distributed across the market. A healthy market has broad participation — many stocks and sectors moving in the same direction. A narrow market, where only a few large-cap stocks are driving the index, is fragile and prone to reversal.

This skill provides a systematic framework to assess NSE/BSE breadth health, score it on a 0-100 composite scale, and translate it into actionable equity exposure recommendations.

---

## Data Sources

> **Breadth is COMPUTED from constituent OHLCV via the seam — no WebSearch, no broker MCP, no
> keys.** `data_api.breadth()` (see `data/breadth.py`) returns advancers/decliners, A/D line,
> %>50/200-DMA, and new 52w highs/lows over our tracked constituent universe (~200 names across
> the 11 sector indices, with a 200-DMA warm-up so every value is valid). All numbers are
> `provenance="computed"`. WebSearch is allowed ONLY for event context (Step: Budget/RBI weeks).

```python
from framework import data_api as api, indicators as ind

# Breadth internals (Steps 1, 3, 4) — broad market = "NIFTY 50" universe (tracked constituents)
b = api.breadth("NIFTY 50", since="2023-01-01")     # cols: pct_above_50, pct_above_200,
                                                    # advancers, decliners, ad_line,
                                                    # new_highs, new_lows, n
latest = b.iloc[-1]
ad_ratio = latest["advancers"] / max(latest["decliners"], 1)

# Nifty level for divergence (Step 5, component 5)
nifty = api.index("NIFTY 50", since="2023-01-01")

# Sector participation (component 4): how many of the 11 sector indices are above their 50-DMA
sectors = ["NIFTY BANK","NIFTY IT","NIFTY PHARMA","NIFTY FMCG","NIFTY AUTO","NIFTY METAL",
           "NIFTY REALTY","NIFTY ENERGY","NIFTY INFRASTRUCTURE","NIFTY PSU BANK","NIFTY PRIVATE BANK"]
in_uptrend = sum(1 for s in sectors
                 if (lambda d: d["close"] > (d["sma_50"] or 1e9))(ind.indicator_snapshot(api.index(s, since="2023-06-01"))))
```

| Data point | Seam source |
|------------|-------------|
| Advance/Decline counts + A/D line | `breadth(...)` -> `advancers`, `decliners`, `ad_line` |
| % above 50 / 200 DMA | `breadth(...)` -> `pct_above_50`, `pct_above_200` |
| New 52-week highs / lows | `breadth(...)` -> `new_highs`, `new_lows` |
| Sector participation (13->11 tracked) | loop `index(sector)` + `indicators.indicator_snapshot` (above 50-DMA) |
| Nifty 50 level (divergence) | `index("NIFTY 50", since)` |
| McClellan oscillator | `indicators.ema` of `(advancers - decliners)` (19 vs 39) from `breadth(...)` |

> Note: our breadth universe is the ~200 tracked constituents across 11 sector indices, not the
> full NSE 500 — state this in the report. Nifty Media / exact NSE A/D totals are not in the
> tracked set (a known scope limit; do NOT WebSearch-substitute the counts).

---

## Workflow

### Step 1: Fetch Advance/Decline Data

From `b = api.breadth("NIFTY 50", since=...)` (above): `advancers`, `decliners`, and `ad_line`
columns over the tracked universe. Use the latest row for today's counts and the series for
trend. (`n` = members with data that day.) Do NOT WebSearch the counts.

### Step 2: Calculate Breadth Indicators

#### A/D Ratio
```
A/D Ratio = Number of Advances / Number of Declines

Interpretation:
  > 2.0:  Strong breadth (broad rally)
  1.5-2.0: Healthy breadth
  1.0-1.5: Neutral
  0.7-1.0: Weak breadth
  < 0.7:  Very weak (broad selling)
```

#### A/D Line (Cumulative)
```
A/D Line = Previous A/D Line + (Advances - Declines)

Rising A/D Line + Rising Nifty = Confirmed uptrend
Falling A/D Line + Rising Nifty = DIVERGENCE (warning)
Rising A/D Line + Falling Nifty = Accumulation (bullish)
Falling A/D Line + Falling Nifty = Confirmed downtrend
```

#### McClellan Oscillator Concept
```
A/D Difference = Advances - Declines
19-day EMA of A/D Difference (fast)
39-day EMA of A/D Difference (slow)
McClellan Oscillator = 19-day EMA - 39-day EMA

> 0:  Bullish breadth momentum
< 0:  Bearish breadth momentum
> +50: Overbought breadth
< -50: Oversold breadth
```

### Step 3: Assess % of Stocks Above 200 DMA and 50 DMA

From `b["pct_above_200"]` and `b["pct_above_50"]` (latest row + trend) — computed across the
tracked universe with a proper 200-DMA warm-up. No WebSearch/screener estimate needed.

#### Key Thresholds

| Metric | Bullish | Neutral | Bearish |
|--------|---------|---------|---------|
| % above 200 DMA | > 60% | 40-60% | < 40% |
| % above 50 DMA | > 55% | 35-55% | < 35% |
| % above 20 DMA | > 50% | 30-50% | < 30% |

### Step 4: Count New 52-Week Highs vs Lows

From `b["new_highs"]` and `b["new_lows"]` (latest row) — counted across the tracked universe
on a 252-day window. No broker MCP needed.

#### Interpretation

| Highs:Lows Ratio | Signal |
|-------------------|--------|
| > 5:1 | Strong bullish breadth |
| 2:1 to 5:1 | Healthy bullish breadth |
| 1:1 to 2:1 | Neutral / transitioning |
| 0.5:1 to 1:1 | Bearish breadth |
| < 0.5:1 | Strong bearish breadth |

### Step 5: Score Breadth Health (0-100 Composite)

The composite score is calculated from 5 components:

| # | Component | Weight | Max Points | Source |
|---|-----------|--------|------------|--------|
| 1 | Advance/Decline Ratio | 25% | 25 | NSE A/D data |
| 2 | Stocks Above 200 DMA | 25% | 25 | Screener data |
| 3 | New Highs vs Lows | 20% | 20 | Groww MCP YEARLY_HIGH/LOW |
| 4 | Sector Participation | 15% | 15 | Sector index performance |
| 5 | Nifty Divergence | 15% | 15 | Nifty vs breadth comparison |

#### Component 1: Advance/Decline Ratio Score (0-25)

| A/D Ratio | Score |
|-----------|-------|
| > 3.0 | 25 |
| 2.5 - 3.0 | 22-25 |
| 2.0 - 2.5 | 19-22 |
| 1.5 - 2.0 | 15-19 |
| 1.2 - 1.5 | 12-15 |
| 1.0 - 1.2 | 8-12 |
| 0.7 - 1.0 | 4-8 |
| 0.5 - 0.7 | 2-4 |
| < 0.5 | 0-2 |

Also consider the 5-day and 20-day trend of A/D ratio:
- Improving trend: +2 bonus points
- Deteriorating trend: -2 penalty points

#### Component 2: Stocks Above 200 DMA Score (0-25)

| % Above 200 DMA | Score |
|------------------|-------|
| > 75% | 25 |
| 65-75% | 21-25 |
| 55-65% | 17-21 |
| 45-55% | 13-17 |
| 35-45% | 9-13 |
| 25-35% | 5-9 |
| < 25% | 0-5 |

#### Component 3: New Highs vs Lows Score (0-20)

| Highs:Lows Ratio | Score |
|-------------------|-------|
| > 5:1 | 20 |
| 3:1 - 5:1 | 16-20 |
| 2:1 - 3:1 | 12-16 |
| 1:1 - 2:1 | 8-12 |
| 0.5:1 - 1:1 | 4-8 |
| < 0.5:1 | 0-4 |

#### Component 4: Sector Participation Score (0-15)

Count how many of the 13 major Nifty sectors are in an uptrend (above their 50 DMA or showing positive 1-month return):

**13 Key NSE Sectors:**
1. Nifty Bank
2. Nifty IT
3. Nifty Pharma
4. Nifty FMCG
5. Nifty Auto
6. Nifty Metal
7. Nifty Realty
8. Nifty Energy
9. Nifty Infrastructure
10. Nifty PSU Bank
11. Nifty Private Bank
12. Nifty Media
13. Nifty Financial Services

| Sectors in Uptrend | Score |
|--------------------|-------|
| 11-13 | 15 |
| 9-10 | 12-14 |
| 7-8 | 9-11 |
| 5-6 | 6-8 |
| 3-4 | 3-5 |
| 0-2 | 0-2 |

#### Component 5: Nifty Divergence Score (0-15)

This measures whether index performance aligns with underlying breadth.

| Scenario | Score |
|----------|-------|
| Nifty rising + breadth improving | 15 (confirmed uptrend) |
| Nifty flat + breadth improving | 13 (stealth accumulation) |
| Nifty rising + breadth flat | 10 (narrow rally, watch closely) |
| Nifty flat + breadth flat | 8 (neutral, no signal) |
| Nifty flat + breadth declining | 5 (stealth distribution) |
| Nifty rising + breadth declining | 3 (BEARISH DIVERGENCE — high risk) |
| Nifty falling + breadth declining | 2 (confirmed downtrend) |
| Nifty falling + breadth improving | 7 (possible bottom formation) |

### Step 6: Map to Equity Exposure Recommendation

#### Health Zones

| Score Range | Zone | Equity Exposure | Action |
|-------------|------|----------------|--------|
| **80-100** | Strong | 90-100% | Full equity allocation. Market has broad participation. Deploy fresh capital. |
| **60-79** | Healthy | 75-90% | Normal allocation. Monitor for deterioration. Favor broad-based positions. |
| **40-59** | Neutral | 60-75% | Cautious allocation. Focus on strong sectors only. Reduce mid/small-cap exposure. |
| **20-39** | Weakening | 40-60% | Defensive allocation. Shift to large-caps and quality. Raise cash on rallies. |
| **0-19** | Critical | 25-40% | Maximum defense. High cash/debt allocation. Only hold strongest positions. Potential capitulation zone. |

#### Exposure Adjustment Rules

1. **Score improving for 5+ days:** Can increase exposure by one zone level
2. **Score deteriorating for 5+ days:** Decrease exposure by one zone level
3. **Score drops >15 points in a week:** Emergency review — consider reducing exposure immediately
4. **Score rises >15 points in a week:** Wait for confirmation (3+ days) before increasing

### Step 7: Generate Report

Use the template from `assets/breadth_report_template.md` to produce a structured report. Include:

1. Composite score and health zone
2. All 5 component scores with supporting data
3. Trend direction (improving/deteriorating)
4. Equity exposure recommendation
5. Divergence analysis
6. Historical context
7. Disclaimer

---

## Quick Reference: NSE Sector Indices

Use these symbols with `get_ltp` for sector breadth assessment:

| Sector | Symbol | Approx Constituents |
|--------|--------|-------------------|
| Bank Nifty | NIFTY BANK | 12 banks |
| Nifty IT | NIFTY IT | 10 IT companies |
| Nifty Pharma | NIFTY PHARMA | 20 pharma companies |
| Nifty FMCG | NIFTY FMCG | 15 FMCG companies |
| Nifty Auto | NIFTY AUTO | 15 auto companies |
| Nifty Metal | NIFTY METAL | 15 metal companies |
| Nifty Realty | NIFTY REALTY | 10 realty companies |
| Nifty Energy | NIFTY ENERGY | 10 energy companies |
| Nifty Infra | NIFTY INFRA | 30 infra companies |
| Nifty PSU Bank | NIFTY PSU BANK | 12 PSU banks |
| Nifty Pvt Bank | NIFTY PVT BANK | 10 private banks |
| Nifty Media | NIFTY MEDIA | 14 media companies |
| Nifty Fin Service | NIFTY FIN SERVICE | 20 financial companies |

---

## Example Breadth Assessment

```
Date: 2025-03-10

COMPONENT SCORES:
  1. A/D Ratio: 1.8 (5-day avg: 1.5)          -> Score: 17/25
  2. Stocks above 200 DMA: ~55%                 -> Score: 17/25
  3. New Highs:Lows: 85:25 (3.4:1)             -> Score: 16/20
  4. Sectors in uptrend: 9/13                   -> Score: 12/15
  5. Nifty rising + breadth flat                -> Score: 10/15

  COMPOSITE SCORE: 72/100
  HEALTH ZONE: Healthy
  EQUITY EXPOSURE: 75-90%

RECOMMENDATION:
  Market breadth is healthy with broad participation. 9 of 13 sectors are
  in uptrend. A/D ratio has been above 1.0 for the past week. However,
  Nifty is making new highs while breadth is flat — watch for divergence.
  Maintain normal equity allocation but be ready to reduce if breadth
  starts deteriorating.
```

---

## Divergence Detection — The Most Important Signal

### What is Breadth Divergence?

When the Nifty 50 makes a new high but breadth indicators do not confirm, it signals that the rally is narrowing. This is the single most important breadth signal for risk management.

### How to Detect

1. **Nifty at 52-week high BUT** advance/decline ratio < 1.5
2. **Nifty at 52-week high BUT** fewer new 52-week highs than at the previous Nifty high
3. **Nifty at 52-week high BUT** % above 200 DMA is declining
4. **Nifty at 52-week high BUT** fewer sectors participating than at previous high

### Historical Examples (Indian Market)

| Date | Nifty Level | Breadth Signal | What Happened |
|------|-------------|---------------|---------------|
| Oct 2021 | All-time high (18,600) | Midcap/smallcap already correcting | Nifty corrected 15% by Jun 2022 |
| Jan 2018 | All-time high (11,170) | Only large-caps rallying, midcaps weak | Midcap/smallcap correction of 30-40% through 2018 |
| Jan 2008 | All-time high (21,200, Sensex) | Breadth divergence from Sep 2007 | Market crashed 60% by Oct 2008 |

### Action on Divergence

| Divergence Duration | Action |
|--------------------|--------|
| 1-3 days | Monitor — could be noise |
| 1-2 weeks | Start tightening stops, reduce weakest positions |
| 3-4 weeks | Reduce overall exposure by one zone level |
| 1+ month | Significant risk — move to defensive posture |

---

## India-Specific Nuances

- **F&O Expiry Effects:** Weekly and monthly F&O expiry Thursdays can distort breadth readings due to derivatives-related hedging and unwinding. Flag expiry-day breadth readings and consider using the non-expiry-day average for comparison.
- **Budget and RBI Policy Weeks:** Union Budget day and RBI monetary policy announcement days create abnormal breadth swings. Note these as event-driven rather than trend-driven.
- **FII/DII Flow Correlation:** Sustained FII selling often narrows breadth from the large-cap end first, while DII buying may support mid/small caps, creating a cap-tier divergence.
- **SEBI Regulatory Impact:** Regulations like small-cap mutual fund stress tests can cause episodic breadth disruptions in the small-cap tier — these are flow-driven, not fundamental.
- **IPO Market as Breadth Proxy:** A hot IPO market (high subscription rates, listing gains) often correlates with broad market risk appetite. A freeze in IPO activity can signal breadth contraction ahead.

---

## Files in This Skill

- `references/breadth_methodology.md` — Comprehensive breadth analysis methodology for Indian markets
- `assets/breadth_report_template.md` — Structured report template for breadth analysis output
