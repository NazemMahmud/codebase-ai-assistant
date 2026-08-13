"""
enable pg extensions

Revision ID: ab25cfa5bbc7
Revises: 
Create Date: 2026-08-12

Enable extensions before any table depends on them:
  - vector  : VECTOR column type for embeddings (pgvector)
  - pg_trgm : trigram GIN index for exact/fuzzy identifier search

Reason: the vector column type and the gin_trgm_ops index don't exist until their extensions are enabled,
and this must run before any table uses them
so it's the first revision (down_revision = None).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ab25cfa5bbc7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS vector")
