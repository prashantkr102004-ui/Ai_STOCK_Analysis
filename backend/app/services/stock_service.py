from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from backend.app.core.config import get_settings


def _processed_path() -> Path:
    return get_settings().processed_path / "all_stocks_features.parquet"


def normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized or not normalized.replace("-", "").isalnum():
        raise ValueError("Invalid symbol.")
    return normalized


def validate_date_range(start_date: str | None, end_date: str | None) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    start = pd.to_datetime(start_date, errors="coerce") if start_date else None
    end = pd.to_datetime(end_date, errors="coerce") if end_date else None
    if start_date and pd.isna(start):
        raise ValueError("Invalid start_date. Use YYYY-MM-DD.")
    if end_date and pd.isna(end):
        raise ValueError("Invalid end_date. Use YYYY-MM-DD.")
    if start is not None and end is not None and end < start:
        raise ValueError("end_date must be greater than or equal to start_date.")
    return start, end


def load_processed_data() -> pd.DataFrame:
    path = _processed_path()
    if path.exists():
        return pd.read_parquet(path)
    cleaned = get_settings().cleaned_path / "all_stocks.parquet"
    if cleaned.exists():
        return pd.read_parquet(cleaned)
    raise FileNotFoundError("No processed or cleaned dataset found. Run the data pipeline first.")


def get_data_status() -> dict:
    status_path = get_settings().processed_path / "data_status.json"
    if status_path.exists():
        status = json.loads(status_path.read_text(encoding="utf-8"))
        return {
            "number_of_stocks": int(status.get("stocks", 0)),
            "total_historical_records": int(status.get("records", 0)),
            "earliest_available_date": status.get("earliest_date"),
            "latest_available_date": status.get("latest_date"),
            "number_of_processed_files": len(list(get_settings().processed_path.glob("*_features.parquet"))),
            "last_processing_time": status.get("last_processing_time"),
        }
    df = load_processed_data()
    return {
        "number_of_stocks": int(df["Symbol"].nunique()),
        "total_historical_records": int(len(df)),
        "earliest_available_date": str(pd.to_datetime(df["Date"]).min().date()),
        "latest_available_date": str(pd.to_datetime(df["Date"]).max().date()),
        "number_of_processed_files": len(list(get_settings().processed_path.glob("*_features.parquet"))),
        "last_processing_time": None,
    }


def list_stocks() -> list[dict]:
    df = load_processed_data()
    return [{"symbol": symbol} for symbol in sorted(df["Symbol"].unique())]


def get_stock(symbol: str) -> dict:
    df = load_processed_data()
    symbol = normalize_symbol(symbol)
    stock = df[df["Symbol"] == symbol].sort_values("Date")
    if stock.empty:
        raise KeyError(symbol)
    latest = stock.iloc[-1]
    return {
        "symbol": symbol,
        "record_count": int(len(stock)),
        "start_date": str(pd.to_datetime(stock["Date"]).min().date()),
        "end_date": str(pd.to_datetime(stock["Date"]).max().date()),
        "latest_close": float(latest["Close"]),
        "latest_date": str(pd.to_datetime(latest["Date"]).date()),
    }


def get_history(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 400,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")
    start, end = validate_date_range(start_date, end_date)
    df = load_processed_data()
    symbol = normalize_symbol(symbol)
    stock = df[df["Symbol"] == symbol].sort_values("Date")
    if start is not None:
        stock = stock[pd.to_datetime(stock["Date"]) >= start]
    if end is not None:
        stock = stock[pd.to_datetime(stock["Date"]) <= end]
    stock = stock.tail(limit)
    if stock.empty:
        raise KeyError(symbol)
    columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    present = [column for column in columns if column in stock.columns]
    out = stock[present].copy()
    out.rename(
        columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"},
        inplace=True,
    )
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    return out.where(pd.notna(out), None).to_dict(orient="records")


def get_indicators(symbol: str) -> dict:
    df = load_processed_data()
    symbol = normalize_symbol(symbol)
    stock = df[df["Symbol"] == symbol].sort_values("Date")
    if stock.empty:
        raise KeyError(symbol)
    latest = stock.iloc[-1]
    mapping = {
        "rsi": "RSI",
        "macd": "MACD",
        "macd_signal": "MACD_signal",
        "macd_histogram": "MACD_hist",
        "sma_20": "SMA_20",
        "sma_50": "SMA_50",
        "sma_200": "SMA_200",
        "ema_20": "EMA_20",
        "ema_50": "EMA_50",
        "bollinger_upper": "BB_upper",
        "bollinger_middle": "BB_middle",
        "bollinger_lower": "BB_lower",
        "atr": "ATR",
        "volume": "Volume",
        "volume_ratio": "Volume_Ratio",
        "volatility": "Rolling_Volatility",
    }
    response = {"symbol": symbol}
    for api_name, column in mapping.items():
        value = latest.get(column)
        response[api_name] = None if pd.isna(value) else float(value)
    return response
