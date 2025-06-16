"""User settings model for persistent user preferences."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.user import User


class UserSettings(Base):
    """User settings model for persistent preferences."""

    __tablename__ = "user_settings"

    # Foreign key to user
    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True, index=True
    )

    # General Settings
    theme: Mapped[str] = mapped_column(
        String(20), default="Light", nullable=False
    )  # Light, Dark, Auto
    preferred_currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False
    )  # USD, EUR, GBP, JPY
    date_format: Mapped[str] = mapped_column(
        String(20), default="MM/DD/YYYY", nullable=False
    )  # MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Data Source Settings
    preferred_data_provider: Mapped[str] = mapped_column(
        String(50), default="auto", nullable=False
    )  # auto, yfinance, alpha_vantage, finnhub
    price_update_frequency: Mapped[int] = mapped_column(
        Integer, default=15, nullable=False
    )  # Minutes
    enable_real_time_updates: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Dashboard Settings
    default_dashboard_view: Mapped[str] = mapped_column(
        String(50), default="overview", nullable=False
    )  # overview, positions, analytics
    items_per_page: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    show_advanced_metrics: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Notification Settings
    email_notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    notification_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    performance_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    news_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    daily_summary_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Alert Thresholds
    price_change_threshold: Mapped[float | None] = mapped_column(
        nullable=True
    )  # Percentage change to trigger alert
    portfolio_change_threshold: Mapped[float | None] = mapped_column(
        nullable=True
    )  # Portfolio percentage change to trigger alert

    # Privacy Settings
    share_portfolio_data: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    enable_analytics_tracking: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Chart and Display Settings
    chart_theme: Mapped[str] = mapped_column(
        String(20), default="plotly", nullable=False
    )  # plotly, seaborn, custom
    default_chart_period: Mapped[str] = mapped_column(
        String(10), default="1M", nullable=False
    )  # 1D, 1W, 1M, 3M, 6M, 1Y, YTD, MAX
    show_percentage_changes: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_market_hours_only: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Custom Settings (JSON stored as text)
    custom_dashboard_layout: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON string for custom layouts
    watchlist_settings: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON string for watchlist preferences
    alert_preferences: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON string for detailed alert settings

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id}, currency={self.preferred_currency}, theme={self.theme})>"

    @classmethod
    def get_default_settings(cls) -> dict:
        """Get default settings as a dictionary."""
        return {
            "theme": "Light",
            "preferred_currency": "USD",
            "date_format": "MM/DD/YYYY",
            "timezone": "UTC",
            "preferred_data_provider": "auto",
            "price_update_frequency": 15,
            "enable_real_time_updates": True,
            "default_dashboard_view": "overview",
            "items_per_page": 20,
            "show_advanced_metrics": False,
            "email_notifications_enabled": False,
            "notification_email": None,
            "price_alerts_enabled": False,
            "performance_alerts_enabled": False,
            "news_alerts_enabled": False,
            "daily_summary_enabled": False,
            "price_change_threshold": 5.0,
            "portfolio_change_threshold": 2.0,
            "share_portfolio_data": False,
            "enable_analytics_tracking": True,
            "chart_theme": "plotly",
            "default_chart_period": "1M",
            "show_percentage_changes": True,
            "show_market_hours_only": False,
            "custom_dashboard_layout": None,
            "watchlist_settings": None,
            "alert_preferences": None,
        }

    def to_dict(self) -> dict:
        """Convert settings to dictionary format."""
        return {
            "user_id": self.user_id,
            "theme": self.theme,
            "preferred_currency": self.preferred_currency,
            "date_format": self.date_format,
            "timezone": self.timezone,
            "preferred_data_provider": self.preferred_data_provider,
            "price_update_frequency": self.price_update_frequency,
            "enable_real_time_updates": self.enable_real_time_updates,
            "default_dashboard_view": self.default_dashboard_view,
            "items_per_page": self.items_per_page,
            "show_advanced_metrics": self.show_advanced_metrics,
            "email_notifications_enabled": self.email_notifications_enabled,
            "notification_email": self.notification_email,
            "price_alerts_enabled": self.price_alerts_enabled,
            "performance_alerts_enabled": self.performance_alerts_enabled,
            "news_alerts_enabled": self.news_alerts_enabled,
            "daily_summary_enabled": self.daily_summary_enabled,
            "price_change_threshold": self.price_change_threshold,
            "portfolio_change_threshold": self.portfolio_change_threshold,
            "share_portfolio_data": self.share_portfolio_data,
            "enable_analytics_tracking": self.enable_analytics_tracking,
            "chart_theme": self.chart_theme,
            "default_chart_period": self.default_chart_period,
            "show_percentage_changes": self.show_percentage_changes,
            "show_market_hours_only": self.show_market_hours_only,
            "custom_dashboard_layout": self.custom_dashboard_layout,
            "watchlist_settings": self.watchlist_settings,
            "alert_preferences": self.alert_preferences,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def update_from_dict(self, settings_dict: dict) -> None:
        """Update settings from dictionary."""
        for key, value in settings_dict.items():
            if hasattr(self, key) and key not in [
                "id",
                "user_id",
                "created_at",
                "updated_at",
            ]:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
