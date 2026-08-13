from fastapi import APIRouter, status

from app.schemas.chat import ChatRequest

router = APIRouter()


@router.post("/chat", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def chat(payload: ChatRequest):
    # TODO: embed → hybrid retrieve → fuse → assemble context → stream LLM (next slice)
    return {"success": False, "message": "Chat not implemented yet"}
