from pydantic import BaseModel


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float


class ModelStatusResponse(BaseModel):
    trained: bool
    model_name: str | None = None
    model_version: str | None = None
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
