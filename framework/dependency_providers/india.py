"""India RelationshipProvider — composes the Indian authoritative stack.

Structured (implemented here, thin):
- resolve: ticker via our existing constituent/ticker maps (data_api); listed flag.
- discover (LISTED): screener Related-Party transactions -> GROUP_ENTITY edges with ₹ strength
  (corroboration; screener flags it experimental, so it's SOURCED + low/medium confidence).

Agent-driven (the SKILL.md directs; not auto-parsed — unstructured or behind portals):
- LISTED authoritative: NSE/BSE LODR Reg-23 related-party filings + annual-report Ind-AS 24 note
  (₹ amounts), AOC-1 subsidiaries/associates, concall named customers/partners, dated news.
- board interlocks + promoter group: MCA director↔company via DIN (Tofler/Zauba), shareholding
  promoter-group entity names, SEBI SAST.
- PRIVATE companies (e.g. Razorpay — no ticker/exchange/EDGAR): RBI licence lists (e.g. Payment
  Aggregators) for domain, MCA for directors/charges/group, company case-studies + news for
  customers, funding announcements for investors. Then map customers' sectors -> listed peers via
  our nselib sector constituents (data_api.constituents).
"""
from __future__ import annotations

import sys
from pathlib import Path

from ..dependency_graph import Entity, Edge, Evidence, Relation, register_provider

_SCRIPTS = Path(__file__).resolve().parents[2] / "skills/fundamentals/equity-research/scripts"


def _num(s: str) -> float | None:
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


class IndiaProvider:
    country = "IN"

    def resolve(self, name_or_ticker: str) -> Entity | None:
        t = name_or_ticker.upper().strip()
        try:
            from framework import data_api
            members: set[str] = set()
            for syms in data_api.constituents().values():
                members.update(syms)
            if t in members:
                return Entity(id=t, name=t, country="IN", ticker=t, listed=True)
        except Exception:  # noqa: BLE001
            pass
        # unknown -> treat as private/unlisted (Razorpay path); domain filled by the agent (SKILL)
        return Entity(id=name_or_ticker, name=name_or_ticker, country="IN", kind="company",
                      listed=False)

    def discover(self, entity: Entity, kinds: set[Relation]) -> list[Edge]:
        if not entity.listed or not entity.ticker:
            return []   # private: agent sources RBI/MCA/news per SKILL.md
        if Relation.GROUP_ENTITY not in kinds:
            return []
        if str(_SCRIPTS) not in sys.path:
            sys.path.insert(0, str(_SCRIPTS))
        try:
            from screener_reader import fetch_related_party
            rp = fetch_related_party(entity.ticker, headless=True)
        except Exception:  # noqa: BLE001
            return []
        edges: list[Edge] = []
        for party in rp.get("parties", []):
            amts = [v for v in (_num(x) for x in party.get("transactions", {}).values()) if v]
            edges.append(Edge(src=entity.id, dst=party["name"], relation=Relation.GROUP_ENTITY,
                              strength=max(amts) if amts else None,
                              confidence="medium" if amts else "low",
                              evidence=[Evidence(quote=f"related party (screener): {party['name']}",
                                                 url=rp.get("url", ""), source_type="related_party")]))
        return edges

    def board_members(self, entity: Entity) -> list[Entity]:
        return []   # MCA/DIN via Tofler/Zauba is agent-driven (SKILL.md)

    def promoter_group(self, entity: Entity) -> list[Entity]:
        return []   # shareholding promoter-group names + SEBI SAST are agent-driven (SKILL.md)


register_provider(IndiaProvider())
