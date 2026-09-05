from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import text

from backend.app.core.database import engine
from backend.app.schemas.health import HealthResponse
from backend.app.services.stock_service import _processed_path

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Lightweight service health check.",
)
def health():
    database_status = "unavailable"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "available"
    except Exception:
        database_status = "unavailable"

    model_status = "available" if Path("models/model_metadata_latest.json").exists() else "unavailable"
    data_status = "available" if _processed_path().exists() else "unavailable"
    return {
        "status": "healthy",
        "service": "AI MarketGuard",
        "backend": "available",
        "database": database_status,
        "model": model_status,
        "data": data_status,
    }
