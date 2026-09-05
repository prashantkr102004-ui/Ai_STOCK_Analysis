from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from ml.features.technical_indicators import FEATURE_COLUMNS
from ml.training.evaluate import evaluate_classifier


BASE_FEATURE_CANDIDATES = ["Open", "High", "Low", "Close", "Volume"]
FEATURE_CANDIDATES = BASE_FEATURE_CANDIDATES + FEATURE_COLUMNS
LEAKAGE_PATTERNS = ("future", "next", "target", "label")
MIN_ROWS = 100


def validate_processed_data(df: pd.DataFrame) -> dict:
    required = {"Date", "Symbol", "Close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Processed dataset is missing required columns: {sorted(missing)}")

    data = df.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    if data["Date"].isna().any():
        raise ValueError("Processed dataset contains invalid dates.")
    if len(data) < MIN_ROWS:
        raise ValueError(f"Insufficient processed data. Need at least {MIN_ROWS} rows.")

    missing_values = int(data.isna().sum().sum())
    feature_count = len(select_feature_columns(data))
    if feature_count == 0:
        raise ValueError("No usable model features found in processed dataset.")

    return {
        "rows": int(len(data)),
        "stocks": int(data["Symbol"].nunique()),
        "earliest_date": str(data["Date"].min().date()),
        "latest_date": str(data["Date"].max().date()),
        "feature_count": int(feature_count),
        "missing_values": missing_values,
    }


def ensure_target(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data.sort_values(["Symbol", "Date"], inplace=True)
    future_close = data.groupby("Symbol")["Close"].shift(-1)
    data["Target"] = (future_close > data["Close"]).astype("float")
    data.loc[future_close.isna(), "Target"] = np.nan
    return data.dropna(subset=["Target"]).reset_index(drop=True)


def select_feature_columns(df: pd.DataFrame) -> list[str]:
    existing = [column for column in FEATURE_CANDIDATES if column in df.columns]
    verify_no_leakage(existing)
    return existing


def verify_no_leakage(features: list[str]) -> None:
    leaky = [
        feature
        for feature in features
        if any(pattern in feature.lower() for pattern in LEAKAGE_PATTERNS)
    ]
    if leaky:
        raise ValueError(f"Potential leakage columns cannot be used as features: {leaky}")


def chronological_split(df: pd.DataFrame, train_size: float = 0.70, validation_size: float = 0.15):
    frames = {"train": [], "validation": [], "test": []}
    for _, group in df.groupby("Symbol"):
        ordered = group.sort_values("Date").reset_index(drop=True)
        if len(ordered) < MIN_ROWS:
            continue
        train_end = int(len(ordered) * train_size)
        validation_end = int(len(ordered) * (train_size + validation_size))
        frames["train"].append(ordered.iloc[:train_end])
        frames["validation"].append(ordered.iloc[train_end:validation_end])
        frames["test"].append(ordered.iloc[validation_end:])

    if not frames["train"] or not frames["validation"] or not frames["test"]:
        raise ValueError("Insufficient per-stock rows for chronological train/validation/test split.")

    train_df = pd.concat(frames["train"], ignore_index=True).sort_values(["Date", "Symbol"]).reset_index(drop=True)
    validation_df = pd.concat(frames["validation"], ignore_index=True).sort_values(["Date", "Symbol"]).reset_index(drop=True)
    test_df = pd.concat(frames["test"], ignore_index=True).sort_values(["Date", "Symbol"]).reset_index(drop=True)
    return train_df, validation_df, test_df


def split_date_range(split_df: pd.DataFrame) -> dict:
    return {
        "start": str(pd.to_datetime(split_df["Date"]).min().date()),
        "end": str(pd.to_datetime(split_df["Date"]).max().date()),
    }


def next_model_version(model_dir: Path) -> str:
    existing = sorted(model_dir.glob("model_metadata_v*.json"))
    if not existing:
        return "v1"
    versions = []
    for path in existing:
        match = re.search(r"_v(\d+)\.json$", path.name)
        if match:
            versions.append(int(match.group(1)))
    return f"v{max(versions, default=0) + 1}"


def class_balance_settings(y_train: pd.Series) -> tuple[dict, dict]:
    counts = y_train.value_counts().to_dict()
    negative = int(counts.get(0, 0))
    positive = int(counts.get(1, 0))
    settings = {"target_0": negative, "target_1": positive, "scale_pos_weight": 1.0, "weighted": False}
    if negative and positive:
        ratio = negative / positive
        settings["scale_pos_weight"] = float(ratio)
        if ratio > 1.5 or ratio < 0.67:
            settings["weighted"] = True
            return {"scale_pos_weight": ratio}, settings
    return {}, settings


def train_xgboost_model(
    processed: pd.DataFrame,
    model_dir: str | Path = "models",
    symbol: str | None = None,
) -> dict:
    data = processed.copy()
    if symbol:
        data = data[data["Symbol"] == symbol.upper()]
    validation_summary = validate_processed_data(data)
    data = ensure_target(data)
    features = select_feature_columns(data)
    data.dropna(subset=features + ["Target"], inplace=True)
    if len(data) < MIN_ROWS:
        raise ValueError("Insufficient historical data after target and feature validation.")

    train_df, validation_df, test_df = chronological_split(data)
    x_train, y_train = train_df[features].astype(float), train_df["Target"].astype(int)
    x_validation, y_validation = validation_df[features].astype(float), validation_df["Target"].astype(int)
    x_test, y_test = test_df[features].astype(float), test_df["Target"].astype(int)
    class_params, class_balance = class_balance_settings(y_train)

    model = XGBClassifier(
        n_estimators=160,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        **class_params,
    )
    model.fit(x_train, y_train, eval_set=[(x_validation, y_validation)], verbose=False)

    metrics = evaluate_classifier(model, x_test, y_test)
    output_dir = Path(model_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    version = next_model_version(output_dir)
    scope = symbol.upper() if symbol else "global"
    model_path = output_dir / f"xgboost_model_{version}.joblib"
    latest_model_path = output_dir / "xgboost_model_latest.joblib"
    payload = {"model": model, "features": features, "version": version, "scope": scope}
    joblib.dump(payload, model_path)
    joblib.dump(payload, latest_model_path)

    importance = sorted(
        zip(features, model.feature_importances_.tolist()),
        key=lambda item: item[1],
        reverse=True,
    )
    feature_importance = [{"feature": name, "importance": float(value)} for name, value in importance]
    feature_importance_path = output_dir / "feature_importance.json"
    feature_importance_path.write_text(json.dumps(feature_importance, indent=2), encoding="utf-8")

    metadata = {
        "version": version,
        "model_name": "XGBoost",
        "model_path": str(model_path),
        "latest_model_path": str(latest_model_path),
        "training_date": datetime.now(timezone.utc).isoformat(),
        "dataset_size": int(len(data)),
        "number_of_stocks": int(data["Symbol"].nunique()),
        "symbol": symbol.upper() if symbol else "GLOBAL",
        "feature_list": features,
        "feature_count": len(features),
        "training_samples": int(len(train_df)),
        "validation_samples": int(len(validation_df)),
        "test_samples": int(len(test_df)),
        "training_date_range": split_date_range(train_df),
        "validation_date_range": split_date_range(validation_df),
        "test_date_range": split_date_range(test_df),
        "processed_data_summary": validation_summary,
        "class_balance": class_balance,
        "leakage_check": "Feature columns are selected from current and historical OHLCV/technical fields only; future/next/target/label columns are rejected.",
        "feature_importance_path": str(feature_importance_path),
        "top_features": feature_importance[:10],
        "metrics": metrics,
    }
    versioned_metadata_path = output_dir / f"model_metadata_{version}.json"
    latest_metadata_path = output_dir / "model_metadata_latest.json"
    legacy_metadata_path = output_dir / "metadata.json"
    for path in (versioned_metadata_path, latest_metadata_path, legacy_metadata_path):
        path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
