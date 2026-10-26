-- Full local schema snapshot (mirrors migrations 001–010).
-- Prefer applying migrations via: ./db/migrate.sh
-- Do not hand-edit the live database from this file in production later.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             TEXT NOT NULL UNIQUE,
    password_hash     TEXT NOT NULL,
    preferred_language TEXT NOT NULL DEFAULT 'en',
    city              TEXT NOT NULL,
    interests         TEXT[] NOT NULL DEFAULT '{}',
    profession        TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX users_city_idx ON users (city);

CREATE TABLE sources (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             TEXT NOT NULL,
    url              TEXT NOT NULL,
    host             TEXT NOT NULL,
    type             TEXT NOT NULL,
    last_fetched_at  TIMESTAMPTZ,
    content_hash     TEXT,
    status           TEXT NOT NULL DEFAULT 'active',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT sources_status_check CHECK (status IN ('active', 'paused', 'error'))
);
CREATE UNIQUE INDEX sources_url_uidx ON sources (url);
CREATE INDEX sources_last_fetched_idx ON sources (last_fetched_at DESC NULLS LAST);

CREATE TABLE documents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id     UUID NOT NULL REFERENCES sources (id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    url           TEXT NOT NULL,
    published_at  TIMESTAMPTZ,
    type          TEXT NOT NULL,
    city          TEXT NOT NULL,
    language      TEXT NOT NULL DEFAULT 'en',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT documents_type_check CHECK (
        type IN ('news', 'council', 'voter_guide', 'ballot')
    )
);
CREATE UNIQUE INDEX documents_url_uidx ON documents (url);
CREATE INDEX documents_city_type_idx ON documents (city, type);
CREATE INDEX documents_published_idx ON documents (published_at DESC NULLS LAST);

CREATE TABLE ingest_runs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status      TEXT NOT NULL DEFAULT 'running',
    added       INTEGER NOT NULL DEFAULT 0,
    updated     INTEGER NOT NULL DEFAULT 0,
    inactivated INTEGER NOT NULL DEFAULT 0,
    error_log   TEXT,
    CONSTRAINT ingest_runs_status_check CHECK (
        status IN ('running', 'success', 'failed')
    )
);

CREATE TABLE chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    text            TEXT NOT NULL,
    page            INTEGER,
    text_hash       TEXT NOT NULL,
    embedding       vector(768),
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_seen_run   UUID REFERENCES ingest_runs (id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX chunks_document_text_hash_uidx ON chunks (document_id, text_hash);
CREATE INDEX chunks_active_idx ON chunks (is_active) WHERE is_active = true;
CREATE INDEX chunks_document_id_idx ON chunks (document_id);
CREATE INDEX chunks_embedding_hnsw_idx ON chunks
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX chunks_text_fts_idx ON chunks
    USING gin (to_tsvector('english', text));

CREATE TABLE translations (
    chunk_id         UUID NOT NULL REFERENCES chunks (id) ON DELETE CASCADE,
    language         TEXT NOT NULL,
    translated_text  TEXT NOT NULL,
    provider         TEXT NOT NULL,
    verified         BOOLEAN NOT NULL DEFAULT false,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (chunk_id, language)
);
CREATE INDEX translations_language_verified_idx
    ON translations (language, verified);

CREATE TABLE reports (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    category       TEXT NOT NULL,
    description    TEXT NOT NULL,
    location       TEXT,
    status         TEXT NOT NULL DEFAULT 'draft',
    external_link  TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT reports_status_check CHECK (status IN ('draft', 'ready'))
);
CREATE INDEX reports_user_id_idx ON reports (user_id);
CREATE INDEX reports_created_idx ON reports (created_at DESC);

CREATE TABLE saved_items (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    document_id  UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, document_id)
);
CREATE INDEX saved_items_user_id_idx ON saved_items (user_id);

CREATE TABLE feedback (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users (id) ON DELETE SET NULL,
    query       TEXT NOT NULL,
    chunk_ids   UUID[] NOT NULL DEFAULT '{}',
    helpful     BOOLEAN,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX feedback_created_idx ON feedback (created_at DESC);

CREATE TABLE example_answers (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question     TEXT NOT NULL,
    language     TEXT NOT NULL DEFAULT 'en',
    answer       TEXT NOT NULL,
    chunk_ids    UUID[] NOT NULL DEFAULT '{}',
    city         TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX example_answers_lang_idx ON example_answers (language);
