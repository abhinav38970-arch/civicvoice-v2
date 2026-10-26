-- multilingual-e5-base uses 768 dimensions (architecture named the model; 1024 was a mismatch).
DROP INDEX IF EXISTS chunks_embedding_hnsw_idx;

ALTER TABLE chunks
    ALTER COLUMN embedding TYPE vector(768)
    USING NULL;

CREATE INDEX chunks_embedding_hnsw_idx ON chunks
    USING hnsw (embedding vector_cosine_ops);
