"""Unified HTTP fetch with an automatic Playwright fallback — one client, no per-script Akamai hacks.

`fetch(url, expect=..., with_playwright=True)` tries a normal request first; if the response looks
BLOCKED (an Akamai/HTML challenge when binary was expected, a redirect-to-gated-host, a non-200, or
an error) it retries through a real headless-chromium **navigation** and captures the actual response
bytes (which beats hosts like BSE `AttachHis` / RBI `rbidocs` where a plain GET — even with cookies —
returns a challenge page). Returns raw bytes, or None if every route is blocked.

Usage:
    from framework.fetch import fetch
    pdf  = fetch(url, expect="pdf", referer="https://www.bseindia.com/")
    xlsx = fetch(url, expect="xlsx")
"""
from __future__ import annotations

from urllib.parse import urlsplit

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# magic-byte signatures per expected type (zip = xlsx/pptx/docx OOXML container)
_SIG = {"pdf": (b"%PDF",), "xlsx": (b"PK\x03\x04",), "pptx": (b"PK\x03\x04",),
        "zip": (b"PK\x03\x04",)}


def _ok(data: bytes | None, expect: str) -> bool:
    if not data:
        return False
    sig = _SIG.get(expect)
    if sig is None:                      # expect="any" — just reject obvious HTML challenge pages
        head = data[:512].lstrip().lower()
        return not head.startswith((b"<!doctype html", b"<html"))
    return any(data[:16].find(s) != -1 for s in sig)


def _via_requests(url: str, referer: str | None, timeout: int) -> bytes | None:
    import requests
    headers = {"User-Agent": _UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r.content
    except Exception:  # noqa: BLE001
        pass
    return None


def _via_browser(url: str, referer: str | None, expect: str, timeout: int) -> bytes | None:
    """Headless-chromium NAVIGATION + response capture — solves the Akamai JS challenge, then
    returns the bytes the browser actually received for `url` (works where ctx.request.get fails)."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:  # noqa: BLE001
        return None
    host_root = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=_UA, accept_downloads=True)
        try:
            page = ctx.new_page()
            # warm the origin so Akamai sets/solves its cookie, then capture the file response
            try:
                page.goto(referer or host_root, wait_until="domcontentloaded", timeout=timeout * 1000)
                page.wait_for_timeout(1200)
            except Exception:  # noqa: BLE001
                pass
            # 1) cookies set -> a context request often now returns the real bytes
            data = ctx.request.get(url, headers={"Referer": referer or host_root}).body()
            if _ok(data, expect):
                return data
            # 2) otherwise navigate AT the file and capture the network response (handles the
            #    redirect to AttachHis + the JS challenge the browser auto-solves)
            try:
                with page.expect_response(lambda r: r.url.rstrip("/") == url.rstrip("/")
                                          or url.split("/")[-1] in r.url, timeout=timeout * 1000) as ri:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
                data = ri.value.body()
                if _ok(data, expect):
                    return data
            except Exception:  # noqa: BLE001
                pass
        finally:
            browser.close()
    return None


def _via_curl_cffi(url: str, referer: str | None, timeout: int) -> bytes | None:
    """TLS/JA3 browser impersonation — beats many Akamai/WAF setups WITHOUT a browser. Optional dep
    (`curl_cffi`); cheap rung between plain requests and Playwright."""
    try:
        from curl_cffi import requests as creq
    except Exception:  # noqa: BLE001
        return None
    try:
        r = creq.get(url, headers={"Referer": referer} if referer else {},
                     impersonate="chrome", timeout=timeout)
        if r.status_code == 200:
            return r.content
    except Exception:  # noqa: BLE001
        pass
    return None


def fetch(url: str, *, expect: str = "any", referer: str | None = None,
          with_playwright: bool = True, timeout: int = 45) -> bytes | None:
    """Fetch with an escalation ladder. `expect` in {pdf,xlsx,pptx,zip,any}.

    PHILOSOPHY: prefer an alternate UN-GATED source over fighting anti-bot. The CALLER should cascade
    to a different source (e.g. concall: BSE PDF → screener AI-summary) rather than rely on defeating
    Akamai. This fn only escalates the transport for ONE url:
      1. requests (browser-like UA)            — cheap
      2. curl_cffi TLS impersonation           — cheap, optional dep; beats many WAFs sans browser
      3. Playwright headless navigation+capture — solves JS challenges that render the file
      (future rungs if ever needed: playwright-stealth / headful; undetected-chromedriver/Selenium)
    Returns bytes or None (None ⇒ caller should try a different source/format)."""
    data = _via_requests(url, referer, timeout)
    if _ok(data, expect):
        return data
    data = _via_curl_cffi(url, referer, timeout)
    if _ok(data, expect):
        return data
    if with_playwright:
        return _via_browser(url, referer, expect, timeout)
    return None
