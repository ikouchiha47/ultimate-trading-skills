"""US RelationshipProvider for PRIVATE (unlisted) companies — thin gatherer, agent-driven.

Private B2B/B2C companies (e.g. Rippling, Stripe, Databricks) have NO EDGAR 10-K/10-Q filings,
so the EDGAR reverse-lookup in us.py is useless here. Instead:

Structured (implemented here, thin):
- resolve: name-based slug; no ticker (unlisted), listed=False.
- discover: returns empty — the agent (SKILL.md) drives all discovery via WebSearch, Crunchbase,
  G2/Gartner, company websites, and news.

Agent-driven (the SKILL directs; this provider is a placeholder):
- Funding rounds / investors: Crunchbase, PitchBook, press releases
- Customers / case studies: company website, G2 reviews, integration marketplaces
- Competitors: G2/Gartner category pages, analyst reports
- Partners / integrations: company integrations page, partner directory
- Key people / board: LinkedIn, Crunchbase profiles, press releases (hires/departures)
- Employment history: LinkedIn profiles, company leadership pages

The agent fills the discovery_plan.md template and adds edges directly to the graph.
"""
from __future__ import annotations

from ..dependency_graph import Entity, Edge, Relation, register_provider


class USPrivateProvider:
    country = "US_PRIVATE"  # Separate key from US (EDGAR) — use for unlisted/private companies

    def resolve(self, name_or_ticker: str) -> Entity | None:
        """Resolve a private US company name to an Entity (listed=False, no ticker)."""
        slug = name_or_ticker.lower().replace(" ", "-").replace(",", "")
        return Entity(
            id=slug,
            name=name_or_ticker,
            country="US",
            kind="private",
            listed=False,
            domain=None,  # agent fills from discovery
        )

    def discover(self, entity: Entity, kinds: set[Relation]) -> list[Edge]:
        """Returns empty — all discovery is agent-driven via SKILL.md.

        The agent should:
        1. Write a discovery_plan.md (use the template)
        2. Search Crunchbase/PitchBook for funding rounds -> investor_in edges
        3. Search company website/case studies for customers -> supplies_to edges
        4. Search G2/Gartner for competitors -> competes_with edges
        5. Search integrations page for partners -> partners_with edges
        6. Search LinkedIn/Crunchbase for key people -> executive_of/director_of edges
        7. Track employment history for each person -> Entity.employment_history

        Add edges directly to the graph with Evidence(quote, url, source_type).
        """
        return []

    def board_members(self, entity: Entity) -> list[Entity]:
        return []  # Agent-driven: Crunchbase board seats, press releases, DEF 14A (if public parent)

    def promoter_group(self, entity: Entity) -> list[Entity]:
        return []  # Agent-driven: Crunchbase investors, 13D/G (if public minority stake)


register_provider(USPrivateProvider())
