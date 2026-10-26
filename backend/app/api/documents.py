from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.config import SUPPORTED_LANGUAGES
from app.db import get_connection
from app.translate import persist_chunk_translation, translate_text

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents/{document_id}")
def get_document(
    document_id: uuid.UUID,
    language: str = Query(default="en"),
) -> dict:
    lang = language.lower().strip()
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"

    with get_connection() as conn:
        doc = conn.execute(
            """
            SELECT
                d.id, d.title, d.url, d.published_at, d.type, d.city, d.language,
                s.name AS source_name,
                s.last_fetched_at
            FROM documents d
            JOIN sources s ON s.id = d.source_id
            WHERE d.id = %s
            """,
            (document_id,),
        ).fetchone()

        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        chunks = conn.execute(
            """
            SELECT
                c.id,
                c.text,
                c.page,
                t.translated_text
            FROM chunks c
            LEFT JOIN translations t
              ON t.chunk_id = c.id AND lower(t.language) = lower(%s)
            WHERE c.document_id = %s AND c.is_active = true
            ORDER BY c.page NULLS LAST, c.created_at
            """,
            (lang, document_id),
        ).fetchall()

    title = doc["title"] or ""
    source_name = doc["source_name"] or ""
    if lang != "en":
        title = translate_text(title, lang, allow_live=True)
        source_name = translate_text(source_name, lang, allow_live=True)

    out_chunks = []
    for c in chunks:
        original = c["text"]
        text = c["translated_text"]
        available = bool(text)
        if not text and lang != "en":
            text = translate_text(original, lang, allow_live=True)
            available = text != original
            if available:
                persist_chunk_translation(str(c["id"]), lang, text, provider="live")
        elif not text:
            text = original
        out_chunks.append(
            {
                "id": str(c["id"]),
                "text": text,
                "original_text": original if available and lang != "en" else None,
                "page": c["page"],
                "translation_available": available or lang == "en",
            }
        )

    return {
        "id": str(doc["id"]),
        "title": title,
        "url": doc["url"],
        "published_at": doc["published_at"].isoformat() if doc["published_at"] else None,
        "type": doc["type"],
        "city": doc["city"],
        "language": doc["language"],
        "requested_language": lang,
        "source_name": source_name,
        "last_updated": doc["last_fetched_at"].isoformat()
        if doc["last_fetched_at"]
        else None,
        "chunks": out_chunks,
    }
