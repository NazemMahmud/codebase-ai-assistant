from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Code Documentation Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database — sync psycopg 3 driver (see ADR-008)
    DATABASE_URL: str = "postgresql+psycopg://app:app@localhost:5432/codedoc"

    # Embeddings — local sentence-transformers, no API key needed (ADR-003)
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBED_DIMENSIONS: int = 384  # bge-small-en-v1.5 = 384

    # LLM generation — model-agnostic, BYOK (ADR-004)
    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = ""
    LLM_API_KEY: str = ""

    # Retrieval tuning (ADR-006)
    VECTOR_TOP_K: int = 50   # candidates from vector cosine search
    KEYWORD_TOP_K: int = 30  # candidates from lexical search
    RRF_K: int = 60          # reciprocal rank fusion smoothing constant

    # Context assembly (ADR-009)
    CONTEXT_MAX_CHUNKS: int = 10   # cap by chunk count, never string-truncate code
    CONTEXT_TOKEN_BUDGET: int = 6000

    # Ingest safety limits (ADR-010 / -012)
    MAX_REPO_MB: int = 100
    MAX_FILES: int = 5000
    MAX_FILE_BYTES: int = 1_000_000  # skip files larger than this

    # Observability — optional, app runs fully without it (ADR-011)
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()