"""STT-transcribe concall RECORDINGS for the banks where we only had an AI summary.

Picks the RIGHT acquisition tool per URL type (direct-audio -> ffmpeg, YouTube -> yt-dlp)
via concall_reader.fetch_recording_audio, then transcribes the FULL call in one
faster-whisper pass (small.en — better proper nouns than base.en). The recording transcript
is the PRIMARY concall source; the screener AI summary stays as a supplement (per the user).

UCOBANK omitted: its only recording link is unavailable. CANBK/INDIANB recordings lag to an
earlier quarter than the AI summary — each transcript is labelled with its actual call title.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills/fundamentals/equity-research/scripts"))

from concall_reader import fetch_recording_audio, transcribe_file   # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "filings" / "concall"
AUDIO = HERE / "filings" / "concall" / "_audio"

# latest AVAILABLE recording per bank (newest first in screener concalls list)
RECORDINGS = {
    "UNIONBANK": ("https://youtu.be/qEdClPrHVqY", "Union Bank of India Q4 FY26 Earnings Concall"),
    "INDIANB":   ("https://youtu.be/YAimioUc_xo", "Indian Bank Q3 FY26 Concall (22 Jan 2026)"),
    "CANBK":     ("https://youtu.be/x6BgY8XLz8k", "Canara Bank Q2 FY26 Earnings Concall"),
}
MODEL = "small.en"


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    for sym, (url, title) in RECORDINGS.items():
        t0 = time.time()
        mp3 = AUDIO / f"{sym}_rec.mp3"
        print(f"[{sym}] acquiring {url} -> {mp3}")
        got = fetch_recording_audio(url, str(mp3))
        if not got:
            print(f"[{sym}] FAILED to acquire recording; skipping")
            continue
        print(f"[{sym}] transcribing ({MODEL}) ...")
        text = transcribe_file(str(mp3), MODEL) or ""
        rec = {"symbol": sym, "source": "recording_stt", "model": MODEL,
               "recording_url": url, "title": title, "chars": len(text),
               "transcript": text}
        (OUT / f"{sym}_recording.json").write_text(json.dumps(rec, indent=2))
        print(f"[{sym}] DONE {len(text)} chars in {time.time()-t0:.0f}s "
              f"-> filings/concall/{sym}_recording.json")


if __name__ == "__main__":
    main()
