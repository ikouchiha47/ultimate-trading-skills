#!/usr/bin/env python3
"""
drhp_reader.py — Find and extract Risk Factors from a company's DRHP.

Priority for finding the DRHP PDF:
  1. --url from screener_reader.py documents output (SEBI/BSE page)
  2. --from-docs JSON from screener_reader.py
  3. Google search fallback: "{company} DRHP site:sebi.gov.in OR site:bseindia.com"

Usage:
    python drhp_reader.py --from-docs /tmp/jublfood_docs.json
    python drhp_reader.py --url https://www.sebi.gov.in/filings/public-issues/...
    python drhp_reader.py --symbol JUBLFOOD --name "Jubilant Foodworks"
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

import requests
from playwright.async_api import async_playwright
import asyncio
from pdf_to_md import convert as pdf_convert

HEADERS = {
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

COVID_DATE = 2020  # split pre/post COVID by year


def resolve_pdf_url(landing_url: str) -> str | None:
    """
    Given a SEBI/BSE landing page URL, find the actual PDF URL.
    SEBI embeds PDFs in an <iframe src='...pdf'>.
    BSE links may be direct PDFs already.
    """
    if landing_url.endswith(".pdf"):
        return landing_url

    print(f"[drhp] Resolving PDF from landing page: {landing_url}")
    try:
        r = requests.get(landing_url, headers=HEADERS, timeout=15)
        html = r.text

        # SEBI pattern: <iframe src='/web/?file=/sebi_data/...pdf'>
        match = re.search(r"<iframe[^>]+src=['\"]([^'\"]+)['\"]", html, re.I)
        if match:
            src = match.group(1)
            from urllib.parse import urljoin, urlparse, parse_qs
            # If it's a viewer URL like /web/?file=...pdf, extract the file param
            parsed = urlparse(src)
            qs = parse_qs(parsed.query)
            if "file" in qs:
                file_path = qs["file"][0]
                base = f"{urlparse(landing_url).scheme}://{urlparse(landing_url).netloc}"
                return base + file_path
            if src.startswith("http"):
                return src
            return urljoin(landing_url, src)

        # BSE pattern: direct PDF link in page
        match = re.search(r'href=["\']([^"\']+\.pdf)["\']', html, re.I)
        if match:
            src = match.group(1)
            return src if src.startswith("http") else f"https://www.bseindia.com{src}"

    except Exception as e:
        print(f"[drhp] Failed to resolve PDF URL: {e}")

    return None


def download_pdf(url: str, referer: str = "https://www.sebi.gov.in/") -> bytes | None:
    headers = {**HEADERS, "Referer": referer}
    try:
        print(f"[drhp] Downloading: {url}")
        with requests.get(url, headers=headers, timeout=(10, 120), stream=True) as r:
            if r.status_code != 200:
                print(f"[drhp] HTTP {r.status_code}")
                return None
            chunks = []
            for chunk in r.iter_content(chunk_size=1024 * 256):
                chunks.append(chunk)
            data = b"".join(chunks)
            if b"%PDF" not in data[:10]:
                print(f"[drhp] Response is not a PDF")
                return None
            print(f"[drhp] Downloaded {len(data)//1024}KB")
            return data
    except Exception as e:
        print(f"[drhp] Download error: {e}")
    return None


async def google_search_drhp(company_name: str) -> str | None:
    """Search Google for the DRHP landing page URL."""
    query = f"{company_name} DRHP prospectus site:sebi.gov.in OR site:bseindia.com"
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    print(f"[drhp] Searching: {query}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=HEADERS["User-Agent"])
        await page.goto(search_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # Grab first result links from sebi.gov.in or bseindia.com
        links = await page.locator("a[href]").all()
        for link in links:
            href = await link.get_attribute("href") or ""
            if ("sebi.gov.in" in href or "bseindia.com" in href) and (
                "drhp" in href.lower() or "prospectus" in href.lower() or "public-issues" in href.lower()
            ):
                # Google wraps in /url?q=...
                match = re.search(r"/url\?q=([^&]+)", href)
                url = match.group(1) if match else href
                print(f"[drhp] Found via search: {url}")
                await browser.close()
                return url

        await browser.close()
    return None


def extract_pdf(pdf_bytes: bytes) -> dict:
    """Extract full text and tables — agent decides what's relevant."""
    markdown, pages = pdf_convert(pdf_bytes)
    print(f"[drhp] {len(pages)} pages")
    return {
        "markdown": markdown,
        "pages": [{"page": pg.number, "text": pg.text, "tables": pg.tables} for pg in pages],
    }


def run(args):
    landing_url = args.url

    # Get URL from docs JSON
    if not landing_url and args.from_docs:
        raw = json.loads(Path(args.from_docs).read_text())
        docs = raw.get("documents", raw)
        landing_url = docs.get("drhp")
        if not landing_url:
            print("[drhp] No DRHP URL found in documents JSON.")
        else:
            print(f"[drhp] Using DRHP URL from docs: {landing_url}")

    # Google search fallback
    if not landing_url and args.name:
        landing_url = asyncio.run(google_search_drhp(args.name))

    if not landing_url:
        print("ERROR: Could not find DRHP URL. Provide --url, --from-docs, or --name.")
        sys.exit(1)

    # Resolve landing page → actual PDF URL
    pdf_url = resolve_pdf_url(landing_url)
    if not pdf_url:
        print(f"ERROR: Could not find PDF link on page: {landing_url}")
        sys.exit(1)

    # Determine referer based on domain
    referer = "https://www.sebi.gov.in/" if "sebi.gov.in" in pdf_url else "https://www.bseindia.com/"

    pdf_bytes = download_pdf(pdf_url, referer=referer)
    if not pdf_bytes:
        sys.exit(1)

    result = extract_pdf(pdf_bytes)
    result["url"] = pdf_url

    print(f"[drhp] {len(result['pages'])} pages, {len(result['markdown'])} chars")
    print(f"\n── PREVIEW (first 2000 chars) ──\n")
    print(result["markdown"][:2000])

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2))
        print(f"\n[saved] {out}")

    if args.save_pdf:
        pdf_path = Path(args.save_pdf)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(pdf_bytes)
        print(f"[saved pdf] {pdf_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract risk factors from a company DRHP")
    parser.add_argument("--from-docs", help="JSON from screener_reader.py --section documents")
    parser.add_argument("--url", help="SEBI/BSE DRHP landing page or direct PDF URL")
    parser.add_argument("--name", help="Company name for Google search fallback")
    parser.add_argument("--output", help="Save JSON result to this path")
    parser.add_argument("--save-pdf", help="Also save raw PDF bytes to this path (needed for drhp_vision.py)")
    args = parser.parse_args()

    if not any([args.from_docs, args.url, args.name]):
        parser.error("Provide --from-docs, --url, or --name")

    run(args)


if __name__ == "__main__":
    main()
