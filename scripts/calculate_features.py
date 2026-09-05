import json
import logging
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

import _bootstrap  # noqa: F401
from backend.app.core.config import get_settings
from ml.features.technical_indicators import FEATURE_COLUMNS, create_features


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main():
    settings = get_settings()
    source = settings.cleaned_path / "all_stocks.parquet"
    if not source.exists():
        raise FileNotFoundError("Cleaned data not found. Run python scripts/load_data.py first.")
    cleaned = pd.read_parquet(source)
    processed = create_features(cleaned)
    settings.processed_path.mkdir(parents=True, exist_ok=True)
    output = settings.processed_path / "all_stocks_features.parquet"
    processed.to_parquet(output, index=False)
    for symbol, group in processed.groupby("Symbol"):
        group.to_parquet(settings.processed_path / f"{symbol}_features.parquet", index=False)
    summary = {
        "output": str(output),
        "records": int(len(processed)),
        "stocks": int(processed["Symbol"].nunique()),
        "features": FEATURE_COLUMNS,
        "earliest_date": str(processed["Date"].min().date()),
        "latest_date": str(processed["Date"].max().date()),
        "last_processing_time": datetime.now(timezone.utc).isoformat(),
    }
    (Path(settings.processed_path) / "data_status.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
