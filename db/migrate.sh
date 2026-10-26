#!/usr/bin/env bash
# Apply db/migrations/*.sql in order.
# Uses host psql if available; otherwise docker compose exec into the local db container.
# Safe to re-run: already-applied files are skipped.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MIGDIR="$ROOT/db/migrations"

if [[ -f "$ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "$ROOT/.env"
  set +a
fi

DATABASE_URL="${DATABASE_URL:-postgresql://civicvoice:civicvoice@localhost:5432/civicvoice}"

run_sql() {
  # stdin SQL
  if command -v psql >/dev/null 2>&1; then
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 "$@"
  else
    docker compose -f "$ROOT/docker-compose.yml" exec -T db \
      psql -U civicvoice -d civicvoice -v ON_ERROR_STOP=1 "$@"
  fi
}

run_sql_file() {
  local file="$1"
  if command -v psql >/dev/null 2>&1; then
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$file"
  else
    docker compose -f "$ROOT/docker-compose.yml" exec -T db \
      psql -U civicvoice -d civicvoice -v ON_ERROR_STOP=1 < "$file"
  fi
}

run_sql <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

shopt -s nullglob
for file in "$MIGDIR"/*.sql; do
  name="$(basename "$file")"
  already="$(run_sql -tAc "SELECT 1 FROM schema_migrations WHERE filename = '$name'" | tr -d '[:space:]')"
  if [[ "$already" == "1" ]]; then
    echo "skip  $name"
    continue
  fi
  echo "apply $name"
  run_sql_file "$file"
  run_sql -c "INSERT INTO schema_migrations (filename) VALUES ('$name');"
done

echo "done."
