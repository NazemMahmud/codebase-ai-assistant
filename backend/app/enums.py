from enum import Enum


class CodebaseSource(str, Enum):
    GITHUB = "github"  # zip/local will be added later


class CodebaseStatus(str, Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class SymbolType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"


class ErrorLevel(str, Enum):
    ERROR = "error"
    CRITICAL = "critical"
