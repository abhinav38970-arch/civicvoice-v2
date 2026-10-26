# CivicVoice

Local government news, council updates, and ballots — in your language.

See [docs/architecture.md](docs/architecture.md) for how the app is designed.

## Local development (this machine only)

Nothing here needs a cloud deploy. Use Docker for Postgres (with pgvector) and Redis.

```bash
# 1. Copy env template
cp .env.example .env

# 2. Start database + Redis
docker compose up -d

# 3. Check they are healthy
docker compose ps
```

| Service | Local URL |
|---------|-----------|
| Postgres | `localhost:5432` (user/pass/db: `civicvoice`) |
| Redis | `localhost:6379` |

Folders:

- `frontend/` — Next.js (step 5)
- `backend/` — FastAPI (steps 2–4)
- `ingest/` — scheduled fetch worker (step 6)
- `db/migrations/` — schema changes (step 1)
