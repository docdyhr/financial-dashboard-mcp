"""User settings schemas for API requests and responses."""

from typing import Any

from pydantic import Field, field_validator

from backend.schemas.base import BaseSchema, TimestampMixin


class UserSettingsBase(BaseSchema):
    """Base user settings schema with common fields."""

    # General Settings
    theme: str = Field(default="Light", description="UI theme")
    preferred_currency: str = Field(default="USD", description="Default currency")
    date_format: str = Field(default="MM/DD/YYYY", description="Date format preference")
    timezone: str = Field(default="UTC", description="User timezone")

    # Data Source Settings
    preferred_data_provider: str = Field(
        default="auto", description="Preferred market data provider"
    )
    price_update_frequency: int = Field(
        default=15, ge=1, le=60, description="Price update frequency in minutes"
    )
    enable_real_time_updates: bool = Field(
        default=True, description="Enable real-time price updates"
    )

    # Dashboard Settings
    default_dashboard_view: str = Field(
        default="overview", description="Default dashboard view"
    )
    items_per_page: int = Field(default=20, ge=10, le=100, description="Items per page")
    show_advanced_metrics: bool = Field(
        default=False, description="Show advanced portfolio metrics"
    )

    # Notification Settings
    email_notifications_enabled: bool = Field(
        default=False, description="Enable email notifications"
    )
    notification_email: str | None = Field(
        None, description="Notification email address"
    )
    price_alerts_enabled: bool = Field(default=False, description="Enable price alerts")
    performance_alerts_enabled: bool = Field(
        default=False, description="Enable performance alerts"
    )
    news_alerts_enabled: bool = Field(default=False, description="Enable news alerts")
    daily_summary_enabled: bool = Field(
        default=False, description="Enable daily portfolio summary"
    )

    # Alert Thresholds
    price_change_threshold: float | None = Field(
        None, ge=0, le=100, description="Price change threshold percentage"
    )
    portfolio_change_threshold: float | None = Field(
        None, ge=0, le=100, description="Portfolio change threshold percentage"
    )

    # Privacy Settings
    share_portfolio_data: bool = Field(
        default=False, description="Allow sharing portfolio data"
    )
    enable_analytics_tracking: bool = Field(
        default=True, description="Enable analytics tracking"
    )

    # Chart and Display Settings
    chart_theme: str = Field(default="plotly", description="Chart theme")
    default_chart_period: str = Field(
        default="1M", description="Default chart time period"
    )
    show_percentage_changes: bool = Field(
        default=True, description="Show percentage changes"
    )
    show_market_hours_only: bool = Field(
        default=False, description="Show market hours only"
    )

    # Custom Settings
    custom_dashboard_layout: str | None = Field(
        None, description="Custom dashboard layout JSON"
    )
    watchlist_settings: str | None = Field(
        None, description="Watchlist settings JSON"
    )
    alert_preferences: str | None = Field(None, description="Alert preferences JSON")

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme option."""
        allowed_themes = ["Light", "Dark", "Auto"]
        if v not in allowed_themes:
            raise ValueError(f"Theme must be one of: {allowed_themes}")
        return v

    @field_validator("preferred_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        allowed_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"]
        if v not in allowed_currencies:
            raise ValueError(f"Currency must be one of: {allowed_currencies}")
        return v

    @field_validator("date_format")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format."""
        allowed_formats = ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"]
        if v not in allowed_formats:
            raise ValueError(f"Date format must be one of: {allowed_formats}")
        return v

    @field_validator("preferred_data_provider")
    @classmethod
    def validate_data_provider(cls, v: str) -> str:
        """Validate data provider."""
        allowed_providers = ["auto", "yfinance", "alpha_vantage", "finnhub"]
        if v not in allowed_providers:
            raise ValueError(f"Data provider must be one of: {allowed_providers}")
        return v

    @field_validator("default_dashboard_view")
    @classmethod
    def validate_dashboard_view(cls, v: str) -> str:
        """Validate dashboard view."""
        allowed_views = ["overview", "positions", "analytics", "tasks"]
        if v not in allowed_views:
            raise ValueError(f"Dashboard view must be one of: {allowed_views}")
        return v

    @field_validator("chart_theme")
    @classmethod
    def validate_chart_theme(cls, v: str) -> str:
        """Validate chart theme."""
        allowed_themes = ["plotly", "seaborn", "custom"]
        if v not in allowed_themes:
            raise ValueError(f"Chart theme must be one of: {allowed_themes}")
        return v

    @field_validator("default_chart_period")
    @classmethod
    def validate_chart_period(cls, v: str) -> str:
        """Validate chart period."""
        allowed_periods = ["1D", "1W", "1M", "3M", "6M", "1Y", "YTD", "MAX"]
        if v not in allowed_periods:
            raise ValueError(f"Chart period must be one of: {allowed_periods}")
        return v

    @field_validator("notification_email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format."""
        if v is not None and v.strip():
            import re

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, v):
                raise ValueError("Invalid email format")
        return v


class UserSettingsCreate(UserSettingsBase):
    """Schema for creating user settings."""

    user_id: int = Field(..., gt=0, description="User ID")


class UserSettingsUpdate(BaseSchema):
    """Schema for updating user settings (all fields optional)."""

    # General Settings
    theme: str | None = None
    preferred_currency: str | None = None
    date_format: str | None = None
    timezone: str | None = None

    # Data Source Settings
    preferred_data_provider: str | None = None
    price_update_frequency: int | None = Field(None, ge=1, le=60)
    enable_real_time_updates: bool | None = None

    # Dashboard Settings
    default_dashboard_view: str | None = None
    items_per_page: int | None = Field(None, ge=10, le=100)
    show_advanced_metrics: bool | None = None

    # Notification Settings
    email_notifications_enabled: bool | None = None
    notification_email: str | None = None
    price_alerts_enabled: bool | None = None
    performance_alerts_enabled: bool | None = None
    news_alerts_enabled: bool | None = None
    daily_summary_enabled: bool | None = None

    # Alert Thresholds
    price_change_threshold: float | None = Field(None, ge=0, le=100)
    portfolio_change_threshold: float | None = Field(None, ge=0, le=100)

    # Privacy Settings
    share_portfolio_data: bool | None = None
    enable_analytics_tracking: bool | None = None

    # Chart and Display Settings
    chart_theme: str | None = None
    default_chart_period: str | None = None
    show_percentage_changes: bool | None = None
    show_market_hours_only: bool | None = None

    # Custom Settings
    custom_dashboard_layout: str | None = None
    watchlist_settings: str | None = None
    alert_preferences: str | None = None

    # Apply the same validators for non-None values
    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str | None) -> str | None:
        if v is not None:
            allowed_themes = ["Light", "Dark", "Auto"]
            if v not in allowed_themes:
                raise ValueError(f"Theme must be one of: {allowed_themes}")
        return v

    @field_validator("preferred_currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is not None:
            allowed_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"]
            if v not in allowed_currencies:
                raise ValueError(f"Currency must be one of: {allowed_currencies}")
        return v

    @field_validator("date_format")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        if v is not None:
            allowed_formats = ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"]
            if v not in allowed_formats:
                raise ValueError(f"Date format must be one of: {allowed_formats}")
        return v

    @field_validator("preferred_data_provider")
    @classmethod
    def validate_data_provider(cls, v: str | None) -> str | None:
        if v is not None:
            allowed_providers = ["auto", "yfinance", "alpha_vantage", "finnhub"]
            if v not in allowed_providers:
                raise ValueError(f"Data provider must be one of: {allowed_providers}")
        return v

    @field_validator("default_dashboard_view")
    @classmethod
    def validate_dashboard_view(cls, v: str | None) -> str | None:
        if v is not None:
            allowed_views = ["overview", "positions", "analytics", "tasks"]
            if v not in allowed_views:
                raise ValueError(f"Dashboard view must be one of: {allowed_views}")
        return v

    @field_validator("chart_theme")
    @classmethod
    def validate_chart_theme(cls, v: str | None) -> str | None:
        if v is not None:
            allowed_themes = ["plotly", "seaborn", "custom"]
            if v not in allowed_themes:
                raise ValueError(f"Chart theme must be one of: {allowed_themes}")
        return v

    @field_validator("default_chart_period")
    @classmethod
    def validate_chart_period(cls, v: str | None) -> str | None:
        if v is not None:
            allowed_periods = ["1D", "1W", "1M", "3M", "6M", "1Y", "YTD", "MAX"]
            if v not in allowed_periods:
                raise ValueError(f"Chart period must be one of: {allowed_periods}")
        return v

    @field_validator("notification_email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            import re

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, v):
                raise ValueError("Invalid email format")
        return v


class UserSettingsResponse(UserSettingsBase, TimestampMixin):
    """Schema for user settings response."""

    id: int = Field(..., description="Settings ID")
    user_id: int = Field(..., description="User ID")


class UserSettingsBulkUpdate(BaseSchema):
    """Schema for bulk updating multiple settings."""

    settings: dict[str, Any] = Field(..., description="Settings to update")

    @field_validator("settings")
    @classmethod
    def validate_settings_dict(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate that all keys are valid setting names."""
        valid_keys = {
            "theme",
            "preferred_currency",
            "date_format",
            "timezone",
            "preferred_data_provider",
            "price_update_frequency",
            "enable_real_time_updates",
            "default_dashboard_view",
            "items_per_page",
            "show_advanced_metrics",
            "email_notifications_enabled",
            "notification_email",
            "price_alerts_enabled",
            "performance_alerts_enabled",
            "news_alerts_enabled",
            "daily_summary_enabled",
            "price_change_threshold",
            "portfolio_change_threshold",
            "share_portfolio_data",
            "enable_analytics_tracking",
            "chart_theme",
            "default_chart_period",
            "show_percentage_changes",
            "show_market_hours_only",
            "custom_dashboard_layout",
            "watchlist_settings",
            "alert_preferences",
        }

        invalid_keys = set(v.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid setting keys: {invalid_keys}")

        return v


class UserSettingsPreferences(BaseSchema):
    """Simplified schema for frontend preferences."""

    # Core preferences for frontend
    theme: str = "Light"
    currency: str = "USD"
    date_format: str = "MM/DD/YYYY"
    provider: str = "auto"
    frequency: int = 15
    email_enabled: bool = False
    email: str | None = None
    price_alerts: bool = False
    performance_alerts: bool = False
    news_alerts: bool = False
