"""
create_chunks_table

Revision ID: 3b1073776649
Revises: 9a45016a0ebd
Create Date: 2026-08-13

chunks uses:
  - Vector(768) for jina-embeddings-v2-base-code embeddings + HNSW cosine index
  - content_tsv (tsvector GENERATED column, 'simple' config) + GIN index
  - pg_trgm GIN index on symbol_name for exact identifier lookup
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from app.models.table_names import TableName


# revision identifiers, used by Alembic.
revision: str = '3b1073776649'
down_revision: Union[str, Sequence[str], None] = '9a45016a0ebd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBED_DIM = 768  # jina-embeddings-v2-base-code (kept literal — migrations are frozen snapshots)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        TableName.CHUNKS,
        sa.Column("id", sa.UUID(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("codebase_id", sa.UUID(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("programming_language", sa.String(length=30), nullable=True),
        sa.Column("symbol_name", sa.Text(), nullable=True),
        sa.Column("symbol_type", sa.String(length=20), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(dim=EMBED_DIM), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["codebase_id"], [f"{TableName.CODEBASES}.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Generated lexical column ('simple' config keeps code identifiers intact).
    op.execute(
        f"""
        ALTER TABLE {TableName.CHUNKS}
        ADD COLUMN content_tsv tsvector
        GENERATED ALWAYS AS (
            to_tsvector('simple', coalesce(symbol_name, '') || ' ' || content)
        ) STORED
        """
    )

    # Vector cosine search (ADR-006).
    op.create_index(
        f"idx_{TableName.CHUNKS}_embedding_hnsw",
        TableName.CHUNKS,
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    # Full-text lexical search.
    op.create_index(
        f"idx_{TableName.CHUNKS}_content_tsv",
        TableName.CHUNKS,
        ["content_tsv"],
        postgresql_using="gin",
    )
    # Trigram search on identifiers (needs pg_trgm).
    op.create_index(
        f"idx_{TableName.CHUNKS}_symbol_trgm",
        TableName.CHUNKS,
        ["symbol_name"],
        postgresql_using="gin",
        postgresql_ops={"symbol_name": "gin_trgm_ops"},
    )
    op.create_index(
        f"idx_{TableName.CHUNKS}_codebase_file",
        TableName.CHUNKS,
        ["codebase_id", "file_path"],
    )
    op.create_index(
        f"idx_{TableName.CHUNKS}_deleted_at",
        TableName.CHUNKS,
        ["deleted_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(f"idx_{TableName.CHUNKS}_deleted_at", table_name=TableName.CHUNKS)
    op.drop_index(f"idx_{TableName.CHUNKS}_codebase_file", table_name=TableName.CHUNKS)
    op.drop_index(f"idx_{TableName.CHUNKS}_symbol_trgm", table_name=TableName.CHUNKS, postgresql_using="gin")
    op.drop_index(f"idx_{TableName.CHUNKS}_content_tsv", table_name=TableName.CHUNKS, postgresql_using="gin")
    op.drop_index(f"idx_{TableName.CHUNKS}_embedding_hnsw", table_name=TableName.CHUNKS, postgresql_using="hnsw")
    op.drop_table(TableName.CHUNKS)
