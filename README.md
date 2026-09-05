# AI MarketGuard

AI MarketGuard is a local, educational stock-market intelligence system. It combines historical price data, technical indicators, machine-learning direction prediction, explainability, historical news sentiment, company fundamentals, and backtesting behind a FastAPI backend and React dashboard.

The project does not use API keys, paid market APIs, broker integrations, live trading, Kafka, PySpark, or LLM-based price prediction.

## Problem Statement

Most market dashboards mix historical charts with opaque signals. AI MarketGuard makes the full analytical chain inspectable:

- Where the stock data comes from
- Which technical features are used
- What the model predicts
- How confident the model is
- Which technical, sentiment, and fundamental factors support or contradict the signal
- How the model behaved in historical backtests
- Whether alternative ML models perform better

Predictions and backtests are analytical outputs only. They are not financial advice and do not guarantee future performance.

## Features

- Local historical stock-data ingestion from CSV/Parquet
- Data cleaning and duplicate prevention
- Technical indicators: RSI, MACD, SMA, EMA, Bollinger Bands, ATR, volume ratio, volatility, returns
- XGBoost production prediction model
- Offline model comparison: baseline, Logistic Regression, Random Forest, current XGBoost, tuned XGBoost
- Chronological train/validation/test splitting
- Time-series validation and walk-forward evaluation
- Probability threshold analysis and calibration summary
- Model feature importance
- Model-based signal engine with confidence bands, technical score, combined score, and risk score
- Optional local historical news sentiment using FinBERT
- Optional local company fundamental analysis
- Leakage-aware historical backtesting
- FastAPI REST API with Swagger docs
- Responsive React/Vite dashboard with Recharts
- PostgreSQL schema and optional database sync
- Backend/ML test suite

## Architecture

```text
Historical Stock Data
  |
  v
Preprocessing + Cleaning
  |
  v
Technical Features
  |
  v
ML Models + Model Comparison
  |
  v
Production Prediction
  |
  v
Signal Engine
  |------ Technical Indicators
  |------ Historical News Sentiment
  |------ Company Fundamentals
  v
Risk + Explainability
  |
  v
Backtesting
  |
  v
FastAPI REST Backend
  |
  v
React Dashboard
```

## Technology Stack

- Backend: Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy
- Data: Pandas, NumPy, PyArrow, Parquet
- Indicators: ta
- Machine learning: Scikit-learn, XGBoost, Joblib
- Sentiment: optional Hugging Face FinBERT through `transformers` and `torch`
- Database: PostgreSQL
- Frontend: React, Vite, JavaScript, CSS
- Charts: Recharts
- Tests: Pytest, FastAPI TestClient

## Folder Structure

```text
backend/app/            FastAPI app, routes, schemas, services, config
backend/tests/          Backend, ML, API, leakage, and edge-case tests
data/stocks/            Local stock CSV inputs and sample stock data
data/news/              Optional local historical news CSV files
data/fundamentals/      Optional local company fundamental CSV files
database/schema.sql     PostgreSQL schema
frontend/               React dashboard
ml/features/            Technical indicator feature engineering
ml/preprocessing/       Stock and fundamental cleaning
ml/training/            XGBoost training and Phase 10 model comparison
ml/prediction/          Saved-model loading and prediction
ml/backtesting/         Leakage-aware backtesting engine
models/                 Model metadata, feature importance, comparison reports
scripts/                Local pipeline, training, testing, and startup helpers
sentiment/              News cleaning and FinBERT sentiment processing
```

## Windows Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

Optional sentiment dependencies:

```powershell
python -m pip install -r requirements-sentiment.txt
```

## Environment Variables

Copy `.env.example` to `.env` only if you need local overrides.

Important variables:

```text
DATABASE_URL
CORS_ORIGINS
DATA_PATH
NEWS_PATH
FUNDAMENTALS_PATH
MODEL_METADATA_PATH
MODEL_COMPARISON_PATH
PRODUCTION_MODEL_KEY
BULLISH_THRESHOLD
BEARISH_THRESHOLD
ML_WEIGHT
TECHNICAL_WEIGHT
SENTIMENT_WEIGHT
FUNDAMENTAL_WEIGHT
FINBERT_MODEL_NAME
```

No external API key is required.

## Full Workflow

1. Add local historical stock files to `data/stocks/`.
2. Load raw data:

```powershell
python scripts/load_data.py
```

3. Clean data:

```powershell
python scripts/clean_data.py
```

4. Generate technical features:

```powershell
python scripts/calculate_features.py
```

5. Train the production XGBoost model:

```powershell
python scripts/train_model.py
```

6. Compare candidate models offline:

```powershell
python scripts/compare_models.py
```

7. Process optional local news sentiment:

```powershell
python scripts/process_news_sentiment.py
```

8. Process optional company fundamentals:

```powershell
python scripts/process_fundamentals.py
```

9. Run a backtest:

```powershell
python scripts/run_backtest.py RELIANCE
```

10. Start the backend:

```powershell
.\scripts\start_backend.ps1
```

11. Start the frontend in another terminal:

```powershell
.\scripts\start_frontend.ps1
```

12. Open the dashboard:

```text
http://127.0.0.1:5173/
```

## Backend

Direct backend command:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Frontend

Direct frontend command:

```powershell
cd frontend
npm run dev
```

Production build:

```powershell
cd frontend
npm run build
```

Frontend environment example:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## PostgreSQL

The database is optional for local dashboard use when Parquet/model files already exist. The schema is safe to rerun because it uses `CREATE TABLE IF NOT EXISTS`.

Start PostgreSQL with Docker Compose:

```powershell
docker compose up -d postgres
```

Sync local processed market data into PostgreSQL:

```powershell
python scripts/sync_database.py
```

Tables:

- `stocks`
- `market_data`
- `predictions`
- `backtests`
- `model_versions`

`market_data` has a `UNIQUE(stock_id, date)` constraint to prevent duplicate historical rows.

## ML Reproducibility

Current production model: `xgboost_current`

Current saved model version: `v1`

Training command:

```powershell
python scripts/train_model.py
```

Model comparison command:

```powershell
python scripts/compare_models.py
```

Current comparison uses:

- Chronological per-symbol split: 70% train, 15% validation, 15% final test
- TimeSeriesSplit expanding-window validation on train+validation data
- Fixed random seed: 42
- Target: `1` if next trading day's close is higher than today's close, otherwise `0`
- Feature count: 25
- Dataset range in the current artifacts: 2015-10-21 to 2023-12-28

Results can vary slightly across Python, NumPy, Scikit-learn, and XGBoost versions.

## Backtesting

Backtest execution rule:

```text
Prediction at day T -> trade execution at next trading day's Open
```

The engine applies initial capital, transaction cost, slippage, whole-share position sizing, a same-range Buy & Hold benchmark, and final liquidation at the final close.

Default example:

```powershell
python scripts/run_backtest.py RELIANCE
```

## News Sentiment

Place local historical news files under `data/news/`.

Minimum columns: `date`, `headline`

Optional columns: `symbol`, `article`

Process news:

```powershell
python scripts/process_news_sentiment.py
```

The FinBERT model is downloaded and cached locally when available. If the model cannot be downloaded, the rest of the app still works and sentiment endpoints return clear unavailable/no-data states.

Leakage rule:

```text
News dated T can influence signals on T or later only.
```

## Fundamental Data

Place local fundamental files under `data/fundamentals/`.

Supported fields include:

```text
symbol,date,revenue,net_profit,eps,pe_ratio,pb_ratio,roe,roce,debt,debt_to_equity,market_cap,operating_margin,net_margin,free_cash_flow,dividend_yield
```

Process fundamentals:

```powershell
python scripts/process_fundamentals.py
```

Missing metrics are not treated as zero. Fundamental category weights are re-normalized over available categories, and `data_completeness` is reported.

Leakage rule:

```text
Fundamental records dated T can influence signals on T or later only.
```

## API Summary

- `GET /api/health`
- `GET /api/stocks`
- `GET /api/stocks/{symbol}`
- `GET /api/stocks/{symbol}/history`
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
- `GET /api/model/comparison`
- `GET /api/model/feature-importance`
- `GET /api/data/status`

## Testing

Backend and ML tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Frontend build test:

```powershell
cd frontend
npm run build
```

## Demo Flow

Recommended stock for demo: `RELIANCE`

1. Open `http://127.0.0.1:5173/`.
2. Select `RELIANCE`.
3. Review latest close, date range, and price chart.
4. Review prediction, confidence, signal, and explanation.
5. Review news sentiment and company fundamentals if local data is available.
6. Run a backtest.
7. Compare strategy return with Buy & Hold.
8. Review equity curve and trade table.
9. Scroll to Model Performance and review the model comparison table.

`RELIANCE` is only a demo suggestion and is not hardcoded in the dashboard.

## Screenshots

Screenshots can be added here before final presentation.

Suggested screenshots:

- Dashboard overview
- Prediction and signal explanation
- News sentiment and fundamentals
- Backtest results
- Model comparison table
- Swagger docs

## Security And Safety Review

- `.env` is ignored by Git.
- `.venv/`, `node_modules/`, `frontend/dist/`, pytest temp files, and binary model artifacts are ignored.
- No API keys are required.
- No paid APIs are used.
- No broker API or live trade execution exists.
- User-facing API errors avoid exposing Python stack traces.
- Stock symbols, dates, limits, and backtest inputs are validated.
- The app reads local configured paths and does not expose arbitrary file-path access.

## Deployment Preparation

This project is prepared for future deployment, but no cloud deployment is required yet.

Typical future deployment pieces:

- Backend: any Python ASGI host capable of running FastAPI/Uvicorn
- Frontend: static hosting for the Vite production build
- Database: managed or self-hosted PostgreSQL
- Environment variables: `DATABASE_URL`, `CORS_ORIGINS`, model/data paths
- Production build: `npm run build`

Keep CORS restricted to the deployed frontend origin in production.

## Docker

Docker Compose is optional. It currently supports PostgreSQL plus local backend/frontend services.

```powershell
docker compose up --build
```

Services:

- PostgreSQL: `localhost:5432`
- FastAPI: `http://localhost:8000`
- React: `http://localhost:5173`

## Known Limitations

- Uses local historical datasets only.
- Optional news and fundamental analysis depend on local file coverage.
- FinBERT may require an initial model download.
- Current model metrics are only modestly better than random on classification metrics.
- Historical backtests are not proof of future performance.
- Model comparison artifacts are generated offline and are not automatically refreshed by the API.
- Optional sentiment/fundamental-aware backtest modes remain disabled when historical coverage is insufficient.
- Vite may warn that the production JavaScript chunk is larger than 500 kB.

## Disclaimer

AI MarketGuard is an analytical and educational system. Predictions, signals, model outputs, and historical backtests are not financial advice and do not guarantee future market performance.
