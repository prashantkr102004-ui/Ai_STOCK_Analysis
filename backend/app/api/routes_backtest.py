from fastapi import APIRouter, HTTPException

from backend.app.schemas.backtest import BacktestRequest, BacktestResponse, EquityCurveResponse, TradeResponse
from backend.app.services.backtest_service import (
    BacktestNotFoundError,
    get_equity_curve,
    get_trade_history,
    latest_backtest,
    run_symbol_backtest,
)
from ml.prediction.predict import ModelNotTrainedError

router = APIRouter(prefix="/stocks/{symbol}/backtest", tags=["backtest"])


@router.post(
    "",
    response_model=BacktestResponse,
    summary="Run backtest",
    description="Run the existing Phase 4 long-only backtesting engine for a symbol.",
)
def run_backtest(symbol: str, request: BacktestRequest):
    try:
        if request.use_sentiment or request.use_fundamentals:
            raise ValueError(
                "Optional sentiment/fundamental-aware backtesting is not enabled because historical coverage is insufficient. "
                "Run the default Phase 4 backtest with use_sentiment=false and use_fundamentals=false."
            )
        return run_symbol_backtest(
            symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            transaction_cost=request.transaction_cost,
            slippage=request.slippage,
        )
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "",
    response_model=BacktestResponse,
    summary="Get latest backtest",
    description="Return the latest saved backtest summary. This endpoint does not recalculate a backtest.",
)
def get_backtest(symbol: str):
    try:
        return latest_backtest(symbol)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except BacktestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/equity",
    response_model=EquityCurveResponse,
    summary="Get backtest equity curve",
    description="Return the saved Phase 4 equity curve for charting without recalculating the backtest.",
)
def equity(symbol: str):
    try:
        return get_equity_curve(symbol)
    except BacktestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/trades",
    response_model=list[TradeResponse],
    summary="Get backtest trades",
    description="Return the saved Phase 4 trade log for a symbol.",
)
def trades(symbol: str):
    try:
        return get_trade_history(symbol)
    except BacktestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
