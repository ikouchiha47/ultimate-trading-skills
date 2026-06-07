#!/usr/bin/env python3
"""
pdf_to_md.py — Pure transformer: PDF bytes -> clean Markdown.

Responsibilities:
- Text extraction per page
- ALL CAPS lines -> ## headings
- Tables -> Markdown table format
- Page separators

Does NOT download anything. Callers handle their own HTTP.

Usage as library:
    from pdf_to_md import convert
    markdown, pages = convert(pdf_bytes)

Standalone:
    python pdf_to_md.py --input report.pdf --output report.md
    python pdf_to_md.py --input report.pdf  # prints to stdout
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Page:
    number: int
    text: str
    tables: list[list[list[str]]] = field(default_factory=list)


def table_to_md(table: list[list[str | None]]) -> str:
    """Convert a pdfplumber table (list of rows) to a Markdown table."""
    if not table:
        return ""

    rows = [[str(cell or "").strip().replace("\n", " ") for cell in row] for row in table]
    if not rows:
        return ""

    col_count = max(len(r) for r in rows)
    rows = [r + [""] * (col_count - len(r)) for r in rows]

    lines = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * col_count) + " |",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def is_heading(line: str) -> bool:
    """Detect section headings: ALL CAPS, ≥3 words or ≥20 chars."""
    s = line.strip()
    if not s or len(s) < 3:
        return False
    if s == s.upper() and re.search(r"[A-Z]", s):
        if len(s) >= 20 or len(s.split()) >= 3:
            return True
    return False


def text_to_md(text: str) -> str:
    """Convert raw page text to Markdown, promoting headings."""
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            lines.append("")
        elif is_heading(s):
            lines.append(f"\n## {s}\n")
        else:
            lines.append(s)
    return "\n".join(lines)


def pdf_to_pages(pdf_bytes: bytes) -> list[Page]:
    """Extract all pages from PDF bytes."""
    import pdfplumber

    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, pg in enumerate(pdf.pages):
            pages.append(Page(
                number=i + 1,
                text=pg.extract_text() or "",
                tables=pg.extract_tables() or [],
            ))
    return pages


def pages_to_markdown(pages: list[Page]) -> str:
    """Render extracted pages as a single Markdown document."""
    parts = []
    for pg in pages:
        section = [f"---\n*Page {pg.number}*\n"]
        for table in pg.tables:
            md = table_to_md(table)
            if md:
                section.append(md + "\n")
        if pg.text:
            section.append(text_to_md(pg.text))
        parts.append("\n".join(section))
    return "\n\n".join(parts)


def convert(pdf_bytes: bytes) -> tuple[str, list[Page]]:
    """Convert PDF bytes -> (markdown, pages). Main entry point for callers."""
    pages = pdf_to_pages(pdf_bytes)
    return pages_to_markdown(pages), pages


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Convert a local PDF file to Markdown")
    parser.add_argument("--input", required=True, help="Path to PDF file")
    parser.add_argument("--output", help="Output .md file (default: stdout)")
    args = parser.parse_args()

    pdf_bytes = Path(args.input).read_bytes()
    markdown, pages = convert(pdf_bytes)
    print(f"[pdf_to_md] {len(pages)} pages -> {len(markdown)} chars", file=sys.stderr)

    if args.output:
        Path(args.output).write_text(markdown)
        print(f"[pdf_to_md] Saved to {args.output}", file=sys.stderr)
    else:
        print(markdown)
