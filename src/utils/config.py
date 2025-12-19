"""Config settings."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App config."""

    # MongoDB - Connect to mongos router for sharded cluster
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017  # mongos port
    mongodb_username: str = ""  # No auth for local dev
    mongodb_password: str = ""
    mongodb_database: str = "startup_analytics"
    mongodb_auth_source: str = "admin"

    log_level: str = "INFO"
    data_dir: Path = Path("./data")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


_settings: Optional[Settings] = None


def get_config() -> Settings:
    """Get config (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


