from pydantic import BaseModel


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    meaning: str | None = None


class MetricSet(BaseModel):
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    confusion_matrix: list[list[int]] | None = None


class BacktestMetricSet(BaseModel):
    symbol: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    strategy_return: float | None = None
    strategy_return_pct: float | None = None
    buy_hold_return: float | None = None
    buy_hold_return_pct: float | None = None
    max_drawdown: float | None = None
    max_drawdown_pct: float | None = None
    sharpe_ratio: float | None = None
    number_of_trades: int | None = None
    win_rate: float | None = None


class ModelComparisonItem(BaseModel):
    model_key: str
    model_name: str
    version: str | None = None
    selected_threshold: float | None = None
    train_metrics: MetricSet | None = None
    validation_metrics: MetricSet | None = None
    test_metrics: MetricSet | None = None
    backtest: BacktestMetricSet | None = None
    training_time_seconds: float | None = None
    overfitting_warning: str | None = None
    production_model: bool = False


class ModelComparisonResponse(BaseModel):
    available: bool
    message: str | None = None
    generated_at: str | None = None
    production_model: str | None = None
    production_model_name: str | None = None
    recommended_model: str | None = None
    production_model_changed: bool | None = None
    selection_reason: str | None = None
    validation_methodology: str | None = None
    leakage_check: str | None = None
    feature_count: int | None = None
    dataset_summary: dict | None = None
    split_ranges: dict | None = None
    target_distribution: dict | None = None
    hyperparameters_tested: dict | None = None
    walk_forward: dict | None = None
    backtest_settings: dict | None = None
    models: list[ModelComparisonItem] = []


class ModelStatusResponse(BaseModel):
    trained: bool
    model_name: str | None = None
    model_version: str | None = None
    production_model: str | None = None
    production_model_name: str | None = None
    recommended_model: str | None = None
    selected_threshold: float | None = None
    validation_metrics: MetricSet | None = None
    test_metrics: MetricSet | None = None
    overfitting_warning: str | None = None
    training_date: str | None = None
    feature_count: int | None = None
    training_samples: int | None = None
    validation_samples: int | None = None
    test_samples: int | None = None
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    message: str | None = None
