from __future__ import annotations

import math
from typing import Any

import pandas as pd

from backend.app.core.config import get_settings


FEATURE_DESCRIPTIONS = {
    "RSI": "Momentum strength on a 0-100 scale.",
    "MACD": "Trend and momentum relationship.",
    "MACD_signal": "Smoothed MACD signal line used for momentum comparison.",
    "MACD_hist": "Difference between MACD and its signal line.",
    "SMA_20": "Short-term average closing price.",
    "SMA_50": "Medium-term average closing price.",
    "SMA_200": "Long-term average closing price.",
    "EMA_20": "Short-term average that reacts faster to recent prices.",
    "EMA_50": "Medium-term average that reacts faster than SMA.",
    "Volume_Ratio": "Current volume relative to recent average volume.",
    "Rolling_Volatility": "Recent variability in daily returns.",
    "ATR": "Average true range, a volatility measure.",
    "Return_5D": "Recent five-session price change.",
    "Return_10D": "Recent ten-session price change.",
    "Return_20D": "Recent twenty-session price change.",
}


def confidence_level(confidence: float) -> str:
    for upper_bound, label in get_settings().confidence_bands:
        if confidence < upper_bound:
            return label
    return "Very High Confidence"


def signal_from_score(score: float) -> str:
    settings = get_settings()
    if score >= settings.bullish_threshold:
        return "BULLISH"
    if score <= settings.bearish_threshold:
        return "BEARISH"
    return "NEUTRAL"


def risk_level(score: float) -> str:
    settings = get_settings()
    if score < settings.low_risk_threshold:
        return "LOW"
    if score >= settings.high_risk_threshold:
        return "HIGH"
    return "MEDIUM"


def explain_signal(
    processed: pd.DataFrame,
    symbol: str,
    prediction: dict[str, Any],
    features: list[dict] | None = None,
    sentiment: dict | None = None,
    fundamentals: dict | None = None,
) -> dict:
    symbol = symbol.upper()
    stock = processed[processed["Symbol"] == symbol].sort_values("Date")
    if stock.empty:
        raise ValueError(f"Stock not found: {symbol}")
    latest = stock.iloc[-1]

    positive, negative, confirmations, contradictions = technical_factors(latest, prediction["prediction"])
    technical_score, technical_bias = technical_score_from_factors(positive, negative)
    ml_score = round(float(prediction["probability_up"]) * 100, 2)
    if sentiment:
        sentiment_text = f"Historical news sentiment is {str(sentiment['sentiment']).lower()} as of {sentiment['date']}"
        if sentiment["signal_score"] >= 60:
            positive.append(sentiment_text)
        elif sentiment["signal_score"] <= 40:
            negative.append(sentiment_text)
    if fundamentals:
        fundamental_text = (
            f"Fundamental quality is {str(fundamentals['fundamental_bias']).lower()} "
            f"as of {fundamentals['date']}"
        )
        if fundamentals["fundamental_score"] >= 65:
            positive.append(fundamental_text)
        elif fundamentals["fundamental_score"] < 45:
            negative.append(fundamental_text)
    sentiment_signal_score = sentiment.get("signal_score") if sentiment else None
    fundamental_score = fundamentals.get("fundamental_score") if fundamentals else None
    combined_score = combined_signal_score(ml_score, technical_score, sentiment_signal_score, fundamental_score)
    final_signal = signal_from_score(combined_score)
    confidence = float(prediction["confidence"])
    risk_score_value = calculate_risk_score(latest, confidence)
    business_risk_score = fundamentals.get("business_risk_score") if fundamentals else None
    business_risk_level = fundamentals.get("business_risk_level") if fundamentals else None

    top_features = enrich_feature_importance(features or [])
    summary = build_summary(
        prediction=prediction["prediction"],
        final_signal=final_signal,
        confidence=confidence,
        confidence_level_value=confidence_level(confidence),
        technical_bias=technical_bias,
        risk_level_value=risk_level(risk_score_value),
        sentiment=sentiment,
        fundamentals=fundamentals,
    )

    return {
        "symbol": symbol,
        "signal": final_signal,
        "final_signal": final_signal,
        "model_prediction": prediction["prediction"],
        "prediction_date": prediction.get("prediction_date"),
        "confidence": confidence,
        "confidence_level": confidence_level(confidence),
        "ml_score": ml_score,
        "technical_score": technical_score,
        "sentiment_score": None if sentiment is None else round(float(sentiment["sentiment_score"]), 2),
        "sentiment_signal_score": None if sentiment is None else round(float(sentiment["signal_score"]), 2),
        "sentiment_date": None if sentiment is None else sentiment["date"],
        "sentiment_news_count": None if sentiment is None else int(sentiment["news_count"]),
        "fundamental_score": None if fundamentals is None else round(float(fundamentals["fundamental_score"]), 2),
        "fundamental_bias": None if fundamentals is None else fundamentals["fundamental_bias"],
        "fundamental_date": None if fundamentals is None else fundamentals["date"],
        "fundamental_data_completeness": None if fundamentals is None else fundamentals["data_completeness"],
        "business_risk_score": business_risk_score,
        "business_risk_level": business_risk_level,
        "technical_bias": technical_bias,
        "combined_score": combined_score,
        "risk_score": risk_score_value,
        "risk_level": risk_level(risk_score_value),
        "positive_factors": positive,
        "negative_factors": negative,
        "technical_confirmations": confirmations,
        "technical_contradictions": contradictions,
        "top_model_features": top_features,
        "local_contributions": None,
        "summary": summary,
        "reasons": positive[:3] or negative[:3] or ["Model and technical evidence are mixed."],
        "description": "Model-based analytical signal; not financial advice.",
    }


def technical_factors(latest: pd.Series, prediction_label: str) -> tuple[list[str], list[str], list[str], list[str]]:
    bullish: list[str] = []
    bearish: list[str] = []

    close = _number(latest.get("Close"))
    sma_20 = _number(latest.get("SMA_20"))
    sma_50 = _number(latest.get("SMA_50"))
    ema_20 = _number(latest.get("EMA_20"))
    ema_50 = _number(latest.get("EMA_50"))
    rsi = _number(latest.get("RSI"))
    macd = _number(latest.get("MACD"))
    macd_signal = _number(latest.get("MACD_signal"))
    volume_ratio = _number(latest.get("Volume_Ratio"))
    return_5d = _number(latest.get("Return_5D"))

    if close is not None and sma_50 is not None:
        _append_by_sign(close - sma_50, "Price is above SMA 50", "Price is below SMA 50", bullish, bearish)
    if close is not None and sma_20 is not None:
        _append_by_sign(close - sma_20, "Price is above SMA 20", "Price is below SMA 20", bullish, bearish)
    if ema_20 is not None and ema_50 is not None:
        _append_by_sign(ema_20 - ema_50, "EMA 20 is above EMA 50", "EMA 20 is below EMA 50", bullish, bearish)
    if macd is not None and macd_signal is not None:
        _append_by_sign(macd - macd_signal, "MACD is above its signal line", "MACD is below its signal line", bullish, bearish)
    if rsi is not None:
        if 45 <= rsi <= 70:
            bullish.append("RSI is in a constructive momentum range")
        elif rsi < 45:
            bearish.append("RSI shows weak momentum")
        elif rsi > 75:
            bearish.append("RSI is extended, which can increase reversal risk")
    if volume_ratio is not None:
        if volume_ratio >= 1 and (return_5d or 0) >= 0:
            bullish.append("Volume is above recent average with positive price action")
        elif volume_ratio < 0.8:
            bearish.append("Volume is below recent average")
    if return_5d is not None:
        _append_by_sign(return_5d, "Five-session return is positive", "Five-session return is negative", bullish, bearish)

    if prediction_label == "UP":
        confirmations = bullish
        contradictions = bearish
    else:
        confirmations = bearish
        contradictions = bullish
    return bullish, bearish, confirmations, contradictions


def technical_score_from_factors(positive: list[str], negative: list[str]) -> tuple[float, str]:
    total = len(positive) + len(negative)
    if total == 0:
        return 50.0, "NEUTRAL"
    score = round((len(positive) / total) * 100, 2)
    return score, signal_from_score(score)


def combined_signal_score(
    ml_score: float,
    technical_score: float,
    sentiment_score: float | None = None,
    fundamental_score: float | None = None,
) -> float:
    settings = get_settings()
    sentiment_weight = settings.sentiment_weight if sentiment_score is not None else 0
    fundamental_weight = settings.fundamental_weight if fundamental_score is not None else 0
    total_weight = settings.ml_weight + settings.technical_weight + sentiment_weight + fundamental_weight
    if total_weight <= 0:
        return round((ml_score + technical_score) / 2, 2)
    total = (settings.ml_weight * ml_score) + (settings.technical_weight * technical_score)
    if sentiment_score is not None:
        total += sentiment_weight * sentiment_score
    if fundamental_score is not None:
        total += fundamental_weight * fundamental_score
    return round(total / total_weight, 2)


def calculate_risk_score(latest: pd.Series, confidence: float) -> float:
    close = _number(latest.get("Close")) or 0
    atr = _number(latest.get("ATR")) or 0
    volatility = abs(_number(latest.get("Rolling_Volatility")) or 0)
    return_5d = abs(_number(latest.get("Return_5D")) or 0)

    atr_component = min((atr / close) * 1000, 35) if close > 0 else 0
    volatility_component = min(volatility * 1200, 35)
    swing_component = min(return_5d * 300, 20)
    confidence_component = min(max(70 - confidence, 0) * 0.5, 10)
    return round(min(atr_component + volatility_component + swing_component + confidence_component, 100), 2)


def enrich_feature_importance(features: list[dict], limit: int = 8) -> list[dict]:
    enriched = []
    for item in features[:limit]:
        feature = item.get("feature")
        enriched.append(
            {
                "feature": feature,
                "importance": item.get("importance"),
                "explanation": FEATURE_DESCRIPTIONS.get(feature, "Model input feature from the processed dataset."),
            }
        )
    return enriched


def build_summary(
    prediction: str,
    final_signal: str,
    confidence: float,
    confidence_level_value: str,
    technical_bias: str,
    risk_level_value: str,
    sentiment: dict | None = None,
    fundamentals: dict | None = None,
) -> str:
    if final_signal == "NEUTRAL":
        direction = f"The model predicts {prediction}, but the combined model and technical evidence remains inside the neutral zone."
    else:
        direction = f"The combined score currently supports a {final_signal} analytical signal while the model predicts {prediction}."
    sentiment_note = ""
    if sentiment:
        sentiment_note = (
            f" Historical news sentiment as of {sentiment['date']} is "
            f"{str(sentiment['sentiment']).lower()} from {int(sentiment['news_count'])} item(s)."
        )
    fundamental_note = ""
    if fundamentals:
        fundamental_note = (
            f" Fundamental quality as of {fundamentals['date']} is "
            f"{str(fundamentals['fundamental_bias']).lower()} with "
            f"{float(fundamentals['data_completeness']):.2f}% data completeness."
        )
    return (
        f"{direction} Confidence is {confidence:.2f}% ({confidence_level_value}), "
        f"technical bias is {technical_bias}, and measured risk is {risk_level_value}."
        f"{sentiment_note}{fundamental_note}"
    )


def _append_by_sign(value: float, positive_text: str, negative_text: str, positive: list[str], negative: list[str]) -> None:
    if value > 0:
        positive.append(positive_text)
    elif value < 0:
        negative.append(negative_text)


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number
