#!/usr/bin/env python3
"""
drhp_vision.py — Enhanced DRHP extractor using a local vision model for table-heavy pages.

Strategy per page:
  - If pdfplumber detects tables -> render page as image -> ask the vision model to extract
  - Otherwise -> use pdfplumber text extraction (fast path)

Requires: pdf2image (poppler), ollama with qwen2.5vl:3b (validated chart/table OCR)

Usage:
    python drhp_vision.py --input output/JUBLFOOD/drhp.json --output output/JUBLFOOD/drhp_vision.md
    python drhp_vision.py --pdf output/JUBLFOOD/drhp.pdf --output output/JUBLFOOD/drhp_vision.md
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import urllib.request
from pathlib import Path

import pdfplumber
from pdf2image import convert_from_bytes
from pdf_to_md import table_to_md, text_to_md, Page, pages_to_markdown

OLLAMA_URL = "http://localhost:11434/api/generate"
VISION_MODEL = "qwen2.5vl:3b"

TABLE_PROMPT = (
    "This is a page from a legal/financial document. "
    "Extract all text and tables from this image exactly as they appear. "
    "Format tables using markdown table syntax with | separators. "
    "Preserve headings and paragraph structure. Output only the extracted content, no commentary."
)


def image_to_base64(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def vision_extract(img) -> str:
    payload = json.dumps({
        "model": VISION_MODEL,
        "prompt": TABLE_PROMPT,
        "images": [image_to_base64(img)],
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "").strip()
    except Exception as e:
        print(f"  [vision] Error: {e}")
        return ""


def has_tables(pg) -> bool:
    tables = pg.extract_tables()
    return bool(tables)


def process_pdf_bytes(pdf_bytes: bytes, dpi: int = 150) -> str:
    """Process PDF: vision for table pages, text extraction otherwise."""
    parts = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        total = len(pdf.pages)
        print(f"[drhp_vision] {total} pages total")

        # Identify which pages have tables
        table_pages = set()
        for i, pg in enumerate(pdf.pages):
            if has_tables(pg):
                table_pages.add(i)

        print(f"[drhp_vision] {len(table_pages)} pages with tables -> vision; {total - len(table_pages)} -> text")

        # Render table pages to images
        page_images = {}
        if table_pages:
            # Convert only table pages (1-indexed for pdf2image)
            page_nums_1idx = sorted(i + 1 for i in table_pages)
            # pdf2image supports first_page/last_page but not arbitrary pages; batch convert
            all_images = convert_from_bytes(pdf_bytes, dpi=dpi)
            for i in table_pages:
                page_images[i] = all_images[i]

        for i, pg in enumerate(pdf.pages):
            page_num = i + 1
            section = [f"---\n*Page {page_num}*\n"]

            if i in table_pages:
                print(f"  [vision] page {page_num}", end="\r")
                text = vision_extract(page_images[i])
                if text:
                    section.append(text)
                else:
                    # fallback to pdfplumber text
                    raw = pg.extract_text() or ""
                    section.append(text_to_md(raw))
            else:
                raw = pg.extract_text() or ""
                if raw:
                    section.append(text_to_md(raw))

            parts.append("\n".join(section))

    print()
    return "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Vision-enhanced DRHP extractor using a local vision model")
    parser.add_argument("--input", help="Path to existing drhp.json (from drhp_reader.py)")
    parser.add_argument("--pdf", help="Direct path to DRHP PDF file")
    parser.add_argument("--output", required=True, help="Output .md file path")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for page rendering (default: 150)")
    args = parser.parse_args()

    if args.input:
        data = json.loads(Path(args.input).read_text())
        # Re-download is needed; warn user
        print("ERROR: --input JSON doesn't store raw PDF bytes. Use --pdf with the original PDF file.")
        print("Hint: re-run drhp_reader.py with --output pointing to a .pdf to save raw bytes,")
        print("or download the PDF separately.")
        sys.exit(1)

    if not args.pdf:
        parser.error("Provide --pdf path to the DRHP PDF file")

    pdf_bytes = Path(args.pdf).read_bytes()
    print(f"[drhp_vision] Loaded {len(pdf_bytes)//1024}KB from {args.pdf}")

    markdown = process_pdf_bytes(pdf_bytes, dpi=args.dpi)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown)
    print(f"[drhp_vision] Saved {len(markdown)//1024}KB -> {out}")


if __name__ == "__main__":
    main()
