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
