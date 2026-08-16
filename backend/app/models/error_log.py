import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.enums import ErrorLevel
from app.models.table_names import TableName


class ErrorLog(Base):
    """Minimal record of a critical error — WHAT went wrong and WHERE.

    routine errors/warnings go to the log file.
    Read a row and you get: the component (`source`), the exception type
    (`error_type`) and message, the traceback + any extra data (`context`), and
    which codebase it happened for (`codebase_id`, if any).
    """

    __tablename__ = TableName.ERROR_LOGS

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()")
    )
    level: Mapped[ErrorLevel] = mapped_column(
        String(20), default=ErrorLevel.CRITICAL, nullable=False
    )
    source: Mapped[str] = mapped_column(String(255), nullable=False)  # WHERE, e.g. ingestion.loader.clone
    error_type: Mapped[str] = mapped_column(String(255), nullable=False)  # WHAT, e.g. GitCommandError
    message: Mapped[str] = mapped_column(Text, nullable=False)  # WHAT, str(exc)
    context: Mapped[dict | None] = mapped_column(JSONB)  # traceback + extra detail
    codebase_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{TableName.CODEBASES}.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_error_logs_level", "level"),
        Index("idx_error_logs_created_at", "created_at"),
        Index("idx_error_logs_codebase_id", "codebase_id"),
    )
