import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.services import prediction_service
from backend.app.services.sentiment_service import (
    aggregate_daily_sentiment,
    latest_sentiment,
    sentiment_as_score_0_to_100,
)
from sentiment.finbert import normalize_finbert_output, sentiment_score
from sentiment.preprocessing.clean_news import clean_text, load_news_csv


client = TestClient(app)


def test_news_cleaning_and_duplicate_removal(tmp_path):
    path = tmp_path / "news.csv"
    path.write_text(
        "date,symbol,headline,article\n"
        "2024-01-01, rel , Profit   rises, Revenue up\n"
        "2024-01-01,REL,Profit rises,Revenue up\n"
        "bad,REL,Invalid date,Ignored\n"
        "2024-01-02,REL,,Ignored\n",
        encoding="utf-8",
    )
    frame = load_news_csv(path)
    assert len(frame) == 1
    assert frame.iloc[0]["symbol"] == "REL"
    assert frame.iloc[0]["headline"] == "Profit rises"
    assert clean_text("  profit   loss  ") == "profit loss"


def test_missing_required_news_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("date,article\n2024-01-01,text\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_news_csv(path)


def test_finbert_output_schema_and_score():
    output = normalize_finbert_output(
        [
            {"label": "positive", "score": 0.7},
            {"label": "neutral", "score": 0.2},
            {"label": "negative", "score": 0.1},
        ]
    )
    assert output["sentiment"] == "POSITIVE"
    assert output["confidence"] == 70
    assert output["sentiment_score"] == 60
    assert sentiment_score(0.2, 0.6) == -40


def test_daily_aggregation_and_symbol_filtering():
    frame = pd.DataFrame(
        [
            {"symbol": "RELIANCE", "date": "2024-01-01", "headline": "a", "sentiment_score": 40, "confidence": 80},
            {"symbol": "RELIANCE", "date": "2024-01-01", "headline": "b", "sentiment_score": -10, "confidence": 70},
            {"symbol": None, "date": "2024-01-01", "headline": "market", "sentiment_score": 90, "confidence": 60},
        ]
    )
    daily = aggregate_daily_sentiment(frame)
    assert len(daily) == 1
    row = daily.iloc[0]
    assert row["symbol"] == "RELIANCE"
    assert row["news_count"] == 2
    assert row["average_sentiment_score"] == 15
    assert row["dominant_sentiment"] == "POSITIVE"


def test_no_future_news_leakage(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "processed_sentiment_path", tmp_path)
    sentiment_file = tmp_path / "all_news_sentiment.parquet"
    pd.DataFrame(
        [
            {
                "date": "2024-01-01",
                "symbol": "RELIANCE",
                "headline": "Known news",
                "article": "",
                "sentiment": "POSITIVE",
                "confidence": 80,
                "sentiment_score": 50,
                "positive_probability": 0.7,
                "neutral_probability": 0.2,
                "negative_probability": 0.1,
            },
            {
                "date": "2024-01-05",
                "symbol": "RELIANCE",
                "headline": "Future news",
                "article": "",
                "sentiment": "NEGATIVE",
                "confidence": 90,
                "sentiment_score": -90,
                "positive_probability": 0.05,
                "neutral_probability": 0.05,
                "negative_probability": 0.9,
            },
        ]
    ).to_parquet(sentiment_file, index=False)

    latest = latest_sentiment("RELIANCE", as_of_date="2024-01-03")
    assert latest["date"] == "2024-01-01"
    assert latest["sentiment_score"] == 50
    assert sentiment_as_score_0_to_100("RELIANCE", as_of_date="2024-01-03")["signal_score"] == 75


def test_news_and_sentiment_api(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "processed_sentiment_path", tmp_path)
    pd.DataFrame(
        [
            {
                "date": "2023-12-27",
                "symbol": "RELIANCE",
                "headline": "Cached headline",
                "article": "",
                "sentiment": "POSITIVE",
                "confidence": 75,
                "sentiment_score": 35,
                "positive_probability": 0.55,
                "neutral_probability": 0.35,
                "negative_probability": 0.2,
            }
        ]
    ).to_parquet(tmp_path / "all_news_sentiment.parquet", index=False)

    news = client.get("/api/stocks/RELIANCE/news")
    assert news.status_code == 200
    assert news.json()[0]["headline"] == "Cached headline"

    sentiment = client.get("/api/stocks/RELIANCE/sentiment")
    assert sentiment.status_code == 200
    assert sentiment.json()["sentiment"] == "POSITIVE"

    history = client.get("/api/stocks/RELIANCE/sentiment/history")
    assert history.status_code == 200
    assert history.json()[0]["average_sentiment_score"] == 35


def test_signal_endpoint_falls_back_when_sentiment_missing(monkeypatch):
    monkeypatch.setattr(prediction_service, "sentiment_as_score_0_to_100", lambda symbol, as_of_date=None: None)
    response = client.get("/api/stocks/RELIANCE/signal")
    assert response.status_code == 200
    payload = response.json()
    assert payload["sentiment_score"] is None
    assert payload["signal"] in {"BULLISH", "NEUTRAL", "BEARISH"}


def test_signal_endpoint_includes_sentiment_when_available(monkeypatch):
    monkeypatch.setattr(
        prediction_service,
        "sentiment_as_score_0_to_100",
        lambda symbol, as_of_date=None: {
            "symbol": symbol,
            "date": "2023-12-28",
            "sentiment": "POSITIVE",
            "sentiment_score": 60,
            "signal_score": 80,
            "confidence": 88,
            "news_count": 2,
        },
    )
    response = client.get("/api/stocks/RELIANCE/signal")
    assert response.status_code == 200
    payload = response.json()
    assert payload["sentiment_score"] == 60
    assert payload["sentiment_news_count"] == 2
    assert any("Historical news sentiment" in factor for factor in payload["positive_factors"])
