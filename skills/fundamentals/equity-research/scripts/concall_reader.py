#!/usr/bin/env python3
"""
concall_reader.py — Extract content from a concall. Priority: Transcript PDF > AI Summary > PPT.

Usage:
    # From screener_reader.py --section documents output, pass the concall URLs:
    python concall_reader.py --symbol JUBLFOOD --date "Feb 2026"
    python concall_reader.py --transcript <pdf_url> --ai-summary <screener_url>
    python concall_reader.py --transcript <pdf_url>

    # Run screener_reader first to get URLs, then pass them:
    python screener_reader.py --symbol JUBLFOOD --section documents --output /tmp/docs.json
    python concall_reader.py --from-docs /tmp/docs.json --date "Feb 2026"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import tempfile
from pathlib import Path

import requests
from pdf_to_md import convert as pdf_convert

BSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

SESSION_FILE = Path.home() / ".screener_session.json"


def download_pdf(url: str) -> bytes | None:
    try:
        with requests.get(url, headers=BSE_HEADERS, timeout=(10, 60), stream=True) as r:
            if r.status_code != 200:
                print(f"[concall] HTTP {r.status_code} for {url}")
                return None
            chunks = []
            for chunk in r.iter_content(chunk_size=1024 * 256):
                chunks.append(chunk)
            data = b"".join(chunks)
            if b"%PDF" not in data[:10]:
                print(f"[concall] Response is not a PDF")
                return None
            return data
    except Exception as e:
        print(f"[concall] Download error: {e}")
    return None


async def fetch_ai_summary(url: str) -> str:
    """Fetch AI summary HTML fragment from screener (requires session)."""
    from playwright.async_api import async_playwright

    if not SESSION_FILE.exists():
        print("[ai_summary] No session file. Run screener_login.py first.")
        return ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=str(SESSION_FILE))
        page = await context.new_page()
        resp = await page.goto(url, wait_until="domcontentloaded")
        if resp.status != 200:
            print(f"[ai_summary] {url} → {resp.status}")
            await browser.close()
            return ""
        # Content is in <article> or direct body
        article = page.locator("article")
        if await article.count():
            text = await article.inner_text()
        else:
            text = await page.locator("body").inner_text()
        await browser.close()
        return text.strip()


def pick_concall(docs: dict, date_filter: str) -> dict | None:
    """Find a concall entry matching a date string like 'Feb 2026'."""
    date_filter = date_filter.strip().lower()
    for entry in docs.get("concalls", []):
        if date_filter in entry.get("date", "").lower():
            return entry
    return None


def run(args):
    result = {
        "date": args.date or "",
        "source": None,
        "text": "",
    }

    transcript_url = args.transcript
    ai_summary_url = args.ai_summary

    # Load from docs JSON if provided
    if args.from_docs:
        raw = json.loads(Path(args.from_docs).read_text())
        # screener_reader saves under result["documents"]
        docs = raw.get("documents", raw)
        if not args.date:
            print("ERROR: --date required with --from-docs (e.g. 'Feb 2026')")
            sys.exit(1)
        entry = pick_concall(docs, args.date)
        if not entry:
            print(f"No concall found for '{args.date}'. Available:")
            for c in docs.get("concalls", []):
                print(f"  {c['date']}")
            sys.exit(1)
        transcript_url = entry.get("transcript")
        ai_summary_url = entry.get("ai_summary")
        result["date"] = entry["date"]
        print(f"[concall] {entry['date']} — transcript={bool(transcript_url)} ai_summary={bool(ai_summary_url)}")

    # ── Priority 1: Transcript PDF ────────────────────────────────
    if transcript_url:
        print(f"[concall] Downloading transcript PDF...")
        pdf_bytes = download_pdf(transcript_url)
        if pdf_bytes:
            result["source"] = "transcript_pdf"
            markdown, pages = pdf_convert(pdf_bytes)
            result["text"] = markdown
            result["pages"] = len(pages)
            print(f"[concall] Transcript: {len(markdown)} chars, {len(pages)} pages")

    # ── Priority 2: AI Summary modal ─────────────────────────────
    if not result["text"] and ai_summary_url:
        print(f"[concall] Falling back to AI summary...")
        result["source"] = "ai_summary"
        result["text"] = asyncio.run(fetch_ai_summary(ai_summary_url))
        print(f"[concall] AI Summary: {len(result['text'])} chars extracted")

    if not result["text"]:
        print("[concall] No content retrieved.")
        sys.exit(1)

    # Output
    print(f"\n── SOURCE: {result['source']} ({'%.1f' % (len(result['text'])/1000)}k chars) ──\n")
    preview = result["text"][:3000]
    print(preview)
    if len(result["text"]) > 3000:
        print(f"\n... [{len(result['text']) - 3000} more chars]")

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2))
        print(f"\n[saved] {out}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Read concall transcript, AI summary, or PPT")
    parser.add_argument("--from-docs", help="Path to JSON output from screener_reader.py --section documents")
    parser.add_argument("--date", help="Concall date to pick, e.g. 'Feb 2026'")
    parser.add_argument("--transcript", help="Direct BSE transcript PDF URL")
    parser.add_argument("--ai-summary", help="Screener AI summary URL (/concalls/summary/<id>/)")
    parser.add_argument("--output", help="Save JSON result to this path")
    args = parser.parse_args()

    if not args.from_docs and not args.transcript and not args.ai_summary:
        parser.error("Provide --from-docs or at least one of --transcript / --ai-summary")

    run(args)


if __name__ == "__main__":
    main()
