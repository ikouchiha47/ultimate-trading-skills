"""Per-stock technical chart — price + moving averages + volume, the swing/position view.

This is the chart a trader actually reads (like screener.in's): close price with the
25/50/200-DMA stack and a volume panel underneath. We add what screener does NOT show —
the BNF marker: the 25-DMA (Kotegawa's line), shaded dips below it, and the latest bar's
absorption read — so the fade-vs-trap signal is visible, not just the price.

Generic + thin: takes a normalized OHLCV frame (jugaad, with volume + delivery_pct) and
draws. No decisions — the agent/trader reads it.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def price_volume_chart(symbol: str, df: pd.DataFrame, outdir: str | Path,
                       since: str | None = None) -> str:
    """Draw price + 25/50/200-DMA + volume for one symbol; return the PNG path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Compute MAs on the FULL series FIRST so the 200-DMA is populated across the whole
    # display window (caller fetches >=200 trading days of lead-in before `since`), THEN trim.
    full_close = df["close"].astype(float)
    ma25_f = full_close.rolling(25).mean()
    ma50_f = full_close.rolling(50).mean()
    ma200_f = full_close.rolling(200).mean()
    mask = (df.index >= pd.Timestamp(since)) if since else slice(None)
    d = df.loc[mask].copy()
    close = full_close.loc[mask]
    ma25, ma50, ma200 = ma25_f.loc[mask], ma50_f.loc[mask], ma200_f.loc[mask]

    fig, (ax, axv) = plt.subplots(2, 1, figsize=(13, 7), sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1]})
    ax.plot(close.index, close, color="#3b35d6", lw=1.3, label=f"{symbol} close")
    ax.plot(ma25.index, ma25, color="#cf222e", lw=1.0, label="25-DMA (BNF)")
    ax.plot(ma50.index, ma50, color="#e3a008", lw=1.0, label="50-DMA")
    ax.plot(ma200.index, ma200, color="#6e7781", lw=1.0, ls="--", label="200-DMA")
    # Shade where price is below the 25-DMA — the dip zone where a BNF fade may set up.
    ax.fill_between(close.index, close, ma25, where=(close < ma25),
                    color="#cf222e", alpha=0.08, interpolate=True)
    ax.set_ylabel("price (₹)")
    ax.legend(loc="upper left", fontsize=8)
    # Trend label as a BAND, not a knife-edge flip: when price sits within ~3% of the
    # 200-DMA it's a decision zone, not a clean up/down-trend (and the 200-DMA slope matters).
    if ma200.notna().iloc[-1]:
        gap = float(close.iloc[-1] / ma200.iloc[-1] - 1)
        slope = float(ma200.iloc[-1] / ma200.iloc[-21] - 1) if ma200.notna().iloc[-21] else 0.0
        if abs(gap) <= 0.03:
            trend = f"at 200-DMA ±{abs(gap)*100:.0f}% (decision zone, 200-DMA {'rising' if slope>0 else 'falling'})"
        elif gap > 0:
            trend = f"+{gap*100:.0f}% above 200-DMA (uptrend)"
        else:
            trend = f"{gap*100:.0f}% below 200-DMA (downtrend)"
    else:
        trend = "200-DMA n/a"
    ax.set_title(f"{symbol} — price / 25·50·200-DMA / volume   [{trend}]")

    # Volume panel, bars colored by up/down day; delivery overlaid if present.
    vol = d["volume"].astype(float) if "volume" in d else None
    if vol is not None:
        up = close >= close.shift(1)
        axv.bar(vol.index[up], vol[up], color="#2da44e", width=1.0, alpha=0.6)
        axv.bar(vol.index[~up], vol[~up], color="#cf222e", width=1.0, alpha=0.6)
        axv.set_ylabel("volume")
    if "delivery_pct" in d:
        axd = axv.twinx()
        axd.plot(d.index, d["delivery_pct"].astype(float), color="#8250df", lw=0.8, alpha=0.7)
        axd.set_ylabel("delivery %", color="#8250df")
        axd.tick_params(axis="y", labelcolor="#8250df")

    fig.tight_layout()
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{symbol}_price_volume.png"
    fig.savefig(p, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return str(p)
