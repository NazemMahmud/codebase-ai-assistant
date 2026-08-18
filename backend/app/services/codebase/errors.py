"""Domain exceptions for codebase queries (mapped to HTTP by the route)."""


class CodebaseNotFoundError(ValueError):
    """The requested codebase does not exist (or was soft-deleted)."""
