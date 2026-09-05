from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    initial_capital: float = Field(default=100000, gt=0)
    transaction_cost: float = Field(default=0.001, ge=0, lt=1)
    slippage: float = Field(default=0, ge=0, lt=1)
    use_sentiment: bool = False
    use_fundamentals: bool = False


class BacktestResponse(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_profit_loss: float
    total_return: float
    total_return_pct: float
    annualized_return: float | None
    strategy_return: float
    strategy_return_pct: float
    buy_hold_return: float
    buy_hold_return_pct: float
    buy_hold_final_capital: float
    number_of_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    win_rate_pct: float
    average_trade_return_pct: float | None
    best_trade_pct: float | None
    worst_trade_pct: float | None
    max_drawdown: float
    max_drawdown_pct: float
    volatility: float | None
    sharpe_ratio: float | None
    transaction_cost: float
    slippage: float
    trade_log_path: str | None = None
    equity_curve_path: str | None = None
    summary_path: str | None = None
    equity_curve: list[dict] = Field(default_factory=list)


class EquityCurveItem(BaseModel):
    date: str
    cash: float
    position_value: float
    total_equity: float
    daily_return: float
    cumulative_return: float
    drawdown: float
    buy_hold_equity: float | None = None


class EquityCurveResponse(BaseModel):
    symbol: str
    equity_curve: list[EquityCurveItem]


class TradeResponse(BaseModel):
    trade_id: int
    symbol: str
    signal_date: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    shares: int
    profit_loss: float
    return_percentage: float
