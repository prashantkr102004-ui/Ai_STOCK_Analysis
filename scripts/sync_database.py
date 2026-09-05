import json

import pandas as pd
from sqlalchemy import text

import _bootstrap  # noqa: F401
from backend.app.core.database import engine
from backend.app.core.config import get_settings


def main():
    settings = get_settings()
    source = settings.cleaned_path / "all_stocks.parquet"
    if not source.exists():
        raise FileNotFoundError("Cleaned data not found. Run python scripts/load_data.py first.")

    df = pd.read_parquet(source)
    with engine.begin() as connection:
        for symbol in sorted(df["Symbol"].unique()):
            connection.execute(
                text(
                    """
                    INSERT INTO stocks (symbol, name)
                    VALUES (:symbol, :symbol)
                    ON CONFLICT (symbol) DO NOTHING
                    """
                ),
                {"symbol": symbol},
            )

        stock_ids = {
            row.symbol: row.id
            for row in connection.execute(text("SELECT id, symbol FROM stocks")).fetchall()
        }

        rows = []
        for record in df.itertuples(index=False):
            rows.append(
                {
                    "stock_id": stock_ids[record.Symbol],
                    "date": record.Date.date(),
                    "open": float(record.Open),
                    "high": float(record.High),
                    "low": float(record.Low),
                    "close": float(record.Close),
                    "volume": float(record.Volume),
                }
            )

        connection.execute(
            text(
                """
                INSERT INTO market_data (stock_id, date, open, high, low, close, volume)
                VALUES (:stock_id, :date, :open, :high, :low, :close, :volume)
                ON CONFLICT (stock_id, date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
                """
            ),
            rows,
        )

    print(json.dumps({"stocks": len(stock_ids), "market_data_rows": len(df)}, indent=2))


if __name__ == "__main__":
    main()
