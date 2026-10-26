from __future__ import annotations

import hashlib
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


def assert_allowed(url: str) -> None:
    host = urlparse(url).hostname or ""
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Host not on allowlist: {host}")


def fetch_html(url: str, timeout: float = 30.0) -> tuple[str, str]:
    assert_allowed(url)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text, hashlib.sha256(resp.content).hexdigest()


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text("\n")
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
