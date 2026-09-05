import pandas as pd
import pytest

from ml.features.technical_indicators import FEATURE_COLUMNS, create_features
from ml.preprocessing.clean_data import DataValidationError, clean_stock_data, load_csv


def test_load_csv_adds_symbol_from_filename(tmp_path):
    path = tmp_path / "TEST.csv"
    path.write_text("Date,Open,High,Low,Close,Volume\n2024-01-01,10,11,9,10.5,1000\n", encoding="utf-8")
    df = load_csv(path)
    assert df.loc[0, "Symbol"] == "TEST"


def test_missing_required_columns_raises(tmp_path):
    path = tmp_path / "BAD.csv"
    path.write_text("Date,Open,Close\n2024-01-01,10,10.5\n", encoding="utf-8")
    with pytest.raises(DataValidationError):
        load_csv(path)


def test_clean_stock_data_removes_invalid_rows():
    df = pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02"],
            "Symbol": ["TEST", "TEST"],
            "Open": [10, 10],
            "High": [11, 8],
            "Low": [9, 9],
            "Close": [10.5, 10],
            "Volume": [1000, 1000],
        }
    )
    cleaned, report = clean_stock_data(df)
    assert len(cleaned) == 1
    assert report.invalid_ohlcv_rows == 1


def test_feature_and_target_generation():
    rows = []
    for i in range(240):
        close = 100 + i * 0.1
        rows.append(
            {
                "Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                "Symbol": "TEST",
                "Open": close - 0.5,
                "High": close + 1,
                "Low": close - 1,
                "Close": close,
                "Volume": 1000 + i,
            }
        )
    features = create_features(pd.DataFrame(rows))
    assert not features.empty
    assert set(FEATURE_COLUMNS).issubset(features.columns)
    assert "Target" in features.columns
