#!/usr/bin/env python3
"""Pre-warm durable translations (Postgres + Redis) for dashboard languages.

Skips strings already in text_translations / chunk translations.
Run after ingest / when adding languages:
  python seed_translations.py
  python seed_translations.py hi es
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.catalog_i18n import CATALOG_LANGS, warm_catalog_translations
from app.db import close_pool, get_connection, init_pool
from app.translate import persist_chunk_translation, translate_text

DEFAULT_LANGS = CATALOG_LANGS


def main(langs: tuple[str, ...]) -> None:
    init_pool()
    # Durable curated catalog first (no live MT).
    print("== catalog seed ==")
    print(warm_catalog_translations(langs))
    with get_connection() as conn:
        titles = conn.execute(
            """
            SELECT DISTINCT d.title AS text
            FROM documents d
            JOIN sources s ON s.id = d.source_id
            WHERE s.status = 'active'
            UNION
            SELECT DISTINCT s.name AS text
            FROM sources s
            WHERE s.status = 'active'
            """
        ).fetchall()
        snippets = conn.execute(
            """
            SELECT DISTINCT left(c.text, 800) AS text
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            JOIN sources s ON s.id = d.source_id
            WHERE c.is_active AND s.status = 'active'
            """
        ).fetchall()
        chunks = conn.execute(
            """
            SELECT c.id, c.text
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            JOIN sources s ON s.id = d.source_id
            WHERE c.is_active AND s.status = 'active'
            ORDER BY c.created_at
            """
        ).fetchall()

    warmed = 0
    skipped = 0
    failed = 0

    for lang in langs:
        print(f"== {lang}: titles/sources ==")
        for row in titles:
            text = row["text"]
            cached = translate_text(text, lang, allow_live=False)
            if cached != text:
                skipped += 1
                continue
            out = translate_text(text, lang, allow_live=True)
            if out != text:
                warmed += 1
                print(f"  ok   {text[:56]!r}")
            else:
                failed += 1
                print(f"  miss {text[:56]!r}")
            time.sleep(0.25)

        print(f"== {lang}: snippets ==")
        for row in snippets:
            text = row["text"]
            cached = translate_text(text, lang, allow_live=False)
            if cached != text:
                skipped += 1
                continue
            out = translate_text(text, lang, allow_live=True)
            if out != text:
                warmed += 1
                print(f"  ok   snippet")
            else:
                failed += 1
                print(f"  miss snippet {text[:40]!r}")
            time.sleep(0.25)

        print(f"== {lang}: chunk rows ==")
        with get_connection() as conn:
            for row in chunks:
                exists = conn.execute(
                    """
                    SELECT 1 FROM translations
                    WHERE chunk_id = %s AND language = %s
                    """,
                    (row["id"], lang),
                ).fetchone()
                if exists:
                    skipped += 1
                    continue
                out = translate_text(row["text"], lang, allow_live=True)
                if out != row["text"]:
                    persist_chunk_translation(str(row["id"]), lang, out, provider="seed")
                    warmed += 1
                    print(f"  chunk ok {row['id']}")
                else:
                    failed += 1
                    print(f"  chunk miss {row['id']}")
                time.sleep(0.3)

    close_pool()
    print(f"done. warmed={warmed} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    args = tuple(a.lower() for a in sys.argv[1:] if a.strip())
    main(args or DEFAULT_LANGS)
