"""Configuration settings for the Financial Dashboard backend."""

from functools import lru_cache

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
    database_url: str = "postgresql://localhost:5432/financial_dashboard"  # Set DB credentials via DATABASE_URL env var
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
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
