"""Credit-rating rationale FETCHER (gather only — the agent does the reading).

Thin gatherer, matching the repo's rule "scripts gather, the agent is the analyst" (same as
concall transcripts / screener panels): for each rating-update event in signals.json
(`credit_ratings`: date + agency + link), fetch the rationale doc and store its CLEANED TEXT.
The AGENT then reads the text and extracts the real {instrument, rating, outlook, action} —
rationale docs rate MANY instruments at different grades, so regex parsing is unsafe and is NOT
done here.

Tooling per agency ('right tool' lesson): CRISIL + ICRA serve real HTML to curl_cffi (TLS
impersonation); Fitch/India-Ratings is a JS shell (no rating in raw HTML) → flagged
needs_playwright. Output: data/<sym>_rating_docs.json = [{date, agency, url, chars, text}].
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYMBOLS = ["SBIN", "BANKBARODA", "UNIONBANK", "CANBK", "PNB",
           "INDIANB", "BANKINDIA", "IOB", "MAHABANK", "UCOBANK"]


def _agency(text: str) -> str:
    t = text.lower()
    for k, v in [("crisil", "CRISIL"), ("icra", "ICRA"), ("fitch", "Fitch/India Ratings"),
                 ("india rating", "Fitch/India Ratings"), ("care", "CARE"),
                 ("brickwork", "Brickwork"), ("infomerics", "Infomerics"), ("smera", "Acuité/SMERA")]:
        if k in t:
            return v
    return "unknown"


def _clean(html: str) -> str:
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _fetch_text(url: str) -> str | None:
    try:
        from curl_cffi import requests as cr
        r = cr.get(url, impersonate="chrome", timeout=30)
        return _clean(r.text) if r.status_code == 200 else None
    except Exception as e:  # noqa: BLE001
        print("   fetch error:", e)
        return None


def run(sym: str) -> list[dict]:
    sig = json.loads((HERE / "data" / f"{sym}_signals.json").read_text())
    out = []
    for ev in sig.get("credit_ratings", []):
        label, url = ev.get("text", ""), ev.get("url", "")
        text = _fetch_text(url) if url else None
        rec = {"label": label, "agency": _agency(label + " " + url), "url": url,
               "chars": len(text or "")}
        if not text or len(text) < 12000:        # JS shell (Fitch ~7kb) — no rating in raw HTML
            rec["status"] = "needs_playwright"
            rec["text"] = text or ""
        else:
            rec["status"] = "fetched"
            rec["text"] = text
        out.append(rec)
    return out


if __name__ == "__main__":
    outdir = HERE / "filings" / "ratings"     # gitignored: large gather text, agent reads then extracts
    outdir.mkdir(parents=True, exist_ok=True)
    for sym in (sys.argv[1:] or SYMBOLS):
        print(f"[{sym}] fetching rationale docs ...")
        docs = run(sym)
        (outdir / f"{sym}_rating_docs.json").write_text(json.dumps(docs, indent=2))
        ok = sum(1 for d in docs if d["status"] == "fetched")
        print(f"   {len(docs)} events, {ok} fetched (rest need playwright) -> filings/ratings/{sym}_rating_docs.json")
