from pydantic import BaseModel


class PredictionResponse(BaseModel):
    symbol: str
    prediction: str
    probability_up: float
    probability_down: float
    confidence: float
    model: str
    model_version: str
    prediction_date: str | None = None


class SignalResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float
    confidence_level: str
    ml_score: float
    technical_score: float
    sentiment_score: float | None = None
    sentiment_signal_score: float | None = None
    sentiment_date: str | None = None
    sentiment_news_count: int | None = None
    fundamental_score: float | None = None
    fundamental_bias: str | None = None
    fundamental_date: str | None = None
    fundamental_data_completeness: float | None = None
    business_risk_score: float | None = None
    business_risk_level: str | None = None
    technical_bias: str
    combined_score: float
    risk_score: float
    risk_level: str
    final_signal: str
    model_prediction: str
    prediction_date: str | None = None
    positive_factors: list[str]
    negative_factors: list[str]
    summary: str
    reasons: list[str]
    description: str


class ExplainedFeature(BaseModel):
    feature: str
    importance: float | None = None
    explanation: str


class ExplanationResponse(SignalResponse):
    technical_confirmations: list[str]
    technical_contradictions: list[str]
    top_model_features: list[ExplainedFeature]
    local_contributions: list[dict] | None = None
