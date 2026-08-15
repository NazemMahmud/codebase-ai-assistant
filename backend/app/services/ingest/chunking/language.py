from pathlib import Path

from app.services.ingest.chunking.constants import EXTENSION_TO_LANGUAGE


def detect_language(path: str) -> str | None:
    """Map a file path to a language name by its extension, or None if unknown."""
    return EXTENSION_TO_LANGUAGE.get(Path(path).suffix.lower())
