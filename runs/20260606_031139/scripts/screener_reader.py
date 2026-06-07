#!/usr/bin/env python3
"""
screener_reader.py — Scrape company info from screener.in using Playwright.

Usage:
    # Search by name (uses homepage search)
    python screener_reader.py --search "Jubilant Foodworks"

    # Direct symbol lookup (skips search)
    python screener_reader.py --symbol JUBLFOOD

    # Get documents section (DRHP, annual reports, concalls)
    python screener_reader.py --symbol JUBLFOOD --section documents

    # Get all sections
    python screener_reader.py --symbol JUBLFOOD --section all
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "https://www.screener.in"


async def search_company(page, query: str) -> list[dict]:
    """Search for a company using screener.in's JSON API."""
    import urllib.parse
    search_url = f"{BASE_URL}/api/company/search/?q={urllib.parse.quote(query)}&v=3"
    print(f"[search] Querying: {search_url}")
    await page.goto(search_url, wait_until="domcontentloaded")
    await page.wait_for_timeout(500)

    try:
        body = await page.locator("body").inner_text()
        data = json.loads(body)
        # API returns a list of {id, name, url, ...}
        results = []
        for item in data:
            url = item.get("url") or f"/company/{item.get('id')}/"
            results.append({"name": item.get("name", ""), "url": url})
        return results
    except Exception as e:
        print(f"[search] Failed to parse search API response: {e}")
        # Fallback: try the Playwright-driven homepage search
        return await _search_via_browser(page, query)


async def _search_via_browser(page, query: str) -> list[dict]:
    """Fallback: use homepage search UI (div#desktop-search) via JS injection."""
    print(f"[search] Falling back to browser search UI...")
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(1500)

    # Use JS to reveal the hidden search input and type into it
    await page.evaluate("""
        const el = document.querySelector('div#desktop-search input');
        if (el) {
            el.style.display = 'block';
            el.closest('div#desktop-search').style.display = 'block';
            el.focus();
        }
    """)
    search_box = page.locator("div#desktop-search input")
    await search_box.type(query, delay=80)
    print(f"[search] Typed '{query}', waiting for results...")
    await page.wait_for_timeout(1500)

    results = []
    try:
        await page.wait_for_selector("div#desktop-search ul li a", timeout=6000)
        items = await page.locator("div#desktop-search ul li a").all()
        for item in items:
            text = (await item.inner_text()).strip()
            href = await item.get_attribute("href")
            if href:
                results.append({"name": text, "url": href})
    except PlaywrightTimeout:
        print("[search] No autocomplete results appeared.")

    return results


async def get_commentary(page) -> str:
    """Click Read More and extract the right-side modal content."""
    try:
        btn = page.locator("button[data-url*='/wiki/company/'][data-url*='/commentary/']").first
        await btn.wait_for(state="attached", timeout=8000)

        # The button carries data-modal-id that matches the injected <dialog id="...">
        modal_id = await btn.get_attribute("data-modal-id")
        await btn.click()
        print(f"[commentary] Clicked Read More, waiting for dialog#{modal_id}...")

        # Modal is dynamically injected — wait for it to appear in DOM
        await page.wait_for_selector("dialog.modal-right", state="attached", timeout=10000)
        # Then wait for it to be open/visible
        await page.wait_for_selector("dialog.modal-right[open]", state="attached", timeout=5000)
        dialog = page.locator("dialog.modal-right[open]").last
        content = dialog.locator("div.modal-content")
        await content.wait_for(state="visible", timeout=8000)
        text = await content.inner_text()
        return text.strip()
    except PlaywrightTimeout:
        print("[commentary] Modal did not appear — skipping.")
        return ""
    except Exception as e:
        print(f"[commentary] Error: {e}")
        return ""


async def get_documents(page) -> dict:
    """Navigate to Documents section and extract annual reports, concalls, and DRHP."""
    docs: dict = {"drhp": None, "annual_reports": [], "concalls": []}

    try:
        await page.goto(page.url.split("#")[0] + "#documents", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        # ── Annual reports ───────────────────────────────────────────
        ar_items = await page.locator("div.annual-reports ul.list-links li a").all()
        for a in ar_items:
            label = (await a.inner_text()).strip().splitlines()[0].strip()
            href = await a.get_attribute("href")
            if href and label:
                docs["annual_reports"].append({"label": label, "url": href})

        # DRHP is a standalone button inside the annual-reports block
        drhp = page.locator("div.annual-reports a", has_text="DRHP")
        if await drhp.count():
            docs["drhp"] = await drhp.first.get_attribute("href")

        # ── Concalls ─────────────────────────────────────────────────
        concall_items = await page.locator("div.concalls ul.list-links li").all()
        for li in concall_items:
            date = (await li.inner_text()).strip().splitlines()[0].strip()
            entry: dict = {"date": date, "transcript": None, "ppt": None, "ai_summary": None}

            for a in await li.locator("a.concall-link[href]").all():
                title = (await a.inner_text()).strip()
                href = await a.get_attribute("href")
                if "Transcript" in title:
                    entry["transcript"] = href
                elif "PPT" in title:
                    entry["ppt"] = href

            # AI Summary is a button with data-url, not a link
            ai_btn = li.locator("button.concall-link[data-url*='/concalls/summary/']")
            if await ai_btn.count():
                entry["ai_summary"] = "https://www.screener.in" + await ai_btn.first.get_attribute("data-url")

            docs["concalls"].append(entry)

    except PlaywrightTimeout as e:
        print(f"[documents] Timeout: {e}")
    except Exception as e:
        print(f"[documents] Error: {e}")

    return docs


SESSION_FILE = Path.home() / ".screener_session.json"


async def run(args):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.headed)

        ctx_kwargs = dict(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        if SESSION_FILE.exists():
            print(f"[auth] Using saved session from {SESSION_FILE}")
            ctx_kwargs["storage_state"] = str(SESSION_FILE)
        else:
            print(f"[auth] No session found. Run screener_login.py first for authenticated access.")

        context = await browser.new_context(**ctx_kwargs)
        page = await context.new_page()

        # ── Search flow ──────────────────────────────────────────────
        if args.search:
            results = await search_company(page, args.search)
            if not results:
                print("No results found.")
                await browser.close()
                return

            print(f"\nFound {len(results)} result(s):")
            for i, r in enumerate(results):
                print(f"  [{i}] {r['name']}  ->  {r['url']}")

            if args.pick is not None:
                chosen = results[args.pick]
            else:
                chosen = results[0]
                print(f"\nAuto-picking first result: {chosen['name']}")

            company_url = BASE_URL + chosen["url"].rstrip("/") + "/"
            if "consolidated" not in company_url:
                company_url += "consolidated/"
        else:
            company_url = f"{BASE_URL}/company/{args.symbol}/consolidated/"

        # ── Navigate to company page ─────────────────────────────────
        print(f"\n[nav] Opening {company_url}")
        await page.goto(company_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        result: dict = {"url": company_url, "commentary": "", "documents": {}}

        section = args.section

        if section in ("commentary", "all"):
            result["commentary"] = await get_commentary(page)
            if result["commentary"]:
                print("\n── COMMENTARY ──────────────────────────────────────────")
                print(result["commentary"][:2000])
                if len(result["commentary"]) > 2000:
                    print(f"... [{len(result['commentary']) - 2000} more chars]")

        if section in ("documents", "all"):
            result["documents"] = await get_documents(page)
            print("\n── DOCUMENTS ───────────────────────────────────────────")
            print(json.dumps(result["documents"], indent=2))

        # Save output
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(result, indent=2))
            print(f"\n[saved] {out}")

        await browser.close()
        return result


SESSION_FILE = SESSION_FILE if "SESSION_FILE" in globals() else Path.home() / ".screener_session.json"

# Screener top-ratios label -> snake_case key for the quality ("shouldn't have fallen") test.
_RATIO_KEYS = {
    "Market Cap": "market_cap_cr", "Current Price": "price", "Stock P/E": "pe",
    "Book Value": "book_value", "Dividend Yield": "dividend_yield_pct",
    "ROCE": "roce_pct", "ROE": "roe_pct", "Face Value": "face_value",
    "Debt to equity": "debt_to_equity", "Debt": "debt_cr",
}


def _num(raw: str) -> float | None:
    """Parse a screener value cell ('₹ 9,02,155 Cr.', '6.13 %', '10.8') to a float."""
    import re
    if raw is None:
        return None
    m = re.search(r"-?\d[\d,]*\.?\d*", raw.replace(",", ""))
    return float(m.group()) if m else None


def fetch_company_ratios(symbol: str, headless: bool = True) -> dict:
    """Sync scrape of screener.in top-ratios for SYMBOL (the quality metrics).

    Uses the saved session if present (public ratios don't require login). Returns
    {symbol, url, ratios{label:raw}, numeric{key:float}}. Raises if Playwright/chromium
    is unavailable (caller surfaces as MISSING + install hint).
    """
    from playwright.sync_api import sync_playwright

    url = f"{BASE_URL}/company/{symbol}/consolidated/"
    ratios: dict[str, str] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx_kwargs = dict(user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"))
        if SESSION_FILE.exists():
            ctx_kwargs["storage_state"] = str(SESSION_FILE)
        context = browser.new_context(**ctx_kwargs)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1500)
        for li in page.locator("ul#top-ratios li").all():
            try:
                name = li.locator("span.name").inner_text().strip()
                val = li.locator("span.value").inner_text().strip().replace("\n", " ")
            except Exception:  # noqa: BLE001
                continue
            if name:
                ratios[name] = val
        browser.close()
    numeric = {key: _num(ratios[label]) for label, key in _RATIO_KEYS.items() if label in ratios}
    return {"symbol": symbol, "url": url, "ratios": ratios, "numeric": numeric}


def _parse_ranges_table(t) -> dict:
    """One 'ranges-table' (e.g. Compounded Sales Growth) -> {'10y':15.0,'5y':18.0,...}."""
    period_key = {"10 years": "10y", "5 years": "5y", "3 years": "3y",
                  "ttm": "ttm", "1 year": "1y", "last year": "last_yr"}
    out: dict = {}
    for r in t.locator("tr").all()[1:]:
        txt = r.inner_text().strip()
        if ":" not in txt:
            continue
        label, _, val = txt.partition(":")
        key = period_key.get(label.strip().lower(), label.strip().lower())
        out[key] = _num(val)
    return out


def _parse_data_table(page, section_id: str) -> dict:
    """A financial section table -> {'periods':[...], 'rows':{label:[floats]}}.

    Covers profit-loss / balance-sheet / cash-flow (the trajectory the quality test needs:
    OPM%, Net Profit, Borrowings/debt, Cash from Operating)."""
    tbl = page.locator(f"section#{section_id} table.data-table").first
    if not tbl.count():
        return {"periods": [], "rows": {}}
    periods = [th.inner_text().strip() for th in tbl.locator("thead th").all()][1:]
    rows: dict[str, list] = {}
    for tr in tbl.locator("tbody tr").all():
        cells = tr.locator("td").all()
        if not cells:
            continue
        label = cells[0].inner_text().strip().splitlines()[0].strip().rstrip("+").strip()
        if label:
            rows[label] = [_num(c.inner_text()) for c in cells[1:]]
    return {"periods": periods, "rows": rows}


def fetch_company_fundamentals(symbol: str, headless: bool = True) -> dict:
    """Full quality picture in ONE page load: header ratios + growth trajectory + financial
    tables + document pointers (concall/DRHP/AR URLs for the skill to read — NOT read here).

    Returns {symbol, url, numeric, ratios, growth, tables, documents}.
    """
    from playwright.sync_api import sync_playwright

    url = f"{BASE_URL}/company/{symbol}/consolidated/"
    ratios: dict[str, str] = {}
    growth: dict[str, dict] = {}
    tables: dict[str, dict] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx_kwargs = dict(user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"))
        if SESSION_FILE.exists():
            ctx_kwargs["storage_state"] = str(SESSION_FILE)
        page = browser.new_context(**ctx_kwargs).new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1500)

        for li in page.locator("ul#top-ratios li").all():
            try:
                ratios[li.locator("span.name").inner_text().strip()] = \
                    li.locator("span.value").inner_text().strip().replace("\n", " ")
            except Exception:  # noqa: BLE001
                continue

        _growth_title = {"compounded sales growth": "sales_growth",
                         "compounded profit growth": "profit_growth",
                         "stock price cagr": "stock_cagr", "return on equity": "roe_trend"}
        for t in page.locator("table.ranges-table").all():
            title = t.locator("th").first.inner_text().strip().lower()
            key = _growth_title.get(title)
            if key:
                growth[key] = _parse_ranges_table(t)

        # shareholding = India-critical (promoter %, FII/DII trend). Pledge lives in the
        # promoter expand sub-row and is NOT captured here (skill reads it on demand).
        for sec in ("profit-loss", "balance-sheet", "cash-flow", "shareholding"):
            tables[sec.replace("-", "_")] = _parse_data_table(page, sec)

        browser.close()

    numeric = {key: _num(ratios[label]) for label, key in _RATIO_KEYS.items() if label in ratios}
    return {"symbol": symbol, "url": url, "numeric": numeric, "ratios": ratios,
            "growth": growth, "tables": tables,
            # Concall / DRHP / annual-report READING is the equity-research skill's agentic
            # job (PDF->text->LLM), not the data seam. The skill calls get_documents()/
            # concall_reader/drhp_reader on demand against this same `url`.
            "documents_note": "use equity-research skill (get_documents + concall/drhp readers)"}


def main():
    parser = argparse.ArgumentParser(description="Scrape screener.in company data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--search", help="Search query (uses homepage search box)")
    group.add_argument("--symbol", help="NSE/BSE symbol for direct URL (e.g. JUBLFOOD)")

    parser.add_argument(
        "--section",
        choices=["commentary", "documents", "all"],
        default="all",
        help="Which section to scrape (default: all)",
    )
    parser.add_argument("--pick", type=int, default=None, help="Index of search result to pick (default: 0)")
    parser.add_argument("--output", help="Save JSON output to this path")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser (debug)")

    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
