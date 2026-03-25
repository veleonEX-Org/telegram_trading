
import sqlalchemy
from app.core.db import engine
from sqlalchemy import text
import time

print("Starting connectivity test...")
try:
    with engine.connect() as conn:
        start = time.time()
        result = conn.execute(text('SELECT 1'))
        val = result.scalar()
        end = time.time()
        print(f"Success! Result: {val} (took {end-start:.2f}s)")
except Exception as e:
    print(f"Error: {e}")
