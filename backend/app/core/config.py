from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Telegram
    telegram_group_link: str
    telegram_api_id: str = "YOUR_ID"
    telegram_api_hash: str = "YOUR_HASH"
    telegram_session_string: str = ""  # Set on Render to avoid ephemeral filesystem issues

    # Trading logic
    base_balance: float = 1000.0
    max_lot: float = 1.0
    magic_number: int = 202512
    min_balance_guard: float = 200.0
    laptop_api_base_url: str = "http://localhost:8000"

    # System
    allow_trading: bool = True
    use_signal_lot: bool = False

    # Storage
    fallback_json_path: str = "backend/data/fallback_store.json"

    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/trade_copier"

    # SMTP Notifications
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False
    )


settings = Settings()
