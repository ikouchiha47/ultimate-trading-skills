"""Strategy proving-ground for the PSU Bank sector -> strategies/.

(1) Anchor sweep (25/50/100/200-DMA) ranked by Sharpe-over-null  -> strategies/anchor_sweep/.
(2) Best anchor stacked with the flow gate (BnfFlowReversion) vs the same null -> its own folder.
Every result reports Sharpe-OVER-NULL and an EARNED / NO-EDGE verdict. Nothing is persisted to
sector_params here unless the edge clears the bar (over_null > 0).
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from framework import sector_params                      # noqa: E402
from framework.calibrate import calibrate_anchor, format_sweep, _load_basket  # noqa: E402
from framework.harness import BacktestHarness            # noqa: E402
from framework.interfaces import DataKind                # noqa: E402
from framework.strategies.bnf_flow_reversion import BnfFlowReversion  # noqa: E402
from framework.strategies.nulls import BuyAndHoldBasket  # noqa: E402

HERE = Path(__file__).resolve().parent
SECTOR = "PSU Bank"
SINCE = "2021-01-01"


def _verdict(over_null) -> str:
    return "EARNED" if (over_null or -1) > 0 else "NO EDGE"


def main() -> None:
    # (1) anchor sweep
    results = calibrate_anchor(SECTOR, since=SINCE)
    sweep_dir = HERE / "strategies" / "anchor_sweep"
    sweep_dir.mkdir(parents=True, exist_ok=True)
    txt = format_sweep(SECTOR, results)
    print(txt)
    (sweep_dir / "verdict.txt").write_text(txt + "\n")
    (sweep_dir / "results.json").write_text(
        json.dumps([asdict(r) for r in results], indent=2, default=str))
    best = results[0]

    # (2) flow gate on the best anchor
    data = _load_basket(SECTOR, SINCE, min_bars=max(sector_params.candidates()) + 50)
    null = BuyAndHoldBasket(list(data[DataKind.OHLCV]))
    h = BacktestHarness()
    strat = BnfFlowReversion(ma=best.anchor, uptrend_ma=200)
    r = h.run(strat, data, null=null, n_trials=len(sector_params.candidates()))
    flow_dir = HERE / "strategies" / f"bnf_flow_reversion_{best.anchor}dma"
    flow_dir.mkdir(parents=True, exist_ok=True)
    rec = {"strategy": "BnfFlowReversion", "anchor_dma": best.anchor,
           "sharpe": r.sharpe, "sharpe_over_null": r.sharpe_over_null,
           "cagr": r.cagr, "max_drawdown": r.max_drawdown, "n_trades": r.n_trades,
           "deflated_sharpe": getattr(r, "deflated_sharpe", None),
           "notes": r.notes, "verdict": _verdict(r.sharpe_over_null)}
    (flow_dir / "result.json").write_text(json.dumps(rec, indent=2, default=str))
    print("FLOW-GATE on", best.anchor, "DMA:", rec["verdict"],
          "over_null", f"{r.sharpe_over_null:+.2f}", "trades", r.n_trades)

    print("BEST_ANCHOR", best.anchor, "EARNED" if (best.sharpe_over_null or -1) > 0 else "NO_EDGE")


if __name__ == "__main__":
    main()
