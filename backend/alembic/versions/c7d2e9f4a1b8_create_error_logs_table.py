"""
create_error_logs_table

Revision ID: c7d2e9f4a1b8
Revises: 3b1073776649
Create Date: 2026-08-13

Minimal store for critical errors: level, source (where), error_type + message
(what), context (traceback/extra JSONB), and optional codebase_id.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.models.table_names import TableName


# revision identifiers, used by Alembic.
revision: str = "c7d2e9f4a1b8"
down_revision: Union[str, Sequence[str], None] = "3b1073776649"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        TableName.ERROR_LOGS,
        sa.Column("id", sa.UUID(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("error_type", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("codebase_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["codebase_id"], [f"{TableName.CODEBASES}.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(f"idx_{TableName.ERROR_LOGS}_level", TableName.ERROR_LOGS, ["level"])
    op.create_index(f"idx_{TableName.ERROR_LOGS}_created_at", TableName.ERROR_LOGS, ["created_at"])
    op.create_index(f"idx_{TableName.ERROR_LOGS}_codebase_id", TableName.ERROR_LOGS, ["codebase_id"])

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(f"idx_{TableName.ERROR_LOGS}_codebase_id", table_name=TableName.ERROR_LOGS)
    op.drop_index(f"idx_{TableName.ERROR_LOGS}_created_at", table_name=TableName.ERROR_LOGS)
    op.drop_index(f"idx_{TableName.ERROR_LOGS}_level", table_name=TableName.ERROR_LOGS)
    op.drop_table(TableName.ERROR_LOGS)
