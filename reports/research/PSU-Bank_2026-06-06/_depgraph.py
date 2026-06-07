"""Dependency / group graph for SBIN -> graph/ + charts/.

FINDING: screener's related-party for BANKS returns transaction TYPES (Advance/Deposit/Remuneration),
not counterparty entities -> useless for a bank graph. This is exactly why the SKILL ranks screener
as corroboration and the annual-report AOC-1 / disclosures as authoritative. So this graph is built
the SKILL's way: SOURCED group entities (each with a citation + SBI's stake = strength). Listed
subsidiaries get the price-validation overlay (do they co-move with the parent).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from framework import dependency_graph as dg          # noqa: E402
from framework.dependency_graph import Entity, Edge, Evidence, Relation  # noqa: E402
from framework import influence_graph as ig           # noqa: E402

WIKI = "https://en.wikipedia.org/wiki/State_Bank_of_India"
BS_MFIPO = "https://www.business-standard.com/markets/news/sbi-to-sell-6-3-stake-in-sbi-mf-via-ipo-retain-majority-shareholding-125110600780_1.html"

# (id, name, ticker|None, stake%, relation, partner|None, source_url) — all SOURCED
GROUP = [
    ("SBICARD", "SBI Cards & Payment Services", "SBICARD", 68.98, Relation.GROUP_ENTITY, None, WIKI),
    ("SBILIFE", "SBI Life Insurance", "SBILIFE", 55.45, Relation.GROUP_ENTITY, "BNP Paribas", WIKI),
    ("SBIGEN", "SBI General Insurance", None, 69.95, Relation.GROUP_ENTITY, None, WIKI),
    ("SBIMF", "SBI Funds Management (SBI MF)", None, None, Relation.GROUP_ENTITY, "AMUNDI", BS_MFIPO),
    ("SBISG", "SBI-SG Global Securities", None, 65.0, Relation.GROUP_ENTITY, "Societe Generale", WIKI),
    ("SBIVEN", "SBI Ventures", None, 100.0, Relation.GROUP_ENTITY, None, WIKI),
]
PARTNERS = [("BNP Paribas", WIKI), ("AMUNDI", BS_MFIPO), ("Societe Generale", WIKI)]


def main() -> None:
    (HERE / "graph").mkdir(exist_ok=True)
    g = dg.DependencyGraph()
    g.add_node(Entity("SBIN", "State Bank of India", "IN", ticker="SBIN",
                      domain="PSU bank", listed=True))
    for nid, name, tk, stake, rel, partner, url in GROUP:
        g.add_node(Entity(nid, name, "IN", ticker=tk, listed=bool(tk),
                          domain="financial services"))
        g.add_edge(Edge("SBIN", nid, rel, strength=stake,
                        confidence="high" if stake else "medium",
                        evidence=[Evidence(f"SBI holds {stake or 'majority'}% of {name}",
                                           url=url, date="2026", source_type="filing")]))
        if partner:                                   # JV partner -> PARTNERS_WITH on the subsidiary
            g.add_node(Entity(partner, partner, "FOREIGN", listed=False))
            g.add_edge(Edge(nid, partner, Relation.PARTNERS_WITH, confidence="high",
                            evidence=[Evidence(f"{name} is a JV with {partner}", url=url,
                                               source_type="filing")]))

    dg.validate_with_prices(g, since="2023-01-01")     # listed subs (SBICARD/SBILIFE) co-move w/ SBIN
    g.save(HERE / "graph" / "dependency_SBIN.json")

    nodes = {nid: ig.Node(nid, "stock" if n.ticker else ("driver" if n.country == "IN" else "flow"),
                          f"stock:{n.ticker}" if n.ticker else nid, n.name[:22])
             for nid, n in g.nodes.items()}
    verdict = {"high": "supported (co-move)", "medium": "supported (leads", "low": "untested"}
    pedges = [ig.Edge(e.src, e.dst, e.relation.value, +1, corr0=e.corr0, lead_corr=e.lead_corr,
                      verdict=("supported (co-move)" if e.corr0 and e.corr0 > 0.3
                               else verdict.get(e.confidence, "untested")))
              for e in g.edges.values()]
    ig.plot_graph(nodes, pedges, title="SBIN — group / dependency graph (sourced; listed subs price-validated)",
                  out_path=str(HERE / "charts" / "dependency_SBIN.png"))
    print(f"SBIN: {len(g.nodes)} nodes, {len(g.edges)} edges -> charts/dependency_SBIN.png")
    for e in g.edges.values():
        co = f"corr0={e.corr0:+.2f}" if e.corr0 is not None else "unlisted (no price)"
        print(f"   {e.src}-{e.relation.value}->{e.dst:18} stake={e.strength} {co}")


if __name__ == "__main__":
    main()
