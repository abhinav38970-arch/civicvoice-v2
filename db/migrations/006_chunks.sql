-- Document pieces + embeddings.
-- vector(1024) matches architecture.md (e5 family; confirm dim when wiring the model).
CREATE TABLE chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    text            TEXT NOT NULL,
    page            INTEGER,
    text_hash       TEXT NOT NULL,
    embedding       vector(1024),
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_seen_run   UUID REFERENCES ingest_runs (id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX chunks_document_text_hash_uidx ON chunks (document_id, text_hash);
CREATE INDEX chunks_active_idx ON chunks (is_active) WHERE is_active = true;
CREATE INDEX chunks_document_id_idx ON chunks (document_id);

-- Meaning search
CREATE INDEX chunks_embedding_hnsw_idx ON chunks
    USING hnsw (embedding vector_cosine_ops);

-- Keyword / full-text search
CREATE INDEX chunks_text_fts_idx ON chunks
    USING gin (to_tsvector('english', text));
