from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
import logging
from app.models.tradingheart import TradingHeart
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("")
def ping_tradingheart(db: Session = Depends(get_db)):
    try:
        # Check if record exists, create if not
        heart = db.query(TradingHeart).filter(TradingHeart.id == 1).first()
        if not heart:
            heart = TradingHeart(id=1, counter=1, last_ping=datetime.utcnow())
            db.add(heart)
        else:
            heart.counter += 1
            heart.last_ping = datetime.utcnow()
        
        db.commit()
        return {"status": "alive", "heart": "beating"}
    except Exception as e:
        logger.error(f"TradingHeart check failed: {e}")
        raise HTTPException(status_code=500, detail="Heartbeat failed")
