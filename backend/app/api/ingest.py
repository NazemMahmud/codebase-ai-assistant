from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas.common import ApiResponse
from app.schemas.ingest import IngestRequest
from app.services.ingest import (
    RepoCloneError,
    RepoLimitError,
    RepoValidationError,
    ingest_repository,
)

router = APIRouter()

_INGEST_OK_MESSAGE = "Repository cloned and filtered; ready for chunking."


@router.post("/ingest", response_model=ApiResponse)
def ingest(payload: IngestRequest, session: Session = Depends(get_session)) -> ApiResponse:
    try:
        result = ingest_repository(session, payload.repo_url)
    except RepoValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except (RepoCloneError, RepoLimitError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return ApiResponse(success=True, message=_INGEST_OK_MESSAGE, data=result.model_dump())
