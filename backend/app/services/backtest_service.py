import json
from pathlib import Path
import pandas as pd

from ml.backtesting.backtest import run_backtest
from backend.app.services.stock_service import load_processed_data, normalize_symbol, validate_date_range


class BacktestNotFoundError(FileNotFoundError):
    pass


def run_symbol_backtest(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    initial_capital: float = 100000,
    transaction_cost: float = 0.001,
    slippage: float = 0,
) -> dict:
    validate_date_range(start_date, end_date)
    result = run_backtest(
        load_processed_data(),
        normalize_symbol(symbol),
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        transaction_cost=transaction_cost,
        slippage=slippage,
    )
    output = Path("ml/data/backtests") / f"{symbol.upper()}_summary.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def latest_backtest(symbol: str) -> dict:
    symbol = normalize_symbol(symbol)
    path = Path("ml/data/backtests") / f"{symbol}_summary.json"
    if not path.exists():
        raise BacktestNotFoundError(f"No saved backtest found for {symbol}. Run POST /api/stocks/{symbol}/backtest first.")
    result = json.loads(path.read_text(encoding="utf-8"))
    if "equity_curve" not in result:
        equity_path = Path("ml/data/backtests") / f"{symbol}_equity_curve.csv"
        if equity_path.exists():
            result["equity_curve"] = get_equity_curve(symbol)["equity_curve"]
    return result


def _normalize_records(df: pd.DataFrame) -> list[dict]:
    records = []
    for row in df.where(pd.notna(df), None).to_dict(orient="records"):
        records.append({str(key).strip().lower().replace(" ", "_"): value for key, value in row.items()})
    return records


def get_equity_curve(symbol: str) -> dict:
    symbol = normalize_symbol(symbol)
    path = Path("ml/data/backtests") / f"{symbol}_equity_curve.csv"
    if not path.exists():
        raise BacktestNotFoundError(f"No saved equity curve found for {symbol}.")
    records = _normalize_records(pd.read_csv(path))
    return {"symbol": symbol, "equity_curve": records}


def get_trade_history(symbol: str) -> list[dict]:
    symbol = normalize_symbol(symbol)
    path = Path("ml/data/backtests") / f"{symbol}_trades.csv"
    if not path.exists():
        raise BacktestNotFoundError(f"No saved trade log found for {symbol}.")
    records = _normalize_records(pd.read_csv(path))
    for record in records:
        if "return_pct" in record:
            record["return_percentage"] = record.pop("return_pct")
    return records
