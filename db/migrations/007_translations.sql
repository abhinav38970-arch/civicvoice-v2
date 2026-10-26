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
