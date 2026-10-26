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
