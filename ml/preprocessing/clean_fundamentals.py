from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

COLUMN_ALIASES = {
    "ticker": "symbol",
    "company_symbol": "symbol",
    "report_date": "date",
    "period": "date",
    "sales": "revenue",
    "total_revenue": "revenue",
    "profit_after_tax": "net_profit",
    "pat": "net_profit",
    "net_income": "net_profit",
    "earnings_per_share": "eps",
    "p/e": "pe_ratio",
    "pe": "pe_ratio",
    "price_to_earnings": "pe_ratio",
    "p/b": "pb_ratio",
    "pb": "pb_ratio",
    "price_to_book": "pb_ratio",
    "return_on_equity": "roe",
    "return_on_capital_employed": "roce",
    "d/e": "debt_to_equity",
    "de_ratio": "debt_to_equity",
    "fcf": "free_cash_flow",
}

NUMERIC_COLUMNS = {
    "revenue",
    "net_profit",
    "eps",
    "pe_ratio",
    "pb_ratio",
    "roe",
    "roce",
    "debt",
    "debt_to_equity",
    "market_cap",
    "operating_margin",
    "net_margin",
    "free_cash_flow",
    "dividend_yield",
}

NON_NEGATIVE_COLUMNS = {
    "revenue",
    "pe_ratio",
    "pb_ratio",
    "debt",
    "debt_to_equity",
    "market_cap",
    "dividend_yield",
}


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for column in frame.columns:
        normalized = str(column).strip().lower().replace(" ", "_")
        renamed[column] = COLUMN_ALIASES.get(normalized, normalized)
    return frame.rename(columns=renamed)


def clean_fundamental_frame(frame: pd.DataFrame, source: str | Path = "fundamentals") -> pd.DataFrame:
    loaded = len(frame)
    frame = normalize_columns(frame)
    required = {"symbol", "date"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Fundamental data missing required columns: {', '.join(sorted(missing))}")

    frame["symbol"] = frame["symbol"].map(_clean_symbol)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in NUMERIC_COLUMNS & set(frame.columns):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    valid = frame.dropna(subset=["symbol", "date"]).copy()
    for column in NON_NEGATIVE_COLUMNS & set(valid.columns):
        valid = valid[(valid[column].isna()) | (valid[column] >= 0)]
    if "pe_ratio" in valid.columns:
        valid = valid[(valid["pe_ratio"].isna()) | (valid["pe_ratio"] <= 500)]
    if "pb_ratio" in valid.columns:
        valid = valid[(valid["pb_ratio"].isna()) | (valid["pb_ratio"] <= 100)]
    if "debt_to_equity" in valid.columns:
        valid = valid[(valid["debt_to_equity"].isna()) | (valid["debt_to_equity"] <= 100)]

    valid = valid.drop_duplicates(subset=["symbol", "date"], keep="last").sort_values(["symbol", "date"])
    valid["date"] = valid["date"].dt.strftime("%Y-%m-%d")
    retained = len(valid)
    logger.info("Loaded fundamental rows=%s removed=%s retained=%s source=%s", loaded, loaded - retained, retained, source)
    return valid.reset_index(drop=True)


def load_fundamental_file(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
    else:
        frame = pd.read_csv(path)
    return clean_fundamental_frame(frame, source=path)


def load_fundamental_folder(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    files = sorted([*path.glob("*.csv"), *path.glob("*.parquet")])
    if not files:
        return pd.DataFrame(columns=["symbol", "date"])
    frames = [load_fundamental_file(file) for file in files]
    combined = pd.concat(frames, ignore_index=True)
    loaded = len(combined)
    combined = combined.drop_duplicates(subset=["symbol", "date"], keep="last").sort_values(["symbol", "date"])
    logger.info("Combined fundamental rows=%s removed=%s retained=%s", loaded, loaded - len(combined), len(combined))
    return combined.reset_index(drop=True)


def _clean_symbol(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    symbol = str(value).strip().upper()
    if not symbol or not symbol.replace("-", "").isalnum():
        return None
    return symbol
