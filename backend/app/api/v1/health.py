"""
V1 Health & System Diagnostics Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def get_v1_health():
    """
    Versioned system health status endpoint.
    """
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
        database_configured=bool(settings.DATABASE_URL),
    )


@router.get("/db", tags=["Health"])
async def get_db_health(db: Session = Depends(get_db)):
    """
    Performs a lightweight SQL ping to verify database connectivity.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {"status": "error", "database": "disconnected", "detail": str(exc)}
