#!/usr/bin/env python3
"""
NSE VCP Screener — Main Orchestrator
Screens Indian stocks (Nifty 50/200/500) for Minervini's Volatility Contraction Pattern.

Usage:
    python3 screen_vcp.py --universe nifty50
    python3 screen_vcp.py --universe nifty500 --output-dir reports/
    python3 screen_vcp.py --custom-tickers RELIANCE,TCS,INFY
"""

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

# Path: parent dir for calculators, repo root for the framework seam.
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from calculators.trend_template_calculator import calculate_trend_template
from calculators.vcp_pattern_calculator import calculate_vcp
from calculators.volume_pattern_calculator import calculate_volume_pattern
from calculators.pivot_proximity_calculator import calculate_pivot_proximity
from calculators.relative_strength_calculator import calculate_relative_strength
from scorer import calculate_composite_score
from report_generator import generate_reports

from framework import data_api


def _seam_ohlcv(symbol: str, lookback_days: int = 400, source: str = "yfinance") -> pd.DataFrame:
    """OHLCV via the audited seam, with Capitalized columns the calculators expect.

    `symbol` is a bare NSE symbol (no .NS). source="yfinance" for fast bulk scans;
    source="jugaad" adds delivery% for a single-name deep read.
    """
    start = date.today() - timedelta(days=lookback_days)
    df = data_api.history(symbol, start, source=source)               # lowercase normalized
    return df.rename(columns={c: c.capitalize() for c in df.columns})  # -> Open/High/Low/Close/Volume


# Curated Nifty 50 constituents — a clean, reliable SEED list (guardrail philosophy: a
# hardcoded list is fine as a known-good fallback). Used directly for --universe nifty50,
# and unioned into the broader universe so it's a true superset.
NIFTY50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "BHARTIARTL", "ITC", "SBIN", "LT", "KOTAKBANK",
    "HINDUNILVR", "AXISBANK", "BAJFINANCE", "MARUTI", "TATAMOTORS",
    "SUNPHARMA", "TITAN", "HCLTECH", "NTPC", "POWERGRID",
    "ULTRACEMCO", "ADANIENT", "ASIANPAINT", "TATASTEEL", "WIPRO",
    "ONGC", "JSWSTEEL", "COALINDIA", "NESTLEIND", "BAJAJFINSV",
    "M&M", "TECHM", "DRREDDY", "CIPLA", "EICHERMOT",
    "APOLLOHOSP", "DIVISLAB", "BRITANNIA", "HEROMOTOCO", "INDUSINDBK",
    "TATACONSUM", "HDFCLIFE", "SBILIFE", "BAJAJ-AUTO", "GRASIM",
    "BPCL", "ADANIPORTS", "HINDALCO", "BEL", "TRENT",
]


def get_universe(universe: str, custom_tickers: str | None = None) -> list[str]:
    """Screening universe as BARE NSE symbols (no .NS).

    - custom  -> the user's tickers
    - nifty50 -> the curated NIFTY50 seed list (clean, reliable)
    - else (nifty200/nifty500) -> the live tracked sector constituents (~180 across the 11
      sector indices, cached in data/constituents/) UNIONED with NIFTY50, so the broad set is a
      true superset of Nifty 50. (Exact official Nifty 500 membership is a known gap — fetch
      those index CSVs to extend.)
    """
    if universe == "custom" and custom_tickers:
        return [t.strip().upper() for t in custom_tickers.split(",") if t.strip()]
    if universe == "nifty50":
        return list(NIFTY50)
    # Real index membership via nselib (Akamai-free). nifty200/nifty500 -> the actual index.
    index_name = {"nifty200": "Nifty 200", "nifty500": "Nifty 500"}.get(universe, "Nifty 500")
    try:
        return data_api.index_members(index_name)
    except Exception:  # noqa: BLE001 — fall back to tracked sector union + NIFTY50 seed
        sectors = data_api.constituents(source="nse_csv")
        return sorted({s for syms in sectors.values() for s in syms} | set(NIFTY50))


def fetch_benchmark(benchmark: str = "NIFTY 50") -> pd.DataFrame:
    """Fetch the relative-strength benchmark index via the seam (official NSE OHLC).

    `benchmark` is any NSE index name — default "NIFTY 50" (broad market), or a focused one
    like "NIFTY PSU BANK" / "NIFTY SMALLCAP 100" to judge a stock against its own peer index.
    """
    try:
        df = data_api.index(benchmark, since=date.today() - timedelta(days=400))
        return df.rename(columns={c: c.capitalize() for c in df.columns})
    except Exception as e:
        print(f"Warning: Could not fetch {benchmark} benchmark: {e}", file=sys.stderr)
        return pd.DataFrame()


def screen_stock(
    ticker: str,
    benchmark_df: pd.DataFrame,
    args: argparse.Namespace,
) -> dict | None:
    """Screen a single stock for VCP pattern. Returns result dict or None."""
    try:
        df = _seam_ohlcv(ticker)   # bare NSE symbol; via the audited seam

        if len(df) < 200:
            return None

        # Check minimum liquidity (₹1 crore daily avg turnover)
        if "Volume" in df.columns and "Close" in df.columns:
            avg_turnover = (df["Volume"].tail(20) * df["Close"].tail(20)).mean()
            if avg_turnover < 1_00_00_000:  # ₹1 crore
                return None

        # Phase 1: Trend Template
        trend = calculate_trend_template(df)
        if trend["score"] < args.trend_min_score:
            return None

        # Phase 2: VCP Detection
        vcp = calculate_vcp(
            df,
            lookback_days=args.lookback_days,
            min_contractions=args.min_contractions,
            t1_depth_min=args.t1_depth_min,
            t1_depth_max=args.t1_depth_max,
            contraction_ratio=args.contraction_ratio,
            min_contraction_days=args.min_contraction_days,
        )

        if not vcp["is_vcp"]:
            return None

        # Phase 3: Scoring
        volume = calculate_volume_pattern(df)
        current_price = float(df["Close"].iloc[-1])
        pivot = vcp["pivot"]
        pivot_prox = calculate_pivot_proximity(current_price, pivot)
        rs = calculate_relative_strength(df, benchmark_df)

        composite = calculate_composite_score(
            trend_score=trend["score"],
            contraction_score=vcp["score"],
            volume_score=volume["score"],
            pivot_score=pivot_prox["score"],
            rs_score=rs["score"],
        )

        clean_ticker = ticker.replace(".NS", "").replace(".BO", "")

        return {
            "ticker": clean_ticker,
            "price": round(current_price, 2),
            "composite_score": composite["composite_score"],
            "quality": composite["quality"],
            "stage": trend["stage"],
            "trend_score": trend["score"],
            "contraction_score": vcp["score"],
            "volume_score": volume["score"],
            "pivot_score": pivot_prox["score"],
            "rs_score": rs["score"],
            "pivot": round(pivot, 2),
            "pivot_distance_pct": pivot_prox["distance_pct"],
            "pivot_position": pivot_prox["position"],
            "dry_up_ratio": volume["dry_up_ratio"],
            "rs_value": rs["rs_value"],
            "contractions": vcp["contractions"],
            "trend_details": trend["details"],
        }

    except Exception as e:
        print(f"  Error screening {ticker}: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="NSE VCP Screener")
    parser.add_argument("--universe", default="nifty50",
                        choices=["nifty50", "nifty200", "nifty500", "custom"],
                        help="Stock universe to screen")
    parser.add_argument("--custom-tickers", type=str, default=None,
                        help="Comma-separated tickers for custom universe")
    parser.add_argument("--benchmark", type=str, default="NIFTY 50",
                        help="Relative-strength benchmark index (e.g. 'NIFTY 50', "
                             "'NIFTY PSU BANK', 'NIFTY SMALLCAP 100')")
    parser.add_argument("--min-contractions", type=int, default=2,
                        help="Minimum contractions (2-4)")
    parser.add_argument("--t1-depth-min", type=float, default=10.0,
                        help="Minimum T1 depth %%")
    parser.add_argument("--t1-depth-max", type=float, default=40.0,
                        help="Maximum T1 depth %%")
    parser.add_argument("--contraction-ratio", type=float, default=0.75,
                        help="Max contraction ratio")
    parser.add_argument("--min-contraction-days", type=int, default=5,
                        help="Min days per contraction")
    parser.add_argument("--lookback-days", type=int, default=120,
                        help="Pattern lookback days")
    parser.add_argument("--breakout-volume-ratio", type=float, default=1.5,
                        help="Min breakout volume ratio")
    parser.add_argument("--trend-min-score", type=float, default=85.0,
                        help="Min trend template score")
    parser.add_argument("--output-dir", type=str, default="reports",
                        help="Output directory")

    args = parser.parse_args()

    print(f"NSE VCP Screener — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Universe: {args.universe}")

    # Get tickers
    tickers = get_universe(args.universe, args.custom_tickers)
    print(f"Stocks to screen: {len(tickers)}")

    # Fetch benchmark
    print(f"Fetching benchmark: {args.benchmark}...")
    benchmark_df = fetch_benchmark(args.benchmark)

    # Screen all stocks
    results = []
    total = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        clean = ticker.replace(".NS", "")
        if i % 25 == 0 or i == total:
            print(f"  Progress: {i}/{total} ({clean})")

        result = screen_stock(ticker, benchmark_df, args)
        if result:
            results.append(result)
            print(f"  ✓ VCP found: {clean} (Score: {result['composite_score']:.1f})")

    print(f"\nScreening complete. {len(results)} VCP candidates found.")

    # Generate reports
    if results:
        paths = generate_reports(results, args.output_dir)
        print(f"Reports saved:")
        print(f"  JSON: {paths['json_path']}")
        print(f"  Markdown: {paths['md_path']}")
    else:
        print("No candidates found. Try relaxing parameters or expanding universe.")

    return results


if __name__ == "__main__":
    main()
