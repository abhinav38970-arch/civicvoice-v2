#!/usr/bin/env python3
"""One-shot local ingest from the official allowlist.

fremont.gov blocks automated clients (Akamai 403), so this run uses
Alameda County and California Secretary of State pages that are reachable.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from allowlist import ALLOWED_SOURCES  # noqa: E402
from fetch import chunk_text, fetch_html, html_to_text  # noqa: E402

import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://civicvoice:civicvoice@localhost:5432/civicvoice",
)


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    now = datetime.now(timezone.utc)
    added = updated = 0
    errors: list[str] = []

    # Show target DB host so we don't accidentally ingest into localhost.
    try:
        from urllib.parse import urlparse

        host = urlparse(DATABASE_URL).hostname or "?"
        print(f"ingest target host={host}")
        if host in {"localhost", "127.0.0.1"}:
            print(
                "WARNING: writing to local DB. For Render, set DATABASE_URL to the "
                "External Database URL first."
            )
    except Exception:  # noqa: BLE001
        pass

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        run = conn.execute(
            """
            INSERT INTO ingest_runs (status)
            VALUES ('running')
            RETURNING id
            """
        ).fetchone()
        run_id = run["id"]

        for src in ALLOWED_SOURCES:
            try:
                html, content_hash = fetch_html(src["url"])
                text = html_to_text(html)
                pieces = chunk_text(text)
                if not pieces:
                    raise RuntimeError("No usable text extracted")

                source_row = conn.execute(
                    """
                    INSERT INTO sources (name, url, host, type, last_fetched_at, content_hash, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'active')
                    ON CONFLICT (url) DO UPDATE
                      SET name = EXCLUDED.name,
                          last_fetched_at = EXCLUDED.last_fetched_at,
                          content_hash = EXCLUDED.content_hash,
                          status = 'active'
                    RETURNING id
                    """,
                    (
                        src["name"],
                        src["url"],
                        src["host"],
                        src["type"],
                        now,
                        content_hash,
                    ),
                ).fetchone()
                source_id = source_row["id"]

                doc = conn.execute(
                    """
                    INSERT INTO documents (
                        source_id, title, url, published_at, type, city, language
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'en')
                    ON CONFLICT (url) DO UPDATE
                      SET title = EXCLUDED.title,
                          published_at = EXCLUDED.published_at,
                          type = EXCLUDED.type,
                          source_id = EXCLUDED.source_id
                    RETURNING id
                    """,
                    (
                        source_id,
                        src["title"],
                        src["url"],
                        now,
                        src["doc_type"],
                        src["city"],
                    ),
                ).fetchone()
                doc_id = doc["id"]

                for i, piece in enumerate(pieces, start=1):
                    row = conn.execute(
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
                        RETURNING (xmax = 0) AS inserted
                        """,
                        (doc_id, piece, i, text_hash(piece), run_id),
                    ).fetchone()
                    if row and row["inserted"]:
                        added += 1
                    else:
                        updated += 1

                print(f"ok  {src['url']}  ({len(pieces)} chunks)")
            except Exception as exc:  # noqa: BLE001 — log per-source and continue
                msg = f"fail {src['url']}: {exc}"
                errors.append(msg)
                print(msg)

        status = "success" if not errors else ("failed" if added + updated == 0 else "success")
        conn.execute(
            """
            UPDATE ingest_runs
            SET finished_at = %s,
                status = %s,
                added = %s,
                updated = %s,
                error_log = %s
            WHERE id = %s
            """,
            (
                datetime.now(timezone.utc),
                status,
                added,
                updated,
                "\n".join(errors) if errors else None,
                run_id,
            ),
        )
        conn.commit()

    print(f"done. added={added} updated={updated} errors={len(errors)}")


if __name__ == "__main__":
    main()
