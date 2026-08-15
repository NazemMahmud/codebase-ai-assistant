"""Fallback chunker — naive line-window splitter for unsupported languages."""
from __future__ import annotations

from app.services.ingest.chunking.base import ChunkPiece
from app.services.ingest.chunking.constants import (
    FALLBACK_CHUNK_LINES,
    FALLBACK_OVERLAP_LINES,
)


class FallbackChunker:
    """Split source into overlapping line windows.

    Used for languages without a grammar, or files where the AST chunker found no definitions.
    Keeps line numbers so citations still work; symbol fields are left empty.
    """

    def chunk(self, source: str, language: str | None) -> list[ChunkPiece]:
        lines = source.splitlines()
        if not lines:
            return []

        step = max(FALLBACK_CHUNK_LINES - FALLBACK_OVERLAP_LINES, 1)
        pieces: list[ChunkPiece] = []

        for start in range(0, len(lines), step):
            window = lines[start : start + FALLBACK_CHUNK_LINES]
            if not window:
                break
            pieces.append(
                ChunkPiece(
                    content="\n".join(window),
                    language=language,
                    symbol_name=None,
                    symbol_type=None,
                    start_line=start + 1,
                    end_line=start + len(window),
                )
            )
            if start + FALLBACK_CHUNK_LINES >= len(lines):
                break
        return pieces
