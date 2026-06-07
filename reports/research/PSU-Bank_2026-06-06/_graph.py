"""Influence graph for the PSU Bank cohort: drivers (market/macro) + constituents -> sector,
lead-lag validated. Writes graph/ report + a plotted PNG into charts/. Answers "what drives the
sector / who leads" — replacing the `unknown` lead-lag in the reports.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from framework import influence_graph as ig  # noqa: E402

SECTOR = "PSU Bank"
SINCE = "2023-01-01"


def main() -> None:
    nodes, edges = ig.build_sector_graph(SECTOR, SINCE, with_constituents=True, max_lag=5)
    edges = sorted(edges, key=lambda e: abs(e.corr0 or 0), reverse=True)
    gdir = HERE / "graph"
    gdir.mkdir(exist_ok=True)

    report = ig.format_report(edges)
    print(report)
    (gdir / "influence_report.txt").write_text(report + "\n")
    (gdir / "edges.json").write_text(json.dumps([asdict(e) for e in edges], indent=2, default=str))

    try:
        ig.plot_graph(nodes, edges, title=f"{SECTOR} influence graph (2023- )",
                      out_path=str(HERE / "charts" / "influence_graph.png"))
        print("plotted charts/influence_graph.png")
    except Exception as e:  # noqa: BLE001
        print("plot skipped:", e)


if __name__ == "__main__":
    main()
