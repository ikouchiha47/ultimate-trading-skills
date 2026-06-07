"""Earn the per-sector reversion anchor from the backtest — don't guess it.

Sweeps candidate anchors (25/50/100/200-DMA) for a sector's basket through the SAME harness,
costs and null, and ranks by Sharpe-over-null. Returns the evidence; it deliberately does NOT
write the result — the orchestrator (SKILL.md) judges whether the edge is real (over_null > 0,
enough trades, OOS not collapsing) before persisting via sector_params.set_anchor. Generic:
works for any sector resolvable to an index basket.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import sector_params
from .harness import BacktestHarness
from .interfaces import DataKind
from .strategies.bnf_reversion import BnfReversion
from .strategies.nulls import BuyAndHoldBasket


@dataclass
class AnchorResult:
    anchor: int
    sharpe: float | None
    sharpe_over_null: float | None
    cagr: float | None
    max_drawdown: float | None
    n_trades: int
    notes: list[str] = field(default_factory=list)


def _load_basket(sector: str, since: str, min_bars: int) -> dict:
    from framework import data_api
    members = data_api.index_members(_index_for(sector))
    frames = {}
    for s in members:
        try:
            df = data_api.history(s, since)        # split-adjusted by default
            if len(df) > min_bars:
                frames[s] = df
        except Exception:  # noqa: BLE001
            continue
    if not frames:
        raise ValueError(f"no priceable constituents for {sector!r}")
    return {DataKind.OHLCV: frames}


def _index_for(sector: str) -> str:
    """Sector -> index name via the single source (index_targets.toml), else the sector itself."""
    try:
        from data.nse_constituents import load_index_targets
        return load_index_targets().get("sectors", {}).get(sector, sector)
    except Exception:  # noqa: BLE001
        return sector


def calibrate_anchor(sector: str, since: str = "2021-01-01",
                     candidates: list[int] | None = None,
                     n_trials: int | None = None) -> list[AnchorResult]:
    """Sweep anchors for a sector; return results ranked by sharpe_over_null (best first).

    The agent reads this, checks the winner clears the discipline bar (over_null > 0, trades
    enough, OOS note healthy), and only THEN calls sector_params.set_anchor(sector, best, note).
    """
    cands = candidates or sector_params.candidates()
    data = _load_basket(sector, since, min_bars=max(cands) + 50)
    frames = data[DataKind.OHLCV]
    null = BuyAndHoldBasket(list(frames))
    h = BacktestHarness()
    out: list[AnchorResult] = []
    for ma in cands:
        r = h.run(BnfReversion(ma=ma, uptrend_ma=200), data, null=null,
                  n_trials=n_trials or len(cands))
        out.append(AnchorResult(ma, r.sharpe, r.sharpe_over_null, r.cagr,
                                r.max_drawdown, r.n_trades, r.notes))
    out.sort(key=lambda a: (a.sharpe_over_null if a.sharpe_over_null is not None else -1e9),
             reverse=True)
    return out


def format_sweep(sector: str, results: list[AnchorResult]) -> str:
    lines = [f"anchor sweep — {sector} (ranked by Sharpe-over-null):",
             f"  {'anchor':>8} {'sharpe':>7} {'over_null':>10} {'cagr':>7} {'maxDD':>7} {'trades':>6}"]
    for a in results:
        ov = f"{a.sharpe_over_null:>10.2f}" if a.sharpe_over_null is not None else f"{'n/a':>10}"
        lines.append(f"  {str(a.anchor)+'-DMA':>8} {a.sharpe:>7.2f} {ov} "
                     f"{a.cagr:>7.1%} {a.max_drawdown:>7.1%} {a.n_trades:>6}")
    best = results[0]
    verdict = ("EARNED" if (best.sharpe_over_null or -1) > 0 else "NO EDGE — do not persist")
    lines.append(f"  -> best {best.anchor}-DMA: {verdict} "
                 f"(over_null {best.sharpe_over_null:+.2f}, {best.n_trades} trades)")
    return "\n".join(lines)
