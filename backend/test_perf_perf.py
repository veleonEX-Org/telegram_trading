
from app.core.db import SessionLocal
from app.models.trade import Trade
from app.models.balance import BalanceSnapshot
from sqlalchemy import func
import time

def performance_summary_instrumented(db):
    times = {}
    
    start = time.time()
    trade_query = db.query(Trade)
    snapshot_query = db.query(BalanceSnapshot.equity, BalanceSnapshot.captured_at)
    times["initial_queries"] = time.time() - start
    
    start = time.time()
    total = trade_query.count()
    times["total_count"] = time.time() - start
    
    start = time.time()
    wins = trade_query.filter(Trade.pnl > 0).count()
    times["wins_count"] = time.time() - start
    
    start = time.time()
    pnl_query = db.query(func.sum(Trade.pnl)).filter(Trade.id.in_(trade_query.with_entities(Trade.id)))
    # For instrumenting, execute it
    pnl = pnl_query.scalar() or 0
    times["pnl_query"] = time.time() - start
    
    start = time.time()
    snapshots = snapshot_query.order_by(BalanceSnapshot.captured_at).all()
    times["snapshots_fetch"] = time.time() - start
    
    # Rest of calculation...
    return times

db = SessionLocal()
try:
    times = performance_summary_instrumented(db)
    print("Execution Times:")
    for k, v in times.items():
        print(f"  {k}: {v:.4f}s")
finally:
    db.close()
