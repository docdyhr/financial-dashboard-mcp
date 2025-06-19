"""Configuration settings for the Financial Dashboard backend."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Financial Dashboard API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_host: str = "0.0.0.0"  # nosec
    api_port: int = 8000
    api_reload: bool = True

    # Database
    database_url: str = (
        "postgresql://localhost:5432/financial_dashboard"  # Set DB credentials via DATABASE_URL env var
    )
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Security
    secret_key: str  # Required - must be set via SECRET_KEY env var
    access_token_expire_minutes: int = 43200  # 30 days

    # CORS
    cors_origins: list[str] = ["http://localhost:8501", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Market Data
    alpha_vantage_api_key: str | None = None
    yfinance_start_date: str = "2020-01-01"
    finnhub_api_key: str | None = None

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # Streamlit Configuration
    streamlit_server_port: int = 8501
    streamlit_server_address: str = "localhost"

    # MCP Server Configuration
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8502
    mcp_auth_token: str | None = None  # Set via MCP_AUTH_TOKEN env var

    # Flower UI Configuration
    flower_username: str = "flower"  # Set via FLOWER_USERNAME env var
    flower_password: str | None = None  # Required - set via FLOWER_PASSWORD env var

    # Celery Beat Schedule (in seconds)
    market_data_update_interval: int = 300
    portfolio_snapshot_interval: int = 3600

    @model_validator(mode="after")
    def validate_production_settings(self):
        """Validate critical settings for production environment."""
        if self.environment == "production":
            if self.secret_key == "":
                raise ValueError("SECRET_KEY must be set in production")
            if self.flower_password is None:
                raise ValueError("FLOWER_PASSWORD must be set in production")
            if self.debug:
                raise ValueError("Debug mode must be disabled in production")
        elif self.environment == "development":
            # Allow all origins in development for Claude Desktop access
            self.cors_origins = ["*"]
        return self


def read_secret_file(secret_name: str) -> str | None:
    """Read secret from Docker secret file or environment variable."""
    # First try environment variable with _FILE suffix
    file_path = os.getenv(f"{secret_name}_FILE")
    if file_path and Path(file_path).exists():
        return Path(file_path).read_text().strip()

    # Fall back to regular environment variable
    return os.getenv(secret_name)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance with Docker secrets support."""
    # Override specific settings from Docker secrets if available
    overrides = {}

    secret_key = read_secret_file("SECRET_KEY")
    if secret_key:
        overrides["secret_key"] = secret_key

    database_url = read_secret_file("DATABASE_URL")
    if database_url:
        overrides["database_url"] = database_url

    flower_password = read_secret_file("FLOWER_PASSWORD")
    if flower_password:
        overrides["flower_password"] = flower_password

    mcp_auth_token = read_secret_file("MCP_AUTH_TOKEN")
    if mcp_auth_token:
        overrides["mcp_auth_token"] = mcp_auth_token

    return Settings(**overrides)
