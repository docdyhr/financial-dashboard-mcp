"""Settings service for frontend to interact with backend API."""

import logging
from typing import Any

import requests
import streamlit as st

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing user settings via backend API."""

    def __init__(self, backend_url: str, user_id: int = 5):
        self.backend_url = backend_url
        self.user_id = user_id
        self.api_url = f"{backend_url}/api/v1/user-settings"

    def get_settings(self) -> dict[str, Any]:
        """Get user settings from backend API."""
        try:
            response = requests.get(
                f"{self.api_url}/{self.user_id}/preferences", timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("data", {})
                logger.error(f"API error: {data.get('message', 'Unknown error')}")
                return self._get_default_settings()
            logger.error(f"Failed to fetch settings: HTTP {response.status_code}")
            return self._get_default_settings()

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching settings: {e}")
            return self._get_default_settings()
        except Exception as e:
            logger.error(f"Unexpected error fetching settings: {e}")
            return self._get_default_settings()

    def save_settings(self, settings: dict[str, Any]) -> bool:
        """Save user settings to backend API."""
        try:
            response = requests.put(
                f"{self.api_url}/{self.user_id}/preferences",
                json=settings,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info("Settings saved successfully")
                    return True
                logger.error(
                    f"API error saving settings: {data.get('message', 'Unknown error')}"
                )
                return False
            logger.error(f"Failed to save settings: HTTP {response.status_code}")
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error saving settings: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving settings: {e}")
            return False

    def update_setting(self, key: str, value: Any) -> bool:
        """Update a single setting."""
        try:
            # Get current settings
            current_settings = self.get_settings()

            # Update the specific setting
            current_settings[key] = value

            # Save updated settings
            return self.save_settings(current_settings)

        except Exception as e:
            logger.error(f"Error updating setting {key}: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset settings to defaults."""
        try:
            response = requests.post(f"{self.api_url}/{self.user_id}/reset", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info("Settings reset to defaults")
                    return True

            logger.error("Failed to reset settings")
            return False

        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False

    def _get_default_settings(self) -> dict[str, Any]:
        """Get default settings as fallback."""
        return {
            "theme": "Light",
            "currency": "USD",
            "date_format": "MM/DD/YYYY",
            "provider": "auto",
            "frequency": 15,
            "email_enabled": False,
            "email": None,
            "price_alerts": False,
            "performance_alerts": False,
            "news_alerts": False,
        }


class StreamlitSettingsManager:
    """Manages settings integration with Streamlit session state."""

    def __init__(self, backend_url: str, user_id: int = 5):
        self.settings_service = SettingsService(backend_url, user_id)
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize settings in Streamlit session state."""
        if "settings" not in st.session_state:
            # Load settings from backend
            st.session_state.settings = self.settings_service.get_settings()
            st.session_state.settings_loaded = True
            logger.info("Settings loaded from backend into session state")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value from session state."""
        return st.session_state.settings.get(key, default)

    def update_setting(
        self, key: str, value: Any, save_immediately: bool = True
    ) -> bool:
        """Update a setting in session state and optionally save to backend."""
        try:
            # Update session state
            st.session_state.settings[key] = value

            if save_immediately:
                # Save to backend
                success = self.settings_service.update_setting(key, value)
                if success:
                    logger.info(f"Setting {key} updated and saved")
                    return True
                logger.error(f"Failed to save setting {key}")
                return False
            logger.info(f"Setting {key} updated in session state")
            return True

        except Exception as e:
            logger.error(f"Error updating setting {key}: {e}")
            return False

    def save_all_settings(self) -> bool:
        """Save all current session state settings to backend."""
        try:
            success = self.settings_service.save_settings(st.session_state.settings)
            if success:
                logger.info("All settings saved successfully")
                return True
            logger.error("Failed to save settings")
            return False

        except Exception as e:
            logger.error(f"Error saving all settings: {e}")
            return False

    def reload_settings(self) -> bool:
        """Reload settings from backend."""
        try:
            fresh_settings = self.settings_service.get_settings()
            st.session_state.settings = fresh_settings
            logger.info("Settings reloaded from backend")
            return True

        except Exception as e:
            logger.error(f"Error reloading settings: {e}")
            return False

    def reset_settings(self) -> bool:
        """Reset settings to defaults."""
        try:
            success = self.settings_service.reset_to_defaults()
            if success:
                # Reload settings from backend
                self.reload_settings()
                logger.info("Settings reset to defaults")
                return True
            logger.error("Failed to reset settings")
            return False

        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False

    def get_currency_symbol(self) -> str:
        """Get currency symbol based on user preference."""
        currency = self.get_setting("currency", "USD")
        symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CAD": "C$",
            "AUD": "A$",
            "CHF": "CHF",
        }
        return symbols.get(currency, "$")

    def format_currency(self, amount: float) -> str:
        """Format currency amount according to user preference."""
        try:
            symbol = self.get_currency_symbol()
            currency = self.get_setting("currency", "USD")

            if currency == "JPY":
                # Japanese Yen doesn't use decimal places
                return f"{symbol}{amount:,.0f}"
            return f"{symbol}{amount:,.2f}"

        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return f"${amount:,.2f}"  # Fallback to USD

    def get_theme_config(self) -> dict[str, Any]:
        """Get theme configuration for UI components."""
        theme = self.get_setting("theme", "Light")

        if theme == "Dark":
            return {
                "primary_color": "#ffffff",
                "background_color": "#1e1e1e",
                "secondary_background_color": "#2e2e2e",
                "text_color": "#ffffff",
            }
        if theme == "Auto":
            # Let Streamlit handle auto theme
            return {}
        # Light theme (default)
        return {
            "primary_color": "#1f77b4",
            "background_color": "#ffffff",
            "secondary_background_color": "#f0f2f6",
            "text_color": "#000000",
        }


# Global instance for easy access
def get_settings_manager(
    backend_url: str = "http://localhost:8000",
) -> StreamlitSettingsManager:
    """Get or create settings manager instance."""
    if "settings_manager" not in st.session_state:
        st.session_state.settings_manager = StreamlitSettingsManager(backend_url)
    return st.session_state.settings_manager
