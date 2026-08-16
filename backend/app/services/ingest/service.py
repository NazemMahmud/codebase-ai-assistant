"""Ingest service — the business logic behind POST /ingest.

Pipeline: validate → create codebase → clone → filter → chunk → embed → store → mark ready.
Web-agnostic (raises domain errors; the route maps them to HTTP),
so a background worker could reuse it later.
"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.enums import CodebaseSource, CodebaseStatus
from app.models.chunk import Chunk
from app.models.codebase import Codebase
from app.schemas.ingest import IngestResult
from app.services.embedding import embedder
from app.services.error_log import record_error
from app.services.ingest.chunking import chunk_file
from app.services.ingest.chunking.base import ChunkPiece
from app.services.ingest.errors import IndexingError, RepoCloneError, RepoLimitError
from app.services.ingest.loader import (
    FileEntry,
    clone_and_collect,
    validate_repo_url,
)

logger = logging.getLogger(__name__)

_ERROR_SOURCE = "services.ingest.ingest_repository"


def ingest_repository(session: Session, repo_url: str) -> IngestResult:
    """Validate → create codebase → clone → chunk → embed → store → mark ready.

    Returns IngestResult.
    Raises RepoValidationError (bad URL, before any row is created),
    RepoCloneError / RepoLimitError (clone/limits), or
    IndexingError (chunk/embed/store).
    On any failure the codebase is marked failed and the error is logged.
    """
    url      = validate_repo_url(repo_url)
    codebase = _prepare_codebase(session, url)
    tmp_dir  = None

    try:
        tmp_dir, files = clone_and_collect(url)
        chunk_count    = _index_files(session, codebase, files)
        _mark_ready(session, codebase, chunk_count)
    except (RepoCloneError, RepoLimitError) as exc:
        _mark_failed(session, codebase, url, exc)
        raise
    except Exception as exc:
        # chunk/embed/store failure
        _mark_failed(session, codebase, url, exc)
        raise IndexingError(str(exc)) from exc
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return IngestResult(
        codebase_id=str(codebase.id),
        status=CodebaseStatus.READY.value,
        file_count=len(files),
        chunk_count=chunk_count,
    )


def _prepare_codebase(session: Session, url: str) -> Codebase:
    """Reuse the existing codebase for this URL, or create one; set it to indexing.

    Re-ingest is idempotent: instead of creating a duplicate, the same URL reuses its row
    Old chunks aren't touched here.
    they're soft-deleted in the same transaction as the new inserts (_index_files),
    so a failed re-ingest leaves the previous index intact.
    """
    codebase = _find_codebase(session, url)
    if codebase is None:
        return _create_indexing_codebase(session, url)

    codebase.status     = CodebaseStatus.INDEXING
    codebase.indexed_at = None
    session.commit()

    return codebase


def _find_codebase(session: Session, url: str) -> Codebase | None:
    """Return the most recent non-deleted codebase for this URL, or None."""

    stmt = (
        select(Codebase)
        .where(Codebase.location == url, Codebase.deleted_at.is_(None))
        .order_by(Codebase.created_at.desc())
    )

    return session.scalars(stmt).first()


def _soft_delete_chunks(session: Session, codebase_id) -> None:
    """Mark this codebase's current chunks deleted (staged; commits with the new insert)."""

    session.execute(
        update(Chunk)
        .where(Chunk.codebase_id == codebase_id, Chunk.deleted_at.is_(None))
        .values(deleted_at=datetime.now(timezone.utc))
    )


def _create_indexing_codebase(session: Session, url: str) -> Codebase:
    """Insert a new codebase row and move it pending -> indexing.

    flush() issues INSERT and DB is populated with uuidv7() id
    the status is then set to indexing and committed. Returns the persisted Codebase.
    """
    codebase = Codebase(
        source=CodebaseSource.GITHUB, location=url, status=CodebaseStatus.PENDING
    )
    session.add(codebase)
    session.flush()
    codebase.status = CodebaseStatus.INDEXING
    session.commit()
    return codebase


def _index_files(session: Session, codebase: Codebase, files: list[FileEntry]) -> int:
    """Chunk every file, embed the chunks, and stage them for insert. Returns count.

    Nothing is committed here — _mark_ready commits the chunks + ready status as one unit.
    """
    # Replace any previous index for this codebase (atomic with the new insert
    # at commit; a failure rolls this back too, keeping the old index).
    _soft_delete_chunks(session, codebase.id)

    tagged = _chunk_files(files)
    if not tagged:
        return 0

    vectors = embedder.embed_texts([piece.content for _, piece in tagged])
    session.add_all(
        _build_chunk(codebase, file_path, piece, vector)
        for (file_path, piece), vector in zip(tagged, vectors)
    )

    return len(tagged)


def _chunk_files(files: list[FileEntry]) -> list[tuple[str, ChunkPiece]]:
    """Chunk each file, tagging every piece with its repo-relative path.
    """

    tagged: list[tuple[str, ChunkPiece]] = []

    for entry in files:
        for piece in chunk_file(entry.abs_path, entry.path):
            tagged.append((entry.path, piece))

    return tagged


def _build_chunk(codebase: Codebase, file_path: str, piece: ChunkPiece, vector: list[float]) -> Chunk:
    """Map a (file_path, ChunkPiece, embedding) into a Chunk ORM row.

    `content_tsv` is left unset — the DB generates it from symbol_name + content.
    """
    return Chunk(
        codebase_id=codebase.id,
        file_path=file_path,
        programming_language=piece.language,
        symbol_name=piece.symbol_name,
        symbol_type=piece.symbol_type,
        start_line=piece.start_line,
        end_line=piece.end_line,
        content=piece.content,
        token_count=piece.token_count,
        embedding=vector,
    )


def _mark_ready(session: Session, codebase: Codebase, chunk_count: int) -> None:
    """Flip the codebase to ready and persist chunk_count + indexed_at (commits)."""

    codebase.status = CodebaseStatus.READY
    codebase.chunk_count = chunk_count
    codebase.indexed_at = datetime.now(timezone.utc)
    session.commit()


def _mark_failed(session: Session, codebase: Codebase, url: str, exc: Exception) -> None:
    """Discard half-written work, mark the codebase failed, and log the error."""

    session.rollback()  # drop any staged-but-uncommitted chunks
    codebase.status = CodebaseStatus.FAILED
    session.commit()

    record_error(
        source=_ERROR_SOURCE,
        exc=exc,
        codebase_id=codebase.id,
        context={"repo_url": url},
    )
