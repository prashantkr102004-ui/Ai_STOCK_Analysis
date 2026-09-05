import json

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression

from backend.app.main import app
from backend.app.services import prediction_service
from ml.prediction.predict import latest_model_path
from ml.training.model_comparison import (
    calibration_summary,
    metrics_from_predictions,
    overfitting_warning,
    predict_with_threshold,
    target_distribution,
    time_series_validation,
    tune_thresholds,
)
from ml.training.train import chronological_split, ensure_target, verify_no_leakage


client = TestClient(app)


def _frame(rows=150):
    records = []
    for symbol in ("AAA", "BBB"):
        for index in range(rows):
            close = 100 + index * 0.1 + (index % 5) * 0.2
            records.append(
                {
                    "Date": pd.Timestamp("2021-01-01") + pd.Timedelta(days=index),
                    "Symbol": symbol,
                    "Open": close - 0.2,
                    "High": close + 1,
                    "Low": close - 1,
                    "Close": close,
                    "Volume": 10000 + index,
                    "RSI": 45 + (index % 20),
                }
            )
    return pd.DataFrame(records)


def test_phase10_chronological_split_keeps_time_order():
    targeted = ensure_target(_frame())
    train_df, validation_df, test_df = chronological_split(targeted)
    for symbol in ("AAA", "BBB"):
        assert train_df[train_df["Symbol"] == symbol]["Date"].max() < validation_df[validation_df["Symbol"] == symbol]["Date"].min()
        assert validation_df[validation_df["Symbol"] == symbol]["Date"].max() < test_df[test_df["Symbol"] == symbol]["Date"].min()


def test_phase10_target_leakage_columns_are_rejected():
    for column in ("future_return", "next_close", "target_copy", "Label"):
        try:
            verify_no_leakage(["RSI", column])
        except ValueError as exc:
            assert column.lower().split("_")[0] in str(exc).lower()
        else:
            raise AssertionError(f"{column} should have been rejected")


def test_phase10_threshold_analysis_uses_validation_labels():
    y = pd.Series([0, 0, 1, 1])
    probabilities = np.array([0.2, 0.4, 0.55, 0.7])
    predictions = predict_with_threshold(probabilities, 0.5)
    metrics = metrics_from_predictions(y, predictions, probabilities)
    assert predictions.tolist() == [0, 0, 1, 1]
    assert metrics["f1"] == 1.0


def test_phase10_time_series_validation_uses_expanding_windows():
    x = pd.DataFrame({"a": np.arange(80), "b": np.arange(80) % 3})
    y = pd.Series((x["a"] % 4 > 1).astype(int))
    model = LogisticRegression(max_iter=1000)
    report = time_series_validation(model, x, y, splits=3)
    assert report["method"].startswith("TimeSeriesSplit")
    assert len(report["folds"]) >= 2
    assert all("f1" in fold for fold in report["folds"])


def test_phase10_probability_calibration_schema():
    x = pd.DataFrame({"a": [0, 1, 2, 3, 4, 5], "b": [1, 1, 2, 2, 3, 3]})
    y = pd.Series([0, 0, 0, 1, 1, 1])
    model = DummyClassifier(strategy="prior").fit(x, y)
    report = calibration_summary(model, x, y)
    assert "brier_score" in report
    assert isinstance(report["curve"], list)


def test_phase10_target_distribution_reports_balance():
    distribution = target_distribution(pd.Series([1, 0, 1, 1]))
    assert distribution["up_observations"] == 3
    assert distribution["down_observations"] == 1
    assert distribution["up_percentage"] == 75.0


def test_phase10_overfitting_warning_detects_large_gap():
    warning = overfitting_warning({"f1": 0.9}, {"f1": 0.55}, {"f1": 0.54})
    assert warning and "overfitting" in warning.lower()


def test_phase10_production_model_config_fallback(tmp_path):
    missing_config = tmp_path / "production_model.json"
    missing_config.write_text(json.dumps({"model_path": str(tmp_path / "missing.joblib")}), encoding="utf-8")
    metadata = tmp_path / "model_metadata_latest.json"
    model_file = tmp_path / "xgboost_model_latest.joblib"
    model_file.write_bytes(b"placeholder")
    metadata.write_text(json.dumps({"latest_model_path": str(model_file)}), encoding="utf-8")
    assert latest_model_path(tmp_path) == model_file


def test_phase10_model_comparison_service_reads_saved_results(tmp_path, monkeypatch):
    comparison_path = tmp_path / "model_comparison.json"
    comparison_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-01-01T00:00:00+00:00",
                "production_model": "xgboost_current",
                "production_model_name": "XGBoost Current",
                "recommended_model": "xgboost_current",
                "models": [{"model_key": "xgboost_current", "model_name": "XGBoost Current"}],
            }
        ),
        encoding="utf-8",
    )

    class Settings:
        model_comparison_path = comparison_path

    monkeypatch.setattr(prediction_service, "get_settings", lambda: Settings())
    payload = prediction_service.model_comparison()
    assert payload["available"] is True
    assert payload["models"][0]["production_model"] is True


def test_phase10_model_comparison_api():
    response = client.get("/api/model/comparison")
    assert response.status_code == 200
    payload = response.json()
    assert "available" in payload
    if payload["available"]:
        assert payload["models"]
        assert any(item["production_model"] for item in payload["models"])
