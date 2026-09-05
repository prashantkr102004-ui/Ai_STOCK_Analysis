from fastapi import APIRouter

from backend.app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Lightweight service health check.",
)
def health():
    return {"status": "healthy", "service": "AI MarketGuard"}
