"""Influence graph — GENERIC engine. The agent drives it; this file makes no claim about which
sector or which hypotheses to test.

The CORE provides reusable primitives:
  - lead_lag(x, y)               : causal-direction cross-correlation of two return series
  - validate_edge(edge, series)  : earn an edge from data (sign + lead checked)
  - build_sector_graph(sector)   : auto-assemble drivers + market + constituents -> a sector,
                                   validate every edge, return structured (nodes, edges)
  - company_sector_graph(sector) : which constituents move/lead the sector basket
  - plot_graph(nodes, edges)     : auto-laid-out PNG, edges coloured by verdict

What to analyse (which sector, which extra drivers/hypotheses, how to read it) is decided by the
AGENT via the influence-graph SKILL.md — NOT hardcoded here. `DEFAULT_DRIVERS` is a reusable,
overridable seed (USD/yields/VIX/market affect every sector); the agent passes its own for a
custom graph. Sector->index names come from the single source data/index_targets.toml.

Run FORWARD by scenario-analyzer (event->impacts), BACKWARD by sector-deep-dive stage 6
(divergence->causes). A hypothesis generator + search scoper, NOT a truth oracle (manuals/12):
every empirical edge is earned by lead-lag; untestable ones (macro source MISSING) are marked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from framework import data_api


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Node:
    id: str
    kind: str          # driver | market | sector | stock | flow | missing
    source: str        # "index:<name>" | "driver:<name>" | "stock:<symbol>" | "missing:<reason>"
    label: str = ""


@dataclass
class Edge:
    src: str
    dst: str
    mechanism: str
    expected_sign: int           # +1 move together, -1 move opposite
    kind: str = "empirical"      # "empirical" (testable) | "structural" (source MISSING)
    n: int | None = None
    corr0: float | None = None   # contemporaneous return correlation
    lead_lag: int | None = None  # days src LEADS dst at strongest causal-direction corr
    lead_corr: float | None = None
    verdict: str = ""


# Reusable, OVERRIDABLE driver seed — generic macro/market drivers that plausibly affect ANY
# Indian sector (the agent supplies its own list for a custom graph). (id, source, sign, why).
DEFAULT_DRIVERS: list[tuple[str, str, int, str]] = [
    ("NIFTY50", "index:Nifty 50", +1, "broad-market beta / index flows"),
    ("USDINR", "driver:USDINR", -1, "INR weakness -> FII outflow"),
    ("US10Y", "driver:US10Y", -1, "higher US yields pull FPI out of India"),
    ("VIX", "driver:VIX", -1, "global risk-off -> EM de-risked"),
]


# ---------------------------------------------------------------------------
# Core primitives (generic — work for any series / any edge)
# ---------------------------------------------------------------------------

def node_returns(spec: str, since: str | date, price_source: str = "yfinance") -> pd.Series | None:
    """Daily return series from a source spec, or None. spec: index:/driver:/stock:/missing:"""
    scheme, _, arg = spec.partition(":")
    try:
        if scheme == "index":
            px = data_api.index(arg, since=since)["close"]
        elif scheme == "driver":
            px = data_api.driver(arg, since=since)["close"]
        elif scheme == "stock":
            px = data_api.history(arg, since=since, source=price_source)["close"]
        else:
            return None
    except Exception:  # noqa: BLE001 — a bad source is dropped, never faked
        return None
    r = px.astype(float).dropna().pct_change().dropna()
    r.index = pd.to_datetime(r.index).tz_localize(None)
    return r


def lead_lag(x: pd.Series, y: pd.Series, max_lag: int = 5) -> dict:
    """Causal-direction cross-correlation: corr(x_t, y_{t+L}) for L in 0..max_lag (x leads y).
    Ignores L<0 (that would argue against x->y). Returns corr0 + the strongest lead."""
    df = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    if len(df) < 30:
        return {"n": len(df), "corr0": None, "lead_lag": None, "lead_corr": None}
    corr0 = float(df["x"].corr(df["y"]))
    lead_l, lead_c = 0, corr0
    for L in range(0, max_lag + 1):
        c = df["x"].corr(df["y"].shift(-L))
        if pd.notna(c) and abs(c) > abs(lead_c):
            lead_l, lead_c = L, float(c)
    return {"n": len(df), "corr0": corr0, "lead_lag": lead_l, "lead_corr": lead_c}


def _verdict(e: Edge) -> str:
    """Credit a directionally-correct co-move (L=0) OR lead (L>0). A null daily link is
    'no daily link' (the flow channel may act weekly), never asserted false."""
    if e.corr0 is None:
        return "untested (too few bars)"
    contemp = e.corr0 * e.expected_sign
    lead = (e.lead_corr or 0) * e.expected_sign
    if contemp >= 0.3:
        return "supported (co-move)"
    if e.lead_lag and e.lead_lag > 0 and lead >= 0.2:
        return f"supported (leads {e.lead_lag}d {e.lead_corr:+.2f})"
    if max(abs(e.corr0), abs(e.lead_corr or 0)) < 0.1:
        return "no daily link (try weekly / via flow)"
    if contemp < 0 and abs(e.corr0) >= 0.1:
        return f"wrong sign ({e.corr0:+.2f})"
    return "weak"


def validate_edge(e: Edge, series: dict[str, pd.Series | None], max_lag: int = 5) -> Edge:
    """Earn one edge from data (mutates + returns it)."""
    if e.kind != "empirical":
        e.verdict = "untested (structural — source MISSING)"
        return e
    x, y = series.get(e.src), series.get(e.dst)
    if x is None or y is None:
        e.verdict = "untested (data unavailable)"
        return e
    r = lead_lag(x, y, max_lag)
    e.n, e.corr0, e.lead_lag, e.lead_corr = r["n"], r["corr0"], r["lead_lag"], r["lead_corr"]
    e.verdict = _verdict(e)
    return e


# ---------------------------------------------------------------------------
# Generic graph builders (any sector; agent picks the sector + drivers)
# ---------------------------------------------------------------------------

def _sector_index_name(sector: str) -> str:
    """Sector -> nselib index name from the SINGLE source (data/index_targets.toml).
    index() is case-insensitive, so the title-case names work directly. Catalog: data/index_catalog.md."""
    from data.nse_constituents import load_index_targets
    return load_index_targets().get("sectors", {}).get(sector, f"Nifty {sector}")


def build_sector_graph(
    sector: str,
    since: str | date = "2023-01-01",
    *,
    drivers: list[tuple[str, str, int, str]] | None = None,
    with_constituents: bool = True,
    extra_edges: list[Edge] | None = None,
    max_lag: int = 5,
    price_source: str = "yfinance",
) -> tuple[dict[str, Node], list[Edge]]:
    """Assemble + validate an influence graph for ANY sector. Generic: drivers and any extra
    hypothesis edges are caller-supplied (default DRIVERS seed). Returns (nodes, validated edges)."""
    drivers = drivers if drivers is not None else DEFAULT_DRIVERS
    sector_id = sector.upper().replace(" ", "_")
    index_name = _sector_index_name(sector)

    nodes: dict[str, Node] = {sector_id: Node(sector_id, "sector", f"index:{index_name}", sector)}
    edges: list[Edge] = []
    for did, dsrc, sign, why in drivers:
        kind = "market" if dsrc.startswith("index:") else "driver"
        nodes[did] = Node(did, kind, dsrc, did)
        edges.append(Edge(did, sector_id, why, sign))
    if with_constituents:
        for sym in data_api.constituents()[sector]:
            nodes[sym] = Node(sym, "stock", f"stock:{sym}", sym)
            edges.append(Edge(sym, sector_id, "constituent — moves the sector basket", +1))
    if extra_edges:
        edges += extra_edges
        for e in extra_edges:
            nodes.setdefault(e.src, Node(e.src, "driver", f"driver:{e.src}"))

    series = {nid: node_returns(n.source, since, price_source) for nid, n in nodes.items()}
    for e in edges:
        validate_edge(e, series, max_lag)
    return nodes, edges


def company_sector_graph(sector: str = "PSU Bank", since: str | date = "2023-01-01",
                         max_lag: int = 5, price_source: str = "yfinance") -> list[Edge]:
    """Just the constituent->sector edges, validated and ranked by |corr| (the bellwethers)."""
    _, edges = build_sector_graph(sector, since, drivers=[], with_constituents=True,
                                  max_lag=max_lag, price_source=price_source)
    return sorted(edges, key=lambda e: abs(e.corr0 or 0), reverse=True)


# ---------------------------------------------------------------------------
# Output (generic)
# ---------------------------------------------------------------------------

def format_report(edges: list[Edge]) -> str:
    lines = [f"{'edge':<28} exp  corr0  lead(d)  leadcorr  verdict", "-" * 80]
    for e in edges:
        c0 = f"{e.corr0:+.2f}" if e.corr0 is not None else "  -  "
        bl = f"{e.lead_lag:+d}" if e.lead_lag is not None else " - "
        bc = f"{e.lead_corr:+.2f}" if e.lead_corr is not None else "  -  "
        lines.append(f"{e.src+'->'+e.dst:<28} {e.expected_sign:+d}   {c0:>6}  {bl:>5}  {bc:>7}   {e.verdict}")
    return "\n".join(lines)


def _edge_style(e: Edge):
    mag = max(abs(e.corr0 or 0), abs(e.lead_corr or 0))
    if e.verdict.startswith("supported (co-move)"):
        return "#1a7f37", "-", 1 + 4 * mag
    if e.verdict.startswith("supported (leads"):
        return "#1f6feb", "-", 1 + 4 * mag
    if e.verdict.startswith("wrong sign"):
        return "#cf222e", "--", 1.5
    if e.verdict.startswith("untested"):
        return "#8250df", ":", 1.2
    return "#9aa0a6", (0, (2, 3)), 0.8


def _auto_layout(nodes: dict[str, Node]) -> dict[str, tuple[float, float]]:
    """Columns by kind: drivers/market left, sector centre, stocks right; spread vertically."""
    cols = {"driver": 0.0, "market": 0.0, "missing": 0.0, "flow": 1.5, "sector": 3.0, "stock": 6.0}
    buckets: dict[float, list[str]] = {}
    for nid, n in nodes.items():
        x = cols.get(n.kind, 3.0)
        buckets.setdefault(x, []).append(nid)
    pos: dict[str, tuple[float, float]] = {}
    for x, ids in buckets.items():
        m = len(ids)
        for i, nid in enumerate(ids):
            pos[nid] = (x, (m - 1) / 2 - i)
    return pos


def plot_graph(nodes: dict[str, Node], edges: list[Edge], title: str = "Influence graph",
               out_path: str = "") -> str:
    """Auto-laid-out PNG; supported edges bold/coloured, refuted faint. Generic for any graph."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    pos = _auto_layout(nodes)
    fig, ax = plt.subplots(figsize=(12, max(6, 0.5 * len(nodes))))
    for e in edges:
        if e.src not in pos or e.dst not in pos:
            continue
        (x0, y0), (x1, y1) = pos[e.src], pos[e.dst]
        col, ls, lw = _edge_style(e)
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, linestyle=ls,
                                    shrinkA=16, shrinkB=16, alpha=0.9))
    fc_by_kind = {"driver": "#fff1cc", "market": "#dbeeff", "sector": "#ffd9d9",
                  "stock": "#e6ffe6", "missing": "#eeeeee", "flow": "#f0e6ff"}
    for nid, (x, y) in pos.items():
        n = nodes.get(nid)
        ax.scatter([x], [y], s=2200, c=fc_by_kind.get(n.kind if n else "stock", "#eee"),
                   edgecolors="#444", zorder=3)
        ax.text(x, y, nid, fontsize=7, ha="center", va="center", zorder=4, weight="bold")
    ax.text(0.01, 0.99, "green=co-move  blue=leads  red=wrong-sign  dotted=untested  faint=no link",
            transform=ax.transAxes, fontsize=8, va="top", color="#555")
    ax.set_title(title); ax.axis("off")
    out = Path(out_path) if out_path else Path("reports/influence_graph") / f"{title.replace(' ', '_')}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
    return str(out)


if __name__ == "__main__":  # DEMO only — the agent drives this for any sector via the SKILL
    import sys
    sec = sys.argv[1] if len(sys.argv) > 1 else "PSU Bank"
    nodes, edges = build_sector_graph(sec)
    print(format_report(edges))
    print("\nplot:", plot_graph(nodes, edges, title=f"{sec} influence graph"))
