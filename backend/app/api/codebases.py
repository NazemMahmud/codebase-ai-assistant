import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas.codebase import CodebaseOut
from app.schemas.common import ApiResponse
from app.services.codebase import CodebaseNotFoundError, get_codebase, list_codebases

router = APIRouter()


@router.get("/codebases", response_model=ApiResponse)
def list_codebases_route(session: Session = Depends(get_session)) -> ApiResponse:
    codebases = list_codebases(session)
    data      = [CodebaseOut.model_validate(c).model_dump(mode="json") for c in codebases]

    return ApiResponse(success=True, data=data)


@router.get("/codebases/{codebase_id}", response_model=ApiResponse)
def get_codebase_route(
    codebase_id: uuid.UUID, session: Session = Depends(get_session)
) -> ApiResponse:
    try:
        codebase = get_codebase(session, codebase_id)
    except CodebaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ApiResponse(success=True, data=CodebaseOut.model_validate(codebase).model_dump(mode="json"))
