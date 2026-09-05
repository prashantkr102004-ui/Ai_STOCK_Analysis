import json
from pathlib import Path

from ml.prediction.predict import predict_latest
from backend.app.services.fundamental_service import fundamental_as_score
from backend.app.services.stock_service import load_processed_data
from backend.app.services.sentiment_service import sentiment_as_score_0_to_100
from backend.app.services.signal_explanation_service import explain_signal


def latest_prediction(symbol: str) -> dict:
    result = predict_latest(load_processed_data(), symbol)
    metadata = _model_metadata()
    result["model"] = metadata.get("model_name", "XGBoost")
    result["model_version"] = metadata.get("version", "unknown")
    return result


def latest_signal(symbol: str) -> dict:
    processed = load_processed_data()
    prediction = latest_prediction(symbol)
    sentiment = sentiment_as_score_0_to_100(symbol, as_of_date=prediction.get("prediction_date"))
    fundamentals = fundamental_as_score(symbol, as_of_date=prediction.get("prediction_date"))
    return explain_signal(processed, symbol, prediction, feature_importance(), sentiment=sentiment, fundamentals=fundamentals)


def latest_explanation(symbol: str) -> dict:
    return latest_signal(symbol)


def _model_metadata() -> dict:
    for path in (Path("models/model_metadata_latest.json"), Path("models/metadata.json")):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def model_status() -> dict:
    metadata = _model_metadata()
    if not metadata:
        return {"trained": False, "message": "Model not trained"}
    metrics = metadata.get("metrics", {})
    return {
        "trained": True,
        "model_name": metadata.get("model_name"),
        "model_version": metadata.get("version"),
        "training_date": metadata.get("training_date"),
        "feature_count": metadata.get("feature_count", len(metadata.get("feature_list", []))),
        "training_samples": metadata.get("training_samples"),
        "validation_samples": metadata.get("validation_samples"),
        "test_samples": metadata.get("test_samples"),
        "accuracy": metrics.get("accuracy"),
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "f1": metrics.get("f1"),
        "roc_auc": metrics.get("roc_auc"),
    }


def feature_importance() -> list[dict]:
    path = Path("models/feature_importance.json")
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding="utf-8"))
    return sorted(items, key=lambda item: item["importance"], reverse=True)
