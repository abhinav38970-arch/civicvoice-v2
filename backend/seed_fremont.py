#!/usr/bin/env python3
"""Load sample Fremont sources, documents, and chunks for local feed testing."""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow `python seed_fremont.py` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db import close_pool, get_connection, init_pool


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


DOCUMENTS = [
    {
        "title": "Fremont City Council approves housing element update",
        "url": "https://www.fremont.gov/sample/housing-element-2026",
        "type": "council",
        "days_ago": 3,
        "chunks": [
            "On March 10, the Fremont City Council approved an update to the Housing Element. "
            "The plan outlines how the city will meet state housing goals over the next eight years.",
            "Public comments focused on affordable housing near BART and protecting existing neighborhoods.",
        ],
    },
    {
        "title": "Fremont launches street resurfacing on Warm Springs Boulevard",
        "url": "https://www.fremont.gov/sample/warm-springs-resurfacing",
        "type": "news",
        "days_ago": 7,
        "chunks": [
            "Public Works will resurface Warm Springs Boulevard between South Grimmer and Mission Boulevard. "
            "Lane closures are expected on weekdays from 9 a.m. to 3 p.m.",
        ],
    },
    {
        "title": "November ballot: Measure H library funding overview",
        "url": "https://www.fremont.gov/sample/measure-h-overview",
        "type": "ballot",
        "days_ago": 14,
        "chunks": [
            "Measure H asks voters whether to renew a parcel tax that supports Fremont libraries. "
            "CivicVoice summarizes official language only and does not recommend how to vote.",
        ],
    },
    {
        "title": "Alameda County voter guide — Fremont contests",
        "url": "https://www.acgov.org/sample/fremont-voter-guide",
        "type": "voter_guide",
        "days_ago": 20,
        "chunks": [
            "This voter guide lists candidates and measures for Fremont residents. "
            "Check your ballot for the exact contests that appear in your precinct.",
        ],
    },
    {
        "title": "Parks and Recreation opens Central Park picnic reservations",
        "url": "https://www.fremont.gov/sample/central-park-picnics",
        "type": "news",
        "days_ago": 2,
        "chunks": [
            "Residents can reserve picnic areas at Central Park online. "
            "Peak weekend slots for spring fill quickly after the reservation window opens.",
        ],
    },
    {
        "title": "Council study session on downtown parking and transit",
        "url": "https://www.fremont.gov/sample/downtown-parking-study",
        "type": "council",
        "days_ago": 5,
        "chunks": [
            "Council members reviewed options to expand downtown parking while improving transit access "
            "near the Fremont BART station.",
        ],
    },
]


def seed() -> None:
    init_pool()
    now = datetime.now(timezone.utc)

    with get_connection() as conn:
        source = conn.execute(
            """
            INSERT INTO sources (name, url, host, type, last_fetched_at, content_hash, status)
            VALUES (
                %s, %s, %s, %s, %s, %s, 'active'
            )
            ON CONFLICT (url) DO UPDATE
                SET last_fetched_at = EXCLUDED.last_fetched_at,
                    status = 'active'
            RETURNING id
            """,
            (
                "City of Fremont (sample)",
                "https://www.fremont.gov/sample",
                "www.fremont.gov",
                "city",
                now,
                text_hash("fremont-sample-source-v1"),
            ),
        ).fetchone()
        source_id = source["id"]

        run = conn.execute(
            """
            INSERT INTO ingest_runs (status, finished_at)
            VALUES ('success', %s)
            RETURNING id
            """,
            (now,),
        ).fetchone()
        run_id = run["id"]

        added_docs = 0
        added_chunks = 0

        for doc in DOCUMENTS:
            published = now - timedelta(days=doc["days_ago"])
            row = conn.execute(
                """
                INSERT INTO documents (
                    source_id, title, url, published_at, type, city, language
                )
                VALUES (%s, %s, %s, %s, %s, 'Fremont', 'en')
                ON CONFLICT (url) DO UPDATE
                    SET title = EXCLUDED.title,
                        published_at = EXCLUDED.published_at,
                        type = EXCLUDED.type
                RETURNING id
                """,
                (
                    source_id,
                    doc["title"],
                    doc["url"],
                    published,
                    doc["type"],
                ),
            ).fetchone()
            doc_id = row["id"]
            added_docs += 1

            for i, chunk_text in enumerate(doc["chunks"], start=1):
                conn.execute(
                    """
                    INSERT INTO chunks (
                        document_id, text, page, text_hash, is_active, last_seen_run
                    )
                    VALUES (%s, %s, %s, %s, true, %s)
                    ON CONFLICT (document_id, text_hash) DO UPDATE
                        SET text = EXCLUDED.text,
                            is_active = true,
                            last_seen_run = EXCLUDED.last_seen_run,
                            updated_at = now()
                    """,
                    (doc_id, chunk_text, i, text_hash(chunk_text), run_id),
                )
                added_chunks += 1

        conn.execute(
            """
            UPDATE ingest_runs
            SET added = %s, updated = 0, inactivated = 0
            WHERE id = %s
            """,
            (added_chunks, run_id),
        )
        conn.commit()

    close_pool()
    print(f"Seeded Fremont sample data: {added_docs} documents, {added_chunks} chunks.")


if __name__ == "__main__":
    seed()
