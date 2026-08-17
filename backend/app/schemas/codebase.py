import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CodebaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    location: str
    status: str
    chunk_count: int
    indexed_at: datetime | None = None
    created_at: datetime
