from fastapi import APIRouter, HTTPException

from backend.app.schemas.fundamental import FundamentalAnalysisResponse, FundamentalHistoryItem
from backend.app.services.fundamental_service import (
    FundamentalsNotFoundError,
    get_fundamental_history,
    latest_fundamental_analysis,
)

router = APIRouter(prefix="/stocks/{symbol}/fundamentals", tags=["fundamentals"])


@router.get(
    "",
    response_model=FundamentalAnalysisResponse,
    summary="Get company fundamental analysis",
    description="Return the latest local fundamental analysis for a stock. No live or paid financial API is used.",
)
def fundamentals(symbol: str):
    try:
        return latest_fundamental_analysis(symbol)
    except FundamentalsNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/history",
    response_model=list[FundamentalHistoryItem],
    summary="Get company fundamental history",
    description="Return local historical fundamental records for a stock.",
)
def fundamentals_history(symbol: str, start_date: str | None = None, end_date: str | None = None):
    try:
        return get_fundamental_history(symbol, start_date=start_date, end_date=end_date)
    except FundamentalsNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
