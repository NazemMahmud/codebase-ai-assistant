from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    repo_id: str | None = None
