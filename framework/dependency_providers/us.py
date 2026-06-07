"""US RelationshipProvider — backed by SEC EDGAR (free, structured, no Akamai).

Structured (implemented here, thin):
- resolve: ticker <-> CIK via EDGAR company_tickers.json; company name from submissions.
- discover: EDGAR **full-text search reverse lookup** — who NAMES this company in their 10-K/10-Q
  (candidate depends_on / customer / competitor edges, each citing the filing). Authoritative and
  computable; the AGENT (SKILL.md) classifies the exact relation/direction from filing context.

Agent-driven (the SKILL directs; not auto-parsed here, they're unstructured):
- forward customers/suppliers/concentration from the seed's own 10-K Item 1 / 1A,
- board interlocks from DEF 14A proxies, large holders from 13F / SCHED 13D/G.
"""
from __future__ import annotations

from ..dependency_graph import Entity, Edge, Evidence, Relation, register_provider

_UA = "ultimate-trading-skills research amitavaa.ag@gmail.com"   # EDGAR requires a UA with contact
_TICKERS: dict[str, dict] | None = None


def _load_tickers() -> dict[str, dict]:
    global _TICKERS
    if _TICKERS is None:
        import requests
        r = requests.get("https://www.sec.gov/files/company_tickers.json",
                         headers={"User-Agent": _UA}, timeout=30)
        r.raise_for_status()
        _TICKERS = {row["ticker"].upper(): row for row in r.json().values()}
    return _TICKERS


class USProvider:
    country = "US"

    def resolve(self, name_or_ticker: str) -> Entity | None:
        t = name_or_ticker.upper().strip()
        tickers = _load_tickers()
        if t in tickers:
            row = tickers[t]
            return Entity(id=t, name=row["title"], country="US", kind="company",
                          ticker=t, listed=True)
        # name match (loose) — first title containing the query
        for tk, row in tickers.items():
            if name_or_ticker.lower() in row["title"].lower():
                return Entity(id=tk, name=row["title"], country="US", ticker=tk, listed=True)
        return Entity(id=name_or_ticker, name=name_or_ticker, country="US", listed=False)

    def discover(self, entity: Entity, kinds: set[Relation],
                 lookback_years: int = 3) -> list[Edge]:
        """Reverse full-text lookup: companies whose RECENT 10-Ks NAME `entity` -> candidate edges.

        Date-filtered to the last `lookback_years` (no decade-old defunct names) and DEDUPED per
        company keeping its most-recent mention, then sorted newest-first. Still `low` confidence —
        the agent must read context to confirm relation/direction (SKILL.md)."""
        import datetime as _dt
        import requests
        edges: list[Edge] = []
        q = f'"{entity.name.split(",")[0]}"'                      # quote the core name
        today = _dt.date.today()
        startdt = today.replace(year=today.year - lookback_years).isoformat()
        try:
            r = requests.get("https://efts.sec.gov/LATEST/search-index",
                             params={"q": q, "forms": "10-K",
                                     "startdt": startdt, "enddt": today.isoformat()},
                             headers={"User-Agent": _UA}, timeout=30)
            r.raise_for_status()
            hits = r.json().get("hits", {}).get("hits", [])
        except Exception:  # noqa: BLE001
            return edges
        tickers = _load_tickers()
        cik_to_ticker = {str(row["cik_str"]).zfill(10): tk for tk, row in tickers.items()}
        best: dict[str, tuple[str, str, str]] = {}                # company_id -> (date, disp, cik)
        for h in hits:
            src = h.get("_source", {})
            ciks = src.get("ciks", [])
            disp = (src.get("display_names") or ["?"])[0]
            fdate = src.get("file_date", "")
            if not ciks:
                continue
            other_id = cik_to_ticker.get(str(ciks[0]).zfill(10)) or disp
            if other_id == entity.id:
                continue
            if other_id not in best or fdate > best[other_id][0]:   # keep most-recent mention
                best[other_id] = (fdate, disp, str(ciks[0]))
        for other_id, (fdate, disp, cik) in sorted(best.items(), key=lambda kv: kv[1][0],
                                                    reverse=True):
            url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
            edges.append(Edge(src=other_id, dst=entity.id, relation=Relation.DEPENDS_ON,
                              confidence="low",
                              evidence=[Evidence(quote=f"{disp} 10-K names {entity.name}",
                                                 url=url, date=fdate or None,
                                                 source_type="filing")]))
        return edges

    def board_members(self, entity: Entity) -> list[Entity]:
        return []   # DEF 14A proxy parsing is agent-driven (SKILL.md)

    def promoter_group(self, entity: Entity) -> list[Entity]:
        return []   # 13D/G + 13F holders are agent-driven (SKILL.md)


register_provider(USProvider())
