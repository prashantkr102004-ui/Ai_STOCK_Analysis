from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import pandas as pd

from backend.app.core.config import get_settings


class SentimentModelUnavailable(RuntimeError):
    pass


def sentiment_score(positive_probability: float, negative_probability: float) -> float:
    """Scale FinBERT positive-minus-negative probability to -100..100."""
    return round(100 * (float(positive_probability) - float(negative_probability)), 2)


@lru_cache(maxsize=1)
def load_finbert_pipeline():
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise SentimentModelUnavailable(
            "Sentiment model unavailable. Install transformers and torch, then cache the configured FinBERT model locally."
        ) from exc
    try:
        return pipeline("text-classification", model=get_settings().finbert_model_name, top_k=None)
    except Exception as exc:
        raise SentimentModelUnavailable(
            f"Sentiment model unavailable. Cache '{get_settings().finbert_model_name}' locally or allow a one-time download."
        ) from exc


def analyze_texts(texts: Iterable[str]) -> list[dict]:
    classifier = load_finbert_pipeline()
    raw_results = classifier(list(texts), truncation=True)
    return [normalize_finbert_output(result) for result in raw_results]


def normalize_finbert_output(result: list[dict] | dict) -> dict:
    if isinstance(result, dict):
        result = [result]
    scores = {str(item["label"]).lower(): float(item["score"]) for item in result}
    positive = scores.get("positive", 0.0)
    neutral = scores.get("neutral", 0.0)
    negative = scores.get("negative", 0.0)
    sentiment = max(
        [("POSITIVE", positive), ("NEUTRAL", neutral), ("NEGATIVE", negative)],
        key=lambda item: item[1],
    )[0]
    confidence = round(max(positive, neutral, negative) * 100, 2)
    return {
        "positive_probability": round(positive, 4),
        "neutral_probability": round(neutral, 4),
        "negative_probability": round(negative, 4),
        "sentiment": sentiment,
        "confidence": confidence,
        "sentiment_score": sentiment_score(positive, negative),
    }


def attach_sentiment(news: pd.DataFrame, outputs: list[dict]) -> pd.DataFrame:
    return pd.concat([news.reset_index(drop=True), pd.DataFrame(outputs)], axis=1)
