#!/usr/bin/env python3
"""
screener_login.py — One-time login to screener.in. Saves session cookies for reuse.

Usage:
    python screener_login.py

Opens a visible browser. Log in manually, then press Enter in the terminal.
Session is saved to ~/.screener_session.json and reused by screener_reader.py.
"""

import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright

SESSION_FILE = Path.home() / ".screener_session.json"


BROWSERS = {
    "1": ("chromium", "Chromium (bundled)"),
    "2": ("firefox", "Firefox (bundled)"),
    "3": ("webkit", "WebKit/Safari (bundled)"),
}


def pick_browser() -> str:
    print("Which browser should open for login?")
    for key, (_, label) in BROWSERS.items():
        print(f"  {key}) {label}")
    choice = input("\nEnter number [default: 1]: ").strip() or "1"
    if choice not in BROWSERS:
        print(f"Invalid choice '{choice}', defaulting to chromium.")
        choice = "1"
    browser_type, label = BROWSERS[choice]
    print(f"Using: {label}\n")
    return browser_type


async def _wait_for_login(page, poll_interval=3, timeout=300):
    """Poll until the user is logged in (logout link appears)."""
    print("Waiting for you to log in", end="", flush=True)
    elapsed = 0
    while elapsed < timeout:
        await page.wait_for_timeout(poll_interval * 1000)
        elapsed += poll_interval
        try:
            if await page.locator("a[href='/logout/']").count():
                print(" ✓")
                return
        except Exception:
            pass
        print(".", end="", flush=True)
    print("\nTimed out waiting for login.")


async def run(browser_type: str):
    print("Opening browser for screener.in login...")
    print("Log in with your account, then come back here and press Enter.\n")

    token = _load_token_from_env()
    if token:
        # Token available — no browser needed, just save a storage state directly
        print("[token] Found SCREENER_TOKEN — saving session without opening browser.")
        cookies = _parse_cookie_string(token)
        state = {"cookies": [], "origins": []}
        for c in cookies:
            state["cookies"].append({**c, "sameSite": "Lax", "expires": -1})
        import json
        SESSION_FILE.write_text(json.dumps(state))
        print(f"[saved] Session saved to {SESSION_FILE}")
        return

    async with async_playwright() as p:
        launcher = getattr(p, browser_type)
        browser = await launcher.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        # Check if .env.dev has a token to pre-fill
        token = _load_token_from_env()
        if token:
            print(f"[token] Found SCREENER_TOKEN in env — injecting cookies directly.")
            cookies = _parse_cookie_string(token)
            await context.add_cookies(cookies)
            print(f"[token] Injected: {[c['name'] for c in cookies]}")

        page = await context.new_page()
        await page.goto("https://www.screener.in/login/", wait_until="domcontentloaded")

        if token:
            await page.goto("https://www.screener.in/", wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            logged_in = await page.locator("a[href='/logout/']").count()
            if logged_in:
                print("[token] Token worked — logged in successfully.")
            else:
                print("[token] Token didn't work. Please log in manually in the browser window.")
                await _wait_for_login(page)
        else:
            print("No token found. Please log in manually in the browser window.")
            await _wait_for_login(page)

        # Save session state
        await context.storage_state(path=str(SESSION_FILE))
        print(f"\n[saved] Session saved to {SESSION_FILE}")
        print("You can now run screener_reader.py — it will use this session automatically.")

        await browser.close()


def _parse_cookie_string(cookie_str: str) -> list[dict]:
    """Parse 'name=value; name2=value2' into Playwright cookie dicts."""
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies.append({
            "name": name.strip(),
            "value": value.strip(),
            "domain": ".screener.in",
            "path": "/",
            "httpOnly": name.strip() == "sessionid",
            "secure": True,
        })
    return cookies


def _load_token_from_env() -> str | None:
    """Try loading SCREENER_TOKEN from .env.dev in the project root."""
    env_files = [".env.dev", ".env", ".env.local"]
    for env_file in env_files:
        path = Path(env_file)
        if not path.exists():
            # try project root relative to this script
            path = Path(__file__).parent.parent.parent / env_file
        if path.exists():
            for line in path.read_text().splitlines():
                line = line.strip()
                if line.startswith("SCREENER_TOKEN=") or line.startswith("SCREENER_SESSION="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    # Also check environment
    return os.environ.get("SCREENER_TOKEN") or os.environ.get("SCREENER_SESSION")


def ensure_browser(browser_type: str):
    """Install the playwright browser if not already present."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", browser_type],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[warn] Could not install {browser_type}: {result.stderr.strip()}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"],
                        help="Browser to use (skips interactive prompt)")
    args = parser.parse_args()

    btype = args.browser if args.browser else pick_browser()
    ensure_browser(btype)
    asyncio.run(run(btype))
