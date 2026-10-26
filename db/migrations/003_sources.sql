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
