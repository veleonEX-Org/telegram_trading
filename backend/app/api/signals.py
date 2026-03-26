from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.trade import TradeSignal
from sqlalchemy import desc
import threading

router = APIRouter()


@router.get("/")
def get_signals(db: Session = Depends(get_db)):
    signals = db.query(TradeSignal).order_by(desc(TradeSignal.timestamp)).all()
    return signals


@router.post("/{signal_id}/execute")
def execute_signal_manually(
    signal_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    signal = db.query(TradeSignal).filter(TradeSignal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    if signal.action != "OPEN":
        raise HTTPException(
            status_code=400,
            detail="Only OPEN signals can be manually executed"
        )

    signal_dict = {
        "signal_order_id": signal.signal_order_id,
        "symbol": signal.symbol,
        "direction": signal.direction,
        "signal_lot": signal.signal_lot,
        "action": signal.action,
    }

    # Run in a background thread so the response returns immediately
    def run_trade():
        from app.core.db import SessionLocal
        from app.trading.executor import initialize_mt5, open_trade
        from app.core.storage import Storage

        inner_db = SessionLocal()
        try:
            initialize_mt5()
            # Fetch balance for guard check
            from app.models.balance import BalanceSnapshot
            snap = (
                inner_db.query(BalanceSnapshot)
                .order_by(BalanceSnapshot.id.desc())
                .first()
            )
            balance = snap.balance if snap else 0.0
            open_trade(inner_db, signal_dict, balance)
        except Exception as e:
            print(f"Manual signal execution error: {e}")
        finally:
            inner_db.close()

    thread = threading.Thread(target=run_trade, daemon=True)
    thread.start()

    return {"status": "queued", "signal_id": signal_id, "message": "Trade execution started"}
