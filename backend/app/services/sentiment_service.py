from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.app.core.config import get_settings
from backend.app.services.stock_service import normalize_symbol, validate_date_range
from sentiment.finbert import SentimentModelUnavailable, analyze_texts, attach_sentiment
from sentiment.preprocessing.clean_news import load_news_folder


class SentimentNotFoundError(FileNotFoundError):
    pass


def processed_sentiment_file() -> Path:
    return get_settings().processed_sentiment_path / "all_news_sentiment.parquet"


def process_news_sentiment(use_model: bool = True) -> dict:
    settings = get_settings()
    settings.processed_sentiment_path.mkdir(parents=True, exist_ok=True)
    news = load_news_folder(settings.news_path)
    if news.empty:
        raise SentimentNotFoundError("No local historical news CSV files found.")
    if not use_model:
        raise SentimentModelUnavailable("Sentiment model unavailable. FinBERT inference was not requested.")

    outputs = analyze_texts(news["text"].tolist())
    scored = attach_sentiment(news, outputs)
    scored.to_parquet(processed_sentiment_file(), index=False)
    for symbol, stock_news in scored.dropna(subset=["symbol"]).groupby("symbol"):
        stock_news.to_parquet(settings.processed_sentiment_path / f"{symbol}_sentiment.parquet", index=False)
    aggregate_daily_sentiment(scored).to_parquet(settings.processed_sentiment_path / "daily_sentiment.parquet", index=False)
    return {"loaded_records": int(len(news)), "processed_records": int(len(scored)), "output_path": str(processed_sentiment_file())}


def load_processed_sentiment() -> pd.DataFrame:
    path = processed_sentiment_file()
    if path.exists():
        return pd.read_parquet(path)
    raise SentimentNotFoundError("No processed sentiment cache found. Run sentiment processing after adding local news data.")


def get_news(symbol: str, start_date: str | None = None, end_date: str | None = None, limit: int = 25) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")
    start, end = validate_date_range(start_date, end_date)
    symbol = normalize_symbol(symbol)
    df = load_processed_sentiment()
    filtered = df[(df["symbol"] == symbol)].copy()
    filtered = _filter_dates(filtered, start, end).sort_values("date", ascending=False).head(limit)
    if filtered.empty:
        raise SentimentNotFoundError(f"No historical news sentiment available for {symbol}.")
    columns = [
        "date",
        "symbol",
        "headline",
        "article",
        "sentiment",
        "confidence",
        "sentiment_score",
        "positive_probability",
        "neutral_probability",
        "negative_probability",
    ]
    return _records(filtered[[column for column in columns if column in filtered.columns]])


def get_sentiment_history(symbol: str, start_date: str | None = None, end_date: str | None = None, limit: int = 250) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")
    start, end = validate_date_range(start_date, end_date)
    symbol = normalize_symbol(symbol)
    daily = aggregate_daily_sentiment(load_processed_sentiment())
    filtered = daily[daily["symbol"] == symbol].copy()
    filtered = _filter_dates(filtered, start, end).sort_values("date").tail(limit)
    if filtered.empty:
        raise SentimentNotFoundError(f"No sentiment history available for {symbol}.")
    return _records(filtered)


def latest_sentiment(symbol: str, as_of_date: str | None = None) -> dict:
    symbol = normalize_symbol(symbol)
    history = pd.DataFrame(get_sentiment_history(symbol, limit=5000))
    if as_of_date:
        as_of = pd.to_datetime(as_of_date, errors="coerce")
        if pd.isna(as_of):
            raise ValueError("Invalid as_of_date. Use YYYY-MM-DD.")
        history = history[pd.to_datetime(history["date"]) <= as_of]
    if history.empty:
        raise SentimentNotFoundError(f"No sentiment available for {symbol}.")
    latest = history.sort_values("date").iloc[-1].to_dict()
    return {
        "symbol": symbol,
        "date": latest["date"],
        "sentiment": latest["dominant_sentiment"],
        "sentiment_score": latest["average_sentiment_score"],
        "confidence": latest["average_confidence"],
        "news_count": latest["news_count"],
    }


def sentiment_as_score_0_to_100(symbol: str, as_of_date: str | None = None) -> dict | None:
    try:
        item = latest_sentiment(symbol, as_of_date=as_of_date)
    except SentimentNotFoundError:
        return None
    item["signal_score"] = round((float(item["sentiment_score"]) + 100) / 2, 2)
    return item


def aggregate_daily_sentiment(news: pd.DataFrame) -> pd.DataFrame:
    if news.empty:
        return pd.DataFrame(
            columns=["symbol", "date", "news_count", "average_sentiment_score", "dominant_sentiment", "average_confidence"]
        )
    stock_news = news.dropna(subset=["symbol"]).copy()
    if stock_news.empty:
        return pd.DataFrame(
            columns=["symbol", "date", "news_count", "average_sentiment_score", "dominant_sentiment", "average_confidence"]
        )
    grouped = (
        stock_news.groupby(["symbol", "date"], as_index=False)
        .agg(
            news_count=("headline", "count"),
            average_sentiment_score=("sentiment_score", "mean"),
            average_confidence=("confidence", "mean"),
        )
        .round({"average_sentiment_score": 2, "average_confidence": 2})
    )
    grouped["dominant_sentiment"] = grouped["average_sentiment_score"].map(_dominant_sentiment)
    return grouped.sort_values(["symbol", "date"]).reset_index(drop=True)


def _dominant_sentiment(score: float) -> str:
    if score > 10:
        return "POSITIVE"
    if score < -10:
        return "NEGATIVE"
    return "NEUTRAL"


def _filter_dates(df: pd.DataFrame, start: pd.Timestamp | None, end: pd.Timestamp | None) -> pd.DataFrame:
    if df.empty:
        return df
    dates = pd.to_datetime(df["date"])
    if start is not None:
        df = df[dates >= start]
        dates = pd.to_datetime(df["date"])
    if end is not None:
        df = df[dates <= end]
    return df


def _records(df: pd.DataFrame) -> list[dict]:
    return df.where(pd.notna(df), None).to_dict(orient="records")
