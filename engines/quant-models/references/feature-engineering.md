# Feature Engineering for Stock Prediction

Build predictive feature matrices for any sector. Features encode domain knowledge about what drives returns — they differ by sector but follow a common structure.

## Installation

```bash
uv pip install yfinance pandas numpy scipy scikit-learn matplotlib requests
```

## The Framework

Every stock prediction task uses 6 feature categories. The first 3 are universal. The last 3 are domain-specific — you must select them based on what drives the sector.

```
UNIVERSAL (same for any stock)
├── Technical     — price-derived (momentum, volatility, RSI, Bollinger)
├── Cross-Asset   — correlated instruments (sector index, commodities, VIX, currency)
├── Macro         — global regime (VIX level, interest rates, currency trend)

DOMAIN-SPECIFIC (changes per sector)
├── External Signals  — the real-world events that move this sector
├── Seasonal          — calendar effects specific to this sector
├── Interaction       — signal × price crosses (domain × technical)
```

## Feature Categories

### 1. Technical (Universal)

Always include. These capture price dynamics regardless of sector.

```python
ret = close.pct_change()

# Momentum (multiple horizons)
feat["ret_1d"] = ret
feat["ret_5d"] = close.pct_change(5)
feat["ret_20d"] = close.pct_change(20)
feat["ret_60d"] = close.pct_change(60)

# Moving average position
ma20, ma50, ma200 = close.rolling(20).mean(), close.rolling(50).mean(), close.rolling(200).mean()
feat["price_vs_ma20"] = close / ma20 - 1
feat["price_vs_ma50"] = close / ma50 - 1
feat["price_vs_ma200"] = close / ma200 - 1
feat["golden_cross"] = (ma50 > ma200).astype(int)

# Volatility
feat["vol_10d"] = ret.rolling(10).std() * np.sqrt(252)
feat["vol_30d"] = ret.rolling(30).std() * np.sqrt(252)
feat["vol_ratio"] = feat["vol_10d"] / (feat["vol_30d"] + 1e-10)  # expansion/contraction

# RSI
delta = ret.copy()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
feat["rsi_14"] = 100 - (100 / (1 + gain / (loss + 1e-10)))

# Bollinger position
bb_mid = close.rolling(20).mean()
bb_std = close.rolling(20).std()
feat["bb_position"] = (close - bb_mid) / (2 * bb_std + 1e-10)

# Drawdown
feat["drawdown"] = (close - close.cummax()) / close.cummax()

# Volume (if available)
if vol is not None:
    vol_ma20 = vol.rolling(20).mean()
    feat["vol_ratio_price"] = vol / (vol_ma20 + 1)
    feat["vol_spike"] = (vol > vol_ma20 * 2).astype(int)
```

### 2. Cross-Asset (Sector-Specific Selection)

Pick the instruments that actually move your sector. Fetch with yfinance, align dates, compute returns.

```python
# Example: fetch and align a cross-asset
proxy = yf.download(ticker, start=START, end=END, progress=False)["Close"]
proxy = proxy.reindex(close.index, method="ffill")
feat[f"{name}_ret_5d"] = proxy.pct_change(5)
feat[f"{name}_ret_20d"] = proxy.pct_change(20)
```

**Cross-asset selection by sector:**

| Sector | Key Cross-Assets |
|--------|-----------------|
| Mining | Gold, Copper, Iron Ore, Nifty Metal, USD/INR, VIX |
| Auto | Steel prices, Nifty Auto, Crude Oil, USD/INR, auto loan rates |
| IT Services | NASDAQ, USD/INR (revenue in $), Nifty IT |
| Banking | Bond yields (10Y), Nifty Bank, Gold (inverse), RBI repo rate |
| Pharma | USD/INR (export revenue), Nifty Pharma, FDA approval news flow |
| FMCG | Rural demand proxies, monsoon rainfall (agri income), Nifty FMCG |
| Real Estate | Home loan rates, cement/steel prices, DLF/Godrej relative |
| Energy | Crude Oil, Natural Gas, USD/INR, OPEC output |

Always include:
- **VIX** (`^VIX`) — global risk regime
- **USD/INR** (`USDINR=X`) — for any Indian stock
- **Nifty 50** (`^NSEI`) — broad market
- **Sector index** — relative strength vs sector

### 3. External Signals (Domain-Specific)

This is where domain knowledge matters most. These are the real-world events that create edge.

**Mining:**
```python
# Rainfall in mining regions (Open-Meteo API)
feat["rain_30d"]              # 30-day cumulative rainfall
feat["heavy_rain_days_30d"]   # days with >20mm
feat["rain_anomaly"]          # deviation from 60-day rolling mean
# Earthquakes near mines (USGS API) — low predictive power but included for completeness
feat["eq_count_30d"]
feat["eq_energy_30d"]
```

**Auto Manufacturing:**
```python
# Steel/input costs (proxy via yfinance commodity tickers)
feat["steel_price_change_30d"]
# Fuel prices (EIA API or crude oil proxy)
feat["crude_ret_20d"]
# Monthly auto sales data (SIAM, if available)
feat["monthly_sales_yoy"]
# Showroom footfall proxy: rainfall in top-10 cities
feat["urban_rain_7d"]
```

**IT Services:**
```python
# US tech hiring/layoffs (proxy: NASDAQ trend)
feat["nasdaq_ret_20d"]
# USD strength (direct revenue impact)
feat["usd_inr_change_20d"]
# US GDP/PMI (quarterly, forward-fill)
feat["us_pmi"]
```

**Banking:**
```python
# Yield curve (10Y - 2Y spread)
feat["yield_spread"]
# RBI policy rate changes (manual or API)
feat["rate_hike_flag"]
# NPA/credit growth (quarterly, forward-fill)
feat["credit_growth_yoy"]
# Gold price (inverse relationship — savings shift)
feat["gold_ret_20d"]
```

**Energy (Oil & Gas):**
```python
# Crude oil price and inventory (EIA API)
feat["crude_ret_5d"]
feat["crude_inventory_change"]
# OPEC output decisions (event flags)
feat["opec_cut_flag"]
# Natural gas prices
feat["natgas_ret_20d"]
# Refining margins (crack spread proxy)
feat["crack_spread"]
```

### 4. Seasonal Features

Calendar effects that are specific to the sector's demand/supply cycle.

```python
# Universal
feat["month"] = close.index.month
feat["day_of_week"] = close.index.dayofweek
feat["is_monday"] = (close.index.dayofweek == 0).astype(int)
feat["is_friday"] = (close.index.dayofweek == 4).astype(int)
feat["is_fiscal_yearend"] = close.index.month.isin([3]).astype(int)
```

**Sector-specific seasonal:**

| Sector | Key Seasons |
|--------|------------|
| Mining | Monsoon (Jun-Sep) = operational disruption. Pre-monsoon accumulation. |
| Auto | Festive season (Oct-Nov) = peak sales. Jan = budget expectations. |
| IT | Q4 (Jan-Mar) = US budget flush, deal closures. Q1 = visa season. |
| Banking | Q4 = NPA provisioning. Rate decision months. |
| FMCG | Monsoon = rural income (good monsoon → demand). Festive season. |
| Real Estate | Post-monsoon (Oct-Dec) = auspicious buying season. Budget month. |

### 5. Interaction Features

Cross domain signals with price features. These capture "does the external signal matter more when the stock is already stressed?"

```python
# Signal × momentum
feat["rain_x_momentum"] = feat["rain_30d"] * feat["ret_20d"]

# Signal × volatility
feat["rain_x_vol"] = feat["rain_30d"] * feat["vol_30d"]

# Signal × season
feat["rain_x_monsoon"] = feat["rain_30d"] * feat["is_monsoon"]

# Cross-asset × momentum
feat["gold_x_momentum"] = feat["Gold_ret_5d"] * feat["ret_5d"]
```

## Validation: Walk-Forward + Ablation

Never use random train/test split for time series. Always walk-forward.

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

# Target: 5-day forward return direction
feat["fwd_5d_ret"] = close.shift(-5) / close - 1
feat["target"] = (feat["fwd_5d_ret"] > 0).astype(int)

# Walk-forward: train on first 70%, test on last 30%
split = int(len(feat) * 0.7)
X = StandardScaler().fit_transform(feat[feature_cols].values)
y = feat["target"].values

gb = GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.05,
                                 min_samples_leaf=20, random_state=42)
gb.fit(X[:split], y[:split])
auc = roc_auc_score(y[split:], gb.predict_proba(X[split:])[:, 1])
```

### Ablation Study

Test which feature categories actually contribute by dropping each one and measuring AUC change.

```python
CATEGORIES = {
    "EXTERNAL": lambda c: c.startswith("rain") or c.startswith("eq_"),
    "TECHNICAL": lambda c: c.startswith("ret_") or c.startswith("vol_") or c.startswith("rsi"),
    "CROSS_ASSET": lambda c: c.startswith("Gold") or c.startswith("VIX"),
    "SEASONAL": lambda c: c.startswith("is_") or c.startswith("monsoon"),
}

for cat_name, cat_filter in CATEGORIES.items():
    remaining = [c for c in feature_cols if not cat_filter(c)]
    X_abl = StandardScaler().fit_transform(feat[remaining].values)
    gb_abl = GradientBoostingClassifier(n_estimators=200, max_depth=3,
                                         learning_rate=0.05, min_samples_leaf=20, random_state=42)
    gb_abl.fit(X_abl[:split], y[:split])
    abl_auc = roc_auc_score(y[split:], gb_abl.predict_proba(X_abl[split:])[:, 1])
    print(f"Drop {cat_name}: AUC {abl_auc:.3f} (delta: {abl_auc - auc:+.3f})")
```

If dropping a category doesn't hurt AUC, those features aren't contributing. Remove them.

### Permutation Importance

More reliable than model-native feature importance.

```python
from sklearn.inspection import permutation_importance

perm = permutation_importance(gb, X[split:], y[split:], n_repeats=20, random_state=42)
imp_df = pd.DataFrame({
    "feature": feature_cols,
    "importance": perm.importances_mean,
}).sort_values("importance", ascending=False)
print(imp_df.head(20))
```

## Output: Tiered Feature Spec

After ablation+importance analysis, produce a tiered spec:

```json
{
  "tier1_always_include": ["ret_5d", "ret_20d", "price_vs_ma50", "vol_ratio", "rsi_14", "Gold_ret_5d"],
  "tier2_adds_lift": ["rain_30d", "heavy_rain_days_30d", "is_monsoon", "VIX_level"],
  "tier3_marginal": ["eq_count_30d", "is_monday", "rain_x_monsoon"]
}
```

Save to `output/<analysis_name>/feature_spec.json` for reuse.

## Advanced Features: Model Outputs as Inputs

The basic 6 categories above use raw data. The next level: **use model outputs as features** for a downstream model. This is where quant-models skill outputs feed back into feature engineering.

### 6. Model-Derived Features

#### HMM Regime State

Use regime detection output as a categorical feature or to condition other features.

```python
from hmmlearn.hmm import GaussianHMM

returns = close.pct_change().dropna().values.reshape(-1, 1)
model = GaussianHMM(n_components=3, covariance_type="full", n_iter=200)
model.fit(returns)
regimes = model.predict(returns)

# Sort by mean return → 0=bear, 1=sideways, 2=bull
means = model.means_.flatten()
order = np.argsort(means)
regime_map = {order[0]: 0, order[1]: 1, order[2]: 2}

feat["hmm_regime"] = pd.Series([regime_map[r] for r in regimes], index=close.index[1:])
feat["is_bull_regime"] = (feat["hmm_regime"] == 2).astype(int)
feat["is_bear_regime"] = (feat["hmm_regime"] == 0).astype(int)

# Regime transition probability (from current state)
trans = model.transmat_
feat["regime_persistence"] = pd.Series(
    [trans[r, r] for r in regimes], index=close.index[1:]
)
```

#### GARCH Forecast Volatility

Use conditional volatility and volatility surprises as features.

```python
from arch import arch_model

ret_pct = close.pct_change().dropna() * 100
am = arch_model(ret_pct, vol="Garch", p=1, q=1, dist="studentst")
res = am.fit(disp="off")

feat["garch_cond_vol"] = res.conditional_volatility
feat["garch_vol_percentile"] = feat["garch_cond_vol"].rolling(252).apply(
    lambda x: stats.percentileofscore(x, x.iloc[-1]) / 100
)
# Volatility surprise: realized vs predicted
feat["vol_surprise"] = ret_pct.abs() - res.conditional_volatility
# Persistence — high alpha+beta = slow vol decay
persistence = res.params['alpha[1]'] + res.params['beta[1]']
feat["garch_persistence"] = persistence  # Constant, but useful in multi-stock models
```

#### Kalman Filter Dynamic Beta

Track time-varying sensitivity to any factor.

```python
from pykalman import KalmanFilter

# y = stock return, X = factor (e.g., rainfall)
y = close.pct_change().dropna().values.reshape(-1, 1)
X_factor = rain_30d.reindex(close.index[1:]).values.reshape(-1, 1, 1)

kf = KalmanFilter(
    n_dim_obs=1, n_dim_state=1,
    initial_state_mean=[0],
    initial_state_covariance=np.eye(1) * 0.01,
    transition_matrices=np.eye(1),
    transition_covariance=np.eye(1) * 1e-5,
    observation_matrices=X_factor,
    observation_covariance=np.array([[y.var()]]),
)
state_means, _ = kf.filter(y)

feat["kalman_rain_beta"] = pd.Series(state_means.flatten(), index=close.index[1:])
# Is sensitivity increasing or decreasing?
feat["kalman_rain_beta_trend"] = feat["kalman_rain_beta"].diff(20)
```

### 7. Derivatives-Derived Features

Options market data contains forward-looking information that price alone doesn't.

```python
import yfinance as yf

ticker = yf.Ticker("RELIANCE.NS")
# Get nearest expiry options chain
opts = ticker.option_chain(ticker.options[0])

# Put-call ratio (high = bearish sentiment)
feat["put_call_ratio"] = len(opts.puts) / (len(opts.calls) + 1)

# Implied volatility (from at-the-money options)
atm_calls = opts.calls.iloc[(opts.calls['strike'] - close.iloc[-1]).abs().argsort()[:3]]
feat["implied_vol"] = atm_calls["impliedVolatility"].mean()

# IV vs realized vol spread (IV premium = fear)
feat["iv_rv_spread"] = feat["implied_vol"] - feat["vol_30d"]

# Options volume as fraction of stock volume (high = event expected)
feat["options_volume_ratio"] = (opts.calls["volume"].sum() + opts.puts["volume"].sum()) / vol.iloc[-1]

# Max pain (price where most options expire worthless)
# Useful as a gravitational price level near expiry
```

Note: Options data availability varies. For Indian stocks, NSE options data may need scraping or paid feeds. yfinance has limited options support for .NS tickers.

### 8. Microstructure Features

Order book and tick-level data. Only available from exchange feeds or brokers. Not in yfinance.

```python
# These require tick data from a broker API (Zerodha Kite, IBKR, etc.)
# Included here as feature definitions, not fetchable via yfinance

# Order book imbalance: (bid_volume - ask_volume) / (bid_volume + ask_volume)
# Values > 0 = more buy pressure, < 0 = more sell pressure
feat["book_imbalance"] = (bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-10)

# Bid-ask spread (wider = less liquid, more uncertainty)
feat["spread_bps"] = (ask_price - bid_price) / mid_price * 10000

# Trade flow imbalance (net buy vs sell initiated trades)
feat["trade_flow"] = buy_initiated_volume - sell_initiated_volume

# VWAP deviation (price vs volume-weighted average)
feat["vwap_deviation"] = (close - vwap) / vwap
```

### 9. NLP / Sentiment Features

Extract sentiment from news, earnings calls, social media. Requires text data + an LLM or sentiment model.

```python
# Option A: Use GDELT (geo-intelligence skill) for event tone
# GDELT returns average tone for events matching a query
feat["gdelt_tone_7d"]  # Rolling 7-day average tone for company/sector mentions

# Option B: Use an LLM to score news headlines
# Feed headlines to Claude/GPT → score -1 to +1 → aggregate as feature
feat["news_sentiment_3d"]  # 3-day rolling average sentiment score

# Option C: Earnings call sentiment (quarterly, forward-filled)
# Transcript → LLM scores tone → feature
feat["earnings_tone"]  # -1 (bearish) to +1 (bullish), updated quarterly

# Option D: Social media buzz (Reddit, Twitter/X volume)
feat["social_mention_count_7d"]  # Rolling 7-day mention count
feat["social_sentiment_7d"]      # Rolling 7-day average sentiment
```

### 10. Alternative Data Features

Non-traditional data sources that may lead price.

```python
# Satellite imagery (paid: Planet, Orbital Insight)
# e.g., count trucks at a mine, measure stockpile size
feat["satellite_stockpile_change"]  # Week-over-week change in visible ore stockpile

# Web traffic (SimilarWeb, Google Trends)
import requests
# Google Trends for "coal india share price" → proxy for retail interest
feat["google_trends_7d"]  # Rolling search interest

# Shipping / logistics (AIS vessel tracking, port congestion)
feat["port_congestion_index"]  # Ships waiting at key ports (Paradip, Vizag for mining)
feat["dry_bulk_freight_rate"]  # Baltic Dry Index as demand proxy

# Power consumption (proxy for industrial activity)
# India: POSOCO grid data (publicly available daily)
feat["power_demand_deviation"]  # Deviation from seasonal norm

# Credit card / spending data (aggregated, anonymized)
feat["consumer_spending_yoy"]  # Proxy for economic activity
```

Most alternative data is paid or requires scraping. Google Trends and GDELT are free. The value is in the **lead time** — these signals may move before price does.

### 11. Ensemble & Stacking Features

Use predictions from multiple models as features for a meta-model.

```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

# Train base models on train set
rf = RandomForestClassifier(n_estimators=200, max_depth=5).fit(X_train, y_train)
gb = GradientBoostingClassifier(n_estimators=200, max_depth=3).fit(X_train, y_train)
lr = LogisticRegression(C=0.1, penalty='l1', solver='saga').fit(X_train, y_train)

# Base model predictions as features (use out-of-fold predictions to avoid leakage)
from sklearn.model_selection import cross_val_predict
feat["rf_prob"] = cross_val_predict(rf, X_train, y_train, cv=5, method="predict_proba")[:, 1]
feat["gb_prob"] = cross_val_predict(gb, X_train, y_train, cv=5, method="predict_proba")[:, 1]
feat["lr_prob"] = cross_val_predict(lr, X_train, y_train, cv=5, method="predict_proba")[:, 1]

# Meta-model (stacker) — learns optimal combination
meta_X = np.column_stack([feat["rf_prob"], feat["gb_prob"], feat["lr_prob"]])
meta_model = LogisticRegression().fit(meta_X, y_train)

# On test set: get base model predictions, then stack
test_rf = rf.predict_proba(X_test)[:, 1]
test_gb = gb.predict_proba(X_test)[:, 1]
test_lr = lr.predict_proba(X_test)[:, 1]
meta_test = np.column_stack([test_rf, test_gb, test_lr])
final_pred = meta_model.predict_proba(meta_test)[:, 1]
```

### 12. Cointegration & Pairs Features

For mean-reversion strategies. The spread between cointegrated pairs is itself a feature.

```python
from statsmodels.tsa.stattools import coint

# Test if two stocks are cointegrated
stock_a = prices["COALINDIA.NS"].dropna()
stock_b = prices["NMDC.NS"].dropna()
common = stock_a.index.intersection(stock_b.index)
score, pvalue, _ = coint(stock_a.loc[common], stock_b.loc[common])

if pvalue < 0.05:
    # Cointegrated — compute spread features
    from statsmodels.regression.linear_model import OLS
    import statsmodels.api as sm

    model = OLS(stock_a.loc[common], sm.add_constant(stock_b.loc[common])).fit()
    hedge_ratio = model.params.iloc[1]

    spread = stock_a.loc[common] - hedge_ratio * stock_b.loc[common]
    spread_mean = spread.rolling(60).mean()
    spread_std = spread.rolling(60).std()

    feat["spread_zscore"] = (spread - spread_mean) / (spread_std + 1e-10)
    feat["spread_zscore_5d"] = feat["spread_zscore"].rolling(5).mean()
    # Mean reversion signal: z > 2 = short spread, z < -2 = long spread
    feat["spread_extreme"] = (feat["spread_zscore"].abs() > 2).astype(int)
```

### 13. Monte Carlo Simulation Features

Forward-looking distribution of possible outcomes.

```python
# Simulate 1000 paths of 20-day forward returns
n_sims = 1000
horizon = 20
mu_daily = ret.mean()
sigma_daily = ret.std()

# GBM simulation
simulated_returns = np.random.normal(mu_daily, sigma_daily, (n_sims, horizon))
simulated_cumulative = (1 + simulated_returns).cumprod(axis=1)
final_values = simulated_cumulative[:, -1]

feat["mc_expected_20d"] = np.mean(final_values) - 1
feat["mc_var_95_20d"] = np.percentile(final_values, 5) - 1  # 5th percentile = 95% VaR
feat["mc_prob_positive_20d"] = (final_values > 1).mean()
feat["mc_skew_20d"] = stats.skew(final_values)

# With GARCH vol instead of constant vol (more realistic)
if "garch_cond_vol" in feat.columns:
    current_vol = feat["garch_cond_vol"].iloc[-1] / 100  # Convert from % to decimal
    sim_garch = np.random.normal(mu_daily, current_vol, (n_sims, horizon))
    sim_garch_cum = (1 + sim_garch).cumprod(axis=1)
    feat["mc_garch_var_95_20d"] = np.percentile(sim_garch_cum[:, -1], 5) - 1
```

### 14. Bayesian Features

Incorporate prior beliefs and update with data. Useful when you have domain knowledge about factor relationships.

```python
# Bayesian linear regression — prior on factor betas
# Use PyMC or conjugate normal-inverse-gamma for speed

# Simple conjugate approach: prior beta ~ N(prior_mean, prior_var)
# Posterior after observing data:
prior_mean_rain = -0.001  # Belief: rain hurts mining stocks slightly
prior_var = 0.01

# OLS estimate
ols_beta = np.cov(ret, rain_factor)[0, 1] / np.var(rain_factor)
ols_var = np.var(ret - ols_beta * rain_factor) / (np.var(rain_factor) * len(ret))

# Bayesian posterior (conjugate normal)
posterior_var = 1 / (1/prior_var + 1/ols_var)
posterior_mean = posterior_var * (prior_mean_rain/prior_var + ols_beta/ols_var)

feat["bayesian_rain_beta"] = posterior_mean  # Shrunk toward prior
feat["bayesian_confidence"] = 1 / posterior_var  # Higher = more certain

# As you get more data, posterior converges to OLS estimate
# With little data, prior dominates — this prevents overfitting on small samples
```

### 15. Survivorship Bias Handling

Not a feature category, but critical for feature validity.

```python
# Problem: yfinance only returns currently listed stocks
# Stocks that delisted (went bankrupt, merged) are missing → upward bias

# Mitigations:
# 1. Use index constituents as of each historical date (hard to get for free)
# 2. Include known delistings manually
# 3. At minimum, document the bias in your analysis
# 4. For Indian markets: NSE publishes historical index constituent changes

# When backtesting:
# - Don't use current Nifty 50 members for historical analysis
# - The stocks in Nifty 50 in 2023 are survivors — they look good BY DEFINITION
# - Use point-in-time constituent lists if available

# Practical workaround for feature engineering:
# If you can't get historical constituents, at least:
feat["years_listed"] = (pd.Timestamp.now() - ipo_date).days / 365
# Longer-listed stocks have more survivorship bias in their historical returns
```

## Worked Example

See `scripts/mining_prediction_features.py` for a complete implementation on Indian mining stocks (Coal India, NMDC, Vedanta, Tata Steel, Hindalco) with:
- 6 mining regions (USGS earthquakes + Open-Meteo weather)
- 6 cross-asset proxies (Gold, Copper, Aluminium, Nifty, USD/INR, VIX)
- Walk-forward validation with 3 models (Logistic, RF, GBM)
- Full ablation study
- Result: Technical + Cross-Asset = 60-70% of predictive power. Weather adds 5-10% for rain-sensitive stocks (Vedanta, Coal India). Earthquakes add <2%.

## Typical Findings

Across most Indian equity sectors:
- **Technical features dominate** (60-70%) — markets are semi-efficient, price contains most information
- **Cross-asset adds 10-20%** — commodity/currency links matter
- **External signals add 5-10%** — real but modest; strongest for operationally exposed stocks
- **Seasonal adds 2-5%** — calendar effects exist but are mostly captured by technical features
- **Model edge is modest** (1-5% above baseline) — consistent with semi-efficient markets

Don't expect magic. If a simple feature set beats the market by 20%, you have a bug or overfitting.

## Linking Features to Other Skills

| Feature Source | Skill | API/Data |
|---------------|-------|----------|
| Price, volume, fundamentals | yfinance | `yf.download()` |
| Commodity prices, forex | yfinance | `yf.download("GC=F")` |
| Earthquakes | geo-intelligence | USGS FDSNWS |
| Weather/rainfall | geo-intelligence | Open-Meteo Archive |
| Geopolitical events | geo-intelligence | GDELT |
| Energy data | geo-intelligence | EIA API |
| Backtesting strategy returns | backtesting | vectorbt |
| Volatility forecasts | quant-models | GARCH (arch) |
| Regime state | quant-models | HMM (hmmlearn) |
| Dynamic betas | quant-models | Kalman (pykalman) |
| Cointegration spreads | quant-models | statsmodels coint |
| Monte Carlo simulations | quant-models | numpy + scipy |
| Portfolio risk | quant-models | pyportfolioopt, empyrical |
| Options / implied vol | yfinance | `yf.Ticker().option_chain()` |
| News sentiment | geo-intelligence | GDELT tone scores |
| Google Trends | alternative data | pytrends / manual |
| Past findings | memory | SQLite search |
| Relationship map | memory | NetworkX graph |
