from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.sentiment import NewsItemResponse, SentimentHistoryItem, SentimentResponse
from backend.app.services.sentiment_service import SentimentModelUnavailable, SentimentNotFoundError, get_news, get_sentiment_history, latest_sentiment

router = APIRouter(prefix="/stocks/{symbol}", tags=["sentiment"])


@router.get(
    "/news",
    response_model=list[NewsItemResponse],
    summary="Get local historical news",
    description="Return cached local historical news sentiment rows for a symbol. No live news API is used.",
)
def news(symbol: str, start_date: str | None = None, end_date: str | None = None, limit: int = Query(25, gt=0, le=500)):
    try:
        return get_news(symbol, start_date=start_date, end_date=end_date, limit=limit)
    except SentimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/sentiment",
    response_model=SentimentResponse,
    summary="Get latest local-news sentiment",
    description="Return the latest cached stock-level aggregated sentiment for a symbol.",
)
def sentiment(symbol: str):
    try:
        return latest_sentiment(symbol)
    except SentimentModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SentimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/sentiment/history",
    response_model=list[SentimentHistoryItem],
    summary="Get local-news sentiment history",
    description="Return cached daily stock-level sentiment history for charts.",
)
def sentiment_history(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(250, gt=0, le=5000),
):
    try:
        return get_sentiment_history(symbol, start_date=start_date, end_date=end_date, limit=limit)
    except SentimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
