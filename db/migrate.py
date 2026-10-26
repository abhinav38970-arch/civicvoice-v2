#!/usr/bin/env python3
"""Apply db/migrations/*.sql using psycopg (no local psql required).

Usage:
  DATABASE_URL='postgresql://…' python db/migrate.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGDIR = ROOT / "db" / "migrations"


def main() -> None:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("Set DATABASE_URL to your Render External Database URL", file=sys.stderr)
        sys.exit(1)

    # Render external URLs often need SSL.
    if "sslmode=" not in url and "render.com" in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"

    try:
        import psycopg
    except ImportError:
        print("Install psycopg first: pip install 'psycopg[binary]'", file=sys.stderr)
        sys.exit(1)

    files = sorted(MIGDIR.glob("*.sql"))
    if not files:
        print(f"No migrations in {MIGDIR}", file=sys.stderr)
        sys.exit(1)

    with psycopg.connect(url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename    TEXT PRIMARY KEY,
                applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.commit()

        for path in files:
            name = path.name
            row = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE filename = %s",
                (name,),
            ).fetchone()
            if row:
                print(f"skip  {name}")
                continue
            print(f"apply {name}")
            sql = path.read_text(encoding="utf-8")
            conn.execute(sql)
            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (name,),
            )
            conn.commit()

    print("done.")


if __name__ == "__main__":
    main()
