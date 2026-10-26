"""Public dashboard catalog: news and ballots from the DB."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.config import SUPPORTED_LANGUAGES
from app.db import get_connection
from app.translate import translate_text

router = APIRouter(prefix="/api", tags=["catalog"])

DEFAULT_CITY = "Fremont"
# CA-14 region cities shown in the News city filter (matches v1 pills).
REGION_CITIES = ("Fremont", "Newark", "Union City", "Alameda County")


def _normalize_city_filter(city: str) -> str | tuple[str, ...]:
    """Return 'all' region tuple, or a single city name for exact match."""
    raw = (city or "").strip()
    if not raw or raw.lower() in ("all", "*", "all cities"):
        return REGION_CITIES
    # Accept common aliases from the GUI.
    aliases = {
        "alameda": "Alameda County",
        "alameda county": "Alameda County",
        "union city": "Union City",
        "union_city": "Union City",
    }
    key = raw.lower()
    if key in aliases:
        return aliases[key]
    for known in REGION_CITIES:
        if known.lower() == key:
            return known
    return raw


def _localize(text: str, language: str) -> tuple[str, bool]:
    """Translate with durable cache; fall back to original if providers fail."""
    if not text or language == "en":
        return text, language == "en"
    out = translate_text(text, language, allow_live=True)
    return out, out != text and bool(out.strip())


def _serialize(row: dict[str, Any], language: str) -> dict[str, Any]:
    title_en = row["title"] or ""
    snippet_en = row.get("snippet") or ""
    source_en = row["source_name"] or ""
    title = title_en
    snippet = row.get("translated_snippet") or snippet_en
    source_name = source_en
    title_ok = language == "en"
    snippet_ok = language == "en"

    if language != "en":
        title, title_ok = _localize(title_en, language)

        cached_snip = row.get("translated_snippet")
        if cached_snip and cached_snip.strip() and cached_snip.strip() != snippet_en.strip():
            snippet = cached_snip
            snippet_ok = True
        elif snippet_en:
            snippet, snippet_ok = _localize(snippet_en, language)

        source_name, _ = _localize(source_en, language)

    return {
        "id": str(row["id"]),
        "title": title,
        # Always keep English originals for client-side topic/category filters.
        "title_original": title_en if language != "en" else None,
        "url": row["url"],
        "published_at": row["published_at"].isoformat() if row["published_at"] else None,
        "type": row["type"],
        "city": row["city"],
        "language": row["language"],
        "requested_language": language,
        "source_name": source_name,
        "source_name_original": source_en if language != "en" else None,
        "last_updated": row["last_fetched_at"].isoformat()
        if row["last_fetched_at"]
        else None,
        "snippet": snippet or None,
        "snippet_original": snippet_en if language != "en" else None,
        # Honest: available only when the user-visible title was localized.
        "translation_available": title_ok if language != "en" else True,
        "snippet_translated": snippet_ok if language != "en" else True,
    }


def _list_docs(
    city: str,
    types: tuple[str, ...],
    limit: int,
    language: str,
) -> list[dict[str, Any]]:
    city_filter = _normalize_city_filter(city)
    if isinstance(city_filter, tuple):
        city_clause = "lower(d.city) = ANY(%s)"
        city_param: Any = [c.lower() for c in city_filter]
    else:
        city_clause = "lower(d.city) = lower(%s)"
        city_param = city_filter

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                d.id, d.title, d.url, d.published_at, d.type, d.city, d.language,
                s.name AS source_name,
                s.last_fetched_at,
                (
                    SELECT left(c.text, 220)
                    FROM chunks c
                    WHERE c.document_id = d.id AND c.is_active = true
                    ORDER BY c.page NULLS LAST, c.created_at
                    LIMIT 1
                ) AS snippet,
                (
                    SELECT left(t.translated_text, 220)
                    FROM chunks c
                    JOIN translations t ON t.chunk_id = c.id
                    WHERE c.document_id = d.id
                      AND c.is_active = true
                      AND lower(t.language) = lower(%s)
                    ORDER BY c.page NULLS LAST, c.created_at
                    LIMIT 1
                ) AS translated_snippet
            FROM documents d
            JOIN sources s ON s.id = d.source_id
            WHERE {city_clause}
              AND s.status = 'active'
              AND d.type = ANY(%s)
              AND EXISTS (
                SELECT 1 FROM chunks c
                WHERE c.document_id = d.id AND c.is_active = true
              )
            ORDER BY
                COALESCE(d.published_at, s.last_fetched_at) DESC NULLS LAST
            LIMIT %s
            """,
            (language, city_param, list(types), limit),
        ).fetchall()
    return [_serialize(r, language) for r in rows]


def _response_city(city: str) -> str:
    raw = (city or "").strip()
    if not raw or raw.lower() in ("all", "*", "all cities"):
        return "all"
    normalized = _normalize_city_filter(raw)
    if isinstance(normalized, tuple):
        return "all"
    return normalized


@router.get("/notices")
def get_notices(
    limit: int = Query(default=20, ge=1, le=100),
    city: str = Query(default="all"),
    language: str = Query(default="en"),
) -> dict:
    lang = language.lower().strip()
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    city_q = city.strip() or "all"
    items = _list_docs(city_q, ("news", "council"), limit, lang)
    return {
        "city": _response_city(city_q),
        "language": lang,
        "section": "news",
        "items": items,
    }


@router.get("/ballots")
def get_ballots(
    limit: int = Query(default=20, ge=1, le=100),
    city: str = Query(default="all"),
    language: str = Query(default="en"),
) -> dict:
    lang = language.lower().strip()
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    city_q = city.strip() or "all"
    items = _list_docs(city_q, ("ballot", "voter_guide"), limit, lang)
    return {
        "city": _response_city(city_q),
        "language": lang,
        "section": "ballots",
        "items": items,
    }
