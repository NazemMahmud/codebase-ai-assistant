"""Constants for the repository loader — hosts, filter lists, and messages.
"""

# Only public GitHub for slice 1 (ADR-012).
ALLOWED_HOSTS = {"github.com", "www.github.com"}
ALLOWED_SCHEMES = {"http", "https"}

# File-name patterns treated as ignorable.
ENV_FILENAME = ".env"
ENV_FILE_PREFIX = ".env."
SSH_KEY_FILENAMES = {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
TMP_DIR_PREFIX = "ingest_"

# Directories never worth indexing.
IGNORED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "env",
    "__pycache__", "dist", "build", "out", ".next", "target", "vendor",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".gradle", ".terraform", "coverage", ".cache",
}

# Lockfiles + generated manifests (noise, not source).
IGNORED_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Cargo.lock", "composer.lock", "Gemfile.lock", ".DS_Store",
}

# Binaries / media / archives / compiled artifacts.
IGNORED_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp", ".pdf",
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a", ".class", ".jar",
    ".war", ".pyc", ".pyo", ".wasm",
    ".mp3", ".mp4", ".mov", ".avi", ".wav", ".ogg", ".webm",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".db", ".sqlite", ".sqlite3",
}

# Secret/key material — never read or store.
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".crt", ".cer", ".der", ".keystore", ".jks"}

# User-facing / error messages.
MSG_URL_REQUIRED = "Repository URL is required."
MSG_INVALID_SCHEME = "Only http(s) URLs are allowed (no file://, ssh, git)."
MSG_CREDENTIALS_NOT_ALLOWED = "Credentials in the URL are not allowed."
MSG_HOST_NOT_ALLOWED = "Only public github.com repositories are supported."
MSG_UNRESOLVABLE_HOST = "Could not resolve host: {host}"
MSG_NON_PUBLIC_ADDRESS = "Host resolves to a non-public address."
MSG_CLONE_FAILED = "Failed to clone repository: {detail}"
MSG_FILE_LIMIT_EXCEEDED = "Repository exceeds the {limit}-file limit."
MSG_SIZE_LIMIT_EXCEEDED = "Repository exceeds the {limit} MB size limit."

BYTES_PER_MB = 1024 * 1024
