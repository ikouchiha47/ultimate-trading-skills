"""Group / dependency graphs for the PSU banks -> graph/ + charts/.

FINDING: screener related-party is useless for BANKS (returns transaction TYPES, not entities), so
each bank's group entities are SOURCED from the bank's own subsidiaries/JV disclosures (+ Wikipedia/
news), each edge cited, with the bank's stake as strength. Listed subsidiaries get the price-overlay
(do they co-move with the parent). Builds one graph per bank PLUS a combined PSU-network graph where
shared JVs (e.g. Star Union Dai-ichi Life = BOI + Union Bank) cross-link the banks.
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

# Sources (sourced disclosures)
S = {
    "SBIN": "https://en.wikipedia.org/wiki/State_Bank_of_India",
    "SBIMF": "https://www.business-standard.com/markets/news/sbi-to-sell-6-3-stake-in-sbi-mf-via-ipo-retain-majority-shareholding-125110600780_1.html",
    "BBK": "https://bankofbaroda.bank.in/about-us/subsidiaries-and-joint-ventures",
    "CANBK": "https://en.wikipedia.org/wiki/Canara_Bank",
    "PNB": "https://pnb.bank.in/subsidiaries-and-JVs.html",
    "UNION": "https://www.unionbankofindia.bank.in/en/common/subsidiaries-and-joint-ventures",
    "INDIANB": "https://www.indianbank.in/departments/subsidiaries-and-joint-ventures/",
    "BOI": "https://www.business-standard.com/article/finance/bank-of-india-to-divest-25-in-star-union-dai-ichi-life-for-rs-1-106-crore-119040600066_1.html",
}

# Per bank: (entity_id, display, ticker|None, stake%|None, jv_partner|None, src_key)
GROUPS: dict[str, list[tuple]] = {
    "SBIN": [
        ("SBICARD", "SBI Cards", "SBICARD", 68.98, None, "SBIN"),
        ("SBILIFE", "SBI Life", "SBILIFE", 55.45, "BNP Paribas", "SBIN"),
        ("SBIGEN", "SBI General Insurance", None, 69.95, None, "SBIN"),
        ("SBIMF", "SBI Funds Mgmt (SBI MF)", None, None, "AMUNDI", "SBIMF"),
        ("SBISG", "SBI-SG Global Sec", None, 65.0, "Societe Generale", "SBIN"),
        ("SBIVEN", "SBI Ventures", None, 100.0, None, "SBIN"),
    ],
    "BANKBARODA": [
        ("BOBCAPS", "BOB Capital Markets", None, 100.0, None, "BBK"),
        ("BOBFIN", "BOB Financial Solutions", None, 100.0, None, "BBK"),
        ("NAINITAL", "Nainital Bank", None, 98.57, None, "BBK"),
        ("INDIAFIRST", "IndiaFirst Life", None, None, "Legal & General", "BBK"),
        ("INDIAINFRADEBT", "India Infradebt", None, None, None, "BBK"),
    ],
    "CANBK": [
        ("CANFINHOME", "Can Fin Homes", "CANFINHOME", 29.99, None, "CANBK"),
        ("CANHSBCLIFE", "Canara HSBC Life", None, 51.0, "HSBC", "CANBK"),
        ("CRAMC", "Canara Robeco AMC", None, 51.0, "Robeco/ORIX", "CANBK"),
        ("CANBANKFACTORS", "Canbank Factors", None, 100.0, None, "CANBK"),
        ("CANBANKVENTURE", "Canbank Venture Capital", None, 100.0, None, "CANBK"),
    ],
    "PNB": [
        ("PNBHOUSING", "PNB Housing Finance", "PNBHOUSING", 28.0, None, "PNB"),
        ("PNBGILTS", "PNB Gilts", "PNBGILTS", 74.0, None, "PNB"),
        ("PNBMETLIFE", "PNB MetLife", None, 30.0, "MetLife", "PNB"),
        ("PNBINVEST", "PNB Investment Services", None, 100.0, None, "PNB"),
        ("PNBINTL", "PNB International (UK)", None, 100.0, None, "PNB"),
    ],
    "UNIONBANK": [
        ("UNIONAMC", "Union Asset Management", None, 100.0, "Dai-ichi Life", "UNION"),
        ("SUDLIFE", "Star Union Dai-ichi Life", None, 25.1, "Dai-ichi Life", "UNION"),
    ],
    "INDIANB": [
        ("INDBANKMB", "Indbank Merchant Banking", None, None, None, "INDIANB"),
        ("INDBANKHOUSING", "Ind Bank Housing", None, None, None, "INDIANB"),
        ("UNIVSOMPO", "Universal Sompo Gen Ins", None, None, "Sompo (JV)", "INDIANB"),
        ("ASREC", "ASREC (India)", None, None, None, "INDIANB"),
        ("INDBANKGSS", "Indbank Global Support", None, 100.0, None, "INDIANB"),
    ],
    "BANKINDIA": [
        ("SUDLIFE", "Star Union Dai-ichi Life", None, 28.96, "Dai-ichi Life", "BOI"),
        ("BOIMB", "BOI Merchant Bankers", None, 100.0, None, "BOI"),
        ("BOISHL", "BOI Shareholding", None, 100.0, None, "BOI"),
        ("STCI", "STCI Finance", None, None, None, "BOI"),
    ],
}
BANK_NAMES = {"SBIN": "State Bank of India", "BANKBARODA": "Bank of Baroda",
              "CANBK": "Canara Bank", "PNB": "Punjab National Bank",
              "UNIONBANK": "Union Bank of India", "INDIANB": "Indian Bank",
              "BANKINDIA": "Bank of India"}
LISTED_SUBS = {"SBICARD", "SBILIFE", "CANFINHOME", "PNBHOUSING", "PNBGILTS"}


def _add_bank(g: dg.DependencyGraph, bank: str) -> None:
    g.add_node(Entity(bank, BANK_NAMES[bank], "IN", ticker=bank, domain="PSU bank", listed=True))
    for eid, name, tk, stake, partner, src in GROUPS[bank]:
        g.add_node(Entity(eid, name, "IN", ticker=tk, listed=bool(tk), domain="financial services"))
        g.add_edge(Edge(bank, eid, Relation.GROUP_ENTITY, strength=stake,
                        confidence="high" if stake else "medium",
                        evidence=[Evidence(f"{BANK_NAMES[bank]} holds {stake or 'stake'}% of {name}",
                                           url=S[src], date="2026", source_type="filing")]))
        if partner:
            g.add_node(Entity(partner, partner, "FOREIGN", listed=False))
            g.add_edge(Edge(eid, partner, Relation.PARTNERS_WITH, confidence="high",
                            evidence=[Evidence(f"{name} JV partner {partner}", url=S[src],
                                               source_type="filing")]))


def _plot(g: dg.DependencyGraph, title: str, out: str) -> None:
    nodes = {nid: ig.Node(nid, "stock" if n.ticker else ("driver" if n.country == "IN" else "flow"),
                          f"stock:{n.ticker}" if n.ticker else nid, n.name[:20])
             for nid, n in g.nodes.items()}
    pedges = [ig.Edge(e.src, e.dst, e.relation.value, +1, corr0=e.corr0, lead_corr=e.lead_corr,
                      verdict=("supported (co-move)" if e.corr0 and e.corr0 > 0.3
                               else ("supported (co-move)" if e.confidence == "high"
                                     else "untested")))
              for e in g.edges.values()]
    ig.plot_graph(nodes, pedges, title=title, out_path=out)


def main() -> None:
    (HERE / "graph").mkdir(exist_ok=True)
    # per-bank graphs
    for bank in GROUPS:
        g = dg.DependencyGraph()
        _add_bank(g, bank)
        dg.validate_with_prices(g, since="2023-01-01")
        g.save(HERE / "graph" / f"dependency_{bank}.json")
        _plot(g, f"{bank} — group / dependency graph (sourced; listed subs price-validated)",
              str(HERE / "charts" / f"dependency_{bank}.png"))
        listed = [n for n in g.nodes.values() if n.ticker and n.id != bank]
        print(f"{bank}: {len(g.nodes)} nodes, {len(g.edges)} edges, listed subs: {[n.id for n in listed]}")

    # combined PSU network (shared JVs cross-link banks)
    G = dg.DependencyGraph()
    for bank in GROUPS:
        _add_bank(G, bank)
    dg.validate_with_prices(G, since="2023-01-01")
    G.save(HERE / "graph" / "dependency_PSU_network.json")
    _plot(G, "PSU banks — combined group network (shared JVs cross-link banks)",
          str(HERE / "charts" / "dependency_PSU_network.png"))
    # report any node referenced by >1 bank (the cross-links)
    from collections import Counter
    parents = Counter(e.src for e in G.edges.values() if e.relation == Relation.GROUP_ENTITY)
    shared = [nid for nid in G.nodes if sum(1 for e in G.edges.values()
              if e.dst == nid and e.relation == Relation.GROUP_ENTITY) > 1]
    print(f"COMBINED: {len(G.nodes)} nodes, {len(G.edges)} edges; cross-bank shared entities: {shared}")


if __name__ == "__main__":
    main()
