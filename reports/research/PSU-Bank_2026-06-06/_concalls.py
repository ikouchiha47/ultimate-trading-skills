"""Background: extract each bank's LATEST concall transcript -> filings/concall/<sym>.json.
The agent then reads it for key points on the company page. Resumable via _concall_tracker.json.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from framework.batch import run_batch  # noqa: E402

BANKS = ["SBIN","BANKBARODA","UNIONBANK","CANBK","PNB","INDIANB","BANKINDIA","IOB","MAHABANK","UCOBANK"]
READER = str(ROOT / "skills/fundamentals/equity-research/scripts/concall_reader.py")


SREADER = str(ROOT / "skills/fundamentals/equity-research/scripts/screener_reader.py")


def fetch(sym: str) -> str:
    """Get screener documents (transcript+ai_summary+ppt per concall), then run the reader on the
    LATEST concall via --from-docs so it cascades transcript-PDF → AI-summary → PPT. BSE transcript
    PDFs are Akamai-gated (AttachHis); the AI summary (screener) is the reliable, clean source."""
    docs = HERE / "filings" / "concall" / f"{sym}_docs.json"
    docs.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["uv","run","--extra","data","--extra","scrape","python",SREADER,
                    "--symbol",sym,"--section","documents","--output",str(docs)],
                   cwd=str(ROOT), capture_output=True, text=True, timeout=300)
    d = json.loads(docs.read_text()); dd = d.get("documents", d)
    concalls = dd.get("concalls", [])
    if not concalls:
        raise RuntimeError("no concalls listed")
    latest = concalls[0]["date"]
    out = HERE / "filings" / "concall" / f"{sym}.json"
    r = subprocess.run(["uv","run","--extra","data","--extra","scrape","python",READER,
                        "--from-docs",str(docs),"--date",latest,"--output",str(out)],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=400)
    if not out.exists():
        raise RuntimeError(f"reader failed: {r.stdout[-150:]} {r.stderr[-150:]}")
    return f"filings/concall/{sym}.json ({latest})"


if __name__ == "__main__":
    tr = run_batch(BANKS, fetch, HERE / "_concall_tracker.json",
                   delay=5.0, jitter=3.0, max_retries=1, backoff=15.0)
    print("CONCALL SUMMARY:", tr.summary())
