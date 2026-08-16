"""Dispatcher — pick the chunker per language and read files for chunking."""
from __future__ import annotations

from pathlib import Path

from app.services.ingest.chunking.base import ChunkPiece
from app.services.ingest.chunking.constants import TEXT_ENCODING, TREE_SITTER_LANGUAGES
from app.services.ingest.chunking.fallback import FallbackChunker
from app.services.ingest.chunking.language import detect_language
from app.services.ingest.chunking.tree_sitter_chunker import TreeSitterChunker

_tree_sitter_chunker = TreeSitterChunker()
_fallback_chunker = FallbackChunker()


def chunk_source(source: str, language: str | None) -> list[ChunkPiece]:
    """Chunk raw source: tree-sitter for py/js/ts, else the fallback splitter.

    Falls back when the AST chunker finds no definitions
    (e.g. a plain script or a module with only top-level code).
    """
    if language in TREE_SITTER_LANGUAGES:
        pieces = _tree_sitter_chunker.chunk(source, language)

        if pieces:
            return pieces

    return _fallback_chunker.chunk(source, language)


def chunk_file(abs_path: Path, rel_path: str) -> list[ChunkPiece]:
    """Read a file and chunk it. Returns [] for unreadable/binary files.

    `rel_path` drives language detection (and is what citations reference);
    `abs_path` is where the content is read from.
    """
    source = _read_text(abs_path)
    if source is None:
        return []

    return chunk_source(source, detect_language(rel_path))


def _read_text(abs_path: Path) -> str | None:
    try:
        return abs_path.read_text(encoding=TEXT_ENCODING)
    except (OSError, UnicodeDecodeError):
        return None
