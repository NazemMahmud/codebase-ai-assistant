"""Ingest service — the business logic behind POST /ingest.

This keeps the logic reusable (e.g. from a background worker later).
"""
from __future__ import annotations

import logging
import shutil

from sqlalchemy.orm import Session

from app.enums import CodebaseSource, CodebaseStatus
from app.services.ingest.loader import (
    RepoCloneError,
    RepoLimitError,
    clone_and_collect,
    validate_repo_url,
)
from app.models.codebase import Codebase
from app.schemas.ingest import IngestResult
from app.services.error_log import record_error

logger = logging.getLogger(__name__)

_ERROR_SOURCE = "services.ingest.ingest_repository"


def ingest_repository(session: Session, repo_url: str) -> IngestResult:
    """Validate → create codebase (pending→indexing) → clone → filter.

    Returns an IngestResult.
    Raises RepoValidationError (bad URL, before any row is created) or
    RepoCloneError / RepoLimitError (after the row is marked failed and the error is logged).
    """
    url      = validate_repo_url(repo_url)
    codebase = _create_indexing_codebase(session, url)

    tmp_dir = None
    try:
        tmp_dir, files = clone_and_collect(url)
    except (RepoCloneError, RepoLimitError) as exc:
        _mark_failed(session, codebase, url, exc)
        raise
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # TODO(next slice): chunk -> embed -> store, then set status = READY.
    return IngestResult(
        codebase_id=str(codebase.id),
        status=CodebaseStatus.INDEXING.value,
        file_count=len(files),
    )


def _create_indexing_codebase(session: Session, url: str) -> Codebase:
    """
        Insert a new codebase row and move it pending -> indexing.
        LATER WILL SHIFT FOR COMMON INSERT METHOD
    """
    codebase = Codebase(
        source=CodebaseSource.GITHUB, location=url, status=CodebaseStatus.PENDING
    )
    session.add(codebase)
    session.flush()
    codebase.status = CodebaseStatus.INDEXING
    session.commit()
    return codebase


def _mark_failed(session: Session, codebase: Codebase, url: str, exc: Exception) -> None:
    codebase.status = CodebaseStatus.FAILED
    session.commit()
    record_error(
        source=_ERROR_SOURCE,
        exc=exc,
        codebase_id=codebase.id,
        context={"repo_url": url},
    )
