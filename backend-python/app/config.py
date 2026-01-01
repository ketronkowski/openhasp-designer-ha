"""Configuration management for the backend."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    ha_url: str = "https://ha-nh.tronkowski.org"
    ha_token: str
    ha_config_path: str = "/config/openhasp"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
