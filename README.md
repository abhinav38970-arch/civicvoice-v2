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

Apply database migrations (local Docker only — no cloud DB required):

```bash
./db/migrate.sh
```

Backend (local):

```bash
cd backend
# Use Python 3.12 (system python3 may be 3.14, which is too new for our deps)
/usr/local/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed_fremont.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 5001
```

API smoke checks: `GET /health`, `POST /api/auth/signup`, `POST /api/auth/login`, `GET /api/feed`, `GET /api/auth/me`, `POST /api/ask`.

Ask works without an LLM key: it returns retrieved document pieces (and seeded example answers when the question matches). Set `CIVICVOICE_LLM_*` only when you want generated summaries.

Folders:

- `frontend/` — Next.js (step 5)
- `backend/` — FastAPI (steps 2–4)
- `ingest/` — scheduled fetch worker (step 6)
- `db/migrations/` — schema changes (step 1)
