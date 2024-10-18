from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    telegram_token: str
    database_url: str
    envirement: str
    caxap: str
    postgres_user: str
    pguser: str
    postgres_db: str
    postgres_password: str
    database_url: str
    ozon_seller_client_id: Optional[str]
    ozon_seller_token: Optional[str]
    ozon_performance_client_id: Optional[str]
    ozon_performance_token: Optional[str]
    google_sheets_api_token: Optional[str]
    timezone: str = "Europe/Moscow"

    model_config = SettingsConfigDict(env_file="local.env", env_file_encoding="utf-8")


# Создание экземпляра настроек
settings = Settings()
