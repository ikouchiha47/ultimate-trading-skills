"""Business / social dependency graph — country-polymorphic core.

The graph model, BFS expansion engine, social-layer (board-interlock / promoter) derivation and
the price-validation bridge are COUNTRY-AGNOSTIC. How relationships are *discovered* differs per
market (India: related-party note + board + promoter shareholding; US: 10-K Item 1/1A + SEC), so
discovery is delegated to a pluggable `RelationshipProvider` selected by country code. Add a new
country by writing a provider and registering it — nothing else changes (composition, not a class
hierarchy of graphs).

DISCIPLINE: every edge is a SOURCED disclosure (quote + dated link) — a relationship is NEVER
inferred from price. The optional price layer only ANNOTATES listed-listed edges with co-movement
(corroboration that the market recognises a link), never creates them. Absence of co-move != no
dependency; presence != causation.
"""
from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable


class Relation(str, Enum):
    DEPENDS_ON = "depends_on"        # dst is an input/vendor to src (src needs dst)
    SUPPLIES_TO = "supplies_to"      # src is an input/vendor to dst (dst depends on src)
    CUSTOMER_OF = "customer_of"      # src buys from dst
    PARTNERS_WITH = "partners_with"  # alliance / integration (symmetric)
    COMPETES_WITH = "competes_with"  # rivalry (symmetric)
    GROUP_ENTITY = "group_entity"    # subsidiary / associate / related party
    BOARD_INTERLOCK = "board_interlock"   # shares a director (social, symmetric)
    PROMOTER_LINK = "promoter_link"  # shared promoter / promoter-group cross-holding
    # --- people layer (person Entity -> company); the social graph proper ---
    DIRECTOR_OF = "director_of"      # person sits on the board
    EXECUTIVE_OF = "executive_of"    # person is a C-suite/KMP
    FOUNDER_OF = "founder_of"
    INVESTOR_IN = "investor_in"      # person/fund holds/funded the company
    # Events = dated relationship CHANGES: model as one of the above Edges with Evidence.date set
    # and source_type in {news, filing, board} (e.g. an appointment, exit, deal, funding round).


SYMMETRIC = {Relation.PARTNERS_WITH, Relation.COMPETES_WITH,
             Relation.BOARD_INTERLOCK, Relation.PROMOTER_LINK}


@dataclass
class Entity:
    id: str                          # canonical key (ticker if listed, else slug)
    name: str
    country: str                     # "IN", "US", ...
    kind: str = "company"            # company | person | private
    ticker: str | None = None        # NSE/BSE/US symbol if listed (enables price validation)
    domain: str | None = None        # sector/domain, SOURCED (e.g. "fintech/payments" for Razorpay)
    listed: bool = True              # private cos (Razorpay) have NO exchange/EDGAR filings -> MCA/news


@dataclass
class Evidence:
    quote: str                       # the sourcing sentence/figure
    url: str                         # dated link to the disclosure
    date: str | None = None
    source_type: str = "filing"      # filing | related_party | concall | news | board | shareholding


@dataclass
class Edge:
    src: str                         # Entity.id
    dst: str
    relation: Relation
    evidence: list[Evidence] = field(default_factory=list)
    strength: float | None = None    # e.g. ₹ transaction value or revenue %, if disclosed
    confidence: str = "low"          # low (single mention) | medium | high (quantified/repeated)
    # price-validation overlay (filled only if both ends are listed and validate=True):
    corr0: float | None = None
    lead_lag: int | None = None
    lead_corr: float | None = None

    def key(self) -> tuple:
        return (self.src, self.dst, self.relation.value)


@runtime_checkable
class RelationshipProvider(Protocol):
    """One per country. Thin gatherer: returns SOURCED edges + entity resolution. The agent
    (SKILL.md) drives any unstructured extraction; structured sources are parsed here."""

    country: str

    def resolve(self, name_or_ticker: str) -> Entity | None:
        """Canonicalise a name/ticker to an Entity (with ticker if listed)."""

    def discover(self, entity: Entity, kinds: set[Relation]) -> list[Edge]:
        """Return sourced edges for `entity` limited to the requested relation kinds."""

    def board_members(self, entity: Entity) -> list[Entity]:
        """Directors as person Entities (for board-interlock derivation). [] if unavailable."""

    def promoter_group(self, entity: Entity) -> list[Entity]:
        """Promoter-group entities (for promoter-link derivation). [] if unavailable."""


_REGISTRY: dict[str, RelationshipProvider] = {}


def register_provider(provider: RelationshipProvider) -> None:
    _REGISTRY[provider.country.upper()] = provider


def get_provider(country: str) -> RelationshipProvider:
    c = country.upper()
    if c not in _REGISTRY:
        # lazy import the bundled providers on first use
        from . import dependency_providers  # noqa: F401
    if c not in _REGISTRY:
        raise KeyError(f"no RelationshipProvider registered for country {country!r} "
                       f"(have: {sorted(_REGISTRY)})")
    return _REGISTRY[c]


class DependencyGraph:
    """Holds Entities + Edges; dedups edges and merges their evidence."""

    def __init__(self) -> None:
        self.nodes: dict[str, Entity] = {}
        self.edges: dict[tuple, Edge] = {}

    def add_node(self, e: Entity) -> None:
        self.nodes.setdefault(e.id, e)

    def add_edge(self, e: Edge) -> None:
        cur = self.edges.get(e.key())
        if cur is None:
            self.edges[e.key()] = e
            return
        cur.evidence.extend(e.evidence)                  # merge evidence, keep strongest confidence
        rank = {"low": 0, "medium": 1, "high": 2}
        if rank[e.confidence] > rank[cur.confidence]:
            cur.confidence = e.confidence
        if e.strength is not None:
            cur.strength = e.strength

    def to_dict(self) -> dict:
        return {"nodes": [asdict(n) for n in self.nodes.values()],
                "edges": [{**asdict(e), "relation": e.relation.value}
                          for e in self.edges.values()]}

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, default=str))


def derive_social_edges(graph: DependencyGraph, persons: dict[str, set[str]],
                        promoters: dict[str, set[str]]) -> None:
    """Add BOARD_INTERLOCK / PROMOTER_LINK edges between companies that SHARE a person/promoter.

    `persons`/`promoters` map company-id -> set of director/promoter names (collected during BFS).
    Pure derivation over already-sourced membership — no new external calls.
    """
    def _link(membership: dict[str, set[str]], rel: Relation, src_type: str) -> None:
        by_member: dict[str, list[str]] = {}
        for company, members in membership.items():
            for m in members:
                by_member.setdefault(m, []).append(company)
        for member, companies in by_member.items():
            for i in range(len(companies)):
                for j in range(i + 1, len(companies)):
                    a, b = sorted((companies[i], companies[j]))
                    graph.add_edge(Edge(a, b, rel, confidence="high",
                                        evidence=[Evidence(f"shared: {member}", url="", date=None,
                                                           source_type=src_type)]))
    _link(persons, Relation.BOARD_INTERLOCK, "board")
    _link(promoters, Relation.PROMOTER_LINK, "shareholding")


def validate_with_prices(graph: DependencyGraph, since: str = "2023-01-01",
                         max_lag: int = 5) -> None:
    """Annotate listed<->listed edges with daily return corr0 + lead-lag (market recognition).
    Corroboration only — never creates or deletes edges."""
    from . import influence_graph as ig
    series: dict[str, object] = {}
    for nid, n in graph.nodes.items():
        if n.ticker:
            series[nid] = ig.node_returns(f"stock:{n.ticker}", since)
    for e in graph.edges.values():
        x, y = series.get(e.src), series.get(e.dst)
        if x is None or y is None:
            continue
        ll = ig.lead_lag(x, y, max_lag=max_lag)
        e.corr0 = ll.get("corr0")
        e.lead_lag = ll.get("best_lag")
        e.lead_corr = ll.get("best_corr")


def build_graph(seed: str, country: str, *, depth: int = 2, breadth: int = 8,
                kinds: set[Relation] | None = None, social: bool = True,
                validate: bool = False, since: str = "2023-01-01") -> DependencyGraph:
    """BFS a dependency graph from `seed` using the country's provider.

    - `depth`: hops from the seed (cap small — the network explodes).
    - `breadth`: max counterparties expanded per node (top by strength/confidence).
    - `kinds`: relation types to discover (default business links; +social if `social`).
    - `social`: also collect board/promoter membership and derive interlock edges.
    - `validate`: annotate listed-listed edges with price co-movement afterwards.
    """
    kinds = kinds or {Relation.DEPENDS_ON, Relation.SUPPLIES_TO, Relation.CUSTOMER_OF,
                      Relation.PARTNERS_WITH, Relation.COMPETES_WITH, Relation.GROUP_ENTITY}
    provider = get_provider(country)
    graph = DependencyGraph()
    persons: dict[str, set[str]] = {}
    promoters: dict[str, set[str]] = {}

    root = provider.resolve(seed)
    if root is None:
        raise ValueError(f"could not resolve seed {seed!r} in {country}")
    graph.add_node(root)
    frontier: deque[tuple[Entity, int]] = deque([(root, 0)])
    seen = {root.id}

    while frontier:
        ent, d = frontier.popleft()
        if social:
            persons[ent.id] = {p.name for p in provider.board_members(ent)}
            promoters[ent.id] = {p.name for p in provider.promoter_group(ent)}
        edges = provider.discover(ent, kinds)
        edges.sort(key=lambda e: (e.strength or 0, {"low": 0, "medium": 1, "high": 2}[e.confidence]),
                   reverse=True)
        for e in edges[:breadth] if d < depth else edges:
            other_id = e.dst if e.src == ent.id else e.src
            other = provider.resolve(other_id) or Entity(other_id, other_id, country, "unlisted")
            graph.add_node(other)
            graph.add_edge(e)
            if d < depth and other.id not in seen:
                seen.add(other.id)
                frontier.append((other, d + 1))

    if social:
        derive_social_edges(graph, persons, promoters)
    if validate:
        validate_with_prices(graph, since=since)
    return graph
