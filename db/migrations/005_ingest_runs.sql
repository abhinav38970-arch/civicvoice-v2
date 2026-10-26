-- Tracks each ingest pass so chunks can be marked inactive / cleaned up safely.
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
