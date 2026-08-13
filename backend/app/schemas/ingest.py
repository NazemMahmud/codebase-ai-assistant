from pydantic import BaseModel


class IngestRequest(BaseModel):
    repo_url: str


class IngestResult(BaseModel):
    repo_id: str
    status: str
