
from app.core.db import SessionLocal
from app.trading.performance import performance_summary
import time

print("Starting performance summary calculation...")
db = SessionLocal()
try:
    start = time.time()
    # Mocking the caller's request
    res = performance_summary(db)
    end = time.time()
    print(f"Success! Result: {res} (took {end-start:.2f}s)")
finally:
    db.close()
