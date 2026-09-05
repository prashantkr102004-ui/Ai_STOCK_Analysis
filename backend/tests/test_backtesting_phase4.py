import math

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app
from ml.backtesting import backtest as bt


class DummyModel:
    def __init__(self, predictions):
        self.predictions = predictions
        self.seen_inputs = None

    def predict(self, x):
        self.seen_inputs = x.copy()
        return self.predictions[: len(x)]

    def predict_proba(self, x):
        self.seen_inputs = x.copy()
        return [[0.1, 0.9] if pred == 1 else [0.8, 0.2] for pred in self.predictions[: len(x)]]


def deterministic_predicted_frame():
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]),
            "Symbol": ["TEST"] * 4,
            "Open": [10.0, 11.0, 12.0, 9.0],
            "Close": [10.0, 12.0, 9.0, 10.0],
            "prediction": ["UP", "UP", "DOWN", "DOWN"],
        }
    )


def test_signal_generation_uses_model_predictions(monkeypatch):
    model = DummyModel([1, 0])
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "Symbol": ["TEST", "TEST"],
            "Close": [10.0, 11.0],
            "RSI": [40.0, 60.0],
        }
    )
    monkeypatch.setattr(bt, "load_model", lambda model_dir: {"model": model, "features": ["RSI"]})
    predicted = bt.generate_predictions(frame, model_dir="unused")
    assert predicted["prediction"].tolist() == ["UP", "DOWN"]
    assert predicted["signal"].tolist() == ["LONG", "CASH"]


def test_entry_exit_timing_whole_shares_and_costs():
    trades, equity = bt.simulate_trades(
        deterministic_predicted_frame(),
        initial_capital=1000,
        transaction_cost=0.01,
        slippage=0,
    )
    first = trades.iloc[0]
    expected_shares = math.floor(1000 / (11 * 1.01))
    assert first["signal_date"] == "2024-01-01"
    assert first["entry_date"] == "2024-01-02"
    assert first["exit_signal_date"] == "2024-01-03"
    assert first["exit_date"] == "2024-01-04"
    assert first["shares"] == expected_shares
    assert round(first["transaction_cost"], 2) == round((expected_shares * 11 + expected_shares * 9) * 0.01, 2)
    assert not equity.empty


def test_profit_loss_and_win_rate_drawdown_buy_hold():
    stock = deterministic_predicted_frame()
    trades, equity = bt.simulate_trades(stock, initial_capital=1000, transaction_cost=0, slippage=0)
    equity = bt.add_buy_hold_equity(stock, equity, 1000, 0, 0)
    metrics = bt.calculate_metrics("TEST", stock, trades, equity, 1000, 0, 0)
    assert metrics["number_of_trades"] == 1
    assert metrics["losing_trades"] == 1
    assert metrics["win_rate"] == 0
    assert metrics["max_drawdown"] < 0
    assert metrics["buy_hold_final_capital"] == 1000


def test_slippage_changes_entry_and_exit_prices():
    trades, _ = bt.simulate_trades(deterministic_predicted_frame(), initial_capital=1000, transaction_cost=0, slippage=0.01)
    first = trades.iloc[0]
    assert first["entry_price"] == 11 * 1.01
    assert first["exit_price"] == 9 * 0.99


def test_no_lookahead_bias_predictions_use_current_features(monkeypatch):
    model = DummyModel([1, 0, 1])
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "Symbol": ["TEST"] * 3,
            "Close": [10.0, 20.0, 5.0],
            "RSI": [10.0, 20.0, 30.0],
            "future_RSI": [999.0, 999.0, 999.0],
        }
    )
    monkeypatch.setattr(bt, "load_model", lambda model_dir: {"model": model, "features": ["RSI"]})
    bt.generate_predictions(frame, model_dir="unused")
    assert model.seen_inputs.columns.tolist() == ["RSI"]
    assert model.seen_inputs["RSI"].tolist() == [10.0, 20.0, 30.0]


def test_backtest_api_post(monkeypatch):
    monkeypatch.setattr(
        "backend.app.api.routes_backtest.run_symbol_backtest",
        lambda symbol, **kwargs: {
            "symbol": symbol.upper(),
            "start_date": "2024-01-01",
            "end_date": "2024-01-04",
            "initial_capital": kwargs["initial_capital"],
            "final_capital": 1000,
            "total_profit_loss": 0,
            "total_return": 0,
            "total_return_pct": 0,
            "annualized_return": None,
            "strategy_return": 0,
            "strategy_return_pct": 0,
            "buy_hold_return": 0,
            "buy_hold_return_pct": 0,
            "buy_hold_final_capital": 1000,
            "number_of_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "win_rate_pct": 0,
            "average_trade_return_pct": None,
            "best_trade_pct": None,
            "worst_trade_pct": None,
            "max_drawdown": 0,
            "max_drawdown_pct": 0,
            "volatility": None,
            "sharpe_ratio": None,
            "transaction_cost": kwargs["transaction_cost"],
            "slippage": kwargs["slippage"],
            "equity_curve": [],
        },
    )
    client = TestClient(app)
    response = client.post("/api/stocks/TEST/backtest", json={"initial_capital": 1000, "slippage": 0.01})
    assert response.status_code == 200
    assert response.json()["symbol"] == "TEST"
