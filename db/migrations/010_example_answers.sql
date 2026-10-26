-- Pre-checked demo Q&A that works without an LLM call.
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
