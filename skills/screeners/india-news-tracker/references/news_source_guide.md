# Indian Financial News Source Guide

## Source Reliability & Speed Matrix

| Source | Reliability | Speed | Bias | Best For |
|--------|------------|-------|------|----------|
| BSE India (bseindia.com) | ★★★★★ | Medium | None (official) | Corporate filings, results, announcements |
| NSE India (nseindia.com) | ★★★★★ | Medium | None (official) | Bulk/block deals, F&O data, circulars |
| SEBI (sebi.gov.in) | ★★★★★ | Slow | None (regulatory) | Regulations, enforcement, circulars |
| RBI (rbi.org.in) | ★★★★★ | Slow | None (regulatory) | Monetary policy, banking norms, forex |
| MoneyControl | ★★★★ | Fast | Slight bullish | Breaking news, earnings, market updates |
| Economic Times | ★★★★ | Fast | Neutral | Corporate news, policy, deep dives |
| LiveMint | ★★★★ | Medium | Neutral | Premium analysis, policy, macro |
| Business Standard | ★★★★ | Medium | Neutral | Corporate, banking, policy |
| NDTV Profit | ★★★ | Fast | Neutral | Quick market updates, interviews |
| Trendlyne | ★★★★ | Medium | Data-driven | Bulk deals, technicals, earnings calendar |
| Screener.in | ★★★★ | Slow | Data-driven | Financials, screening, results |
| Financial Express | ★★★ | Medium | Neutral | Economy, policy, regulation |
| Reuters India | ★★★★★ | Fast | Neutral | Global macro, major corporate events |
| Bloomberg Quint | ★★★★ | Fast | Neutral | Premium analysis, global context |

## Optimal Search Patterns

### Breaking News (Last 24 hours)
```
"Indian stock market news today"
"NSE BSE market update [date]"
"site:moneycontrol.com markets today"
"site:economictimes.indiatimes.com stock market [date]"
```

### Company-Specific News
```
"[Company Name] NSE stock news [month] [year]"
"site:moneycontrol.com [Company Name]"
"site:bseindia.com [BSE Code] announcement"
"[Company Name] quarterly results [quarter] FY[year]"
"[Company Name] board meeting outcome"
```

### Sector News
```
"[Sector] sector India stock market [month] [year]"
"Nifty [Sector Index] news analysis"
"[Sector] policy regulation India [year]"
```

### Regulatory Updates
```
"SEBI circular [month] [year]"
"SEBI new regulation [year]"
"RBI monetary policy [month] [year]"
"RBI circular banking [year]"
```

### Institutional Activity
```
"FII DII data [date] NSE"
"bulk deals NSE today [date]"
"block deals BSE today [date]"
"promoter buying selling [month] [year]"
"mutual fund portfolio changes [quarter] [year]"
```

### Earnings & Results
```
"quarterly results schedule NSE [month] [year]"
"[Company] Q[x] FY[xx] results"
"earnings surprise India [quarter] [year]"
"results calendar upcoming NSE BSE"
```

### IPO News
```
"upcoming IPO India [month] [year]"
"IPO subscription status [company]"
"IPO listing price [company]"
"DRHP filing SEBI [year]"
```

### Corporate Actions
```
"dividend ex-date NSE [month] [year]"
"stock split bonus issue NSE [year]"
"buyback offer India [year]"
"rights issue NSE [year]"
```

## Source-Specific Parsing Notes

### MoneyControl
- URL pattern: `moneycontrol.com/news/business/markets/`
- Earnings URL: `moneycontrol.com/news/business/earnings/`
- Has dedicated earnings calendar section
- Flash news updates are usually reliable and fast
- Best for: Real-time market commentary, earnings analysis

### Economic Times Markets
- URL pattern: `economictimes.indiatimes.com/markets/stocks/`
- Has good ETF and MF coverage
- Policy analysis is particularly strong
- Best for: Deep corporate stories, policy impact analysis

### BSE India Filings
- URL pattern: `bseindia.com/corporates/ann.html`
- Search by scrip code or company name
- Categories: Board Meeting, Financial Results, Corporate Action, Shareholding
- Best for: Official corporate announcements (primary source of truth)

### NSE India
- Bulk deals: `nseindia.com/market-data/bulk-deal-data`
- Block deals: `nseindia.com/market-data/block-deal-data`
- Insider trades: `nseindia.com/companies-listing/corporate-filings-insider-trading`
- F&O ban: `nseindia.com/market-data/fno-ban`
- Best for: Official market data, institutional activity

### Trendlyne
- URL pattern: `trendlyne.com/stock-deals/`
- Has excellent bulk/block deal aggregation
- Earnings calendar with estimates
- Best for: Data-driven news, aggregated institutional activity

## Handling Conflicting Reports

When different sources report conflicting information:

1. **Prioritize official sources** (BSE/NSE filings > media reports)
2. **Check the timestamp** — newer information may supersede older
3. **Verify with 2+ independent sources** before treating as confirmed
4. **Label unconfirmed news** clearly: "Reports suggest..." or "According to [source]..."
5. **Flag rumor vs confirmed**: Clearly distinguish between market rumors and official announcements

## Common Misinformation Patterns

Watch out for:
- **Pump-and-dump social media posts** — verify any "breaking news" from X/Twitter against official sources
- **Misquoted earnings numbers** — always verify against BSE/NSE filing
- **Outdated news recycled** — check dates carefully, especially for regulatory changes
- **Promotional "news"** — some outlets publish sponsored content as news
- **Analyst estimates presented as results** — distinguish between expected and actual numbers

## News Timing Context

| Timing | Impact Pattern |
|--------|---------------|
| **Pre-market (before 9:15 AM)** | Creates gap up/down at open, look for global cues |
| **During market (9:15-3:30)** | Immediate price reaction, watch volume spike |
| **Post-market (after 3:30 PM)** | Impact priced in next day's open |
| **Weekend/Holiday** | Accumulates for Monday/post-holiday opening |
| **After F&O expiry** | May have outsized impact in next series |
| **Before results** | Rumor-driven, verify after official announcement |
