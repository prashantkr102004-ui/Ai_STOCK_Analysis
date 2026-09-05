from pydantic import BaseModel, Field


class FundamentalAnalysisResponse(BaseModel):
    symbol: str
    date: str
    fundamental_score: float
    fundamental_bias: str
    data_completeness: float
    growth_score: float | None = None
    profitability_score: float | None = None
    valuation_score: float | None = None
    balance_sheet_score: float | None = None
    cash_flow_score: float | None = None
    business_risk_score: float
    business_risk_level: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


class FundamentalHistoryItem(BaseModel):
    symbol: str
    date: str
    revenue: float | None = None
    net_profit: float | None = None
    eps: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    roce: float | None = None
    debt: float | None = None
    debt_to_equity: float | None = None
    market_cap: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    free_cash_flow: float | None = None
    dividend_yield: float | None = None
