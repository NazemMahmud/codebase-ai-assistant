"""Domain exceptions for the ingest pipeline.

Web-agnostic: the route maps them to HTTP status codes
(validation → 400, clone/limit → 422, indexing → 500).
"""


class RepoValidationError(ValueError):
    """The URL is not an acceptable public GitHub repository."""


class RepoCloneError(RuntimeError):
    """git clone failed."""


class RepoLimitError(RuntimeError):
    """The repository exceeds the configured size/file-count limits."""


class IndexingError(RuntimeError):
    """Chunking / embedding / storing failed after the repo was cloned."""
