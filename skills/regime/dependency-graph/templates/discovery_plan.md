# Discovery Plan — {ENTITY_NAME}

## Entity Characterization

| Field | Value |
|---|---|
| Name | {ENTITY_NAME} |
| Country | {COUNTRY} |
| Listed | {YES/NO} |
| B2B / B2C | {B2B/B2C} |
| Domain / Sector | {SECTOR} |
| Seed ticker / slug | {TICKER_OR_SLUG} |

## Discovery Strategy

For each edge type, pick a source archetype, name the concrete source, set expected confidence, and define a fallback. Every edge MUST be sourced — never inferred from price.

| Edge type | Source archetype | Concrete source | Expected confidence | Fallback |
|---|---|---|---|---|
| founder_of | Self-disclosure / regulator | {e.g. company about page, MCA DIN} | high | {fallback} |
| executive_of | Self-disclosure / regulator | {e.g. leadership page, SEC DEF 14A} | high | {fallback} |
| director_of | Regulator / registrar | {e.g. SEC DEF 14A, MCA board list} | high | {fallback} |
| investor_in | Regulator / aggregator | {e.g. Crunchbase, SEC 13F/D, screener} | medium | {fallback} |
| supplies_to / customer_of | Counterparty disclosure / news | {e.g. 10-K Item 1, annual report} | medium | {fallback} |
| competes_with | Third-party aggregator | {e.g. G2, Gartner, NSE sector} | medium | {fallback} |
| partners_with | Self-disclosure / news | {e.g. integrations page, press release} | medium | {fallback} |
| group_entity | Regulator / related-party | {e.g. screener related-party, 10-K} | high | {fallback} |

## Key People / Employee History

Track top people beyond the board — founders, CXOs, VPs, key hires, and their employment history. Each person becomes a `kind="person"` entity with `employment_history` and optionally `investments` (angel activity).

| Person | Role | Source | Employment history fields |
|---|---|---|---|
| {Name} | {CEO/CTO/etc} | {e.g. LinkedIn, company leadership page, press release} | `[{company, role, start, end}, ...]` |
| {Name} | {CFO/etc} | {source} | `[{company, role, start, end}, ...]` |

**Why it matters:**
- Shared employment history reveals board interlocks and promoter links
- Angel investment activity shows capital flow networks (person → company `investor_in` edges)
- Key hire patterns (e.g. ex-Google engineers → startup) signal talent migration and competitive dynamics
- Employment gaps or rapid job-hopping can indicate instability or strategic poaching

**Sources for people data:**
- LinkedIn profiles (agent-driven, not scraped)
- Company leadership/about pages
- SEC DEF 14A (US board/exec compensation filings)
- MCA DIN database (India director identification)
- Press releases (key hires, departures)
- Crunchbase / PitchBook (investor profiles, board seats)

## Source Archetypes (pick per edge)

1. **Regulator filings** — EDGAR (US), MCA/LLP (IN), Companies House (UK)
2. **Registrar of companies** — DIN (IN), SEC CIK (US), OpenCorporates
3. **Domain regulator / licence** — RBI (IN fintech), SEC/FINRA (US finance)
4. **Self-disclosure** — company website, annual report, investor presentation
5. **Counterparty disclosure** — customer/supplier named in another entity's filings
6. **News / WebSearch** — GDELT, press releases, dated articles
7. **Third-party aggregators** — Crunchbase, PitchBook, G2, Gartner, NSE/BSE sector lists
8. **Technical / market** — integration APIs, shared tech stack, co-patents

## B2B vs B2C Fork

- **B2B seed:** Named customer/supplier edges expected. Seek 10-K Item 1, case studies, integration marketplace.
- **B2C seed:** No named customer edges. Focus on market position, supply-side (vendors, tech stack), competitor mapping.

## Discipline Checklist

- [ ] Every edge has at least one Evidence with quote + URL
- [ ] No price-inferred edges (correlation ≠ relationship)
- [ ] Direction is correct (src → dst, not reversed)
- [ ] Confidence matches source quality (single mention = low, quantified = high)
- [ ] Unsourceable claims marked `unknown`, not guessed
