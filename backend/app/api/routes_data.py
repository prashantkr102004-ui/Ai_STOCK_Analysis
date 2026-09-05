from fastapi import APIRouter, HTTPException

from backend.app.schemas.data import DataStatusResponse
from backend.app.services.stock_service import get_data_status

router = APIRouter(prefix="/data", tags=["data"])


@router.get(
    "/status",
    response_model=DataStatusResponse,
    summary="Dataset status",
    description="Return status for the processed local historical dataset.",
)
def data_status():
    try:
        return get_data_status()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
