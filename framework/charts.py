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


def composition_chart(title: str, data: dict, outpath: str | Path,
                      unit: str = "%", color: str = "#5b8def") -> str:
    """Generic breakdown chart (horizontal bars, sorted, value-labelled) from a {label: value} dict.

    The agent calls this in the unify/review stage to turn compositional PROSE into a visual —
    loan-book mix, corporate-sector exposure, shareholding, geographic split, revenue mix, etc.
    Generic + thin: the agent decides WHAT is chart-worthy and supplies the parsed numbers (sourced).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    items = sorted(((k, float(v)) for k, v in data.items() if v is not None),
                   key=lambda kv: kv[1])
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(9, max(2.5, 0.45 * len(items) + 1)))
    bars = ax.barh(labels, vals, color=color)
    for b, v in zip(bars, vals):
        ax.text(b.get_width(), b.get_y() + b.get_height() / 2, f" {v:g}{unit}",
                va="center", fontsize=9)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlim(0, max(vals) * 1.15 if vals else 1)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = Path(outpath)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return str(out)


def _read_fin_csv(path) -> dict:
    """Screener financial CSV (line_item, year cols) -> {periods, rows{label:[floats]}}."""
    import csv as _csv
    rows: dict[str, list] = {}
    periods: list[str] = []
    with open(path, newline="") as fh:
        for i, r in enumerate(_csv.reader(fh)):
            if i == 0:
                periods = r[1:]
                continue
            vals = []
            for x in r[1:]:
                try:
                    vals.append(float(str(x).replace(",", "")))
                except (ValueError, AttributeError):
                    vals.append(None)
            rows[r[0]] = vals
    return {"periods": periods, "rows": rows}


def financial_charts(symbol: str, data_dir: str | Path, outdir: str | Path) -> str:
    """Screener-style 2x2 financial dashboard from the gathered CSVs (₹ Cr):
    (1) Revenue & Net Profit, (2) the BOOK — Deposits/Investments/Borrowing (where the money is),
    (3) Quarterly Net Profit, (4) EPS. Returns the PNG path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data_dir = Path(data_dir)
    pl = _read_fin_csv(data_dir / f"{symbol}_profit_loss.csv")
    bs = _read_fin_csv(data_dir / f"{symbol}_balance_sheet.csv")
    q = _read_fin_csv(data_dir / f"{symbol}_quarters.csv")

    def _row(tbl, label):
        return tbl["rows"].get(label, [])

    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle(f"{symbol} — financials (₹ Cr unless noted; source: screener, annual/quarterly)",
                 fontsize=13, fontweight="bold")

    # (1) Revenue & Net Profit
    yrs = pl["periods"]
    rev, npf = _row(pl, "Revenue"), _row(pl, "Net Profit")
    x = range(len(yrs))
    a = ax[0][0]
    a.bar([i - 0.2 for i in x], [v or 0 for v in rev], width=0.4, label="Revenue", color="#5b8def")
    a.bar([i + 0.2 for i in x], [v or 0 for v in npf], width=0.4, label="Net Profit", color="#2da44e")
    a.set_title("Revenue & Net Profit (annual)"); a.legend(fontsize=8)
    a.set_xticks(list(x)); a.set_xticklabels(yrs, rotation=45, ha="right", fontsize=7)

    # (2) The book — Deposits / Investments / Borrowing
    byrs = bs["periods"]; bx = range(len(byrs))
    a = ax[0][1]
    for lbl, col in [("Deposits", "#8250df"), ("Investments", "#e3a008"), ("Borrowing", "#cf222e")]:
        vals = _row(bs, lbl)
        if vals:
            a.plot(list(bx), [v or 0 for v in vals], marker="o", ms=3, label=lbl, color=col)
    a.set_title("The book: Deposits / Investments / Borrowing"); a.legend(fontsize=8)
    a.set_xticks(list(bx)); a.set_xticklabels(byrs, rotation=45, ha="right", fontsize=7)

    # (3) Quarterly Net Profit
    qyrs = q["periods"]; qx = range(len(qyrs)); qnp = _row(q, "Net Profit")
    a = ax[1][0]
    a.bar(list(qx), [v or 0 for v in qnp], color="#2da44e", alpha=0.8)
    a.set_title("Quarterly Net Profit")
    a.set_xticks(list(qx)); a.set_xticklabels(qyrs, rotation=45, ha="right", fontsize=7)

    # (4) EPS
    eps = _row(pl, "EPS in Rs")
    a = ax[1][1]
    a.plot(list(x), [v or 0 for v in eps], marker="o", color="#0969da")
    a.set_title("EPS (₹)")
    a.set_xticks(list(x)); a.set_xticklabels(yrs, rotation=45, ha="right", fontsize=7)

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    p = out / f"{symbol}_financials.png"
    fig.savefig(p, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return str(p)


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
