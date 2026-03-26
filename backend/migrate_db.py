from app.core.db import engine
from sqlalchemy import text

def migrate():
    print("Migrating database...")
    with engine.connect() as conn:
        migrations = [
            (
                "ALTER TABLE balance_snapshots ADD COLUMN IF NOT EXISTS margin_level FLOAT DEFAULT 0.0",
                "Added margin_level to balance_snapshots."
            ),
            (
                "ALTER TABLE trade_signals ADD COLUMN IF NOT EXISTS error_message TEXT",
                "Added error_message to trade_signals."
            ),
            (
                "ALTER TABLE trade_signals ADD COLUMN IF NOT EXISTS error_at TIMESTAMP",
                "Added error_at to trade_signals."
            ),
        ]
        for sql, label in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"SUCCESS: {label}")
            except Exception as e:
                print(f"SKIPPED ({label}): {e}")

if __name__ == "__main__":
    migrate()
