# AI MarketGuard

AI-powered stock market intelligence and historical prediction platform.

AI MarketGuard V1 is designed to run from local historical CSV or Parquet files. It does not require API keys, broker accounts, paid data services, or live market APIs. It does not perform live trading or place real orders.

## Current Status

The project includes local CSV ingestion, cleaning, technical indicators, target generation, XGBoost training, prediction, signal generation, explainability scoring, optional local historical-news sentiment, backtesting, FastAPI endpoints, PostgreSQL schema, Docker Compose, and a Vite React dashboard. V1 still uses local historical files only.

## Architecture

```text
Historical CSV
-> Data Cleaning
-> Technical Indicators
-> Feature Engineering
-> XGBoost
-> Prediction
-> Signal
-> Optional Local News Sentiment
-> Optional Local Fundamentals
-> Backtesting
-> FastAPI
-> React Dashboard
```

## Technology Stack

- Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy
- Data: Pandas, NumPy, PyArrow, Parquet
- Technical indicators: ta
- Machine learning: Scikit-learn, XGBoost, Joblib
- Database: PostgreSQL
- Frontend: React, Vite, JavaScript, CSS
- Charts: Recharts
- Testing: Pytest, FastAPI TestClient

## Local News Sentiment

Historical news CSV files can be placed in `data/news/`. Required columns are `date` and `headline`; optional columns are `symbol` and `article`. Rows without `symbol` are treated as general-market news and are not mapped to stocks automatically.

The sentiment pipeline uses FinBERT without API keys when optional dependencies are installed and the model can be downloaded or cached locally:

```powershell
pip install -r requirements-sentiment.txt
python scripts/process_news_sentiment.py
```

Processed sentiment is cached in `sentiment/data/processed/` as a combined parquet file and per-symbol files such as `RELIANCE_sentiment.parquet`.

Historical alignment rule: news dated `T` may influence signals on date `T` or later only. Future-dated news is never used for earlier stock predictions or backtests.

## Local Fundamentals

Company fundamentals can be placed in `data/fundamentals/` as CSV or Parquet files. Required columns are `symbol` and `date`; optional fields include revenue, net profit, EPS, P/E, P/B, ROE, ROCE, debt-to-equity, margins, free cash flow, market cap, and dividend yield. Alternate names such as `ticker`, `report_date`, `sales`, `pat`, `p/e`, `p/b`, and `d/e` are normalized.

Process local fundamentals with:

```powershell
python scripts/process_fundamentals.py
```

Processed data is cached at `ml/data/fundamentals/fundamentals_processed.parquet`.

Historical alignment rule: a fundamental record dated `T` may influence signals on date `T` or later only. Future-dated financial data is never used for earlier predictions or backtests.

## Dataset Format

Stock CSV files should contain:

```csv
Date,Open,High,Low,Close,Volume,Symbol
2024-01-01,100,105,98,103,500000,TEST
2024-01-02,103,108,101,107,620000,TEST
```

Required columns are `Date`, `Open`, `High`, `Low`, `Close`, and `Volume`. If `Symbol` is missing, the loader will later infer the symbol from the filename.

The included `data/stocks/sample_stock.csv` is demo data for development and testing only. It is not real market data and should not be presented as real performance history.

## Setup

Create a Python virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Pipeline Commands

```powershell
python scripts/load_data.py
python scripts/clean_data.py
python scripts/calculate_features.py
python scripts/train_model.py
python scripts/predict.py --symbol RELIANCE
python scripts/run_backtest.py RELIANCE
python scripts/sync_database.py
uvicorn backend.app.main:app --reload
```

The training command accepts an optional symbol:

```powershell
python scripts/train_model.py --symbol RELIANCE
```

Start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Run tests:

```powershell
pytest
```

## PostgreSQL

The SQL schema is in `database/schema.sql`. The application includes SQLAlchemy models for `stocks`, `market_data`, `predictions`, `backtests`, and `model_versions`. Local development can run the API from generated Parquet/model files even before PostgreSQL is started.

After PostgreSQL is running and `DATABASE_URL` is configured:

```powershell
python scripts/sync_database.py
```

## Docker

```powershell
docker compose up --build
```

Services:

- PostgreSQL: `localhost:5432`
- FastAPI: `http://localhost:8000`
- React: `http://localhost:5173`

## API

- `GET /api/health`
- `GET /api/stocks`
- `GET /api/stocks/{symbol}`
- `GET /api/stocks/{symbol}/history?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&limit=500`
- `GET /api/stocks/{symbol}/indicators`
- `GET /api/stocks/{symbol}/prediction`
- `GET /api/stocks/{symbol}/signal`
- `GET /api/stocks/{symbol}/explanation`
- `GET /api/stocks/{symbol}/news`
- `GET /api/stocks/{symbol}/sentiment`
- `GET /api/stocks/{symbol}/sentiment/history`
- `GET /api/stocks/{symbol}/fundamentals`
- `GET /api/stocks/{symbol}/fundamentals/history`
- `POST /api/stocks/{symbol}/backtest`
- `GET /api/stocks/{symbol}/backtest`
- `GET /api/stocks/{symbol}/backtest/equity`
- `GET /api/stocks/{symbol}/backtest/trades`
- `GET /api/model/status`
- `GET /api/model/feature-importance`
- `GET /api/data/status`

Swagger docs are available at:

```powershell
uvicorn backend.app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs` or `http://127.0.0.1:8000/redoc`.

## Limitations

- V1 uses local historical files only.
- Predictions are model analysis, not financial advice.
- Model confidence is not a guarantee of profit or future performance.
- Live trading, broker integrations, and live market APIs are intentionally excluded.

## Future Improvements

- Fundamental analysis
- PySpark and Delta Lake for large-scale processing
- Kafka streaming
- Model monitoring
- Data drift and concept drift detection
- Automatic retraining
- Self-healing ML workflows
