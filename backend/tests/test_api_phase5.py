from fastapi.testclient import TestClient

from backend.app.api import routes_predictions, routes_stocks
from backend.app.main import app
from ml.prediction.predict import ModelNotTrainedError


client = TestClient(app)


def test_stocks_endpoint_returns_symbol_list():
    response = client.get("/api/stocks")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert {"symbol": "RELIANCE"} in payload


def test_stock_detail_endpoint():
    response = client.get("/api/stocks/RELIANCE")
    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "RELIANCE"
    assert payload["record_count"] > 0
    assert payload["latest_close"] > 0


def test_stock_history_with_filters():
    response = client.get("/api/stocks/RELIANCE/history?start_date=2023-01-01&end_date=2023-12-31&limit=5")
    assert response.status_code == 200
    history = response.json()["history"]
    assert 0 < len(history) <= 5
    assert set(["date", "open", "high", "low", "close", "volume"]).issubset(history[0])


def test_indicators_endpoint():
    response = client.get("/api/stocks/RELIANCE/indicators")
    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "RELIANCE"
    assert "rsi" in payload
    assert "macd" in payload


def test_prediction_endpoint_uses_saved_model():
    response = client.get("/api/stocks/RELIANCE/prediction")
    assert response.status_code == 200
    payload = response.json()
    assert payload["prediction"] in {"UP", "DOWN"}
    assert payload["model"] == "XGBoost"
    assert payload["model_version"]


def test_signal_endpoint():
    response = client.get("/api/stocks/RELIANCE/signal")
    assert response.status_code == 200
    payload = response.json()
    assert payload["signal"] in {"BULLISH", "NEUTRAL", "BEARISH"}
    assert payload["description"] == "Model-based analytical signal; not financial advice."


def test_backtest_post_get_equity_and_trades():
    post_response = client.post(
        "/api/stocks/RELIANCE/backtest",
        json={"initial_capital": 100000, "transaction_cost": 0.001, "slippage": 0},
    )
    assert post_response.status_code == 200
    assert post_response.json()["number_of_trades"] > 0

    get_response = client.get("/api/stocks/RELIANCE/backtest")
    assert get_response.status_code == 200
    assert get_response.json()["symbol"] == "RELIANCE"

    equity_response = client.get("/api/stocks/RELIANCE/backtest/equity")
    assert equity_response.status_code == 200
    assert equity_response.json()["equity_curve"]

    trades_response = client.get("/api/stocks/RELIANCE/backtest/trades")
    assert trades_response.status_code == 200
    assert trades_response.json()


def test_model_status_and_feature_importance():
    status = client.get("/api/model/status")
    assert status.status_code == 200
    assert status.json()["trained"] is True
    assert status.json()["accuracy"] is not None

    importance = client.get("/api/model/feature-importance")
    assert importance.status_code == 200
    payload = importance.json()
    assert payload
    assert payload[0]["importance"] >= payload[-1]["importance"]


def test_data_status_endpoint():
    response = client.get("/api/data/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["number_of_stocks"] > 0
    assert payload["total_historical_records"] > 0


def test_docs_and_redoc_available():
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_unknown_stock_returns_404():
    response = client.get("/api/stocks/NOTREAL")
    assert response.status_code == 404


def test_invalid_dates_return_400():
    response = client.get("/api/stocks/RELIANCE/history?start_date=2024-01-01&end_date=2023-01-01")
    assert response.status_code == 400


def test_invalid_capital_and_transaction_cost():
    capital = client.post("/api/stocks/RELIANCE/backtest", json={"initial_capital": 0})
    assert capital.status_code == 422
    cost = client.post("/api/stocks/RELIANCE/backtest", json={"transaction_cost": -0.1})
    assert cost.status_code == 422


def test_model_unavailable_returns_503(monkeypatch):
    monkeypatch.setattr(
        routes_predictions,
        "latest_prediction",
        lambda symbol: (_ for _ in ()).throw(ModelNotTrainedError("Model not trained")),
    )
    response = client.get("/api/stocks/RELIANCE/prediction")
    assert response.status_code == 503


def test_missing_backtest_returns_404():
    response = client.get("/api/stocks/NEVERBACKTESTED/backtest")
    assert response.status_code == 404


def test_missing_processed_data_returns_503(monkeypatch):
    monkeypatch.setattr(
        routes_stocks,
        "list_stocks",
        lambda: (_ for _ in ()).throw(FileNotFoundError("No processed data")),
    )
    response = client.get("/api/stocks")
    assert response.status_code == 503
