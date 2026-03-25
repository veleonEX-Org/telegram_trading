from fastapi import FastAPI
from app.core.db import engine, Base
from app.models.trade import Trade
from app.models.balance import BalanceSnapshot
from app.models.settings import Setting
from app.api.trades import router as trades_router
from app.api.performance import router as performance_router
from app.api.settings import router as settings_router
from app.api.system import router as system_router
from app.api.tradingheart import router as tradingheart_router
from app.telegram.listener import start_telegram_listener
import threading

from app.core.config import settings
from app.models.settings import Setting
from app.models.tradingheart import TradingHeart
from app.core.db import SessionLocal

# Initialize Database
def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed settings if empty
    db = SessionLocal()
    try:
        print("Database seeded with missing settings.")
        existing_keys = [s.key for s in db.query(Setting.key).all()]
        controllable_settings = [
            ("telegram_group_link", settings.telegram_group_link),
            ("base_balance", str(settings.base_balance)),
            ("max_lot", str(settings.max_lot)),
            ("magic_number", str(settings.magic_number)),
            ("min_balance_guard", str(settings.min_balance_guard)),
            ("allow_trading", str(settings.allow_trading)),
            ("notification_email", settings.notification_email),
        ]
        
        for key, value in controllable_settings:
            if key not in existing_keys:
                db.add(Setting(key=key, value=value))
        
        db.commit()
        if any(key not in existing_keys for key, _ in controllable_settings):
            print("Database seeded with missing settings.")
    finally:
        db.close()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(trades_router, prefix="/api/trades")
app.include_router(performance_router, prefix="/api/performance")
app.include_router(settings_router, prefix="/api/settings")
app.include_router(system_router, prefix="/api/system")
app.include_router(tradingheart_router, prefix="/api/tradingheart")

import asyncio
from app.core.monitor import connection_monitor_loop

@app.on_event("startup")
async def on_startup():
    try:
        init_db()
        # Start background tasks
        asyncio.create_task(connection_monitor_loop())
    except Exception as e:
        print("⚠️ Database unavailable:", e)

    # Launch Telegram listener in a background daemon thread
    thread = threading.Thread(target=start_telegram_listener, daemon=True, name="telegram-listener")
    thread.start()
    print("✅ Telegram listener thread started.")

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
