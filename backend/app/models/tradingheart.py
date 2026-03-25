from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.core.db import Base

class TradingHeart(Base):
    __tablename__ = "tradingheart"
    
    id = Column(Integer, primary_key=True, index=True)
    counter = Column(Integer, default=0)
    last_ping = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
