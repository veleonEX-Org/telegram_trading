from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.settings_service import settings_service
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    # Fetch heartbeats
    telegram_hb_str = settings_service.get(db, "telegram_heartbeat", None)
    mt5_hb_str = settings_service.get(db, "mt5_heartbeat", None)
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # If no heartbeat in last 60 seconds, assume down
    threshold = timedelta(seconds=60)
    
    telegram_connected = False
    if telegram_hb_str:
        try:
            telegram_hb = datetime.fromisoformat(telegram_hb_str).replace(tzinfo=None)
            # Ensure naive datetimes comparison (both utcnow and isoformat are naive or consistent)
            if now - telegram_hb < threshold:
                telegram_connected = True
        except ValueError:
            pass
            
    mt5_connected = False
    if mt5_hb_str:
        try:
            mt5_hb = datetime.fromisoformat(mt5_hb_str).replace(tzinfo=None)
            if now - mt5_hb < threshold:
                mt5_connected = True
        except ValueError:
            pass
            
    balance = 0.0
    equity = 0.0
    margin_level = 0.0
    
    # Priority 1: Direct MT5 access (Laptop case)
    if MT5_AVAILABLE:
        try:
            if not mt5.initialize():
                mt5.initialize() # idempotent mostly
            
            account_info = mt5.account_info()
            if account_info:
                balance = account_info.balance
                equity = account_info.equity
                margin_level = account_info.margin_level
                # If we successfully got info directly, we can consider the node live 
                # for the sake of the dashboard status too
                mt5_connected = True
        except Exception:
            pass
    
    # Priority 2: Fetch from database snapshots (VPS case or MT5 Node disconnected)
    if balance == 0.0 and equity == 0.0:
        from app.models.balance import BalanceSnapshot
        latest = db.query(BalanceSnapshot).order_by(BalanceSnapshot.captured_at.desc()).first()
        if latest:
            balance = latest.balance
            equity = latest.equity
            margin_level = getattr(latest, "margin_level", 0.0) or 0.0

    db_connected = False
    try:
        # Simple query to check DB connectivity
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        pass

    return {
        "db_connected": db_connected,
        "telegram_connected": telegram_connected,
        "mt5_connected": mt5_connected,
        "balance": round(balance, 2),
        "equity": round(equity, 2),
        "margin_level": round(margin_level, 2)
    }

@router.get("/heartbeat")
def get_node_heartbeat():
    # This is targeted by the VPS listener to get local MT5 details
    balance = 0.0
    equity = 0.0
    margin_level = 0.0
    
    if MT5_AVAILABLE:
        try:
            if not mt5.initialize():
                mt5.initialize()
            
            account_info = mt5.account_info()
            if account_info:
                balance = account_info.balance
                equity = account_info.equity
                margin_level = account_info.margin_level
                return {
                    "status": "online",
                    "balance": round(balance, 2),
                    "equity": round(equity, 2),
                    "margin_level": round(margin_level, 2)
                }
        except Exception:
            pass
            
    return {"status": "offline", "balance": 0.0, "equity": 0.0, "margin_level": 0.0}
