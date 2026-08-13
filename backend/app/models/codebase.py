import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.table_names import TableName
from app.database import Base
from app.enums import CodebaseSource, CodebaseStatus


class Codebase(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = TableName.CODEBASES

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()")
    )
    source: Mapped[CodebaseSource] = mapped_column(
        String(20), default=CodebaseSource.GITHUB, nullable=False
    )
    location: Mapped[str] = mapped_column(Text, nullable=False)  # url or path
    commit_sha: Mapped[str | None] = mapped_column(String(64))  # staleness / re-index
    status: Mapped[CodebaseStatus] = mapped_column(
        String(20), default=CodebaseStatus.PENDING, nullable=False
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    indexed_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True)
    )  # set when status -> ready

    chunks = relationship(
        "Chunk", back_populates="codebase", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_codebases_status", "status"),
        Index("idx_codebases_location", "location"),
    )
