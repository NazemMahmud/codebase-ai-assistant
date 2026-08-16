from pydantic import BaseModel


class IngestRequest(BaseModel):
    repo_url: str


class IngestResult(BaseModel):
    codebase_id: str
    status: str
    file_count: int
    chunk_count: int
