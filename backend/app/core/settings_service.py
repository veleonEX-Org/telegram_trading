import logging
from sqlalchemy.orm import Session
from app.models.settings import Setting
from app.core.config import settings
from typing import Any

logger = logging.getLogger(__name__)

class SettingsService:
    @staticmethod
    def get(db: Session, key: str, default: Any = None) -> Any:
        try:
            db_setting = db.query(Setting).filter(Setting.key == key).first()
            if db_setting:
                return SettingsService._parse_value(db_setting.value)
        except Exception as e:
            logger.error(f"Error fetching setting {key} from database: {e}. Falling back to .env")
        
        # Fallback to env settings
        return getattr(settings, key, default)

    @staticmethod
    def get_all(db: Session) -> dict:
        result = {}
        try:
            db_settings = db.query(Setting).all()
            result = {s.key: SettingsService._parse_value(s.value) for s in db_settings}
        except Exception as e:
            logger.error(f"Error fetching all settings from database: {e}. Using .env defaults.")
        
        # Merge with/Fallback to env settings
        env_keys = [
             "telegram_group_link", "base_balance", "max_lot", 
             "magic_number", "min_balance_guard", "allow_trading"
        ]
        for key in env_keys:
            if key not in result:
                result[key] = getattr(settings, key)
        
        return result

    @staticmethod
    def set(db: Session, key: str, value: Any):
        try:
            db_setting = db.query(Setting).filter(Setting.key == key).first()
            str_value = str(value)
            if db_setting:
                db_setting.value = str_value
            else:
                db_setting = Setting(key=key, value=str_value)
                db.add(db_setting)
            db.commit()
        except Exception as e:
            logger.error(f"Error saving setting {key} to database: {e}")
            db.rollback()
            raise  # Re-throw for API to handle if needed, or handle silently

    @staticmethod
    def _parse_value(value: str) -> Any:
        if isinstance(value, (int, float, bool)):
            return value
        if not isinstance(value, str):
            return value
            
        val_lower = value.lower()
        if val_lower == "true":
            return True
        if val_lower == "false":
            return False
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

settings_service = SettingsService()
