"""Discover individual news article URLs (with publish dates) from city listing pages."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from allowlist import ALLOWED_HOSTS

# CivicPlus / city CMS news detail patterns (same host as listing only).
_ARTICLE_HREF = re.compile(
    r"(?:/Home/Components/News/News/\d+)|(?:/newsflash/)|(?:/News/News/\d+)",
    re.I,
)

_SKIP_TITLE = re.compile(
    r"^(home|read more|learn more|click here|next|prev|previous|more)$",
    re.I,
)

_DATE_MDY_SLASH = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_DATE_LONG = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{1,2}),\s+(\d{4})\b"
)
_MONTHS = {
    m: i
    for i, m in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        start=1,
    )
}


def _parse_date(text: str) -> datetime | None:
    m = _DATE_MDY_SLASH.search(text)
    if m:
        mo, d, y = (int(x) for x in m.groups())
        try:
            return datetime(y, mo, d, 12, 0, tzinfo=timezone.utc)
        except ValueError:
            return None
    m = _DATE_LONG.search(text)
    if m:
        try:
            return datetime(
                int(m.group(3)), _MONTHS[m.group(1)], int(m.group(2)), 12, 0,
                tzinfo=timezone.utc,
            )
        except (ValueError, KeyError):
            return None
    return None


def _date_near(a_tag, title: str = "") -> datetime | None:  # type: ignore[no-untyped-def]
    """Look at nearby ancestors (short text only) for a publish date.

    The headline itself is stripped first so titles like
    "November 3, 2026, General Election Info" are not mistaken for the date.
    """
    node = a_tag
    for _ in range(4):
        node = node.parent
        if node is None:
            break
        text = " ".join(node.get_text(" ", strip=True).split())
        if len(text) > 700:
            break
        if title:
            text = text.replace(title, " ")
        found = _parse_date(text)
        if found:
            return found
    return None


def parse_listing_items(
    listing_html: str,
    listing_url: str,
    heading_selector: str,
    *,
    limit: int = 15,
) -> list[tuple[str, str, datetime | None, str]]:
    """Parse news cards straight from a listing page.

    For sites whose detail pages are bot-blocked but whose listing already
    carries the headline, date, and summary. Returns
    [(title, url, published_at|None, body_text), ...].
    """
    soup = BeautifulSoup(listing_html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        tag.decompose()
    headings = soup.select(heading_selector)
    heading_ids = {id(h) for h in headings}
    items: list[tuple[str, str, datetime | None, str]] = []
    seen: set[str] = set()

    for h in headings:
        title = " ".join(h.get_text().split())
        if len(title) < 8:
            continue
        # Smallest ancestor holding this heading plus some body text,
        # but never another heading.
        container = h
        for _ in range(5):
            parent = container.parent
            if parent is None:
                break
            if any(
                id(o) in heading_ids and o is not h for o in parent.select(heading_selector)
            ):
                break
            container = parent
            if len(" ".join(container.get_text().split())) >= len(title) + 120:
                break

        text = " ".join(container.get_text(" ", strip=True).split())
        body = text.replace(title, " ", 1).strip()
        published = _parse_date(body)
        body = re.sub(r"\s+", " ", body).strip()

        link = None
        for a in container.find_all("a", href=True):
            cand = urljoin(listing_url, a["href"]).split("?", 1)[0].split("#", 1)[0]
            host = urlparse(cand).hostname or ""
            if host in ALLOWED_HOSTS and _ARTICLE_HREF.search(cand):
                link = cand
                break
        if not link:
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80]
            link = f"{listing_url.split('#', 1)[0]}#{slug}"

        if link in seen:
            continue
        seen.add(link)
        items.append((title, link, published, body or title))
        if len(items) >= limit:
            break
    return items


def discover_article_links(
    listing_html: str,
    listing_url: str,
    *,
    limit: int = 20,
) -> list[tuple[str, str, datetime | None]]:
    """Return [(title, url, published_at|None), ...] for same-site news articles."""
    listing_host = urlparse(listing_url).hostname or ""
    listing_base = listing_host.replace("www.", "")
    soup = BeautifulSoup(listing_html, "lxml")
    found: list[tuple[str, str, datetime | None]] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#"):
            continue
        abs_url = urljoin(listing_url, href)
        host = urlparse(abs_url).hostname or ""
        if host not in ALLOWED_HOSTS or host.replace("www.", "") != listing_base:
            continue
        if not _ARTICLE_HREF.search(abs_url):
            continue

        title = " ".join((a.get_text() or "").split()).strip()
        if not title or _SKIP_TITLE.match(title) or len(title) < 8:
            continue

        clean_url = abs_url.split("?", 1)[0].split("#", 1)[0]
        if clean_url in seen:
            continue
        seen.add(clean_url)
        found.append((title, clean_url, _date_near(a, title)))
        if len(found) >= limit:
            break

    return found


def extract_article_text(html: str) -> str:
    """Article body only (skip site chrome). Falls back to whole-page text."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        tag.decompose()

    selectors = [
        "section.news_widget",
        "div.news_widget",
        "div.news_detail",
        "article",
        "main",
        "#contentarea",
        "div.content_area",
    ]
    best = ""
    for sel in selectors:
        el = soup.select_one(sel)
        if not el:
            continue
        text = el.get_text("\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if len(text) > len(best) and len(text) >= 80:
            best = text
            break
    return best
