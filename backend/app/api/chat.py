from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas.chat import ChatRequest, ChatResponse, CitationOut
from app.schemas.common import ApiResponse
from app.services.chat import CodebaseNotFoundError, answer_question
from app.services.llm import LLMError

router = APIRouter()


@router.post("/chat", response_model=ApiResponse)
def chat(payload: ChatRequest, session: Session = Depends(get_session)) -> ApiResponse:
    try:
        result = answer_question(session, payload.question, payload.codebase_id)
    except CodebaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LLMError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    response = ChatResponse(
        answer=result.answer,
        citations=[CitationOut(**vars(c)) for c in result.citations],
    )

    return ApiResponse(success=True, data=response.model_dump())
