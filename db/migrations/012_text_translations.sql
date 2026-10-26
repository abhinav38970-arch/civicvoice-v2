-- Durable cache for free-form UI strings (titles, source names, snippets).
-- Keyed by hash of source text so Redis flushes / restarts do not lose translations.
CREATE TABLE text_translations (
    source_hash      TEXT NOT NULL,
    language         TEXT NOT NULL,
    source_text      TEXT NOT NULL,
    translated_text  TEXT NOT NULL,
    provider         TEXT NOT NULL DEFAULT 'unknown',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source_hash, language)
);

CREATE INDEX text_translations_language_idx
    ON text_translations (language);
