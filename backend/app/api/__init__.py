from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router, tags=["health"])
# will implement later
api_router.include_router(ingest_router, tags=["ingest"])
api_router.include_router(chat_router, tags=["chat"])

__all__ = ["api_router"]
