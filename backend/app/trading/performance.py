from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
from app.models.trade import Trade

def performance_summary(db: Session, start_date: str = None, end_date: str = None):
    # Base queries
    trade_query = db.query(Trade)
    
    from app.models.balance import BalanceSnapshot
    snapshot_query = db.query(BalanceSnapshot.equity, BalanceSnapshot.captured_at)

    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        trade_query = trade_query.filter(Trade.opened_at >= start_dt)
        snapshot_query = snapshot_query.filter(BalanceSnapshot.captured_at >= start_dt)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        trade_query = trade_query.filter(Trade.opened_at <= end_dt)
        snapshot_query = snapshot_query.filter(BalanceSnapshot.captured_at <= end_dt)

    # Calculate metrics
    total_trades = trade_query.count()
    closed_trade_query = trade_query.filter(Trade.status == "CLOSED", Trade.pnl.isnot(None))
    total_closed = closed_trade_query.count()
    wins = closed_trade_query.filter(Trade.pnl > 0).count()
    pnl = closed_trade_query.with_entities(func.sum(Trade.pnl)).scalar() or 0
    
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0

    # 1. Overall Max Drawdown
    snapshots = snapshot_query.order_by(BalanceSnapshot.captured_at).all()
    equities = [s[0] for s in snapshots]
    
    def calc_dd(vals):
        if not vals: return 0
        peak = vals[0]
        max_dd = 0
        for e in vals:
            if e > peak: peak = e
            dd = (peak - e) / peak * 100 if peak > 0 else 0
            if dd > max_dd: max_dd = dd
        return max_dd

    max_drawdown = calc_dd(equities)

    # 2. Max Daily Drawdown (Deepest DD within single calendar days)
    # Group snapshots by day
    from collections import defaultdict
    daily_equities = defaultdict(list)
    for eq, t in snapshots:
        day_key = t.date().isoformat()
        daily_equities[day_key].append(eq)
    
    max_daily_drawdown = 0
    for day, vals in daily_equities.items():
        dd = calc_dd(vals)
        if dd > max_daily_drawdown:
            max_daily_drawdown = dd

    # 3. Max Weekly Drawdown
    weekly_equities = defaultdict(list)
    for eq, t in snapshots:
        # ISO week number
        week_key = t.strftime("%Y-W%W")
        weekly_equities[week_key].append(eq)
    
    max_weekly_drawdown = 0
    for week, vals in weekly_equities.items():
        dd = calc_dd(vals)
        if dd > max_weekly_drawdown:
            max_weekly_drawdown = dd

    # Calculate Average Duration
    closed_trades = trade_query.filter(Trade.status == "CLOSED", Trade.opened_at.isnot(None), Trade.closed_at.isnot(None)).all()
    avg_duration_seconds = 0
    if closed_trades:
        durations = [(t.closed_at - t.opened_at).total_seconds() for t in closed_trades]
        avg_duration_seconds = sum(durations) / len(durations)

    return {
        "total_trades": total_trades,
        "total_closed": total_closed,
        "win_rate": win_rate,
        "total_pnl": round(pnl, 2),
        "max_drawdown": round(max_drawdown, 2),
        "max_daily_drawdown": round(max_daily_drawdown, 2),
        "max_weekly_drawdown": round(max_weekly_drawdown, 2),
        "avg_duration_seconds": round(avg_duration_seconds, 0)
    }
