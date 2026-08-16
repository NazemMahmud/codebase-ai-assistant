"""Ingest package: repo loading (validate/clone/filter) + the ingest service."""
from app.services.ingest.errors import (
    IndexingError,
    RepoCloneError,
    RepoLimitError,
    RepoValidationError,
)
from app.services.ingest.loader import FileEntry, clone_and_collect, validate_repo_url
from app.services.ingest.service import ingest_repository

__all__ = [
    "FileEntry",
    "RepoValidationError",
    "RepoCloneError",
    "RepoLimitError",
    "IndexingError",
    "clone_and_collect",
    "validate_repo_url",
    "ingest_repository",
]
