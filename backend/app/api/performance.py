from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.trading.performance import performance_summary

router = APIRouter()

@router.get("/summary")
def summary(
    start_date: str = None, 
    end_date: str = None, 
    db: Session = Depends(get_db)
):
    return performance_summary(db, start_date=start_date, end_date=end_date)
