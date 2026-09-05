import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.signal_explanation_service import (
    calculate_risk_score,
    combined_signal_score,
    confidence_level,
    explain_signal,
    signal_from_score,
    technical_score_from_factors,
)


client = TestClient(app)


def _sample_frame():
    return pd.DataFrame(
        [
            {
                "Date": "2024-01-01",
                "Symbol": "TEST",
                "Close": 110,
                "SMA_20": 105,
                "SMA_50": 100,
                "EMA_20": 108,
                "EMA_50": 102,
                "RSI": 58,
                "MACD": 2.5,
                "MACD_signal": 1.5,
                "Volume_Ratio": 1.2,
                "Return_5D": 0.03,
                "Rolling_Volatility": 0.01,
                "ATR": 2.0,
            }
        ]
    )


def test_confidence_band_logic():
    assert confidence_level(52) == "Very Low Confidence"
    assert confidence_level(57) == "Low Confidence"
    assert confidence_level(65) == "Moderate Confidence"
    assert confidence_level(75) == "High Confidence"
    assert confidence_level(85) == "Very High Confidence"


def test_neutral_zone_logic():
    assert signal_from_score(61) == "BULLISH"
    assert signal_from_score(39) == "BEARISH"
    assert signal_from_score(50) == "NEUTRAL"


def test_technical_and_combined_scoring():
    technical_score, technical_bias = technical_score_from_factors(["a", "b", "c"], ["d"])
    assert technical_score == 75
    assert technical_bias == "BULLISH"
    assert combined_signal_score(50, 100) == 65


def test_risk_score_uses_volatility_and_confidence():
    latest = _sample_frame().iloc[-1]
    low_confidence_risk = calculate_risk_score(latest, confidence=52)
    high_confidence_risk = calculate_risk_score(latest, confidence=82)
    assert 0 <= high_confidence_risk <= 100
    assert low_confidence_risk > high_confidence_risk


def test_explanation_generation_uses_real_row_values():
    prediction = {
        "symbol": "TEST",
        "prediction": "UP",
        "probability_up": 0.62,
        "probability_down": 0.38,
        "confidence": 62,
        "prediction_date": "2024-01-01",
    }
    explanation = explain_signal(
        _sample_frame(),
        "TEST",
        prediction,
        [{"feature": "MACD", "importance": 0.2}],
    )
    assert explanation["signal"] == "BULLISH"
    assert explanation["confidence_level"] == "Moderate Confidence"
    assert explanation["technical_score"] > 50
    assert explanation["combined_score"] >= 60
    assert explanation["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert explanation["positive_factors"]
    assert explanation["top_model_features"][0]["explanation"]


def test_signal_api_returns_phase7_fields():
    response = client.get("/api/stocks/RELIANCE/signal")
    assert response.status_code == 200
    payload = response.json()
    assert payload["signal"] in {"BULLISH", "NEUTRAL", "BEARISH"}
    assert payload["confidence_level"]
    assert "technical_score" in payload
    assert "combined_score" in payload
    assert "risk_score" in payload
    assert payload["description"] == "Model-based analytical signal; not financial advice."


def test_explanation_api_returns_feature_and_factor_details():
    response = client.get("/api/stocks/RELIANCE/explanation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_prediction"] in {"UP", "DOWN"}
    assert isinstance(payload["technical_confirmations"], list)
    assert isinstance(payload["technical_contradictions"], list)
    assert payload["top_model_features"]
    assert payload["summary"]
