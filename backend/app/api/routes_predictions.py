from fastapi import APIRouter, HTTPException

from backend.app.schemas.model import FeatureImportanceItem, ModelComparisonResponse, ModelStatusResponse
from backend.app.schemas.prediction import ExplanationResponse, PredictionResponse, SignalResponse
from backend.app.services.prediction_service import (
    feature_importance,
    latest_explanation,
    latest_prediction,
    latest_signal,
    model_comparison,
    model_status,
)
from ml.prediction.predict import ModelNotTrainedError

router = APIRouter(tags=["predictions"])


@router.get(
    "/stocks/{symbol}/prediction",
    response_model=PredictionResponse,
    summary="Get AI prediction",
    description="Use the saved XGBoost model to predict the next trading-day direction for the latest feature row.",
)
def prediction(symbol: str):
    try:
        return latest_prediction(symbol)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        status_code = 404 if "Stock not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get(
    "/stocks/{symbol}/signal",
    response_model=SignalResponse,
    summary="Get analytical signal",
    description="Return a model-based analytical signal from prediction and current technical factors.",
)
def signal(symbol: str):
    try:
        return latest_signal(symbol)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        status_code = 404 if "Stock not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get(
    "/stocks/{symbol}/explanation",
    response_model=ExplanationResponse,
    summary="Get detailed signal explanation",
    description="Return model prediction, confidence band, technical scoring, risk scoring, and feature explanations.",
)
def explanation(symbol: str):
    try:
        return latest_explanation(symbol)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        status_code = 404 if "Stock not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get(
    "/model/status",
    response_model=ModelStatusResponse,
    summary="Get model status",
    description="Return metadata and test metrics for the latest saved XGBoost model.",
)
def status():
    return model_status()


@router.get(
    "/model/feature-importance",
    response_model=list[FeatureImportanceItem],
    summary="Get feature importance",
    description="Return saved XGBoost feature importance sorted from highest to lowest.",
)
def features():
    return feature_importance()


@router.get(
    "/model/comparison",
    response_model=ModelComparisonResponse,
    summary="Get model comparison results",
    description="Return saved offline model comparison metrics, backtests, validation notes, and production model recommendation.",
)
def comparison():
    return model_comparison()
