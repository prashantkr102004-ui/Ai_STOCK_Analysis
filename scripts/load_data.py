import json
import logging

import _bootstrap  # noqa: F401
from backend.app.core.config import get_settings
from ml.preprocessing.clean_data import load_and_clean_files, save_cleaned_by_symbol


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main():
    settings = get_settings()
    df, reports = load_and_clean_files(settings.data_path)
    paths = save_cleaned_by_symbol(df, settings.cleaned_path)
    summary = {
        "stocks": int(df["Symbol"].nunique()),
        "records": int(len(df)),
        "earliest_date": str(df["Date"].min().date()),
        "latest_date": str(df["Date"].max().date()),
        "outputs": [str(path) for path in paths],
        "reports": [report.__dict__ for report in reports],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
