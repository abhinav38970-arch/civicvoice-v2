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
