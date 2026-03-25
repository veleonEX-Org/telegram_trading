import json
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.trade import Trade, TradeSignal

class Storage:
    def __init__(self):
        self.fallback_file = Path(settings.fallback_json_path)
        self.fallback_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.fallback_file.exists():
            self.fallback_file.write_text(json.dumps([]))

    def log_trade(self, db: Session, trade_data: dict):
        trade_data["logged_at"] = datetime.utcnow().isoformat()

        try:
            self._log_to_db(db, trade_data)
        except Exception:
            self._log_to_json(trade_data)

    def log_signal(self, db: Session, signal_data: dict):
        """Log the signal to the database for later processing."""
        try:
            self._log_signal_to_db(db, signal_data)
            return True
        except Exception:
            # Maybe add a fallback logging for signals as well
            return False

    def _log_to_db(self, db: Session, trade_data: dict):
        # Remove keys that are not in the model if necessary, 
        # but here we assume trade_data matches Trade model
        # We need to filter trade_data to only include valid Trade columns
        valid_keys = Trade.__table__.columns.keys()
        filtered_data = {k: v for k, v in trade_data.items() if k in valid_keys}
        trade = Trade(**filtered_data)
        db.add(trade)
        db.commit()

    def _log_signal_to_db(self, db: Session, signal_data: dict):
        valid_keys = TradeSignal.__table__.columns.keys()
        filtered_data = {k: v for k, v in signal_data.items() if k in valid_keys}
        signal = TradeSignal(**filtered_data)
        db.add(signal)
        db.commit()

    def _log_to_json(self, trade_data: dict):
        data = json.loads(self.fallback_file.read_text())
        data.append(trade_data)
        self.fallback_file.write_text(json.dumps(data, indent=2))
