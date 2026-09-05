from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    market_data = relationship("MarketData", back_populates="stock")
