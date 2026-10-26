from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.db import get_connection

router = APIRouter(prefix="/api", tags=["feed"])


def _rank_score(
    title: str,
    doc_type: str,
    interests: list[str],
    published_at,
    now,
) -> float:
    """Higher is better: interest keyword hits + recency."""
    interest_score = 0.0
    haystack = f"{title} {doc_type}".lower()
    for interest in interests:
        token = interest.strip().lower()
        if token and token in haystack:
            interest_score += 1.0

    recency_score = 0.0
    if published_at is not None and now is not None:
        age_days = max(0.0, (now - published_at).total_seconds() / 86400.0)
        # Newer docs score higher; ~0 after ~90 days
        recency_score = max(0.0, 1.0 - (age_days / 90.0))

    return (interest_score * 2.0) + recency_score


@router.get("/feed")
def get_feed(
    user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    language: str | None = Query(default=None),
) -> dict:
    """Ranked documents for the logged-in user's city."""
    city = user["city"]
    interests = list(user["interests"] or [])
    lang = (language or user["preferred_language"] or "en").lower()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                d.id,
                d.title,
                d.url,
                d.published_at,
                d.type,
                d.city,
                d.language,
                s.name AS source_name,
                s.last_fetched_at,
                now() AS server_now
            FROM documents d
            JOIN sources s ON s.id = d.source_id
            WHERE lower(d.city) = lower(%s)
              AND s.status = 'active'
              AND EXISTS (
                SELECT 1 FROM chunks c
                WHERE c.document_id = d.id AND c.is_active = true
              )
            ORDER BY d.published_at DESC NULLS LAST
            LIMIT 200
            """,
            (city,),
        ).fetchall()

    ranked: list[dict[str, Any]] = []
    for row in rows:
        score = _rank_score(
            row["title"],
            row["type"],
            interests,
            row["published_at"],
            row["server_now"],
        )
        ranked.append(
            {
                "id": str(row["id"]),
                "title": row["title"],
                "url": row["url"],
                "published_at": row["published_at"].isoformat()
                if row["published_at"]
                else None,
                "type": row["type"],
                "city": row["city"],
                "language": row["language"],
                "source_name": row["source_name"],
                "last_updated": row["last_fetched_at"].isoformat()
                if row["last_fetched_at"]
                else None,
                "score": round(score, 4),
                # Feed language request recorded for step 5 translations
                "requested_language": lang,
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return {
        "city": city,
        "language": lang,
        "items": ranked[:limit],
    }
