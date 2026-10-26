"""Fetch allowlisted HTML: httpx first, Playwright browser on bot-block 403."""

from __future__ import annotations

import atexit
import hashlib
import os
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from allowlist import ALLOWED_HOSTS

# Official sites (Akamai / bot filters) reject custom bot UAs with 403.
# Use a normal browser UA for local/educational allowlisted fetches only.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Set INGEST_BROWSER=0 to skip Playwright (e.g. slim CI images without Chromium).
BROWSER_FALLBACK = os.getenv("INGEST_BROWSER", "1").strip().lower() not in (
    "0",
    "false",
    "no",
    "off",
)


def assert_allowed(url: str) -> None:
    host = urlparse(url).hostname or ""
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Host not on allowlist: {host}")


def _looks_blocked(html: str, status_code: int | None = None) -> bool:
    if status_code == 403:
        return True
    low = (html or "").lower()
    markers = (
        "access denied",
        "akamaighost",
        "errors.edgesuite.net",
        "request blocked",
        "bot detection",
        "attention required",
        "cf-browser-verification",
    )
    return any(m in low for m in markers) and len(low) < 8000


def fetch_html_httpx(url: str, timeout: float = 30.0) -> tuple[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
        resp = client.get(url)
        # Allow caller to decide on 403 → browser; other errors still raise.
        if resp.status_code == 403:
            raise httpx.HTTPStatusError(
                f"Client error '403 Forbidden' for url '{resp.url}'",
                request=resp.request,
                response=resp,
            )
        resp.raise_for_status()
        text = resp.text
        if _looks_blocked(text):
            raise RuntimeError("Response looks like a bot-block interstitial")
        return text, hashlib.sha256(resp.content).hexdigest()


def _launch_browser(playwright):  # type: ignore[no-untyped-def]
    """Prefer installed Google Chrome — stock headless Chromium is often 403'd."""
    launch_args = ["--disable-blink-features=AutomationControlled"]
    headed = os.getenv("INGEST_BROWSER_HEADED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    # 1) System Chrome (best success vs Akamai on CivicPlus city sites).
    try:
        return playwright.chromium.launch(
            channel="chrome",
            headless=not headed,
            args=launch_args,
        )
    except Exception:
        pass
    # 2) Bundled Chromium.
    return playwright.chromium.launch(headless=not headed, args=launch_args)


_session: dict = {}


def close_browser() -> None:
    """Close the shared browser session (called automatically at exit)."""
    ctx = _session.pop("context", None)
    browser = _session.pop("browser", None)
    pw = _session.pop("pw", None)
    try:
        if ctx:
            ctx.close()
        if browser:
            browser.close()
    finally:
        if pw:
            pw.stop()


atexit.register(close_browser)


def _get_context():  # type: ignore[no-untyped-def]
    """One shared browser/context so many pages don't each pay a launch cost."""
    if "context" in _session:
        return _session["context"]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        ) from exc
    pw = sync_playwright().start()
    browser = _launch_browser(pw)
    context = browser.new_context(
        user_agent=USER_AGENT,
        locale="en-US",
        viewport={"width": 1280, "height": 900},
    )
    _session.update(pw=pw, browser=browser, context=context)
    return context


def fetch_html_browser(url: str, timeout: float = 45.0) -> tuple[str, str]:
    """Load URL in a real browser (bypasses many Akamai bot checks)."""
    context = _get_context()
    page = context.new_page()
    try:
        page.set_default_timeout(timeout * 1000)
        resp = page.goto(url, wait_until="domcontentloaded")
        # Give CivicPlus / JS a moment to settle.
        page.wait_for_timeout(1200)
        html = page.content()
        final_url = page.url
        status = resp.status if resp else None
    finally:
        page.close()

    # Redirect may land on a sibling official host (e.g. newark.org → newarkca.gov).
    final_host = urlparse(final_url).hostname or ""
    if final_host not in ALLOWED_HOSTS:
        raise ValueError(f"Browser redirected off allowlist: {final_host}")

    if status == 403 or _looks_blocked(html, status):
        raise RuntimeError(
            f"Browser fetch still blocked (status={status}) for {final_url}"
        )
    if not html or len(html) < 200:
        raise RuntimeError(f"Browser fetch returned empty page for {final_url}")

    return html, hashlib.sha256(html.encode("utf-8", errors="replace")).hexdigest()


def fetch_html(url: str, timeout: float = 30.0) -> tuple[str, str]:
    """Fetch allowlisted HTML. Tries httpx, then Playwright on 403/bot-block."""
    assert_allowed(url)
    try:
        return fetch_html_httpx(url, timeout=timeout)
    except (httpx.HTTPStatusError, httpx.TransportError, RuntimeError) as exc:
        blocked = isinstance(exc, httpx.HTTPStatusError) and exc.response is not None and (
            exc.response.status_code == 403
        )
        blocked = blocked or "403" in str(exc) or "bot-block" in str(exc).lower()
        if not blocked or not BROWSER_FALLBACK:
            raise
        print(f"  browser fallback → {url}")
        return fetch_html_browser(url, timeout=max(timeout, 45.0))


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        tag.decompose()
    # Prefer primary content regions on CivicPlus / city CMS pages.
    root = (
        soup.find("main")
        or soup.find(id=re.compile(r"content|center|main", re.I))
        or soup.find(class_=re.compile(r"content|main-content|news", re.I))
        or soup
    )
    text = root.get_text("\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 700) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(para) < 40:
            continue
        if not buf:
            buf = para
        elif len(buf) + 1 + len(para) <= max_chars:
            buf = f"{buf}\n\n{para}"
        else:
            chunks.append(buf)
            buf = para
    if buf:
        chunks.append(buf)
    # Cap so a noisy page does not flood the feed
    return chunks[:12]
