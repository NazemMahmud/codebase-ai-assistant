"""Codebase queries — list indexed repos and fetch one (for the UI / status)."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.codebase import Codebase
from app.services.codebase.constants import MSG_CODEBASE_NOT_FOUND
from app.services.codebase.errors import CodebaseNotFoundError


def list_codebases(session: Session) -> list[Codebase]:
    """Return all non-deleted codebases, newest first."""
    stmt = (
        select(Codebase)
        .where(Codebase.deleted_at.is_(None))
        .order_by(Codebase.created_at.desc())
    )

    return list(session.scalars(stmt))


def get_codebase(session: Session, codebase_id: uuid.UUID) -> Codebase:
    """Return one codebase or raise CodebaseNotFoundError (missing/deleted)."""
    codebase = session.get(Codebase, codebase_id)

    if codebase is None or codebase.deleted_at is not None:
        raise CodebaseNotFoundError(MSG_CODEBASE_NOT_FOUND)

    return codebase
