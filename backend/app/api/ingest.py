from fastapi import APIRouter, status

from app.schemas.ingest import IngestRequest

router = APIRouter()


@router.post("/ingest", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def ingest(payload: IngestRequest):
    # TODO: clone → filter → chunk → embed → store (next slice)
    return {"success": False, "message": "Ingestion not implemented yet"}
