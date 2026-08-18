from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Code Documentation Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database — sync psycopg 3 driver (see ADR-008)
    DATABASE_URL: str = "postgresql+psycopg://app:app@localhost:5432/codedoc"

    # Embeddings — local sentence-transformers, no API key needed (ADR-003)
    EMBEDDING_MODEL: str = "jinaai/jina-embeddings-v2-base-code"
    EMBED_DIMENSIONS: int = 768  # jina-embeddings-v2-base-code = 768 (needs transformers<5)
    EMBED_BATCH_SIZE: int = 8    # texts per encode() batch (small: avoids GPU/MPS OOM)
    EMBED_DEVICE: str = "cpu"    # "cpu" (stable on Mac), "cuda", or "mps"

    # LLM generation — model-agnostic, BYOK
    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = ""
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_TIMEOUT: float = 60.0
    LLM_TEMPERATURE: float = 0.1

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