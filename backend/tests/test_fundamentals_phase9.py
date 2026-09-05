import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.services import prediction_service
from backend.app.services.fundamental_service import (
    calculate_category_scores,
    calculate_metrics,
    fundamental_as_score,
    latest_fundamental_analysis,
    overall_score,
)
from ml.preprocessing.clean_fundamentals import clean_fundamental_frame, load_fundamental_file


client = TestClient(app)


def _write_fundamentals(path):
    pd.DataFrame(
        [
            {"ticker": "ABC", "report_date": "2022-03-31", "sales": 100, "pat": 10, "eps": 5, "roe": 12, "de_ratio": 0.4},
            {"ticker": "ABC", "report_date": "2023-03-31", "sales": 125, "pat": 14, "eps": 7, "roe": 18, "de_ratio": 0.3},
            {"ticker": "ABC", "report_date": "2023-03-31", "sales": 125, "pat": 14, "eps": 7, "roe": 18, "de_ratio": 0.3},
            {"ticker": "BAD", "report_date": "not-a-date", "sales": 1},
            {"ticker": "NEG", "report_date": "2023-03-31", "sales": -10},
        ]
    ).to_csv(path, index=False)


def test_fundamental_csv_loading_column_mapping_and_validation(tmp_path):
    path = tmp_path / "fundamentals.csv"
    _write_fundamentals(path)
    frame = load_fundamental_file(path)
    assert len(frame) == 2
    assert {"symbol", "date", "revenue", "net_profit", "debt_to_equity"}.issubset(frame.columns)
    assert frame["symbol"].tolist() == ["ABC", "ABC"]


def test_fundamental_missing_required_columns():
    with pytest.raises(ValueError):
        clean_fundamental_frame(pd.DataFrame([{"date": "2023-01-01", "revenue": 100}]))


def test_growth_and_category_scoring():
    previous = pd.Series({"revenue": 100, "net_profit": 10, "eps": 5})
    latest = pd.Series(
        {
            "revenue": 125,
            "net_profit": 14,
            "eps": 7,
            "roe": 20,
            "roce": 25,
            "pe_ratio": 20,
            "pb_ratio": 3,
            "debt_to_equity": 0.2,
            "free_cash_flow": 50,
        }
    )
    metrics = calculate_metrics(latest, previous)
    scores = calculate_category_scores(metrics)
    assert metrics["revenue_growth_yoy"] == 0.25
    assert scores["growth"] > 80
    assert scores["profitability"] > 60
    assert scores["balance_sheet"] == 100


def test_missing_category_reweighting():
    score, completeness = overall_score({"growth": 80, "profitability": None, "valuation": 60, "balance_sheet": None, "cash_flow": None})
    assert score == 72.5
    assert completeness == 40


def test_no_future_fundamental_leakage(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "processed_fundamentals_path", tmp_path)
    pd.DataFrame(
        [
            {"symbol": "RELIANCE", "date": "2022-03-31", "revenue": 100, "net_profit": 10, "eps": 5, "roe": 10},
            {"symbol": "RELIANCE", "date": "2025-03-31", "revenue": 999, "net_profit": 999, "eps": 99, "roe": 99},
        ]
    ).to_parquet(tmp_path / "fundamentals_processed.parquet", index=False)
    analysis = latest_fundamental_analysis("RELIANCE", as_of_date="2023-12-28")
    assert analysis["date"] == "2022-03-31"
    assert analysis["metrics"]["revenue"] == 100
    assert fundamental_as_score("RELIANCE", as_of_date="2023-12-28")["date"] == "2022-03-31"


def test_fundamental_api(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "processed_fundamentals_path", tmp_path)
    pd.DataFrame(
        [
            {"symbol": "RELIANCE", "date": "2022-03-31", "revenue": 100, "net_profit": 10, "eps": 5, "roe": 12, "debt_to_equity": 0.5},
            {"symbol": "RELIANCE", "date": "2023-03-31", "revenue": 120, "net_profit": 14, "eps": 7, "roe": 18, "debt_to_equity": 0.3},
        ]
    ).to_parquet(tmp_path / "fundamentals_processed.parquet", index=False)
    latest = client.get("/api/stocks/RELIANCE/fundamentals")
    assert latest.status_code == 200
    assert latest.json()["symbol"] == "RELIANCE"
    assert latest.json()["fundamental_score"] >= 0
    history = client.get("/api/stocks/RELIANCE/fundamentals/history")
    assert history.status_code == 200
    assert len(history.json()) == 2


def test_signal_falls_back_when_fundamentals_missing(monkeypatch):
    monkeypatch.setattr(prediction_service, "fundamental_as_score", lambda symbol, as_of_date=None: None)
    response = client.get("/api/stocks/RELIANCE/signal")
    assert response.status_code == 200
    assert response.json()["fundamental_score"] is None


def test_signal_includes_fundamentals_when_available(monkeypatch):
    monkeypatch.setattr(
        prediction_service,
        "fundamental_as_score",
        lambda symbol, as_of_date=None: {
            "symbol": symbol,
            "date": "2023-03-31",
            "fundamental_score": 72,
            "fundamental_bias": "GOOD",
            "data_completeness": 80,
            "business_risk_score": 30,
            "business_risk_level": "LOW",
        },
    )
    response = client.get("/api/stocks/RELIANCE/signal")
    assert response.status_code == 200
    payload = response.json()
    assert payload["fundamental_score"] == 72
    assert payload["fundamental_bias"] == "GOOD"
    assert any("Fundamental quality" in factor for factor in payload["positive_factors"])
