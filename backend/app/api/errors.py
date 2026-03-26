from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.db import get_db
from app.models.trade import TradeSignal

router = APIRouter()


@router.get("/")
def get_error_signals(db: Session = Depends(get_db)):
    """
    Returns all trade signals that have a recorded error (error_message is not null).
    Includes both retryable and hard errors.
    Ordered newest first.
    """
    signals = (
        db.query(TradeSignal)
        .filter(TradeSignal.error_message.isnot(None))
        .order_by(desc(TradeSignal.error_at))
        .all()
    )
    result = []
    for s in signals:
        # Trim the internal HARD| sentinel prefix before sending to frontend
        raw_msg = s.error_message or ""
        is_hard = raw_msg.startswith("HARD|")
        clean_msg = raw_msg[5:] if is_hard else raw_msg

        result.append({
            "id": s.id,
            "signal_order_id": s.signal_order_id,
            "symbol": s.symbol,
            "direction": s.direction,
            "signal_lot": s.signal_lot,
            "action": s.action,
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            "executed": s.executed,
            "error_message": clean_msg,
            "error_at": s.error_at.isoformat() if s.error_at else None,
            "error_type": "hard" if is_hard else "connection",
        })
    return result


@router.delete("/{signal_id}/dismiss")
def dismiss_error(signal_id: int, db: Session = Depends(get_db)):
    """
    Clears the error_message so the signal no longer appears in the errors page.
    Also marks executed=1 to prevent recovery retries.
    """
    sig = db.query(TradeSignal).filter(TradeSignal.id == signal_id).first()
    if not sig:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Signal not found")

    sig.error_message = None
    sig.error_at = None
    sig.executed = 1  # prevents recovery from retrying
    db.commit()
    return {"status": "dismissed", "id": signal_id}
