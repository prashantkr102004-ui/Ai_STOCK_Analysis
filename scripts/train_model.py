import json
import argparse

import pandas as pd

import _bootstrap  # noqa: F401
from backend.app.core.config import get_settings
from ml.training.train import train_xgboost_model


def main():
    parser = argparse.ArgumentParser(description="Train the AI MarketGuard XGBoost model.")
    parser.add_argument("--symbol", help="Optional symbol for single-stock model training.")
    args = parser.parse_args()

    settings = get_settings()
    source = settings.processed_path / "all_stocks_features.parquet"
    if not source.exists():
        raise FileNotFoundError("Processed features not found. Run python scripts/calculate_features.py first.")
    processed = pd.read_parquet(source)
    metadata = train_xgboost_model(processed, model_dir="models", symbol=args.symbol)
    metrics = metadata["metrics"]
    print("AI MARKETGUARD")
    print("XGBoost training complete")
    print(json.dumps({
        "version": metadata["version"],
        "stocks": metadata["number_of_stocks"],
        "training_samples": metadata["training_samples"],
        "validation_samples": metadata["validation_samples"],
        "test_samples": metadata["test_samples"],
        "feature_count": metadata["feature_count"],
        "training_date_range": metadata["training_date_range"],
        "validation_date_range": metadata["validation_date_range"],
        "test_date_range": metadata["test_date_range"],
        "class_balance": metadata["class_balance"],
        "metrics": metrics,
        "top_features": metadata["top_features"],
        "model_path": metadata["model_path"],
    }, indent=2))


if __name__ == "__main__":
    main()
