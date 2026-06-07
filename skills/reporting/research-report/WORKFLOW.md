# Sectoral research — workflow

The canonical flow for a query like *"research the top-10 PSU banks"*. Hard rule: **scripted core
only gathers + computes; the agent plans, structures, unifies and reviews.** Prose/structure is
authored from the template — never emitted by a program.

> **TODO is the heart.** Before anything, build a plan with the built-in task tools
> (`TaskCreate`) — one task per stage/sub-step — and keep it live (`TaskUpdate`: in_progress →
> completed; `TaskList` to check). Every stage below updates it; every gap found in review is added
> back as a task. The todo list is the single source of truth for progress across the whole flow.
>
> **If the task tools aren't available**, fall back to a **TODO file** — `_todo.md` in the report
> folder, ONE per unique research query/search — and update it the same way. Persist it until the
> **context changes** (the user pivots to a different search/investigation); on a context change,
> **confirm with the user** before replacing or abandoning the existing todo.

```mermaid
flowchart TD
    Q[/"Sector query: research &lt;sector&gt;"/] --> P

    subgraph A1["AGENT · Plan &amp; scope"]
        P["Resolve sector → index → constituents (nselib)"]
        P --> U{"Universe &amp; depth?<br/>(AskUserQuestion:<br/>top-N vs full · loan-book · social graph)"}
        U --> CFG["Create report folder + config<br/>(universe, depth, date)"]
    end

    CFG --> G

    subgraph CORE["CORE · SCRIPTED — gather + compute (batched, resumable)"]
        direction TB
        G["GATHER per name<br/>screener: fundamentals · quarters · about+key-points(segments) · signals<br/>jugaad: OHLCV + delivery (split-adjusted)<br/>filings: audit PDF · annual report · concall (transcript→AI-summary→PPT)"]
        G --> CH["CHARTS<br/>price+vol+DMA · financials(book/quarterly/EPS)"]
        G --> SEC["SECTOR<br/>RBI sectoral deployment (xlsx, Akamai-proof) · constituents"]
        G --> CMP["COMPUTE<br/>strategy harness (Sharpe-over-null) · influence graph · group graphs"]
        G --> T{"tally jugaad ≈ screener?"}
        T -- "mismatch" --> G
    end

    CH --> S
    SEC --> S
    CMP --> S
    T -- "ok" --> S

    subgraph A2["AGENT · Structure → Unify (author via template)"]
        S["AUTHOR company pages (per template)<br/>stat-card → visuals+caption cards → about/key-points →<br/>CFA sections + sector-force→company map → concall → DRHP → refs+news"]
        S --> SS["AUTHOR sector pages<br/>Overview(screener listing) · Industry(Porter/PESTEL/life-cycle/value-chain/SWOT + RBI) · Observations(buy/sell) · Glossary · References"]
        SS --> UNI["UNIFY — one structure, cross-links, colour code, glossary links"]
    end

    UNI --> APPLY

    subgraph A3["AGENT · Review step-by-step (trade-supervisor)"]
        APPLY["APPLY sector analysis → EACH company (seed)<br/>Porter/PESTEL forces · RBI credit-deployment mix · influence-graph<br/>bellwether/beta role · EARNED strategy anchor → how it hits THIS name"]
        APPLY --> UPD["UPDATE each company page<br/>(§ Sector forces → this company · refresh stance/risks)"]
        UPD --> R{"Discipline check<br/>computed-or-sourced? · unknowns genuine? · charts EMBEDDED? ·<br/>Sharpe-over-null? · no inline paths? · news as bullets?"}
    end

    R -- "gaps → re-gather/re-author" --> G
    R -- "ok" --> PUB["PUBLISH<br/>build_pages → MkDocs → GitHub Pages<br/>(no code leaked; fail-closed audit)"]
```

**Legend** — `A1/A2/A3` = agent stages (judgement, prose, review). `CORE` = Python (gather +
compute only). Loops: tally mismatch → re-gather; review gaps → re-gather or re-author.

## Stage outputs
| Stage | Owner | Produces |
|---|---|---|
| Plan &amp; scope | agent | report folder + config (universe, depth) |
| Gather | script | `data/` `filings/` |
| Charts/Sector/Compute | script | `charts/` `graph/` `strategies/` + RBI table |
| Structure/Unify | **agent** | `00_comprehensive` `00_industry` `01_observations` `<SYM>_equity_research` `GLOSSARY` `references` |
| Review | **agent** | discipline-passed report (or gaps routed back) |
| Publish | script | MkDocs site on Pages |
