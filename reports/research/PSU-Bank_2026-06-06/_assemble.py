"""Assemble the per-company pages into the approved structure (idempotent):
  stat-card (colour-coded) + per-company links -> Visuals (charts FIRST, each with a summary card +
  feature legend) -> [preserved CFA narrative] -> Concall key points -> DRHP -> per-company References
  (incl. dated news). Regenerates the front matter + appended sections; keeps the hand-written
  narrative (## 1 .. footer) intact between the BEGIN/END markers.
"""
from __future__ import annotations
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = HERE / "data"
NAMES = {"SBIN":"State Bank of India","BANKBARODA":"Bank of Baroda","UNIONBANK":"Union Bank of India",
         "CANBK":"Canara Bank","PNB":"Punjab National Bank","INDIANB":"Indian Bank",
         "BANKINDIA":"Bank of India","IOB":"Indian Overseas Bank","MAHABANK":"Bank of Maharashtra",
         "UCOBANK":"UCO Bank"}
STANCE = {"CANBK":("🟢","Accumulate on 50-DMA dips"),"UNIONBANK":("🟢","Buy on dips"),
          "INDIANB":("🟢","Buy — let it base"),"SBIN":("🟡","Hold / add at the 200-DMA"),
          "BANKINDIA":("🟡","Watch for 200-DMA reclaim"),"MAHABANK":("🟡","Hold — don't chase (extended)"),
          "BANKBARODA":("🔴","Wait for 200-DMA reclaim"),"PNB":("🔴","Avoid / wait"),
          "IOB":("🔴","Avoid (overvalued laggard)"),"UCOBANK":("🔴","Avoid (weakest)")}
GROUP_IPO = {"SBIN":"SBI Funds Mgmt (SBI MF) IPO expected 2026.",
             "CANBK":"Canara Robeco AMC & Canara HSBC Life IPOs (RBI-approved divestment).",
             "PNB":"PNB Housing Finance already listed.", }
HAVE_GRAPH = {"SBIN","BANKBARODA","UNIONBANK","CANBK","PNB","INDIANB","BANKINDIA"}
BEGIN, END = "<!-- ASSEMBLED:BEGIN -->", "<!-- ASSEMBLED:END -->"


def _digest():
    return {r["s"]: r for r in json.loads((D / "_digest_all10.json").read_text())}


def _trend(d50, d200):
    if d50 > 0 and d200 > 0: return "🟢 uptrend (above both DMAs)"
    if d50 < 0 and d200 < 0: return "🔴 downtrend (below both DMAs)"
    return "🟡 pullback within trend (below 50-DMA, near/above 200-DMA)" if d200 >= -1 else "🟡 mixed"


def front(sym, r, about):
    emoji, stance = STANCE[sym]
    tv = f"https://in.tradingview.com/symbols/NSE-{sym}/"
    pb = r["pb"]; col = lambda c,g: c
    card = [
        f"# {NAMES[sym]} ({sym}) — Equity Research", "",
        f"> ### {emoji} Stance: **{stance}**",
        f"> **₹{r['price']}** · Mcap ₹{r['mcap']:,.0f} Cr · P/E {r['pe']} · P/B {pb} · "
        f"ROE {r['roe']}% · Div {r['divy']}% · 1-yr {r['ret1y']:+}%",
        f"> Trend: {_trend(r['d50'], r['d200'])} — vs50 {r['d50']:+}%, vs200 {r['d200']:+}%",
        f">",
        f"> **Links:** [Screener]({about.get('url','')}) · [TradingView]({tv}) · "
        f"[BSE]({about.get('bse','')}) · [NSE]({about.get('nse','')})", "",
        "_Colour code: 🟢 constructive · 🟡 neutral/watch · 🔴 avoid. "
        "See [GLOSSARY](GLOSSARY.md) for every header, term and chart colour._", "",
        "## Visuals (charts first)", "",
        "### Price · volume · 25/50/200-DMA · delivery",
        f"![{sym} price/volume/DMA](charts/{sym}_price_volume.png)",
        f"> **What it shows:** daily split-adjusted price with 25/50/200-day moving averages, volume "
        f"bars (green up / red down) and delivery%. **How to read:** above the 200-DMA = long-term "
        f"uptrend; the 50-DMA is the buy-the-dip anchor (our EARNED strategy). **This name:** "
        f"{_trend(r['d50'], r['d200'])}; delivery {r['deliv']}%, RelVol {r['volr']}×.", "",
        "### Financials — revenue/profit · the investment book · quarterly · EPS",
        f"![{sym} financials](charts/{sym}_financials.png)",
        f"> **What it shows:** (top-left) annual Revenue & Net Profit; (top-right) **the book** — "
        f"Deposits vs Investments (G-sec/SLR) vs Borrowing = where the money is; (bottom-left) "
        f"quarterly Net Profit momentum; (bottom-right) EPS trend. ₹ Cr, sourced screener.", ""]
    if sym in HAVE_GRAPH:
        card += ["### Group / dependency graph",
                 f"![{sym} group graph](charts/dependency_{sym}.png)",
                 "> **What it shows:** subsidiaries/JVs (sourced; edge = stake %). Green node = listed "
                 "(price-validated co-move with parent), yellow = unlisted, purple = foreign JV partner. "
                 "See [GLOSSARY](GLOSSARY.md#graph-diagrams).", ""]
    return "\n".join(card)


def concall_section(sym):
    """Clean pointer — the latest transcript is captured; KEY POINTS are an agent-read task
    (we never dump raw transcript boilerplate). Manual key points live in concall_keypoints.json."""
    f = HERE / "filings" / "concall" / f"{sym}.json"
    kp_file = HERE / "data" / "concall_keypoints.json"
    bullets = ""
    if kp_file.exists():
        kp = json.loads(kp_file.read_text()).get(sym)
        if kp:
            bullets = "\n".join(f"- {b}" for b in kp) + "\n\n"
    captured = "✅ latest transcript captured" if f.exists() else "⏳ extraction pending"
    status = "" if bullets else ("_Key points pending agent review — the transcript is captured; "
                                 "raw text is **not** dumped here (would be boilerplate). "
                                 "Read it in `filings/concall/" + sym + ".json`._\n")
    return (f"## Concall — key points (latest, sourced)\n_{captured} "
            f"(`filings/concall/{sym}.json`)._\n\n{bullets}{status}")


def drhp_section(sym):
    note = GROUP_IPO.get(sym, "No recent group IPO of note.")
    return (f"## DRHP\nN/A for the parent — {NAMES[sym]} is a long-listed PSU bank (no recent IPO/DRHP). "
            f"Group IPOs: {note}\n")


def refs_section(sym, about, signals):
    tv = f"https://in.tradingview.com/symbols/NSE-{sym}/"
    lines = [f"## References (this company)",
             f"- Screener: {about.get('url','')}",
             f"- TradingView: {tv}",
             f"- BSE: {about.get('bse','')}",
             f"- NSE: {about.get('nse','')}",
             f"- Audit snapshot: `filings/{sym}_screener_page.pdf`",
             f"- Data: `data/{sym}_*.json` / `.csv`",
             "", "**News & disclosures (dated, sourced):**"]
    for a in signals.get("announcements", [])[:6]:
        lines.append(f"- {a['text'][:120]} — {a['url']}")
    return "\n".join(lines) + "\n"


def main():
    dig = _digest()
    for sym in NAMES:
        f = HERE / f"{sym}_equity_research.md"
        if not f.exists():
            continue
        about = json.loads((D / f"{sym}_about.json").read_text())
        signals = json.loads((D / f"{sym}_signals.json").read_text())
        raw = f.read_text()
        # strip any prior assembled block, then find the narrative (## 1 onward)
        raw = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", raw, flags=re.S)
        m = re.search(r"^## 1\.", raw, flags=re.M)
        narrative = raw[m.start():] if m else raw
        # truncate any previously-appended tail sections (idempotent re-runs)
        cuts = [narrative.find("\n## Concall"), narrative.find("\n## DRHP"),
                narrative.find("\n## References (this company)")]
        cuts = [c for c in cuts if c != -1]
        if cuts:
            narrative = narrative[:min(cuts)]
        # narrative may start with the OLD title/visuals; keep only from ## 1.
        page = (f"{BEGIN}\n{front(sym, dig[sym], about)}\n---\n\n{END}\n"
                + narrative.rstrip() + "\n\n---\n\n"
                + concall_section(sym) + "\n" + drhp_section(sym) + "\n"
                + refs_section(sym, about, signals))
        f.write_text(page)
        print(f"assembled {sym}")


if __name__ == "__main__":
    main()
