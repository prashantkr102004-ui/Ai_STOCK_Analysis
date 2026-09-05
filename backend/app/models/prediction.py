from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    stock = relationship("Stock", back_populates="market_data")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False)
    prediction = Column(String(8), nullable=False)
    probability_up = Column(Float, nullable=False)
    probability_down = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(64), nullable=False)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(64), unique=True, nullable=False)
    model_name = Column(String(128), nullable=False)
    training_date = Column(Date, nullable=False)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)
    roc_auc = Column(Float)
    model_path = Column(String(500), nullable=False)
