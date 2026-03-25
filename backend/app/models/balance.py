from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func
from app.core.db import Base

class BalanceSnapshot(Base):
    __tablename__ = "balance_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float)
    equity = Column(Float)
    margin_level = Column(Float, default=0.0)
    captured_at = Column(DateTime, server_default=func.now())
