"""Centralized constants for the Financial Dashboard backend."""

from decimal import Decimal

# Default Values
DEFAULT_CASH_BALANCE = Decimal("0")  # Default cash balance when no cash account exists

# Time intervals (in seconds)
HOUR_IN_SECONDS = 3600
MARKET_DATA_UPDATE_INTERVAL = 300  # 5 minutes
PORTFOLIO_SNAPSHOT_INTERVAL = HOUR_IN_SECONDS  # 1 hour

# API Limits
MAX_API_LIMIT = 1000
DEFAULT_API_LIMIT = 100
MIN_API_LIMIT = 1

# Portfolio Analysis Thresholds
CONCENTRATION_WARNING_THRESHOLD = 0.20  # 20% concentration in single asset
CONCENTRATION_CRITICAL_THRESHOLD = 0.25  # 25% concentration in single asset
MIN_DIVERSIFICATION_ASSETS = 5  # Minimum number of assets for good diversification

# Performance Calculation
ANNUALIZATION_FACTOR = 252  # Trading days in a year
RISK_FREE_RATE = 0.02  # 2% annual risk-free rate

# Cache Expiration Times (in seconds)
MARKET_DATA_CACHE_TTL = 300  # 5 minutes
PORTFOLIO_CACHE_TTL = 600  # 10 minutes
ISIN_MAPPING_CACHE_TTL = 86400  # 24 hours

# Batch Processing
DEFAULT_BATCH_SIZE = 100
MAX_BATCH_SIZE = 500

# Retry Configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1

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
    "GB": ".L",   # United Kingdom (London)
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