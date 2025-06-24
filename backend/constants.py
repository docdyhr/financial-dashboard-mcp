"""Centralized constants for the Financial Dashboard backend."""

from decimal import Decimal

from backend.config import get_settings

# Get settings instance
settings = get_settings()

# Default Values
DEFAULT_CASH_BALANCE = Decimal("0")  # Default cash balance when no cash account exists

# Time intervals (in seconds)
HOUR_IN_SECONDS = 3600
MARKET_DATA_UPDATE_INTERVAL = settings.market_data_update_interval
PORTFOLIO_SNAPSHOT_INTERVAL = settings.portfolio_snapshot_interval

# API Limits
MAX_API_LIMIT = settings.max_api_limit
DEFAULT_API_LIMIT = settings.default_api_limit
MIN_API_LIMIT = 1

# Portfolio Analysis Thresholds
CONCENTRATION_WARNING_THRESHOLD = settings.concentration_warning_threshold
CONCENTRATION_CRITICAL_THRESHOLD = settings.concentration_critical_threshold
MIN_DIVERSIFICATION_ASSETS = settings.min_diversification_assets

# Performance Calculation
ANNUALIZATION_FACTOR = 252  # Trading days in a year
RISK_FREE_RATE = settings.risk_free_rate

# Cache Expiration Times (in seconds)
MARKET_DATA_CACHE_TTL = settings.market_data_cache_ttl
PORTFOLIO_CACHE_TTL = settings.portfolio_cache_ttl
ISIN_MAPPING_CACHE_TTL = settings.isin_mapping_cache_ttl

# Batch Processing
DEFAULT_BATCH_SIZE = settings.default_batch_size
MAX_BATCH_SIZE = settings.max_batch_size

# Retry Configuration
MAX_RETRY_ATTEMPTS = settings.max_retries
RETRY_DELAY_SECONDS = settings.isin_retry_delay

# European Market Suffixes
EUROPEAN_MARKET_SUFFIXES = {
    "DE": ".DE",  # Germany (XETRA)
    "FR": ".PA",  # France (Euronext Paris)
    "IT": ".MI",  # Italy (Milan)
    "ES": ".MC",  # Spain (Madrid)
    "NL": ".AS",  # Netherlands (Amsterdam)
    "BE": ".BR",  # Belgium (Brussels)
    "PT": ".LS",  # Portugal (Lisbon)
    "AT": ".VI",  # Austria (Vienna)
    "CH": ".SW",  # Switzerland (SIX)
    "GB": ".L",  # United Kingdom (London)
    "IE": ".IR",  # Ireland (Dublin)
    "NO": ".OL",  # Norway (Oslo)
    "SE": ".ST",  # Sweden (Stockholm)
    "DK": ".CO",  # Denmark (Copenhagen)
    "FI": ".HE",  # Finland (Helsinki)
}


# Asset Types
class AssetType:
    """Asset type constants."""

    STOCK = "stock"
    BOND = "bond"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    CRYPTOCURRENCY = "cryptocurrency"
    COMMODITY = "commodity"
    CASH = "cash"
    OTHER = "other"


# Transaction Types
class TransactionType:
    """Transaction type constants."""

    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


# Task States
class TaskState:
    """Celery task state constants."""

    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"
