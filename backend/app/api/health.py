from fastapi import APIRouter
from sqlalchemy import text

from app.database import SessionLocal
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse)
def health_check() -> ApiResponse:
    db_status = "ok"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"

    ok = db_status == "ok"
    return ApiResponse(
        success=ok,
        data={"status": "ok" if ok else "degraded", "database": db_status},
    )
