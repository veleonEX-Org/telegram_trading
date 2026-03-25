from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.trade import Trade

router = APIRouter()

@router.get("/")
def all_trades(db: Session = Depends(get_db)):
    return db.query(Trade).all()

@router.get("/open")
def open_trades(db: Session = Depends(get_db)):
    return db.query(Trade).filter(Trade.status == "OPEN").all()
