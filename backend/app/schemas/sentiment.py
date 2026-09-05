from pydantic import BaseModel


class NewsItemResponse(BaseModel):
    date: str
    symbol: str | None = None
    headline: str
    article: str | None = None
    sentiment: str
    confidence: float
    sentiment_score: float
    positive_probability: float
    neutral_probability: float
    negative_probability: float


class SentimentResponse(BaseModel):
    symbol: str
    date: str
    sentiment: str
    sentiment_score: float
    confidence: float
    news_count: int


class SentimentHistoryItem(BaseModel):
    symbol: str
    date: str
    news_count: int
    average_sentiment_score: float
    dominant_sentiment: str
    average_confidence: float
