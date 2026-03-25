
from app.core.db import engine
from sqlalchemy import text
import time

print("Stress testing connectivity...")
with engine.connect() as conn:
    for i in range(10):
        start = time.time()
        result = conn.execute(text('SELECT 1'))
        val = result.scalar()
        end = time.time()
        print(f"Query {i}: {end-start:.4f}s")
