"""Regenerate data/index_catalog.md — the agent-referenceable list of all NSE indices.

The runtime source of truth is nselib (data/nse_constituents._nselib_catalog); this script
dumps a committed snapshot so the Claude/opencode runner can see valid index names (for
--benchmark, universe selection, index_members()) WITHOUT running code.

Run:  uv run --extra data python -m data.dump_index_catalog
"""

from __future__ import annotations

from pathlib import Path

from nselib import indices

CATEGORIES = ("BroadMarketIndices", "SectoralIndices", "ThematicIndices", "StrategyIndices")
OUT = Path(__file__).resolve().parent / "index_catalog.md"


def main() -> None:
    lines = [
        "# NSE index catalog (nselib) — agent reference",
        "",
        "Valid `index_name` values for `data_api.index_members(name)`, the VCP `--benchmark`,",
        "and universe selection. Generated from nselib — regenerate with",
        "`uv run --extra data python -m data.dump_index_catalog`. nselib's category set is fixed",
        f"({', '.join(CATEGORIES)}); any new category here just needs adding to that tuple.",
        "",
    ]
    for cat in CATEGORIES:
        try:
            names = sorted(indices.index_list(cat))
        except Exception as e:  # noqa: BLE001
            lines += [f"## {cat}", f"_(unavailable: {e})_", ""]
            continue
        lines.append(f"## {cat} ({len(names)})")
        lines += [f"- {n}" for n in names]
        lines.append("")
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
