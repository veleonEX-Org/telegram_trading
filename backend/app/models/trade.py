from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.core.db import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)

    signal_order_id = Column(String, index=True, nullable=False)
    mt5_ticket = Column(Integer, unique=True)

    symbol = Column(String, nullable=False)
    direction = Column(String, nullable=False)

    signal_lot = Column(Float)
    executed_lot = Column(Float)

    open_price = Column(Float)
    close_price = Column(Float)

    pnl = Column(Float)

    status = Column(String, nullable=False)  # OPEN / CLOSED

    magic_number = Column(Integer)

    opened_at = Column(DateTime)
    closed_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())

class TradeSignal(Base):
    __tablename__ = "trade_signals"

    id = Column(Integer, primary_key=True, index=True)
    signal_order_id = Column(String, index=True, nullable=False)
    symbol = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    signal_lot = Column(Float)
    action = Column(String, nullable=False)  # OPEN or CLOSE
    timestamp = Column(DateTime, server_default=func.now())
    executed = Column(Integer, server_default="0")  # 0 = pending, 1 = success
    error_message = Column(Text, nullable=True)   # Last failure reason
    error_at = Column(DateTime, nullable=True)    # When the last failure occurred
