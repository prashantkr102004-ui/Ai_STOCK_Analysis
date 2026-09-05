import json

import joblib
import pandas as pd
import pytest

from ml.prediction.predict import predict_latest
from ml.training.train import (
    chronological_split,
    ensure_target,
    select_feature_columns,
    train_xgboost_model,
    verify_no_leakage,
)


def make_processed_frame(symbols=("AAA", "BBB"), rows=230):
    records = []
    for symbol in symbols:
        for i in range(rows):
            close = 100 + i * 0.05 + ((i % 6) - 3) * 0.4 + (1 if symbol == "BBB" else 0)
            records.append(
                {
                    "Date": pd.Timestamp("2020-01-01") + pd.Timedelta(days=i),
                    "Symbol": symbol,
                    "Open": close - 0.4,
                    "High": close + 1,
                    "Low": close - 1,
                    "Close": close,
                    "Volume": 1000 + i,
                    "SMA_20": close - 1,
                    "SMA_50": close - 2,
                    "SMA_200": close - 3,
                    "EMA_20": close - 1.1,
                    "EMA_50": close - 2.1,
                    "RSI": 50 + (i % 10),
                    "MACD": 0.1,
                    "MACD_signal": 0.05,
                    "MACD_hist": 0.05,
                    "BB_upper": close + 5,
                    "BB_lower": close - 5,
                    "BB_middle": close,
                    "ATR": 2,
                    "Daily_Return": 0.001,
                    "Return_5D": 0.005,
                    "Return_10D": 0.01,
                    "Return_20D": 0.02,
                    "Volume_MA_20": 1000,
                    "Volume_Ratio": 1.1,
                    "Rolling_Volatility": 0.02,
                }
            )
    return pd.DataFrame(records)


def test_target_creation_uses_next_close_per_symbol():
    df = make_processed_frame(symbols=("AAA",), rows=5)
    df["Close"] = [10, 11, 10, 12, 12]
    targeted = ensure_target(df)
    assert len(targeted) == 4
    assert targeted["Target"].tolist() == [1, 0, 1, 0]


def test_feature_selection_uses_existing_columns_only():
    df = make_processed_frame(symbols=("AAA",), rows=5)[["Date", "Symbol", "Close", "RSI"]]
    assert select_feature_columns(df) == ["Close", "RSI"]


def test_leakage_columns_are_rejected():
    with pytest.raises(ValueError):
        verify_no_leakage(["RSI", "future_close"])


def test_chronological_split_is_per_stock():
    targeted = ensure_target(make_processed_frame(rows=230))
    train_df, validation_df, test_df = chronological_split(targeted)
    for symbol in ("AAA", "BBB"):
        train_dates = train_df[train_df["Symbol"] == symbol]["Date"]
        validation_dates = validation_df[validation_df["Symbol"] == symbol]["Date"]
        test_dates = test_df[test_df["Symbol"] == symbol]["Date"]
        assert train_dates.max() < validation_dates.min()
        assert validation_dates.max() < test_dates.min()


def test_model_training_saves_model_metadata_and_importance(tmp_path):
    metadata = train_xgboost_model(make_processed_frame(rows=230), model_dir=tmp_path)
    assert metadata["version"] == "v1"
    assert metadata["feature_count"] > 0
    assert (tmp_path / "xgboost_model_v1.joblib").exists()
    assert (tmp_path / "xgboost_model_latest.joblib").exists()
    assert (tmp_path / "model_metadata_v1.json").exists()
    assert (tmp_path / "model_metadata_latest.json").exists()
    assert (tmp_path / "feature_importance.json").exists()
    saved_metadata = json.loads((tmp_path / "model_metadata_latest.json").read_text(encoding="utf-8"))
    assert saved_metadata["test_samples"] > 0
    assert joblib.load(tmp_path / "xgboost_model_latest.joblib")["version"] == "v1"


def test_prediction_probability_output(tmp_path):
    processed = make_processed_frame(rows=230)
    train_xgboost_model(processed, model_dir=tmp_path)
    result = predict_latest(ensure_target(processed), "AAA", model_dir=tmp_path)
    assert result["prediction"] in {"UP", "DOWN"}
    assert 0 <= result["probability_up"] <= 1
    assert 0 <= result["probability_down"] <= 1
    assert 0 <= result["confidence"] <= 100
