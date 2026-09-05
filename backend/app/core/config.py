from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "AI MarketGuard"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://marketguard:marketguard@localhost:5432/marketguard",
    )
    model_path: Path = Path(os.getenv("MODEL_PATH", "models/xgboost_global.joblib"))
    metadata_path: Path = Path(os.getenv("MODEL_METADATA_PATH", "models/metadata.json"))
    data_path: Path = Path(os.getenv("DATA_PATH", "data/stocks"))
    cleaned_path: Path = Path("ml/data/cleaned")
    processed_path: Path = Path("ml/data/processed")
    backtest_path: Path = Path("ml/data/backtests")
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
    )
    bullish_threshold: float = float(os.getenv("BULLISH_THRESHOLD", "60"))
    bearish_threshold: float = float(os.getenv("BEARISH_THRESHOLD", "40"))
    ml_weight: float = float(os.getenv("ML_WEIGHT", "0.7"))
    technical_weight: float = float(os.getenv("TECHNICAL_WEIGHT", "0.3"))
    sentiment_weight: float = float(os.getenv("SENTIMENT_WEIGHT", "0.15"))
    fundamental_weight: float = float(os.getenv("FUNDAMENTAL_WEIGHT", "0.15"))
    low_risk_threshold: float = float(os.getenv("LOW_RISK_THRESHOLD", "35"))
    high_risk_threshold: float = float(os.getenv("HIGH_RISK_THRESHOLD", "65"))
    news_path: Path = Path(os.getenv("NEWS_PATH", "data/news"))
    processed_sentiment_path: Path = Path(os.getenv("PROCESSED_SENTIMENT_PATH", "sentiment/data/processed"))
    finbert_model_name: str = os.getenv("FINBERT_MODEL_NAME", "ProsusAI/finbert")
    sentiment_alignment: str = os.getenv("SENTIMENT_ALIGNMENT", "news_on_or_before_signal_date")
    fundamentals_path: Path = Path(os.getenv("FUNDAMENTALS_PATH", "data/fundamentals"))
    processed_fundamentals_path: Path = Path(os.getenv("PROCESSED_FUNDAMENTALS_PATH", "ml/data/fundamentals"))
    fundamental_category_weights: dict[str, float] = {
        "growth": 0.25,
        "profitability": 0.25,
        "valuation": 0.15,
        "balance_sheet": 0.20,
        "cash_flow": 0.15,
    }
    fundamental_bias_thresholds: dict[str, float] = {
        "strong": 80,
        "good": 65,
        "neutral": 45,
    }
    max_reasonable_pe: float = float(os.getenv("MAX_REASONABLE_PE", "120"))
    max_reasonable_pb: float = float(os.getenv("MAX_REASONABLE_PB", "40"))
    max_reasonable_debt_to_equity: float = float(os.getenv("MAX_REASONABLE_DEBT_TO_EQUITY", "10"))
    confidence_bands: tuple[tuple[float, str], ...] = (
        (55, "Very Low Confidence"),
        (60, "Low Confidence"),
        (70, "Moderate Confidence"),
        (80, "High Confidence"),
        (101, "Very High Confidence"),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
