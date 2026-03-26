try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.settings_service import settings_service
from app.trading.lot_scaler import calculate_scaled_lot
from app.core.storage import Storage
from app.models.trade import Trade

storage = Storage()

def initialize_mt5():
    if not MT5_AVAILABLE:
        print("MT5 is not available on this platform.")
        return
        
    if not mt5.initialize():
        raise RuntimeError("MT5 initialization failed")


def resolve_symbol(input_symbol: str) -> str:
    if not MT5_AVAILABLE:
        return None
        
    # 1. Try exact match
    if mt5.symbol_select(input_symbol, True):
        return input_symbol

    # 2. Search for the symbol in all available symbols
    # This retrieves all symbols containing the input_symbol
    symbols = mt5.symbols_get(group=f"*{input_symbol}*")
    
    if not symbols:
        print(f"Symbol '{input_symbol}' not found on broker (no partial matches).")
        return None

    # 3. Filter for best match (e.g., matching base, just has suffix)
    # Priority: Exact match with suffix -> Shortest match
    matches = []
    for s in symbols:
        # Check if the symbol starts with the input (suffix case) 
        # or ends with the input (prefix case - rarer but possible)
        if s.name.startswith(input_symbol) or s.name.endswith(input_symbol):
            matches.append(s.name)
    
    if not matches:
        return None
        
    # Sort by length to prefer 'EURUSD.m' over 'EURUSD.more_specific'
    matches.sort(key=len)
    
    best_match = matches[0]
    print(f"Resolved '{input_symbol}' to '{best_match}'")
    
    if mt5.symbol_select(best_match, True):
        return best_match
        
    return None

def open_trade(db: Session, signal: dict, account_balance: float):
    min_balance = settings_service.get(db, "min_balance_guard", 200.0)
    if account_balance < min_balance:
        return

    base_balance = settings_service.get(db, "base_balance", 1000.0)
    max_lot = settings_service.get(db, "max_lot", 1.0)
    use_signal_lot = settings_service.get(db, "use_signal_lot", False)
    
    if use_signal_lot:
        lot = float(signal["signal_lot"])
    else:
        lot = calculate_scaled_lot(
            signal["signal_lot"], 
            account_balance, 
            min_balance_guard=min_balance,
            base_balance=base_balance,
            max_lot=max_lot
        )
    
    if lot <= 0:
        return

    raw_symbol = signal["symbol"]
    direction = signal["direction"]
    signal_id = signal["signal_order_id"]

    # Resolve symbol (handle suffixes like .m, .pro)
    if not MT5_AVAILABLE:
        return None
        
    symbol = resolve_symbol(raw_symbol)
    if not symbol:
        print(f"Could not resolve symbol '{raw_symbol}' on this broker.")
        return

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        last_error = mt5.last_error()
        print(f"Failed to get tick for {symbol}. MT5 Error: {last_error}")
        return
        
    price = tick.ask if direction == "BUY" else tick.bid
    
    # Check if price is valid
    if price is None or price <= 0:
        print(f"Invalid price for {symbol}: {price}")
        return

    magic_number = settings_service.get(db, "magic_number", 202512)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "deviation": 20,
        "magic": magic_number,
        "comment": f"EDGE_{signal_id}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }

    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment if result else 'Unknown error'} (Retcode: {result.retcode if result else 'None'})")
        return

    trade_data = {
        "signal_order_id": signal_id,
        "mt5_ticket": result.order,
        "symbol": symbol,
        "direction": direction,
        "signal_lot": signal["signal_lot"],
        "executed_lot": lot,
        "open_price": price,
        "status": "OPEN",
        "magic_number": magic_number,
        "opened_at": datetime.now(timezone.utc).replace(tzinfo=None)
    }

    storage.log_trade(db, trade_data)

def close_trade(db: Session, signal: dict):
    signal_id = signal["signal_order_id"]

    trade = (
        db.query(Trade)
        .filter(
            Trade.signal_order_id == signal_id,
            Trade.status == "OPEN"
        )
        .first()
    )

    if not trade or not MT5_AVAILABLE:
        return

    position = mt5.positions_get(ticket=trade.mt5_ticket)
    if not position:
        return

    pos = position[0]
    symbol = trade.symbol

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return
        
    price = (
        tick.bid
        if pos.type == mt5.POSITION_TYPE_BUY
        else tick.ask
    )

    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": pos.ticket,
        "symbol": symbol,
        "volume": pos.volume,
        "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
        "price": price,
        "deviation": 20,
        "magic": mt5.positions_get(ticket=trade.mt5_ticket)[0].magic if mt5.positions_get(ticket=trade.mt5_ticket) else 0,
        "comment": f"EDGE_CLOSE_{signal_id}"
    }

    result = mt5.order_send(close_request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        return

    trade.close_price = price
    trade.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    trade.status = "CLOSED"
    trade.pnl = pos.profit

    db.commit()
