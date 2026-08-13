import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UserDefinedType

from app.config import settings
from app.database import Base
from app.enums import SymbolType
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.table_names import TableName


class TSVector(UserDefinedType):
    """SQLAlchemy type mapping to PostgreSQL tsvector."""

    cache_ok = True

    def get_col_spec(self, **kw):
        return "TSVECTOR"


class Chunk(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = TableName.CHUNKS

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()")
    )
    codebase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{TableName.CODEBASES}.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)  # relative path; need for file:line citations
    programming_language: Mapped[str | None] = mapped_column(String(30))
    symbol_name: Mapped[str | None] = mapped_column(Text)  # e.g. AuthService.login
    symbol_type: Mapped[SymbolType | None] = mapped_column(String(20))
    start_line: Mapped[int | None] = mapped_column(Integer)  # for citations
    end_line: Mapped[int | None] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)  # for budget assembly
    embedding = mapped_column(Vector(settings.EMBED_DIMENSIONS))

    # Generated lexical column over symbol_name + content. 'simple' config (no
    # stemming) preserves code identifiers like processPayment for exact match.
    content_tsv = mapped_column(
        TSVector,
        Computed(
            "to_tsvector('simple', coalesce(symbol_name, '') || ' ' || content)",
            persisted=True,
        ),
        nullable=True,
    )

    codebase = relationship("Codebase", back_populates="chunks")

    __table_args__ = (
        # Vector cosine search (ADR-006)
        Index(
            "idx_chunks_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        # Full-text lexical search
        Index("idx_chunks_content_tsv", "content_tsv", postgresql_using="gin"),
        # Trigram search on identifiers (needs pg_trgm)
        Index(
            "idx_chunks_symbol_trgm",
            "symbol_name",
            postgresql_using="gin",
            postgresql_ops={"symbol_name": "gin_trgm_ops"},
        ),
        Index("idx_chunks_codebase_file", "codebase_id", "file_path"),
    )
