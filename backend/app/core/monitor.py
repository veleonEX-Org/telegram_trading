import asyncio
import logging
from datetime import datetime, timezone, timedelta
from app.core.db import SessionLocal
from app.core.settings_service import settings_service
from app.core.notifications import send_notification_email

logger = logging.getLogger(__name__)

# State trackers to avoid flooding email
last_alert_states = {
    "telegram": True,  # True means was last seen connected
    "mt5": True
}

async def connection_monitor_loop():
    """
    Background loop to check heartbeats and send notifications on disruption.
    """
    logger.info("Connection monitoring background task started.")
    
    # Wait a bit on startup to allow everything to connect
    await asyncio.sleep(30) 
    
    while True:
        try:
            db = SessionLocal()
            try:
                # Fetch heartbeats from database
                telegram_hb_str = settings_service.get(db, "telegram_heartbeat", None)
                mt5_hb_str = settings_service.get(db, "mt5_heartbeat", None)
                
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                threshold = timedelta(seconds=90) # slightly longer than the 60s dashboard check
                
                # Check Telegram
                telegram_connected = False
                if telegram_hb_str:
                    try:
                        telegram_hb = datetime.fromisoformat(telegram_hb_str).replace(tzinfo=None)
                        if now - telegram_hb < threshold:
                            telegram_connected = True
                    except ValueError:
                        pass
                
                # Alert if Telegram went from connected to disconnected
                if not telegram_connected and last_alert_states["telegram"]:
                    logger.warning("Telegram disruption detected! Sending email...")
                    send_notification_email(
                        "DISRUPTION: Telegram Listener Offline",
                        f"Disruption detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\nThe Telegram listener is no longer sending heartbeats. Please check the backend terminal."
                    )
                    last_alert_states["telegram"] = False
                elif telegram_connected and not last_alert_states["telegram"]:
                    # Optional: notify on recovery
                    logger.info("Telegram connection restored.")
                    last_alert_states["telegram"] = True

                # Check MT5
                mt5_connected = False
                if mt5_hb_str:
                    try:
                        mt5_hb = datetime.fromisoformat(mt5_hb_str).replace(tzinfo=None)
                        if now - mt5_hb < threshold:
                            mt5_connected = True
                    except ValueError:
                        pass

                # Alert if MT5 went from connected to disconnected
                if not mt5_connected and last_alert_states["mt5"]:
                    logger.warning("MT5 disruption detected! Sending email...")
                    send_notification_email(
                        "DISRUPTION: MetaTrader 5 Disconnected",
                        f"Disruption detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\nMetaTrader 5 node is no longer sending heartbeats or is offline. Please check your MT5 terminal and account connection."
                    )
                    last_alert_states["mt5"] = False
                elif mt5_connected and not last_alert_states["mt5"]:
                    logger.info("MT5 connection restored.")
                    last_alert_states["mt5"] = True
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in connection monitor loop: {e}")
            
        await asyncio.sleep(60) # check once per minute
