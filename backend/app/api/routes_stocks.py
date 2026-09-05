from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.stock import IndicatorResponse, StockDetailResponse, StockHistoryResponse, StockSummary
from backend.app.services.stock_service import get_history, get_indicators, get_stock, list_stocks

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get(
    "",
    response_model=list[StockSummary],
    summary="List available stocks",
    description="Return symbols from the processed local stock dataset.",
)
def stocks():
    try:
        return list_stocks()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/{symbol}",
    response_model=StockDetailResponse,
    summary="Get stock details",
    description="Return record counts, date range, and latest close for a symbol.",
)
def stock(symbol: str):
    try:
        return get_stock(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Stock not found: {symbol}") from exc


@router.get(
    "/{symbol}/history",
    response_model=StockHistoryResponse,
    summary="Get historical prices",
    description="Return OHLCV price history from processed local data with optional date and limit filters.",
)
def history(
    symbol: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    limit: int = Query(default=400, gt=0, le=5000),
):
    try:
        return {"symbol": symbol.upper(), "history": get_history(symbol, start_date, end_date, limit)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Stock not found: {symbol}") from exc


@router.get(
    "/{symbol}/indicators",
    response_model=IndicatorResponse,
    summary="Get latest indicators",
    description="Return latest available technical indicators from Phase 2 processed features.",
)
def indicators(symbol: str):
    try:
        return get_indicators(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Stock not found: {symbol}") from exc
