#!/usr/bin/env python3
"""
annual_report_reader.py — Download an annual report PDF and extract full text + tables.

Does not interpret or filter — dumps everything so the agent can analyse.

Usage:
    # From screener_reader.py documents output
    python annual_report_reader.py --from-docs /tmp/jublfood_docs.json --year 2025

    # Direct URL
    python annual_report_reader.py --url <pdf_url> --year 2025

Output JSON:
    {
      "year": 2025,
      "url": "...",
      "pages": [{"page": 1, "text": "...", "tables": [[...]]}],
      "full_text": "..."
    }
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import requests
from pdf_to_md import convert as pdf_convert

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def download_pdf(url: str) -> bytes | None:
    try:
        print(f"[ar] Downloading: {url}")
        with requests.get(url, headers=HEADERS, timeout=(10, 120), stream=True) as r:
            if r.status_code != 200:
                print(f"[ar] HTTP {r.status_code}")
                return None
            chunks = []
            for chunk in r.iter_content(chunk_size=1024 * 256):
                chunks.append(chunk)
            data = b"".join(chunks)
            if b"%PDF" not in data[:10]:
                print(f"[ar] Response is not a PDF")
                return None
            print(f"[ar] Downloaded {len(data)//1024}KB")
            return data
    except Exception as e:
        print(f"[ar] Download error: {e}")
    return None


def extract(pdf_bytes: bytes) -> dict:
    markdown, pages = pdf_convert(pdf_bytes)
    print(f"[ar] {len(pages)} pages")
    return {
        "markdown": markdown,
        "pages": [{"page": pg.number, "text": pg.text, "tables": pg.tables} for pg in pages],
    }


def pick_report(docs: dict, year: int) -> str | None:
    for r in docs.get("annual_reports", []):
        label = r.get("label", "")
        if str(year) in label:
            return r["url"]
    return None


def run(args):
    url = args.url

    if not url and args.from_docs:
        raw = json.loads(Path(args.from_docs).read_text())
        docs = raw.get("documents", raw)
        url = pick_report(docs, args.year)
        if not url:
            available = [r["label"] for r in docs.get("annual_reports", [])]
            print(f"No annual report found for {args.year}. Available: {available}")
            sys.exit(1)
        print(f"[ar] Using: {url}")

    if not url:
        print("ERROR: provide --url or --from-docs")
        sys.exit(1)

    pdf_bytes = download_pdf(url)
    if not pdf_bytes:
        sys.exit(1)

    result = extract(pdf_bytes)
    result["year"] = args.year
    result["url"] = url

    print(f"[ar] {len(result['pages'])} pages, {len(result['markdown'])} chars")
    print(f"\n── PREVIEW (first 2000 chars) ──\n")
    print(result["markdown"][:2000])

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2))
        print(f"\n[saved] {out}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Download and extract an annual report PDF")
    parser.add_argument("--from-docs", help="JSON from screener_reader.py --section documents")
    parser.add_argument("--url", help="Direct PDF URL")
    parser.add_argument("--year", type=int, required=True, help="Financial year e.g. 2025")
    parser.add_argument("--output", help="Save JSON result to this path")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
