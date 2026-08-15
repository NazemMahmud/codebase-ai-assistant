"""Code chunking: tree-sitter AST chunker + naive fallback, dispatched by language."""
from app.services.ingest.chunking.base import ChunkPiece, Chunker
from app.services.ingest.chunking.chunker import chunk_file, chunk_source
from app.services.ingest.chunking.language import detect_language

__all__ = ["ChunkPiece", "Chunker", "chunk_file", "chunk_source", "detect_language"]
