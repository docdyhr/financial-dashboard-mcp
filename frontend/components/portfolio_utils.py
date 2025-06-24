"""Portfolio utility functions for the Financial Dashboard."""


def safe_format_currency(value, default="$0.00"):
    """Safely format a value as currency."""
    try:
        if value is None:
            return default
        return f"${float(value):.2f}"
    except (ValueError, TypeError):
        return default


def validate_ticker_input(ticker: str) -> tuple[bool, str]:
    """Validate ticker input and provide helpful feedback."""
    if not ticker or not ticker.strip():
        return False, "Ticker cannot be empty"

    ticker = ticker.upper().strip()

    # Import validation function
    try:
        from backend.services.ticker_utils import TickerUtils

        is_valid, error_msg = TickerUtils.validate_ticker_format(ticker)
        return is_valid, error_msg or "Valid format"
    except ImportError:
        # Fallback validation if utils not available
        import re

        if not re.match(r"^[A-Z0-9.-]+$", ticker):
            return False, "Ticker can only contain letters, numbers, dots, and hyphens"

        if len(ticker) > 20:
            return False, "Ticker too long (max 20 characters)"

        return True, "Valid format"


def get_ticker_suggestions(ticker: str, exchange_hint: str = None) -> list[str]:
    """Get ticker format suggestions."""
    try:
        from backend.services.ticker_utils import TickerUtils

        suggestions = []

        if exchange_hint:
            suggested = TickerUtils.suggest_ticker_format(ticker, exchange_hint)
            if suggested != ticker:
                suggestions.append(suggested)

        # Add common European formats if base ticker provided
        if "." not in ticker and len(ticker) <= 10:
            common_formats = [
                f"{ticker}.L",  # London
                f"{ticker}.PA",  # Paris
                f"{ticker}.DE",  # Frankfurt
                f"{ticker}.MI",  # Milan
                f"{ticker}.AS",  # Amsterdam
            ]
            suggestions.extend(common_formats)

        return suggestions[:5]  # Limit to 5 suggestions
    except ImportError:
        return []
