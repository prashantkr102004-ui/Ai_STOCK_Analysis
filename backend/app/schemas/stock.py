from pydantic import BaseModel


class StockSummary(BaseModel):
    symbol: str


class StockDetailResponse(BaseModel):
    symbol: str
    record_count: int
    start_date: str
    end_date: str
    latest_close: float
    latest_date: str


class StockHistoryItem(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class StockHistoryResponse(BaseModel):
    symbol: str
    history: list[StockHistoryItem]


class IndicatorResponse(BaseModel):
    symbol: str
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    ema_20: float | None = None
    ema_50: float | None = None
    bollinger_upper: float | None = None
    bollinger_middle: float | None = None
    bollinger_lower: float | None = None
    atr: float | None = None
    volume: float | None = None
    volume_ratio: float | None = None
    volatility: float | None = None
