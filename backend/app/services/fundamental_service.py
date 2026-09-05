from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.core.config import get_settings
from backend.app.services.stock_service import normalize_symbol, validate_date_range
from ml.preprocessing.clean_fundamentals import NUMERIC_COLUMNS, load_fundamental_folder


class FundamentalsNotFoundError(FileNotFoundError):
    pass


def processed_fundamentals_file() -> Path:
    return get_settings().processed_fundamentals_path / "fundamentals_processed.parquet"


def process_fundamentals() -> dict:
    settings = get_settings()
    settings.processed_fundamentals_path.mkdir(parents=True, exist_ok=True)
    data = load_fundamental_folder(settings.fundamentals_path)
    if data.empty:
        raise FundamentalsNotFoundError("No local fundamental dataset found.")
    data.to_parquet(processed_fundamentals_file(), index=False)
    return {
        "companies": int(data["symbol"].nunique()),
        "records": int(len(data)),
        "start_date": str(pd.to_datetime(data["date"]).min().date()),
        "end_date": str(pd.to_datetime(data["date"]).max().date()),
        "output_path": str(processed_fundamentals_file()),
    }


def load_processed_fundamentals() -> pd.DataFrame:
    path = processed_fundamentals_file()
    if path.exists():
        return pd.read_parquet(path)
    if any(get_settings().fundamentals_path.glob("*.csv")) or any(get_settings().fundamentals_path.glob("*.parquet")):
        process_fundamentals()
        return pd.read_parquet(path)
    raise FundamentalsNotFoundError("No processed fundamental data found.")


def get_fundamental_history(symbol: str, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    symbol = normalize_symbol(symbol)
    start, end = validate_date_range(start_date, end_date)
    data = load_processed_fundamentals()
    stock = data[data["symbol"] == symbol].sort_values("date").copy()
    if start is not None:
        stock = stock[pd.to_datetime(stock["date"]) >= start]
    if end is not None:
        stock = stock[pd.to_datetime(stock["date"]) <= end]
    if stock.empty:
        raise FundamentalsNotFoundError(f"No fundamental data available for {symbol}.")
    return _records(stock)


def latest_fundamental_analysis(symbol: str, as_of_date: str | None = None) -> dict:
    symbol = normalize_symbol(symbol)
    data = load_processed_fundamentals()
    stock = data[data["symbol"] == symbol].sort_values("date").copy()
    if as_of_date:
        cutoff = pd.to_datetime(as_of_date, errors="coerce")
        if pd.isna(cutoff):
            raise ValueError("Invalid as_of_date. Use YYYY-MM-DD.")
        stock = stock[pd.to_datetime(stock["date"]) <= cutoff]
    if stock.empty:
        raise FundamentalsNotFoundError(f"No fundamental data available for {symbol}.")
    stock = stock.sort_values("date")
    latest = stock.iloc[-1]
    previous = stock.iloc[-2] if len(stock) >= 2 else None
    metrics = calculate_metrics(latest, previous)
    scores = calculate_category_scores(metrics)
    score, completeness = overall_score(scores)
    strengths, weaknesses = strengths_and_weaknesses(metrics)
    business_risk_score, business_risk_level = business_risk(metrics)
    return {
        "symbol": symbol,
        "date": latest["date"],
        "fundamental_score": score,
        "fundamental_bias": fundamental_bias(score),
        "data_completeness": completeness,
        "growth_score": scores.get("growth"),
        "profitability_score": scores.get("profitability"),
        "valuation_score": scores.get("valuation"),
        "balance_sheet_score": scores.get("balance_sheet"),
        "cash_flow_score": scores.get("cash_flow"),
        "business_risk_score": business_risk_score,
        "business_risk_level": business_risk_level,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "metrics": metrics,
    }


def fundamental_as_score(symbol: str, as_of_date: str | None = None) -> dict | None:
    try:
        analysis = latest_fundamental_analysis(symbol, as_of_date=as_of_date)
    except FundamentalsNotFoundError:
        return None
    return analysis


def calculate_metrics(latest: pd.Series, previous: pd.Series | None = None) -> dict[str, float | None]:
    metrics = {column: _number(latest.get(column)) for column in NUMERIC_COLUMNS}
    if previous is not None:
        metrics["revenue_growth_yoy"] = _growth(latest.get("revenue"), previous.get("revenue"))
        metrics["profit_growth_yoy"] = _growth(latest.get("net_profit"), previous.get("net_profit"))
        metrics["eps_growth_yoy"] = _growth(latest.get("eps"), previous.get("eps"))
    else:
        metrics["revenue_growth_yoy"] = None
        metrics["profit_growth_yoy"] = None
        metrics["eps_growth_yoy"] = None
    return {key: value for key, value in metrics.items() if value is not None}


def calculate_category_scores(metrics: dict[str, float]) -> dict[str, float | None]:
    return {
        "growth": _average(
            [
                _growth_score(metrics.get("revenue_growth_yoy")),
                _growth_score(metrics.get("profit_growth_yoy")),
                _growth_score(metrics.get("eps_growth_yoy")),
            ]
        ),
        "profitability": _average(
            [
                _higher_better(metrics.get("roe"), 5, 25),
                _higher_better(metrics.get("roce"), 8, 30),
                _higher_better(metrics.get("operating_margin"), 8, 25),
                _higher_better(metrics.get("net_margin"), 5, 20),
            ]
        ),
        "valuation": _average(
            [
                _lower_better(metrics.get("pe_ratio"), 15, 60),
                _lower_better(metrics.get("pb_ratio"), 1, 8),
            ]
        ),
        "balance_sheet": _average([_lower_better(metrics.get("debt_to_equity"), 0.2, 2.0)]),
        "cash_flow": _average([_cash_flow_score(metrics.get("free_cash_flow"))]),
    }


def overall_score(scores: dict[str, float | None]) -> tuple[float, float]:
    weights = get_settings().fundamental_category_weights
    available = {key: value for key, value in scores.items() if value is not None}
    if not available:
        return 50.0, 0.0
    total_weight = sum(weights[key] for key in available)
    weighted = sum(float(available[key]) * weights[key] for key in available) / total_weight
    completeness = round((len(available) / len(weights)) * 100, 2)
    return round(weighted, 2), completeness


def fundamental_bias(score: float) -> str:
    thresholds = get_settings().fundamental_bias_thresholds
    if score >= thresholds["strong"]:
        return "STRONG"
    if score >= thresholds["good"]:
        return "GOOD"
    if score >= thresholds["neutral"]:
        return "NEUTRAL"
    return "WEAK"


def strengths_and_weaknesses(metrics: dict[str, float]) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    weaknesses: list[str] = []
    if (value := metrics.get("revenue_growth_yoy")) is not None:
        (strengths if value > 0.08 else weaknesses if value < 0 else []).append(
            "Positive revenue growth" if value > 0.08 else "Revenue declined year over year"
        )
    if (value := metrics.get("profit_growth_yoy")) is not None:
        (strengths if value > 0.08 else weaknesses if value < 0 else []).append(
            "Positive profit growth" if value > 0.08 else "Profit declined year over year"
        )
    if (value := metrics.get("roe")) is not None:
        (strengths if value >= 18 else weaknesses if value < 8 else []).append("Strong ROE" if value >= 18 else "Weak ROE")
    if (value := metrics.get("roce")) is not None:
        (strengths if value >= 20 else weaknesses if value < 10 else []).append("Strong ROCE" if value >= 20 else "Weak ROCE")
    if (value := metrics.get("debt_to_equity")) is not None:
        (strengths if value <= 0.5 else weaknesses if value > 2 else []).append(
            "Low debt-to-equity" if value <= 0.5 else "High debt-to-equity"
        )
    if (value := metrics.get("pe_ratio")) is not None:
        (strengths if 0 < value <= 25 else weaknesses if value > 60 else []).append(
            "Reasonable P/E valuation" if 0 < value <= 25 else "High P/E valuation"
        )
    if (value := metrics.get("free_cash_flow")) is not None:
        (strengths if value > 0 else weaknesses if value < 0 else []).append(
            "Positive free cash flow" if value > 0 else "Negative free cash flow"
        )
    return strengths or ["No clear fundamental strengths from available fields"], weaknesses


def business_risk(metrics: dict[str, float]) -> tuple[float, str]:
    risk = 20.0
    if metrics.get("debt_to_equity") is not None:
        risk += min(max((metrics["debt_to_equity"] - 0.5) * 20, 0), 30)
    if metrics.get("profit_growth_yoy") is not None and metrics["profit_growth_yoy"] < 0:
        risk += 20
    if metrics.get("free_cash_flow") is not None and metrics["free_cash_flow"] < 0:
        risk += 20
    if metrics.get("roe") is not None and metrics["roe"] < 8:
        risk += 15
    risk = round(min(risk, 100), 2)
    level = "LOW" if risk < 35 else "HIGH" if risk >= 65 else "MEDIUM"
    return risk, level


def _growth(current: Any, previous: Any) -> float | None:
    current_number = _number(current)
    previous_number = _number(previous)
    if current_number is None or previous_number in (None, 0):
        return None
    return round((current_number - previous_number) / abs(previous_number), 4)


def _growth_score(value: float | None) -> float | None:
    if value is None:
        return None
    return _clamp((value + 0.10) / 0.30 * 100)


def _higher_better(value: float | None, low: float, high: float) -> float | None:
    if value is None:
        return None
    return _clamp((value - low) / (high - low) * 100)


def _lower_better(value: float | None, good: float, poor: float) -> float | None:
    if value is None or value < 0:
        return None
    return _clamp((poor - value) / (poor - good) * 100)


def _cash_flow_score(value: float | None) -> float | None:
    if value is None:
        return None
    return 75.0 if value > 0 else 25.0 if value < 0 else 50.0


def _average(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 2)


def _clamp(value: float) -> float:
    return round(max(0, min(100, value)), 2)


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def _records(df: pd.DataFrame) -> list[dict]:
    return df.where(pd.notna(df), None).to_dict(orient="records")
