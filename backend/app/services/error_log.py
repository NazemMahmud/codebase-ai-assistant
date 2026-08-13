"""Persist critical errors to the error_logs table.

Uses its own DB session so the record survives even when the request's
transaction is rolled back, and never raises (logging must not mask the
original error).
"""
from __future__ import annotations

import logging
import traceback
import uuid
from typing import Any

from app.database import SessionLocal
from app.enums import ErrorLevel
from app.models.error_log import ErrorLog

logger = logging.getLogger(__name__)

MSG_PERSIST_FAILED = "Failed to persist error log (source=%s)"


def record_error(
    *,
    source: str,
    exc: BaseException,
    level: ErrorLevel = ErrorLevel.CRITICAL,
    codebase_id: uuid.UUID | None = None,
    context: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {"traceback": traceback.format_exc()}
    if context:
        payload.update(context)
    try:
        with SessionLocal() as session:
            session.add(
                ErrorLog(
                    level=level,
                    source=source,
                    error_type=type(exc).__name__,
                    message=str(exc),
                    context=payload,
                    codebase_id=codebase_id,
                )
            )
            session.commit()
    except Exception:
        logger.exception(MSG_PERSIST_FAILED, source)
