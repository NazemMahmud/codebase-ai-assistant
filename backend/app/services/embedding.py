"""Local embedding model (sentence-transformers).

Ingest and retrieval both embed with the SAME model so vectors are comparable.
The model is heavy, so it's loaded lazily on first use and reused as a singleton.
"""
from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)


class Embedder:
    """Wraps the sentence-transformers model behind embed_text(s)."""

    def __init__(self) -> None:
        self._model = None

    def _get_model(self):
        """Load the model on first use (downloads on first run); cache it after."""

        if self._model is None:
            # Imported here so the app can boot without loading torch/the model.
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL, trust_remote_code=True
            )

        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts → one normalized vector each (same order)."""
        if not texts:
            return []

        model   = self._get_model()
        vectors = model.encode(
            texts,
            batch_size=settings.EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return [vector.tolist() for vector in vectors]

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text → one vector (used for the query at retrieval)."""
        return self.embed_texts([text])[0]


embedder = Embedder()
