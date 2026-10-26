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
