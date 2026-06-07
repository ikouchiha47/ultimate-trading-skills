---
name: dependency-graph
description: >
  Build a business + social DEPENDENCY graph for a company: who it depends on, who depends on it,
  partners/competitors, group entities, plus the social layer (board interlocks, promoter group).
  Use for "who uses <X>", "who does <X> depend on", "map <X>'s ecosystem", "what domain is <X> in
  and who's in those sectors". Country-polymorphic (India + US, extensible). You (the agent) DRIVE
  discovery from authoritative sources; the thin core assembles, validates and plots.
tags: [graph, dependency, supply-chain, ecosystem, board, promoter, india, us]
triggers: [dependency graph, who uses, who depends on, ecosystem, supply chain, board interlock]
---

# Dependency graph — the driver

## Core vs driver (read first)
- **Core (thin, generic):** `framework/dependency_graph.py` — the Entity/Edge model, the BFS
  `build_graph(seed, country, ...)` engine, `derive_social_edges` (board/promoter), and
  `validate_with_prices` (price-overlay bridge to `influence_graph`). Country-agnostic.
- **Providers (thin gatherers, per country):** `framework/dependency_providers/{india,us}.py`
  selected by `country`. They return the **structured, cleanly-APIable** edges only.
- **You, the agent (this SKILL):** drive the **unstructured / portal-gated** discovery the
  providers can't auto-parse, classify each candidate edge, enforce discipline, and assemble the
  report. Add a country = write a provider + register it; this driver doesn't change.

## IRON DISCIPLINE (non-negotiable)
- **Every edge is SOURCED** — a quote + dated link. A relationship is **NEVER inferred from price.**
- The **price overlay only corroborates** listed↔listed edges (does the market co-move). Absence of
  co-move ≠ no dependency; presence ≠ causation. Never create an edge from correlation.
- **Direction matters:** `depends_on` (dst is X's vendor/input) vs `supplies_to`/`customer_of`
  (dst depends on X). Classify it from the source context, don't guess.
- **Confidence:** `low` (single mention / name-match) → `medium` (named in a filing) → `high`
  (quantified ₹/$ or repeated). EDGAR reverse-lookup hits start `low` — you must REFINE them
  (read the filing context to confirm the relation/direction, or drop false positives like the
  JPMDB-mortgage-names-Salesforce noise).
- Unsourceable = it doesn't go in the graph.

## Discovery strategy is AGENT-REASONED — we give skeletons, not recipes
There is NO fixed "for Razorpay do X" recipe. Different entities expose different sources (a listed
US SaaS, a private Indian fintech, a PSU bank, a foreign conglomerate all differ). YOU reason which
sources exist for THIS entity and compose a strategy from the archetypes below. Razorpay's
case-studies are just one *instantiation* of the "self-disclosure" archetype — another company may
have none and need a different mix.

### Step A — characterise the entity (this determines what sources EXIST)
Decide and record (each sourced): **listed or private?** (sets `entity.listed`); **country?** (picks
the provider); **domain/sector?** (`entity.domain`); **B2B or B2C?** (B2B → look for named-customer
disclosures; B2C → user-base/market-share); **rough size/stage?** (startup → funding/press; mature →
filings). The answers tell you which archetypes are even available.

### Step B — for each EDGE TYPE you want, pick from the SOURCE ARCHETYPES (generic menu)
Map the abstract archetype to a concrete source for this entity. The country tables further down are
worked instantiations — extend them; they are not exhaustive.
1. **Regulator filings** — what the entity must disclose (US: SEC 10-K/DEF14A/13F · IN listed:
   NSE/BSE LODR, SEBI SAST, annual-report Ind-AS 24/AOC-1). Best for related-party, board, holders.
2. **Registrar of companies** — exists even for PRIVATE cos (IN: **MCA** via DIN → directors,
   charges/lenders, group; US: state filings). Best for board interlocks + group + lenders.
3. **Domain regulator / licence lists** — proves what the entity IS (IN fintech: **RBI** PA/PPI/NBFC
   registers; banks: RBI; pharma: CDSCO). Best for `domain` + the peer set.
4. **Self-disclosure** — company site, **case studies / customer logos**, investor decks, press
   releases. Best for customers/partners (B2B). *Reason about availability — not every firm has these.*
5. **Counterparty disclosure** — someone ELSE names the entity (US: EDGAR reverse full-text — the
   provider does this; IN: a listed customer's AR/concall names the vendor). Best for "who depends on X".
6. **News / dated WebSearch** — partnerships, deals, funding, customer wins (labelled `sourced`).
7. **Third-party aggregators** — Tofler/Zauba (MCA data), Tracxn/Crunchbase (startup cap-table,
   investors, competitors, sector). Useful but lower-trust → corroborate.
8. **Technical / market signals** — integration docs, job posts, app-store, and our **price overlay**
   (corroboration only). Weakest; never the sole basis for an edge.

### B2B vs B2C — a fork in WHAT counts as an edge
- **B2B seed** (Razorpay, Infosys, NVIDIA): "who uses it" = named business customers → real
  `supplies_to`/`customer_of` edges (case-studies, counterparty filings, concall).
- **B2C seed** (Zomato, a bank's retail arm, an FMCG brand): its users are **millions of consumers
  — NOT graph nodes.** Do **not** try to enumerate them as edges. Instead record **market position
  as a sourced node attribute** (market share %, MAU/users, GOV/AUM — from filings/industry reports)
  and build edges only from: **supply-side** (delivery/logistics, payment processor, suppliers),
  **competitors**, **group/subsidiaries**, and **distribution partners**. "Who depends on it" for a
  B2C platform = its **supply-side participants** (e.g. restaurants/merchants), not its end users.

### Step C — gather, extract typed+directional+sourced edges, refine, cite. Then expand.

### Plan FIRST — write a discovery plan before gathering (facilitates reasoning; save it)
Don't dive into sources ad-hoc. After Step A, produce a **discovery plan** — a table mapping each
edge type you want to the archetype+concrete source you'll try, *why* it's credible for THIS entity,
and a fallback. Save it to `graph/discovery_plan.md`; it's the audit trail of your reasoning and
stops you from defaulting to one source. Fill this skeleton:

```md
# Discovery plan — <ENTITY> (<country>, listed/private, domain, B2B/B2C, stage)
Characterisation (Step A, each sourced): listed=<>, country=<>, domain=<>, model=<B2B/B2C>, stage=<>

| Edge type wanted | Archetype | Concrete source for THIS entity | Why credible | Fallback if empty |
|---|---|---|---|---|
| depends_on (its vendors) | regulator/self | <e.g. 10-K Item 1 / site> | <> | <news> |
| supplies_to (who depends on it) | counterparty/self | <EDGAR reverse / case-studies> | <> | <news> |
| partners_with / competes_with | self/news | <> | <> | <> |
| group / subsidiaries | regulator/registrar | <AOC-1 / MCA> | <> | <> |
| board interlocks | registrar | <MCA-DIN / DEF14A> | <> | <> |
| promoter / holders | regulator | <shareholding / 13D-G> | <> | <> |
| domain + sector peers | domain-regulator | <RBI register → data_api.constituents()> | <> | <> |

Expansion: depth=<n>, breadth=<k>, validate(price overlay)=<y/n>. Out of scope / skipped: <…>
```
Then execute the plan row by row (Step C), updating it as sources turn out empty/blocked.

### Skeleton: when no archetype fits cleanly, compose a new strategy
Write down, before gathering: *(a)* the edge type sought, *(b)* the candidate archetype(s) and the
concrete source you'll try, *(c)* why it's credible, *(d)* the fallback if it's empty/blocked. Add
the resulting edges via the core API with full Evidence. If a source recurs, fold it into the
provider as a thin gatherer (and add a row to the country table below) so it stops being ad-hoc.

## Source skeletons by country (instantiations of the archetypes — extend, not exhaustive)

### US (country="US") — SEC EDGAR backbone (free, structured, no Akamai; UA w/ contact required)
| Edge | Archetype → concrete source | Auto? |
|---|---|---|
| who NAMES X (depends_on/competes candidates) | counterparty → EDGAR full-text (`efts.sec.gov`) | ✅ provider |
| X's customers/suppliers/concentration | regulator → **10-K Item 1 + 1A** | agent |
| board interlocks | regulator → **DEF 14A** proxy | agent |
| large holders / cross-holding | regulator → **13F, SCHED 13D/G** | agent |

### India (country="IN")
| Edge | Archetype → concrete source | Auto? |
|---|---|---|
| related-party (₹) corroboration | self/aggregator → screener (`fetch_related_party`) | ✅ provider |
| authoritative related-party (₹) | regulator → **LODR Reg-23** + **annual-report Ind-AS 24** | agent |
| subsidiaries/associates | regulator → **AOC-1** | agent |
| board interlocks (listed OR private) | registrar → **MCA**/DIN (Tofler/Zauba) | agent |
| promoter group / pledge | regulator → **shareholding** names + **SEBI SAST** | agent |
| named customers/partners | self/news → **concall** + dated news | agent |
| domain + peer set (esp. private) | domain-regulator → **RBI** registers; then `data_api.constituents()` for listed peers | agent |

## People & events layer (the social graph proper)
Beyond company↔company, track **people** (directors/founders/executives/investors) and **dated
events** (appointments, exits, deals, funding) — people are the edges that connect companies *before*
the price/filings do. Use `DIRECTOR_OF / EXECUTIVE_OF / FOUNDER_OF / INVESTOR_IN` (person→company);
the core then derives company↔company `board_interlock` from shared people. An **event** is just one
of these edges with `Evidence.date` set (e.g. "Brajesh Kumar Singh → CANBK MD&CEO, 2026-06-01").

**Discipline for the people layer:** only PUBLIC professional/regulatory roles (directors, KMP,
founders, named investors) — never private individuals or personal data. Every person-edge sourced
+ dated, same as company edges.

### Sources for people & events (authoritative-first; beyond manual WebFetch)
| Need | Source (archetype) | Access |
|---|---|---|
| director↔company (IN, incl. private) | **MCA / DIN** master data (registrar) | Tofler/Zauba aggregators; MCA21 |
| director/exec interlocks (US) | **SEC DEF 14A** proxy + **Form 3/4/5** insiders (regulator) | EDGAR (free, structured) |
| officers across companies (global) | **OpenCorporates** officer data (registrar aggregator) | API, free tier |
| corporate ownership hierarchy | **GLEIF LEI** parent/child relationships (regulator) | API, free |
| founders/investors/funding events | **Crunchbase / Tracxn** (aggregator) | API, paid-ish |
| notable person↔company facts | **Wikidata** (employer/founder/board) | SPARQL, free |
| global news EVENTS at scale (deals, appointments, meetings) | **GDELT** events DB (news-mined) | API, free — far beyond manual WebFetch |
| corporate event feed (IN) | **NSE/BSE announcements** (we already capture in equity-research signals) | scrape |
| material events (US) | **SEC 8-K** (regulator) | EDGAR |
| professional connections | LinkedIn-adjacent providers (PeopleDataLabs/Proxycurl) | paid API; ToS-bound — use cautiously |

The structured/authoritative ones (MCA, SEC DEF14A/Form4, OpenCorporates, GLEIF, Wikidata, GDELT)
are the backbone; WebFetch/news fills gaps. Treat aggregators (Tofler/Crunchbase) as corroboration.

## Worked example (a REASONING trace, not a recipe) — Razorpay (private, IN, fintech, B2B)
- *Characterise:* private (no ticker → `listed=False`), IN, B2B. → filings backbone N/A; lean on
  registrar + domain-regulator + self-disclosure + news.
- *domain:* RBI Payment-Aggregator licence list + site → `domain="fintech/payments"` (sourced).
- *who depends on it:* self-disclosure (case-study/customer pages) + news "X integrates Razorpay";
  any *listed* customer naming it in AR/concall → `supplies_to` edges.
- *board/lenders/group:* MCA (DIN directors → interlocks; charges → lenders; group entities).
- *investors:* funding-round news → ownership/`promoter_link` edges.
- *"companies in those sectors":* map each customer's sector → listed peers via
  `data_api.constituents()`.
A different seed (say a listed PSU bank) would instead lean on LODR/AR/shareholding and skip
case-studies entirely — that's the point: **you choose the mix.**

## How to run it
```python
from framework import dependency_graph as dg

# 1) Structured pass — provider does the cleanly-APIable discovery + BFS expansion.
g = dg.build_graph("CRM", "US", depth=2, breadth=8, social=True, validate=True)   # US example
# g = dg.build_graph("RAZORPAY", "IN", depth=1, social=True)                       # private India

# 2) Agent pass — YOU add the sourced edges the provider couldn't auto-parse:
from framework.dependency_graph import Edge, Evidence, Relation, Entity
g.add_node(Entity("VEEV", "Veeva Systems", "US", ticker="VEEV", domain="life-sciences SaaS"))
g.add_edge(Edge("VEEV", "CRM", Relation.DEPENDS_ON, confidence="high",
                evidence=[Evidence("Veeva built on the Salesforce platform; 10-K risk factor",
                                   url="https://www.sec.gov/...", date="2025-03-31",
                                   source_type="filing")]))
# refine/drop the provider's low-confidence reverse-lookup candidates after reading context.

# 3) Persist + (optionally) plot, reusing the influence-graph plotter.
g.save("reports/research/<name>/graph/dependency_graph.json")
from framework import influence_graph as ig
nodes = {nid: ig.Node(nid, n.kind, f"stock:{n.ticker}" if n.ticker else nid, n.name)
         for nid, n in g.nodes.items()}
ig.plot_graph(nodes, list(g.edges.values()), title="<X> dependency graph",
              out_path="reports/research/<name>/charts/dependency_graph.png")
```

## Discovery loop (per node, BFS to `depth`)
1. **Resolve** the entity (provider): listed → ticker; unknown → `listed=False` (private path).
2. **Structured discover** (provider): EDGAR reverse-lookup (US) / screener RPT (IN).
3. **Agent discover** (you): per the source tables above — read 10-K/AR/concall/news/MCA, extract
   typed, directional, sourced edges; refine the provider's `low`-confidence candidates.
4. **Social layer**: collect board directors + promoter-group names per company; the core's
   `derive_social_edges` links companies SHARING a director/promoter (interlock/promoter_link).
5. **Expand**: top-`breadth` counterparties by strength/confidence become new seeds.
6. **Validate** (optional): `validate_with_prices` annotates listed↔listed edges with co-movement.

## Output (assemble like research-report)
`graph/dependency_graph.json` + `charts/dependency_graph.png` + a **sourced narrative**: the seed's
domain, who depends on it (ranked by confidence/strength), who it depends on, partners/competitors,
the social layer (interlocks/promoter links), and — for private seeds — the sector-peer expansion.
Every edge cites its source; the price overlay is labelled corroboration, not proof.

## Discipline checklist
- [ ] Every edge has ≥1 Evidence with a dated link; `low`-confidence provider hits were refined or dropped.
- [ ] Direction + relation type set from source context, not assumed.
- [ ] No edge created from price; price overlay clearly marked corroboration.
- [ ] Private seeds: domain sourced (RBI/site), customers from case-studies/news, sector-peers via constituents.
- [ ] Social edges trace to a named shared director/promoter.
