import uuid

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    codebase_id: uuid.UUID


class CitationOut(BaseModel):
    file_path: str
    start_line: int | None = None
    end_line: int | None = None
    symbol_name: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
