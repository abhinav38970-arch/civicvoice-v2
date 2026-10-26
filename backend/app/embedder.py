"""Query/passage embeddings with multilingual-e5-base labels.

If sentence-transformers is not installed (or the model cannot load),
embed_* returns None and the retriever falls back to full-text search only.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Sequence

from app.config import get_settings

_MODEL_NAME = "intfloat/multilingual-e5-base"
_DIM = 768


class Embedder:
    def __init__(self) -> None:
        self.dim = _DIM
        self._model = None
        self.available = False
        settings = get_settings()
        if not settings.embeddings_enabled:
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(_MODEL_NAME)
            self.available = True
        except Exception:
            self.available = False
            self._model = None

    def embed_query(self, text: str) -> list[float] | None:
        if not self.available or self._model is None:
            return None
        vec = self._model.encode(f"query: {text}", normalize_embeddings=True)
        return [float(x) for x in vec]

    def embed_passages(self, texts: Sequence[str]) -> list[list[float]] | None:
        if not self.available or self._model is None or not texts:
            return None
        labeled = [f"passage: {t}" for t in texts]
        vectors = self._model.encode(labeled, normalize_embeddings=True)
        return [[float(x) for x in row] for row in vectors]


@lru_cache
def get_embedder() -> Embedder:
    return Embedder()
