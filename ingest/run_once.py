#!/usr/bin/env python3
"""One-shot local ingest from the official allowlist.

Includes Fremont / Newark / Union City news URLs plus county/state ballot
sources. httpx is tried first; on Akamai/bot 403, fetch falls back to
headless Chromium (Playwright) unless INGEST_BROWSER=0.

Listing pages with discover_articles=True also pull individual news articles
on the same host so topic filters (Housing, Jobs, …) match real headlines.
"""

from __future__ import annotations

import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from allowlist import ALLOWED_SOURCES  # noqa: E402
from discover import (  # noqa: E402
    discover_article_links,
    extract_article_text,
    parse_listing_items,
)
from fetch import chunk_text, fetch_html, html_to_text  # noqa: E402

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://civicvoice:civicvoice@localhost:5432/civicvoice",
)


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def upsert_document(
    conn: Any,
    *,
    source_id: Any,
    title: str,
    url: str,
    published_at: datetime,
    doc_type: str,
    city: str,
    pieces: list[str],
    run_id: Any,
) -> tuple[int, int]:
    """Insert/update one document + chunks. Returns (added, updated) chunk counts."""
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
              city = EXCLUDED.city,
              source_id = EXCLUDED.source_id
        RETURNING id
        """,
        (source_id, title, url, published_at, doc_type, city),
    ).fetchone()
    doc_id = doc["id"]
    added = updated = 0
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
    return added, updated


def upsert_source(
    conn: Any,
    src: dict[str, Any],
    now: datetime,
    content_hash: str,
) -> Any:
    row = conn.execute(
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
    return row["id"]


def main() -> None:
    now = datetime.now(timezone.utc)
    added = updated = 0
    errors: list[str] = []

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
                source_id = upsert_source(conn, src, now, content_hash)

                # —— Discover child articles from listing pages ——
                if src.get("discover_articles"):
                    limit = int(src.get("discover_limit") or 15)
                    articles = discover_article_links(
                        html, src["url"], limit=limit
                    )
                    print(
                        f"discover {src['url']} → {len(articles)} articles"
                    )
                    for title, article_url, published in articles:
                        try:
                            # Same-host check already in discover; fetch still allowlist-gated.
                            a_html, _ = fetch_html(article_url)
                            a_text = extract_article_text(a_html) or html_to_text(a_html)
                            a_pieces = chunk_text(a_text)
                            if not a_pieces:
                                print(f"  skip thin {article_url}")
                                continue
                            a, u = upsert_document(
                                conn,
                                source_id=source_id,
                                title=title,
                                url=article_url,
                                published_at=published or now,
                                doc_type=src["doc_type"],
                                city=src["city"],
                                pieces=a_pieces,
                                run_id=run_id,
                            )
                            added += a
                            updated += u
                            print(f"  ok  {title[:70]}  ({len(a_pieces)} chunks)")
                        except Exception as art_exc:  # noqa: BLE001
                            msg = f"fail article {article_url}: {art_exc}"
                            errors.append(msg)
                            print(f"  {msg}")

                # —— Cards parsed straight from the listing page ——
                if src.get("listing_items"):
                    cards = parse_listing_items(
                        html,
                        src["url"],
                        src["listing_items"],
                        limit=int(src.get("discover_limit") or 15),
                    )
                    print(f"listing {src['url']} → {len(cards)} items")
                    for title, card_url, published, body in cards:
                        pieces = chunk_text(body) or [body[:700] or title]
                        a, u = upsert_document(
                            conn,
                            source_id=source_id,
                            title=title,
                            url=card_url,
                            published_at=published or now,
                            doc_type=src["doc_type"],
                            city=src["city"],
                            pieces=pieces,
                            run_id=run_id,
                        )
                        added += a
                        updated += u
                        print(f"  ok  {title[:70]}")
                    if src.get("skip_listing_doc"):
                        conn.execute(
                            "DELETE FROM documents WHERE url = %s", (src["url"],)
                        )
                        continue

                if src.get("discover_articles"):
                    if src.get("skip_listing_doc"):
                        # Drop stale index card so topic filters use real headlines.
                        conn.execute(
                            "DELETE FROM documents WHERE url = %s",
                            (src["url"],),
                        )
                        print(f"ok  {src['url']}  (listing → {len(articles)} articles)")
                        continue

                text = html_to_text(html)
                pieces = chunk_text(text)
                if not pieces:
                    raise RuntimeError("No usable text extracted")

                a, u = upsert_document(
                    conn,
                    source_id=source_id,
                    title=src["title"],
                    url=src["url"],
                    published_at=now,
                    doc_type=src["doc_type"],
                    city=src["city"],
                    pieces=pieces,
                    run_id=run_id,
                )
                added += a
                updated += u
                print(f"ok  {src['url']}  ({len(pieces)} chunks)")
            except Exception as exc:  # noqa: BLE001 — log per-source and continue
                msg = f"fail {src['url']}: {exc}"
                errors.append(msg)
                print(msg)

        status = (
            "success"
            if not errors
            else ("failed" if added + updated == 0 else "success")
        )
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
