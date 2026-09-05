from __future__ import annotations

from pathlib import Path
import json

import joblib
import pandas as pd

from ml.features.technical_indicators import FEATURE_COLUMNS


class ModelNotTrainedError(RuntimeError):
    pass


def latest_model_path(model_dir: str | Path = "models") -> Path:
    model_root = Path(model_dir)
    for metadata_path in (model_root / "model_metadata_latest.json", model_root / "metadata.json"):
        if not metadata_path.exists():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        path = Path(metadata.get("latest_model_path") or metadata["model_path"])
        if path.exists():
            return path
    models = sorted(model_root.glob("xgboost_model_v*.joblib")) or sorted(model_root.glob("xgboost_*.joblib"))
    if not models:
        raise ModelNotTrainedError("Model not trained. Run scripts/train_model.py first.")
    return models[-1]


def load_model(model_dir: str | Path = "models") -> dict:
    return joblib.load(latest_model_path(model_dir))


def predict_latest(processed: pd.DataFrame, symbol: str, model_dir: str | Path = "models") -> dict:
    symbol = symbol.upper()
    stock = processed[processed["Symbol"] == symbol].sort_values("Date")
    if stock.empty:
        raise ValueError(f"Stock not found: {symbol}")
    latest = stock.iloc[-1]
    payload = load_model(model_dir)
    model = payload["model"]
    features = payload.get("features", FEATURE_COLUMNS)
    model_input = pd.DataFrame([latest[features].astype(float).to_dict()], columns=features)
    probabilities = model.predict_proba(model_input)[0]
    probability_down = float(probabilities[0])
    probability_up = float(probabilities[1])
    prediction = "UP" if probability_up >= probability_down else "DOWN"
    confidence = round(max(probability_up, probability_down) * 100, 2)
    return {
        "symbol": symbol,
        "prediction_date": str(pd.to_datetime(latest["Date"]).date()),
        "prediction": prediction,
        "probability_up": round(probability_up, 4),
        "probability_down": round(probability_down, 4),
        "confidence": confidence,
    }


def create_signal(processed: pd.DataFrame, symbol: str, model_dir: str | Path = "models") -> dict:
    prediction = predict_latest(processed, symbol, model_dir)
    latest = processed[processed["Symbol"] == symbol.upper()].sort_values("Date").iloc[-1]
    reasons = []
    if latest["Close"] > latest["SMA_50"]:
        reasons.append("Price is above the 50-day moving average")
    if latest["MACD_hist"] > 0:
        reasons.append("MACD momentum is positive")
    if latest["Volume_Ratio"] > 1:
        reasons.append("Volume is above recent average")
    if latest["RSI"] > 70:
        reasons.append("RSI is elevated")
    elif latest["RSI"] < 30:
        reasons.append("RSI is depressed")

    bullish_score = (prediction["prediction"] == "UP") + (latest["Close"] > latest["SMA_50"]) + (latest["MACD_hist"] > 0)
    if bullish_score >= 3:
        signal = "BULLISH"
    elif bullish_score <= 1 and prediction["prediction"] == "DOWN":
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"
    return {
        "symbol": symbol.upper(),
        "signal": signal,
        "confidence": prediction["confidence"],
        "reasons": reasons or ["Mixed technical and model factors"],
        "technical_indicators": {
            "close": float(latest["Close"]),
            "rsi": float(latest["RSI"]),
            "macd": float(latest["MACD"]),
            "macd_hist": float(latest["MACD_hist"]),
            "sma_20": float(latest["SMA_20"]),
            "sma_50": float(latest["SMA_50"]),
            "volume_ratio": float(latest["Volume_Ratio"]),
            "rolling_volatility": float(latest["Rolling_Volatility"]),
        },
    }
