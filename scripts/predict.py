import argparse

import pandas as pd

import _bootstrap  # noqa: F401
from backend.app.core.config import get_settings
from ml.prediction.predict import predict_latest


def main():
    parser = argparse.ArgumentParser(description="Predict the next trading-day direction for a stock.")
    parser.add_argument("--symbol", required=True, help="Stock symbol, for example RELIANCE")
    args = parser.parse_args()

    settings = get_settings()
    source = settings.processed_path / "all_stocks_features.parquet"
    if not source.exists():
        raise FileNotFoundError("Processed features not found. Run python scripts/calculate_features.py first.")

    processed = pd.read_parquet(source)
    result = predict_latest(processed, args.symbol, model_dir="models")

    print("AI MARKETGUARD")
    print("")
    print(f"Stock: {result['symbol']}")
    print("")
    print(f"Prediction: {result['prediction']}")
    print("")
    print(f"Probability UP: {result['probability_up'] * 100:.2f}%")
    print(f"Probability DOWN: {result['probability_down'] * 100:.2f}%")
    print("")
    print(f"Model confidence: {result['confidence']:.2f}%")


if __name__ == "__main__":
    main()
