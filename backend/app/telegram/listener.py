from telethon import TelegramClient, events
from app.telegram.parser import parse_signal
from app.core.db import SessionLocal
from app.core.config import settings
from app.core.storage import Storage
from app.models.trade import TradeSignal, Trade
from app.core.settings_service import settings_service
from app.models.balance import BalanceSnapshot
import asyncio
import datetime
import logging
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = TelegramClient("session", settings.telegram_api_id, settings.telegram_api_hash)
storage = Storage()

# Fetch target group chat
db = SessionLocal()
try:
    telegram_group_link = settings_service.get(db, "telegram_group_link")
    logger.info(f"Target Telegram Group Link: '{telegram_group_link}'")
finally:
    db.close()

async def execute_on_laptop(db, signal_data):
    """
    Attempts to call the laptop local service to execute a trade.
    Returns True if successfully communicated, False otherwise.
    """
    payload = {
        "signal_order_id": signal_data["signal_order_id"],
        "symbol": signal_data["symbol"],
        "direction": signal_data["direction"],
        "signal_lot": signal_data["signal_lot"],
        "action": signal_data["action"],
        "min_balance_guard": settings_service.get(db, "min_balance_guard", 200.0),
        "base_balance": settings_service.get(db, "base_balance", 1000.0),
        "max_lot": settings_service.get(db, "max_lot", 1.0)
    }
    
    endpoint = f"{settings.laptop_api_base_url}/execute_{payload['action'].lower()}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            logger.info(f"Attempting {payload['action']} via Laptop API: {endpoint}")
            resp = await http_client.post(endpoint, json=payload)
            if resp.status_code == 200:
                result = resp.json()
                logger.info(f"Laptop Response: {result}")
                if result["status"] == "success":
                    # Mark trade as executed in DB for recovery purposes (this will be done by caller)
                    # We might want to record the actual executed trade in 'trades' table too
                    if payload["action"] == "OPEN" and "mt5_ticket" in result:
                        # Log to 'trades' table
                        trade_data = {
                            "signal_order_id": payload["signal_order_id"],
                            "mt5_ticket": result["mt5_ticket"],
                            "symbol": result.get("symbol", payload["symbol"]),
                            "direction": payload["direction"],
                            "signal_lot": payload["signal_lot"],
                            "executed_lot": result.get("executed_lot", 0),
                            "open_price": result.get("price", 0),
                            "status": "OPEN",
                            "magic_number": settings.magic_number,
                            "opened_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                        }
                        storage.log_trade(db, trade_data)
                    elif payload["action"] == "CLOSE" and result["status"] == "success":
                         # Update existing trade record
                         trade_record = db.query(Trade).filter(
                             Trade.signal_order_id == payload["signal_order_id"],
                             Trade.status == "OPEN"
                         ).first()
                         if trade_record:
                             trade_record.close_price = result.get("price", 0)
                             trade_record.closed_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                             trade_record.status = "CLOSED"
                             trade_record.pnl = result.get("profit", 0)
                             db.commit()
                    return True
                elif result["status"] == "skipped":
                    logger.warning(f"Trade skipped by laptop: {result.get('reason')}")
                    return True # Count as processed
            else:
                logger.error(f"Laptop API Error (Status {resp.status_code}): {resp.text}")
    except Exception as e:
        logger.error(f"Failed to communicate with laptop service: {e}")
    
    return False

async def run_recovery(db):
    """
    Checks the signals table for unexecuted signals and processes them.
    Rules:
    - Close signals: Always execute.
    - Open signals: Execute only if < 5 minutes old.
    """
    missed_signals = (
        db.query(TradeSignal)
        .filter(TradeSignal.executed == 0)
        .order_by(TradeSignal.timestamp.asc())
        .all()
    )
    
    if not missed_signals:
        return

    logger.info(f"Found {len(missed_signals)} unexecuted signals. Starting recovery...")
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    max_delay = datetime.timedelta(minutes=5)

    for sig in missed_signals:
        signal_dict = {
            "signal_order_id": sig.signal_order_id,
            "symbol": sig.symbol,
            "direction": sig.direction,
            "signal_lot": sig.signal_lot,
            "action": sig.action
        }
        
        should_execute = False
        if sig.action == "CLOSE":
            should_execute = True
        elif sig.action == "OPEN":
            # UTC check
            if (now - sig.timestamp) <= max_delay:
                should_execute = True
            else:
                logger.info(f"Skipping old OPEN signal {sig.signal_order_id} (Age: {now - sig.timestamp})")
                sig.executed = 1

        if should_execute:
            success = await execute_on_laptop(db, signal_dict)
            if success:
                sig.executed = 1
        
        db.commit()

@client.on(events.NewMessage(chats=telegram_group_link))
async def handler(event):
    logger.info(f"Message received: {event.message.text[:50]}...")
    db = SessionLocal()
    try:
        # Check if trading is allowed
        allow_trading = settings_service.get(db, "allow_trading", True)
        if not allow_trading:
            return

        signal = parse_signal(event.message.text)
        if not signal:
            return

        # 1. Always LOG everything immediately to DB
        storage.log_signal(db, signal)
        
        # 2. Try to execute immediately
        success = await execute_on_laptop(db, signal)
        if success:
            stored_sig = db.query(TradeSignal).filter(TradeSignal.signal_order_id == signal["signal_order_id"]).first()
            if stored_sig:
                stored_sig.executed = 1
                db.commit()

    finally:
        db.close()

async def heartbeat_loop():
    while True:
        db = SessionLocal()
        try:
            now_iso = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat()
            
            # 1. Telegram Client Heartbeat
            if client.is_connected():
                settings_service.set(db, "telegram_heartbeat", now_iso)
            
            # 2. Laptop / MT5 Heartbeat
            laptop_online = False
            try:
                async with httpx.AsyncClient(timeout=3.0) as http_client:
                    resp = await http_client.get(f"{settings.laptop_api_base_url}/heartbeat")
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "online":
                            settings_service.set(db, "mt5_heartbeat", now_iso)
                            laptop_online = True
                            
                            # Update balance snapshot from laptop data
                            if "balance" in data:
                                db.add(BalanceSnapshot(
                                    balance=data["balance"], 
                                    equity=data.get("equity", data["balance"]),
                                    margin_level=data.get("margin_level", 0.0)
                                ))
                                db.commit()
            except Exception:
                # Laptop most likely offline
                pass

            # 3. If laptop is online, run recovery for missed signals
            if laptop_online:
                await run_recovery(db)

        except Exception as e:
            logger.error(f"Heartbeat cycle error: {e}")
        finally:
            db.close()
        
        await asyncio.sleep(30)

async def main():
    logger.info("Starting VPS Telegram listener...")
    await client.start()
    logger.info("Telegram client connected.")

    # Start Heartbeat loop
    asyncio.create_task(heartbeat_loop())

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
