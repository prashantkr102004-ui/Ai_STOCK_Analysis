from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}
NUMERIC_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


class DataValidationError(ValueError):
    pass


@dataclass
class CleaningReport:
    source: str
    loaded_rows: int
    removed_rows: int
    retained_rows: int
    symbols: int
    missing_values: int
    invalid_ohlcv_rows: int
    duplicate_rows: int


def _symbol_from_filename(path: Path) -> str:
    return path.stem.upper()


def load_csv(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise DataValidationError(f"{csv_path.name} is missing required columns: {sorted(missing)}")

    if "Symbol" not in df.columns:
        df["Symbol"] = _symbol_from_filename(csv_path)

    return df


def clean_stock_data(df: pd.DataFrame, source: str = "dataframe") -> tuple[pd.DataFrame, CleaningReport]:
    loaded_rows = len(df)
    working = df.copy()
    working.columns = [str(col).strip() for col in working.columns]

    missing = REQUIRED_COLUMNS - set(working.columns)
    if missing:
        raise DataValidationError(f"{source} is missing required columns: {sorted(missing)}")

    if "Symbol" not in working.columns:
        raise DataValidationError(f"{source} has no Symbol column after loading")

    working["Date"] = pd.to_datetime(working["Date"], errors="coerce")
    working["Symbol"] = working["Symbol"].astype(str).str.strip().str.upper()
    for column in NUMERIC_COLUMNS:
        working[column] = pd.to_numeric(working[column], errors="coerce")

    missing_values = int(working[["Date", "Symbol", *NUMERIC_COLUMNS]].isna().sum().sum())
    working.replace([np.inf, -np.inf], np.nan, inplace=True)
    working.dropna(subset=["Date", "Symbol", *NUMERIC_COLUMNS], inplace=True)

    duplicate_rows = int(working.duplicated(subset=["Symbol", "Date"]).sum())
    working.drop_duplicates(subset=["Symbol", "Date"], keep="last", inplace=True)

    invalid_mask = (
        (working["Open"] <= 0)
        | (working["High"] <= 0)
        | (working["Low"] <= 0)
        | (working["Close"] <= 0)
        | (working["Volume"] < 0)
        | (working["High"] < working["Low"])
        | (working["Close"] > working["High"] * 1.05)
        | (working["Close"] < working["Low"] * 0.95)
    )
    invalid_ohlcv_rows = int(invalid_mask.sum())
    working = working.loc[~invalid_mask].copy()

    # Conservative outlier handling: remove rows where daily returns are extreme per symbol.
    working.sort_values(["Symbol", "Date"], inplace=True)
    returns = working.groupby("Symbol")["Close"].pct_change()
    outlier_mask = returns.abs() > 0.7
    outlier_count = int(outlier_mask.fillna(False).sum())
    working = working.loc[~outlier_mask.fillna(False)].copy()

    working = working[["Date", "Symbol", "Open", "High", "Low", "Close", "Volume"]]
    working.sort_values(["Symbol", "Date"], inplace=True)
    working.reset_index(drop=True, inplace=True)

    removed_rows = loaded_rows - len(working)
    if loaded_rows and removed_rows / loaded_rows > 0.2:
        logger.warning("Removed %.1f%% of rows from %s", removed_rows / loaded_rows * 100, source)

    report = CleaningReport(
        source=source,
        loaded_rows=loaded_rows,
        removed_rows=removed_rows,
        retained_rows=len(working),
        symbols=int(working["Symbol"].nunique()),
        missing_values=missing_values,
        invalid_ohlcv_rows=invalid_ohlcv_rows + outlier_count,
        duplicate_rows=duplicate_rows,
    )
    logger.info("Cleaned %s: %s", source, report)
    return working, report


def load_and_clean_files(data_dir: str | Path) -> tuple[pd.DataFrame, list[CleaningReport]]:
    csv_files = sorted(Path(data_dir).glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    frames: list[pd.DataFrame] = []
    reports: list[CleaningReport] = []
    for csv_file in csv_files:
        raw = load_csv(csv_file)
        cleaned, report = clean_stock_data(raw, source=csv_file.name)
        frames.append(cleaned)
        reports.append(report)

    combined = pd.concat(frames, ignore_index=True)
    combined.drop_duplicates(subset=["Symbol", "Date"], keep="last", inplace=True)
    combined.sort_values(["Symbol", "Date"], inplace=True)
    combined.reset_index(drop=True, inplace=True)
    return combined, reports


def save_cleaned_by_symbol(df: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for symbol, group in df.groupby("Symbol"):
        path = output / f"{symbol}.parquet"
        group.to_parquet(path, index=False)
        paths.append(path)
    combined_path = output / "all_stocks.parquet"
    df.to_parquet(combined_path, index=False)
    paths.append(combined_path)
    return paths
