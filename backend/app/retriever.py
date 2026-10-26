"""Hybrid retrieval: pgvector meaning search + Postgres full-text, fused with RRF."""

from __future__ import annotations

import re
from typing import Any

from app.db import get_connection
from app.embedder import get_embedder

VECTOR_CANDIDATES = 50
FTS_CANDIDATES = 50
RRF_K = 60

_STOP = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    "of", "as", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "what", "which", "who", "whom", "when", "where",
    "why", "how", "about", "with", "from", "into", "over", "after", "before",
    "between", "than", "too", "very", "can", "could", "should", "would", "will",
    "just", "also", "this", "that", "these", "those", "it", "its", "my", "our",
    "your", "their", "me", "we", "you", "they", "i",
}


def _or_tsquery(question: str) -> str | None:
    """Build an OR tsquery from content words so multi-word questions still match."""
    words = re.findall(r"[a-zA-Z0-9]+", question.lower())
    terms = [w for w in words if len(w) > 2 and w not in _STOP]
    if not terms:
        return None
    # Escape single quotes for to_tsquery lexemes
    safe = [t.replace("'", "") for t in terms[:12]]
    return " | ".join(safe)


def _rrf_fuse(
    vector_rows: list[dict[str, Any]],
    fts_rows: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    scores: dict[str, float] = {}
    payload: dict[str, dict[str, Any]] = {}

    for rank, row in enumerate(vector_rows, start=1):
        cid = str(row["id"])
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)
        payload[cid] = row

    for rank, row in enumerate(fts_rows, start=1):
        cid = str(row["id"])
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)
        payload[cid] = row

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    results: list[dict[str, Any]] = []
    for cid, score in ordered[:limit]:
        item = dict(payload[cid])
        item["rrf_score"] = round(score, 6)
        results.append(item)
    return results


def _chunk_public(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": str(row["id"]),
        "document_id": str(row["document_id"]),
        "text": row["text"],
        "page": row["page"],
        "title": row["title"],
        "url": row["url"],
        "doc_type": row["type"],
        "city": row["city"],
        "source_name": row["source_name"],
        "rrf_score": row.get("rrf_score"),
    }


def retrieve_chunks(
    question: str,
    city: str | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    embedder = get_embedder()
    query_vec = embedder.embed_query(question)

    with get_connection() as conn:
        vector_rows: list[dict[str, Any]] = []
        if query_vec is not None:
            # pgvector expects a string literal like '[0.1,0.2,...]'
            vec_literal = "[" + ",".join(str(x) for x in query_vec) + "]"
            vector_rows = conn.execute(
                """
                SELECT
                    c.id, c.document_id, c.text, c.page,
                    d.title, d.url, d.type, d.city,
                    s.name AS source_name,
                    (c.embedding <=> %s::vector) AS distance
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                JOIN sources s ON s.id = d.source_id
                WHERE c.is_active = true
                  AND c.embedding IS NOT NULL
                  AND (%s::text IS NULL OR lower(d.city) = lower(%s))
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (vec_literal, city, city, vec_literal, VECTOR_CANDIDATES),
            ).fetchall()

        fts_rows: list[dict[str, Any]] = []
        tsquery = _or_tsquery(question)
        if tsquery:
            fts_rows = conn.execute(
                """
                SELECT
                    c.id, c.document_id, c.text, c.page,
                    d.title, d.url, d.type, d.city,
                    s.name AS source_name,
                    ts_rank_cd(
                        to_tsvector('english', c.text),
                        to_tsquery('english', %s)
                    ) AS rank
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                JOIN sources s ON s.id = d.source_id
                WHERE c.is_active = true
                  AND (%s::text IS NULL OR lower(d.city) = lower(%s))
                  AND to_tsvector('english', c.text) @@ to_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT %s
                """,
                (tsquery, city, city, tsquery, FTS_CANDIDATES),
            ).fetchall()

        # If FTS matches nothing, still return recent active chunks for the city
        # so Ask can show something useful for short / non-English queries.
        if not fts_rows and not vector_rows:
            fts_rows = conn.execute(
                """
                SELECT
                    c.id, c.document_id, c.text, c.page,
                    d.title, d.url, d.type, d.city,
                    s.name AS source_name,
                    0.0 AS rank
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                JOIN sources s ON s.id = d.source_id
                WHERE c.is_active = true
                  AND (%s::text IS NULL OR lower(d.city) = lower(%s))
                ORDER BY d.published_at DESC NULLS LAST
                LIMIT %s
                """,
                (city, city, limit),
            ).fetchall()

    fused = _rrf_fuse(vector_rows, fts_rows, limit=limit)
    return [_chunk_public(row) for row in fused]
