"""
create_codebases_table

Revision ID: 9a45016a0ebd
Revises: ab25cfa5bbc7
Create Date: 2026-08-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.models.table_names import TableName


# revision identifiers, used by Alembic.
revision: str = '9a45016a0ebd'
down_revision: Union[str, Sequence[str], None] = 'ab25cfa5bbc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        TableName.CODEBASES,
        sa.Column("id", sa.UUID(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("chunk_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(f"idx_{TableName.CODEBASES}_status", TableName.CODEBASES, ["status"])
    op.create_index(f"idx_{TableName.CODEBASES}_location", TableName.CODEBASES, ["location"])
    op.create_index(f"idx_{TableName.CODEBASES}_deleted_at", TableName.CODEBASES, ["deleted_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(f"idx_{TableName.CODEBASES}_deleted_at", table_name=TableName.CODEBASES)
    op.drop_index(f"idx_{TableName.CODEBASES}_location", table_name=TableName.CODEBASES)
    op.drop_index(f"idx_{TableName.CODEBASES}_status", table_name=TableName.CODEBASES)
    op.drop_table(TableName.CODEBASES)
