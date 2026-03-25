from app.core.db import engine
from sqlalchemy import text

def migrate():
    print("Migrating database...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE balance_snapshots ADD COLUMN IF NOT EXISTS margin_level FLOAT DEFAULT 0.0"))
            conn.commit()
            print("Successfully added margin_level to balance_snapshots.")
        except Exception as e:
            print("Migration failed:", e)

if __name__ == "__main__":
    migrate()
