"""User settings service for business logic and database operations."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.models.user_settings import UserSettings
from backend.schemas.user_settings import UserSettingsCreate, UserSettingsUpdate

logger = logging.getLogger(__name__)


class UserSettingsService:
    """Service for managing user settings."""

    def get_user_settings(self, db: Session, user_id: int) -> UserSettings | None:
        """Get user settings by user ID."""
        try:
            return (
                db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            )
        except Exception as e:
            logger.error(f"Error getting user settings for user {user_id}: {e}")
            raise

    def create_user_settings(
        self, db: Session, settings_create: UserSettingsCreate
    ) -> UserSettings:
        """Create new user settings."""
        try:
            # Check if settings already exist
            existing = self.get_user_settings(db, settings_create.user_id)
            if existing:
                raise ValueError(
                    f"Settings already exist for user {settings_create.user_id}"
                )

            # Create new settings
            settings_data = settings_create.model_dump()
            settings = UserSettings(**settings_data)

            db.add(settings)
            db.commit()
            db.refresh(settings)

            logger.info(f"Created user settings for user {settings_create.user_id}")
            return settings

        except Exception as e:
            logger.error(f"Error creating user settings: {e}")
            db.rollback()
            raise

    def update_user_settings(
        self, db: Session, user_id: int, settings_update: UserSettingsUpdate
    ) -> UserSettings | None:
        """Update user settings."""
        try:
            settings = self.get_user_settings(db, user_id)
            if not settings:
                # Create default settings if none exist
                default_settings = UserSettingsCreate(
                    user_id=user_id, **UserSettings.get_default_settings()
                )
                settings = self.create_user_settings(db, default_settings)

            # Update only provided fields
            update_data = settings_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(settings, field):
                    setattr(settings, field, value)

            settings.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(settings)

            logger.info(f"Updated user settings for user {user_id}")
            return settings

        except Exception as e:
            logger.error(f"Error updating user settings for user {user_id}: {e}")
            db.rollback()
            raise

    def bulk_update_user_settings(
        self, db: Session, user_id: int, settings_dict: dict[str, Any]
    ) -> UserSettings | None:
        """Bulk update multiple settings at once."""
        try:
            settings = self.get_user_settings(db, user_id)
            if not settings:
                # Create default settings if none exist
                default_settings = UserSettingsCreate(
                    user_id=user_id, **UserSettings.get_default_settings()
                )
                settings = self.create_user_settings(db, default_settings)

            # Update settings from dictionary
            settings.update_from_dict(settings_dict)

            db.commit()
            db.refresh(settings)

            logger.info(
                f"Bulk updated {len(settings_dict)} settings for user {user_id}"
            )
            return settings

        except Exception as e:
            logger.error(f"Error bulk updating user settings for user {user_id}: {e}")
            db.rollback()
            raise

    def delete_user_settings(self, db: Session, user_id: int) -> bool:
        """Delete user settings."""
        try:
            settings = self.get_user_settings(db, user_id)
            if not settings:
                return False

            db.delete(settings)
            db.commit()

            logger.info(f"Deleted user settings for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting user settings for user {user_id}: {e}")
            db.rollback()
            raise

    def reset_to_defaults(self, db: Session, user_id: int) -> UserSettings:
        """Reset user settings to defaults."""
        try:
            # Delete existing settings if they exist
            existing = self.get_user_settings(db, user_id)
            if existing:
                db.delete(existing)

            # Create new default settings
            default_settings = UserSettingsCreate(
                user_id=user_id, **UserSettings.get_default_settings()
            )
            settings = UserSettings(**default_settings.model_dump())

            db.add(settings)
            db.commit()
            db.refresh(settings)

            logger.info(f"Reset user settings to defaults for user {user_id}")
            return settings

        except Exception as e:
            logger.error(f"Error resetting user settings for user {user_id}: {e}")
            db.rollback()
            raise

    def get_setting_value(
        self, db: Session, user_id: int, setting_name: str, default: Any = None
    ) -> Any:
        """Get a specific setting value."""
        try:
            settings = self.get_user_settings(db, user_id)
            if not settings:
                return default

            return getattr(settings, setting_name, default)

        except Exception as e:
            logger.error(
                f"Error getting setting {setting_name} for user {user_id}: {e}"
            )
            return default

    def update_setting_value(
        self, db: Session, user_id: int, setting_name: str, value: Any
    ) -> bool:
        """Update a specific setting value."""
        try:
            settings = self.get_user_settings(db, user_id)
            if not settings:
                # Create default settings if none exist
                default_settings = UserSettingsCreate(
                    user_id=user_id, **UserSettings.get_default_settings()
                )
                settings = self.create_user_settings(db, default_settings)

            if hasattr(settings, setting_name):
                setattr(settings, setting_name, value)
                settings.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(settings)

                logger.info(f"Updated setting {setting_name} for user {user_id}")
                return True
            logger.warning(f"Setting {setting_name} does not exist")
            return False

        except Exception as e:
            logger.error(
                f"Error updating setting {setting_name} for user {user_id}: {e}"
            )
            db.rollback()
            raise

    def get_user_currency(self, db: Session, user_id: int) -> str:
        """Get user's preferred currency."""
        return self.get_setting_value(db, user_id, "preferred_currency", "USD")

    def get_user_timezone(self, db: Session, user_id: int) -> str:
        """Get user's preferred timezone."""
        return self.get_setting_value(db, user_id, "timezone", "UTC")

    def get_user_theme(self, db: Session, user_id: int) -> str:
        """Get user's preferred theme."""
        return self.get_setting_value(db, user_id, "theme", "Light")

    def get_user_date_format(self, db: Session, user_id: int) -> str:
        """Get user's preferred date format."""
        return self.get_setting_value(db, user_id, "date_format", "MM/DD/YYYY")

    def get_price_update_frequency(self, db: Session, user_id: int) -> int:
        """Get user's price update frequency in minutes."""
        return self.get_setting_value(db, user_id, "price_update_frequency", 15)

    def get_preferred_data_provider(self, db: Session, user_id: int) -> str:
        """Get user's preferred data provider."""
        return self.get_setting_value(db, user_id, "preferred_data_provider", "auto")

    def is_email_notifications_enabled(self, db: Session, user_id: int) -> bool:
        """Check if email notifications are enabled for user."""
        return self.get_setting_value(db, user_id, "email_notifications_enabled", False)

    def get_notification_email(self, db: Session, user_id: int) -> str | None:
        """Get user's notification email address."""
        return self.get_setting_value(db, user_id, "notification_email", None)

    def are_price_alerts_enabled(self, db: Session, user_id: int) -> bool:
        """Check if price alerts are enabled for user."""
        return self.get_setting_value(db, user_id, "price_alerts_enabled", False)

    def get_price_change_threshold(self, db: Session, user_id: int) -> float | None:
        """Get user's price change alert threshold."""
        return self.get_setting_value(db, user_id, "price_change_threshold", 5.0)

    def get_portfolio_change_threshold(
        self, db: Session, user_id: int
    ) -> float | None:
        """Get user's portfolio change alert threshold."""
        return self.get_setting_value(db, user_id, "portfolio_change_threshold", 2.0)

    def format_currency(self, db: Session, user_id: int, amount: float) -> str:
        """Format currency amount according to user preferences."""
        try:
            currency = self.get_user_currency(db, user_id)

            # Currency symbols mapping
            symbols = {
                "USD": "$",
                "EUR": "€",
                "GBP": "£",
                "JPY": "¥",
                "CAD": "C$",
                "AUD": "A$",
                "CHF": "CHF",
            }

            symbol = symbols.get(currency, "$")

            # Format based on currency
            if currency == "JPY":
                # Japanese Yen doesn't use decimal places
                return f"{symbol}{amount:,.0f}"
            return f"{symbol}{amount:,.2f}"

        except Exception as e:
            logger.error(f"Error formatting currency for user {user_id}: {e}")
            return f"${amount:,.2f}"  # Fallback to USD format

    def format_date(self, db: Session, user_id: int, date_obj: datetime) -> str:
        """Format date according to user preferences."""
        try:
            date_format = self.get_user_date_format(db, user_id)

            format_mapping = {
                "MM/DD/YYYY": "%m/%d/%Y",
                "DD/MM/YYYY": "%d/%m/%Y",
                "YYYY-MM-DD": "%Y-%m-%d",
            }

            format_str = format_mapping.get(date_format, "%m/%d/%Y")
            return date_obj.strftime(format_str)

        except Exception as e:
            logger.error(f"Error formatting date for user {user_id}: {e}")
            return date_obj.strftime("%m/%d/%Y")  # Fallback format

    def get_dashboard_config(self, db: Session, user_id: int) -> dict[str, Any]:
        """Get dashboard configuration for user."""
        try:
            settings = self.get_user_settings(db, user_id)
            if not settings:
                settings = self.reset_to_defaults(db, user_id)

            return {
                "theme": settings.theme,
                "currency": settings.preferred_currency,
                "date_format": settings.date_format,
                "timezone": settings.timezone,
                "default_view": settings.default_dashboard_view,
                "items_per_page": settings.items_per_page,
                "show_advanced_metrics": settings.show_advanced_metrics,
                "chart_theme": settings.chart_theme,
                "default_chart_period": settings.default_chart_period,
                "show_percentage_changes": settings.show_percentage_changes,
                "show_market_hours_only": settings.show_market_hours_only,
                "price_update_frequency": settings.price_update_frequency,
                "enable_real_time_updates": settings.enable_real_time_updates,
            }

        except Exception as e:
            logger.error(f"Error getting dashboard config for user {user_id}: {e}")
            # Return safe defaults
            return UserSettings.get_default_settings()
