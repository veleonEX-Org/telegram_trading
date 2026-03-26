from telethon import TelegramClient, events
from telethon.sessions import StringSession
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

# Connection-related error keywords that justify a retry
CONNECTION_ERROR_KEYWORDS = [
    "connection", "timeout", "network", "unreachable",
    "refused", "reset", "disconnected", "no route",
    "broker", "offline"
]

def _is_connection_error(error_text: str) -> bool:
    """Returns True if the error string suggests a transient connection/network problem."""
    low = error_text.lower()
    return any(kw in low for kw in CONNECTION_ERROR_KEYWORDS)

# Use StringSession when running on Render (env var set); fall back to file session locally
_session = StringSession(settings.telegram_session_string) if settings.telegram_session_string else "session"
client = TelegramClient(_session, settings.telegram_api_id, settings.telegram_api_hash)
storage = Storage()

# Fetch target group chat
db = SessionLocal()
try:
    telegram_group_link = settings_service.get(db, "telegram_group_link")
    logger.info(f"Target Telegram Group Link: '{telegram_group_link}'")
finally:
    db.close()


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

class ExecuteResult:
    """Simple result object returned by execute_on_laptop."""
    def __init__(self, success: bool, skipped: bool = False, error: str = None, is_connection_error: bool = False):
        self.success = success          # True = MT5 confirmed the trade
        self.skipped = skipped          # True = laptop intentionally skipped (e.g. min-balance guard)
        self.error = error              # Human-readable failure reason
        self.is_connection_error = is_connection_error  # True = network/broker issue → retry


async def execute_on_laptop(db, signal_data) -> ExecuteResult:
    """
    Calls the laptop MT5 local service to execute a trade.

    Returns:
      ExecuteResult(success=True)  – MT5 confirmed TRADE_RETCODE_DONE
      ExecuteResult(skipped=True)  – Laptop intentionally skipped (balance guard, etc.)
      ExecuteResult(error=...)     – MT5 rejected the trade or any other error
      ExecuteResult(is_connection_error=True) – HTTP / network failure → worth retrying
    """
    payload = {
        "signal_order_id": signal_data["signal_order_id"],
        "symbol": signal_data["symbol"],
        "direction": signal_data["direction"],
        "signal_lot": signal_data["signal_lot"],
        "action": signal_data["action"],
        "min_balance_guard": settings_service.get(db, "min_balance_guard", 200.0),
        "base_balance": settings_service.get(db, "base_balance", 1000.0),
        "max_lot": settings_service.get(db, "max_lot", 1.0),
    }

    endpoint = f"{settings.laptop_api_base_url}/execute_{payload['action'].lower()}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            logger.info(f"Attempting {payload['action']} via Laptop API: {endpoint}")
            resp = await http_client.post(endpoint, json=payload)

            if resp.status_code != 200:
                err = f"Laptop API HTTP {resp.status_code}: {resp.text[:200]}"
                logger.error(err)
                return ExecuteResult(success=False, error=err,
                                     is_connection_error=_is_connection_error(err))

            result = resp.json()
            logger.info(f"Laptop Response: {result}")

            if result.get("status") == "success":
                # ── Trade actually executed in MT5 ──────────────────────────
                if payload["action"] == "OPEN" and "mt5_ticket" in result:
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
                        "opened_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
                    }
                    storage.log_trade(db, trade_data)

                elif payload["action"] == "CLOSE" and result.get("status") == "success":
                    trade_record = (
                        db.query(Trade)
                        .filter(
                            Trade.signal_order_id == payload["signal_order_id"],
                            Trade.status == "OPEN",
                        )
                        .first()
                    )
                    if trade_record:
                        trade_record.close_price = result.get("price", 0)
                        trade_record.closed_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                        trade_record.status = "CLOSED"
                        trade_record.pnl = result.get("profit", 0)
                        db.commit()

                return ExecuteResult(success=True)

            elif result.get("status") == "skipped":
                reason = result.get("reason", "No reason given")
                logger.warning(f"Trade skipped by laptop: {reason}")
                # Skipped is intentional – mark as NOT retryable
                return ExecuteResult(success=False, skipped=True,
                                     error=f"Skipped: {reason}")

            else:
                # status == "error" or anything else from the laptop
                err = result.get("error") or result.get("reason") or str(result)
                logger.error(f"MT5 trade rejected: {err}")
                return ExecuteResult(success=False, error=f"MT5 error: {err}",
                                     is_connection_error=_is_connection_error(err))

    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
        err = f"Network error reaching laptop: {e}"
        logger.error(err)
        return ExecuteResult(success=False, error=err, is_connection_error=True)
    except Exception as e:
        err = f"Unexpected error: {e}"
        logger.error(err)
        return ExecuteResult(success=False, error=err,
                             is_connection_error=_is_connection_error(str(e)))


def _mark_signal_error(db, sig: TradeSignal, error: str):
    """Persist a failure reason on the signal row (non-fatal)."""
    try:
        sig.error_message = error
        sig.error_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        db.commit()
    except Exception as ex:
        logger.warning(f"Could not persist error on signal {sig.id}: {ex}")


def _mark_signal_executed(db, sig: TradeSignal):
    """Mark signal as executed (only call on genuine MT5 success)."""
    sig.executed = 1
    sig.error_message = None
    sig.error_at = None
    db.commit()


# ---------------------------------------------------------------------------
# Recovery loop
# ---------------------------------------------------------------------------

async def run_recovery(db):
    """
    Checks the signals table for unexecuted signals and processes them.
    Rules:
    - CLOSE signals: Always execute (retry indefinitely until laptop is online).
    - OPEN signals:  Execute only if < 5 minutes old.
    - Retry only on connection errors; genuine MT5 errors are recorded, not retried.
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
            "action": sig.action,
        }

        if sig.action == "OPEN":
            age = now - sig.timestamp
            if age > max_delay:
                logger.info(
                    f"Expired OPEN signal {sig.signal_order_id} (age: {age}). "
                    "Skipping — too old to trade."
                )
                _mark_signal_error(
                    db, sig,
                    f"Expired: signal was {int(age.total_seconds() // 60)} min old "
                    f"(max 5 min)."
                )
                # Permanently skip — don't retry again
                sig.executed = 1
                db.commit()
                continue

        result = await execute_on_laptop(db, signal_dict)

        if result.success:
            logger.info(f"Recovery: executed {sig.action} signal {sig.signal_order_id}")
            _mark_signal_executed(db, sig)
        elif result.skipped:
            # Intentional skip — record and don't retry
            _mark_signal_error(db, sig, result.error)
            sig.executed = 1
            db.commit()
        elif result.is_connection_error:
            # Keep executed=0 so the next heartbeat recovery will retry
            logger.warning(
                f"Connection error on {sig.action} signal {sig.signal_order_id}. "
                "Will retry on next heartbeat."
            )
            _mark_signal_error(db, sig, result.error)
        else:
            # Hard MT5 error (invalid volume, trade disabled, etc.) – record + skip
            logger.error(
                f"MT5 hard error on {sig.action} signal {sig.signal_order_id}: {result.error}"
            )
            _mark_signal_error(db, sig, result.error)
            # Leave executed=0 so admin can see it in the Errors page,
            # but mark skipped_permanent so recovery loop ignores it.
            # We do NOT set executed=1; it stays visible in Errors page.
            # We persist a special sentinel prefix so recovery won't loop forever.
            if result.error and not result.error.startswith("HARD|"):
                sig.error_message = f"HARD|{result.error}"
                db.commit()


# ---------------------------------------------------------------------------
# New-message handler
# ---------------------------------------------------------------------------

@client.on(events.NewMessage(chats=telegram_group_link))
async def handler(event):
    logger.info(f"Message received: {event.message.text[:50]}...")
    db = SessionLocal()
    try:
        allow_trading = settings_service.get(db, "allow_trading", True)
        if not allow_trading:
            return

        signal = parse_signal(event.message.text)
        if not signal:
            return

        # 1. Always LOG everything immediately to DB (executed=0)
        storage.log_signal(db, signal)

        # 2. Try to execute immediately
        result = await execute_on_laptop(db, signal)

        stored_sig = (
            db.query(TradeSignal)
            .filter(TradeSignal.signal_order_id == signal["signal_order_id"])
            .order_by(TradeSignal.id.desc())
            .first()
        )

        if not stored_sig:
            return

        if result.success:
            _mark_signal_executed(db, stored_sig)

        elif result.skipped:
            # Intentional skip — mark executed so recovery ignores it
            _mark_signal_error(db, stored_sig, result.error)
            stored_sig.executed = 1
            db.commit()

        elif result.is_connection_error:
            # Keep executed=0 → recovery loop will retry within 5-min window
            logger.warning(
                f"Connection error for new signal {signal['signal_order_id']}. "
                "Recovery will retry."
            )
            _mark_signal_error(db, stored_sig, result.error)

        else:
            # Hard MT5 error — record, leave for Errors page
            logger.error(
                f"Hard MT5 error for signal {signal['signal_order_id']}: {result.error}"
            )
            _mark_signal_error(db, stored_sig, f"HARD|{result.error}")

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Heartbeat loop
# ---------------------------------------------------------------------------

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
                                    margin_level=data.get("margin_level", 0.0),
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


# ---------------------------------------------------------------------------
# Entry-points
# ---------------------------------------------------------------------------

async def main():
    logger.info("Starting VPS Telegram listener...")
    await client.start()
    logger.info("Telegram client connected.")

    # Start Heartbeat loop
    asyncio.create_task(heartbeat_loop())

    await client.run_until_disconnected()


def start_telegram_listener():
    """
    Synchronous entry-point for running the Telegram listener inside a daemon thread.
    Creates its own event loop so it does not conflict with FastAPI's event loop.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()


if __name__ == "__main__":
    asyncio.run(main())
