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


def latest_transcript(sym: str) -> str | None:
    sig = json.loads((HERE / "data" / f"{sym}_signals.json").read_text())
    for c in sig.get("concalls", []):
        if "Transcript" in c.get("text", "") and c.get("url"):
            return c["url"]
    return None


def fetch(sym: str) -> str:
    url = latest_transcript(sym)
    if not url:
        raise RuntimeError("no transcript url")
    out = HERE / "filings" / "concall" / f"{sym}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["uv","run","--extra","data","--extra","scrape","python",READER,
                        "--transcript",url,"--output",str(out)],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=400)
    if not out.exists():
        raise RuntimeError(f"reader failed: {r.stderr[-200:]}")
    return f"filings/concall/{sym}.json"


if __name__ == "__main__":
    tr = run_batch(BANKS, fetch, HERE / "_concall_tracker.json",
                   delay=5.0, jitter=3.0, max_retries=1, backoff=15.0)
    print("CONCALL SUMMARY:", tr.summary())
