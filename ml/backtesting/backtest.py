from __future__ import annotations

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

from ml.features.technical_indicators import FEATURE_COLUMNS
from ml.prediction.predict import load_model


BACKTEST_OUTPUT_DIR = Path("ml/data/backtests")


def filter_backtest_data(
    processed: pd.DataFrame,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    stock = processed[processed["Symbol"] == symbol.upper()].sort_values("Date").copy()
    if stock.empty:
        raise ValueError(f"Stock not found: {symbol.upper()}")

    stock["Date"] = pd.to_datetime(stock["Date"])
    if start_date:
        stock = stock[stock["Date"] >= pd.to_datetime(start_date)]
    if end_date:
        stock = stock[stock["Date"] <= pd.to_datetime(end_date)]
    stock.reset_index(drop=True, inplace=True)

    if len(stock) < 3:
        raise ValueError("Insufficient data for backtest after applying date filters.")
    return stock


def generate_predictions(stock: pd.DataFrame, model_dir: str | Path = "models") -> pd.DataFrame:
    payload = load_model(model_dir)
    model = payload["model"]
    features = payload.get("features", FEATURE_COLUMNS)
    missing = [feature for feature in features if feature not in stock.columns]
    if missing:
        raise ValueError(f"Backtest data is missing model features: {missing}")

    result = stock.copy()
    model_input = result[features].astype(float)
    result["probability_up"] = np.asarray(model.predict_proba(model_input))[:, 1]
    result["prediction"] = np.where(np.asarray(model.predict(model_input)) == 1, "UP", "DOWN")
    result["signal"] = np.where(result["prediction"] == "UP", "LONG", "CASH")
    return result


def _entry_price(open_price: float, slippage: float) -> float:
    return float(open_price) * (1 + slippage)


def _exit_price(open_price: float, slippage: float) -> float:
    return float(open_price) * (1 - slippage)


def simulate_trades(
    predicted: pd.DataFrame,
    initial_capital: float = 100000.0,
    transaction_cost: float = 0.001,
    slippage: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if initial_capital <= 0:
        raise ValueError("initial_capital must be greater than zero.")
    if transaction_cost < 0 or transaction_cost >= 1:
        raise ValueError("transaction_cost must be between 0 and 1.")
    if slippage < 0 or slippage >= 1:
        raise ValueError("slippage must be between 0 and 1.")

    cash = float(initial_capital)
    shares = 0
    open_trade: dict | None = None
    trade_rows: list[dict] = []
    equity_rows: list[dict] = []
    previous_equity = float(initial_capital)
    trade_id = 1

    # Signal on row i is executed at row i + 1 Open. The last row can mark equity only.
    for i in range(len(predicted)):
        row = predicted.iloc[i]
        date = pd.to_datetime(row["Date"])

        if i > 0:
            signal_row = predicted.iloc[i - 1]
            should_hold = signal_row["prediction"] == "UP"
            signal_date = pd.to_datetime(signal_row["Date"])
            execution_date = date

            if should_hold and shares == 0:
                entry = _entry_price(row["Open"], slippage)
                shares_to_buy = math.floor(cash / (entry * (1 + transaction_cost)))
                if shares_to_buy > 0:
                    entry_value = shares_to_buy * entry
                    entry_cost = entry_value * transaction_cost
                    cash -= entry_value + entry_cost
                    shares = shares_to_buy
                    open_trade = {
                        "trade_id": trade_id,
                        "symbol": row["Symbol"],
                        "signal_date": signal_date.date().isoformat(),
                        "entry_date": execution_date.date().isoformat(),
                        "entry_price": entry,
                        "shares": shares_to_buy,
                        "entry_value": entry_value,
                        "entry_transaction_cost": entry_cost,
                    }
            elif not should_hold and shares > 0 and open_trade:
                exit_p = _exit_price(row["Open"], slippage)
                exit_value = shares * exit_p
                exit_cost = exit_value * transaction_cost
                cash += exit_value - exit_cost
                total_cost = open_trade["entry_transaction_cost"] + exit_cost
                profit_loss = exit_value - exit_cost - open_trade["entry_value"] - open_trade["entry_transaction_cost"]
                trade_return = profit_loss / (open_trade["entry_value"] + open_trade["entry_transaction_cost"])
                trade_rows.append(
                    {
                        **open_trade,
                        "exit_signal_date": signal_date.date().isoformat(),
                        "exit_date": execution_date.date().isoformat(),
                        "exit_price": exit_p,
                        "exit_value": exit_value,
                        "exit_transaction_cost": exit_cost,
                        "transaction_cost": total_cost,
                        "profit_loss": profit_loss,
                        "return_pct": trade_return * 100,
                    }
                )
                trade_id += 1
                shares = 0
                open_trade = None

        position_value = shares * float(row["Close"])
        total_equity = cash + position_value
        daily_return = (total_equity / previous_equity - 1) if previous_equity else 0
        previous_equity = total_equity
        equity_rows.append(
            {
                "Date": date.date().isoformat(),
                "Cash": cash,
                "Position Value": position_value,
                "Total Equity": total_equity,
                "Daily Return": daily_return,
            }
        )

    # Liquidate any final open position at the final close so metrics represent realized ending capital.
    if shares > 0 and open_trade:
        final_row = predicted.iloc[-1]
        exit_p = _exit_price(final_row["Close"], slippage)
        exit_value = shares * exit_p
        exit_cost = exit_value * transaction_cost
        cash += exit_value - exit_cost
        total_cost = open_trade["entry_transaction_cost"] + exit_cost
        profit_loss = exit_value - exit_cost - open_trade["entry_value"] - open_trade["entry_transaction_cost"]
        trade_return = profit_loss / (open_trade["entry_value"] + open_trade["entry_transaction_cost"])
        trade_rows.append(
            {
                **open_trade,
                "exit_signal_date": pd.to_datetime(final_row["Date"]).date().isoformat(),
                "exit_date": pd.to_datetime(final_row["Date"]).date().isoformat(),
                "exit_price": exit_p,
                "exit_value": exit_value,
                "exit_transaction_cost": exit_cost,
                "transaction_cost": total_cost,
                "profit_loss": profit_loss,
                "return_pct": trade_return * 100,
            }
        )
        equity_rows[-1]["Cash"] = cash
        equity_rows[-1]["Position Value"] = 0.0
        equity_rows[-1]["Total Equity"] = cash

    equity = pd.DataFrame(equity_rows)
    equity["Daily Return"] = equity["Total Equity"].pct_change().fillna(0.0)
    equity["Cumulative Return"] = equity["Total Equity"] / initial_capital - 1
    running_max = equity["Total Equity"].cummax()
    equity["Drawdown"] = equity["Total Equity"] / running_max - 1
    trades = pd.DataFrame(trade_rows)
    return trades, equity


def compare_buy_and_hold(stock: pd.DataFrame, initial_capital: float, transaction_cost: float, slippage: float) -> dict:
    entry = _entry_price(float(stock.iloc[0]["Open"]), slippage)
    exit_p = _exit_price(float(stock.iloc[-1]["Close"]), slippage)
    shares = math.floor(initial_capital / (entry * (1 + transaction_cost)))
    entry_value = shares * entry
    entry_cost = entry_value * transaction_cost
    cash = initial_capital - entry_value - entry_cost
    exit_value = shares * exit_p
    exit_cost = exit_value * transaction_cost
    final_capital = cash + exit_value - exit_cost
    return {
        "buy_hold_final_capital": float(final_capital),
        "buy_hold_return": float(final_capital / initial_capital - 1),
    }


def add_buy_hold_equity(
    stock: pd.DataFrame,
    equity: pd.DataFrame,
    initial_capital: float,
    transaction_cost: float,
    slippage: float,
) -> pd.DataFrame:
    if equity.empty:
        return equity
    entry = _entry_price(float(stock.iloc[0]["Open"]), slippage)
    shares = math.floor(initial_capital / (entry * (1 + transaction_cost)))
    entry_value = shares * entry
    entry_cost = entry_value * transaction_cost
    cash = initial_capital - entry_value - entry_cost

    enriched = equity.copy()
    closes = stock.set_index(pd.to_datetime(stock["Date"]).dt.date)["Close"]
    enriched["Buy Hold Equity"] = enriched["Date"].map(
        lambda value: cash + shares * float(closes[pd.to_datetime(value).date()])
    )
    return enriched


def calculate_metrics(
    symbol: str,
    stock: pd.DataFrame,
    trades: pd.DataFrame,
    equity: pd.DataFrame,
    initial_capital: float,
    transaction_cost: float,
    slippage: float,
) -> dict:
    final_capital = float(equity.iloc[-1]["Total Equity"])
    total_return = final_capital / initial_capital - 1
    total_profit_loss = final_capital - initial_capital

    if trades.empty:
        winning_trades = losing_trades = 0
        win_rate = 0.0
        avg_trade_return = best_trade = worst_trade = None
    else:
        winning_trades = int((trades["profit_loss"] > 0).sum())
        losing_trades = int((trades["profit_loss"] <= 0).sum())
        win_rate = winning_trades / len(trades)
        avg_trade_return = float(trades["return_pct"].mean())
        best_trade = float(trades["return_pct"].max())
        worst_trade = float(trades["return_pct"].min())

    daily_returns = equity["Daily Return"].dropna()
    volatility = float(daily_returns.std() * np.sqrt(252)) if len(daily_returns) > 1 else None
    sharpe = None
    if len(daily_returns) > 30 and daily_returns.std() > 0:
        sharpe = float(np.sqrt(252) * daily_returns.mean() / daily_returns.std())

    benchmark = compare_buy_and_hold(stock, initial_capital, transaction_cost, slippage)
    years = max((pd.to_datetime(stock["Date"]).max() - pd.to_datetime(stock["Date"]).min()).days / 365.25, 0)
    annualized = None
    if years >= 1:
        annualized = float((final_capital / initial_capital) ** (1 / years) - 1)

    return {
        "symbol": symbol.upper(),
        "start_date": str(pd.to_datetime(stock["Date"]).min().date()),
        "end_date": str(pd.to_datetime(stock["Date"]).max().date()),
        "initial_capital": float(initial_capital),
        "final_capital": round(final_capital, 2),
        "total_profit_loss": round(total_profit_loss, 2),
        "total_return": round(total_return, 4),
        "total_return_pct": round(total_return * 100, 2),
        "annualized_return": None if annualized is None else round(annualized, 4),
        "strategy_return": round(total_return, 4),
        "strategy_return_pct": round(total_return * 100, 2),
        "buy_hold_return": round(benchmark["buy_hold_return"], 4),
        "buy_hold_return_pct": round(benchmark["buy_hold_return"] * 100, 2),
        "buy_hold_final_capital": round(benchmark["buy_hold_final_capital"], 2),
        "number_of_trades": int(len(trades)),
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(win_rate, 4),
        "win_rate_pct": round(win_rate * 100, 2),
        "average_trade_return_pct": None if avg_trade_return is None else round(avg_trade_return, 2),
        "best_trade_pct": None if best_trade is None else round(best_trade, 2),
        "worst_trade_pct": None if worst_trade is None else round(worst_trade, 2),
        "max_drawdown": round(float(equity["Drawdown"].min()), 4),
        "max_drawdown_pct": round(float(equity["Drawdown"].min()) * 100, 2),
        "volatility": None if volatility is None else round(volatility, 4),
        "sharpe_ratio": None if sharpe is None else round(sharpe, 4),
        "transaction_cost": float(transaction_cost),
        "slippage": float(slippage),
        "execution_price": "next trading day's Open; final liquidation uses final Close",
        "position_sizing": "whole shares, all-in when predicted UP, cash when predicted DOWN",
    }


def save_backtest_outputs(symbol: str, trades: pd.DataFrame, equity: pd.DataFrame, metrics: dict) -> dict:
    BACKTEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_symbol = symbol.upper()
    trades_path = BACKTEST_OUTPUT_DIR / f"{safe_symbol}_trades.csv"
    equity_path = BACKTEST_OUTPUT_DIR / f"{safe_symbol}_equity_curve.csv"
    summary_path = BACKTEST_OUTPUT_DIR / f"{safe_symbol}_summary.json"
    trades.to_csv(trades_path, index=False)
    equity.to_csv(equity_path, index=False)
    summary_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return {
        "trade_log_path": str(trades_path),
        "equity_curve_path": str(equity_path),
        "summary_path": str(summary_path),
    }


def run_backtest(
    processed: pd.DataFrame,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    initial_capital: float = 100000.0,
    transaction_cost: float = 0.001,
    slippage: float = 0.0,
    model_dir: str | Path = "models",
    save_outputs: bool = True,
) -> dict:
    stock = filter_backtest_data(processed, symbol, start_date, end_date)
    predicted = generate_predictions(stock, model_dir=model_dir)
    trades, equity = simulate_trades(predicted, initial_capital, transaction_cost, slippage)
    equity = add_buy_hold_equity(stock, equity, initial_capital, transaction_cost, slippage)
    metrics = calculate_metrics(symbol, stock, trades, equity, initial_capital, transaction_cost, slippage)
    metrics["equity_curve"] = equity.tail(250).to_dict(orient="records")
    if save_outputs:
        metrics.update(save_backtest_outputs(symbol, trades, equity, {k: v for k, v in metrics.items() if k != "equity_curve"}))
    return metrics
