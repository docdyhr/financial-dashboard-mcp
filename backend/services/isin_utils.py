"""Production ISIN (International Securities Identification Number) utilities.

This module provides comprehensive ISIN functionality including validation, parsing,
caching, and database integration for the Financial Dashboard.
"""

from dataclasses import dataclass
from datetime import datetime
import logging
import re
import time
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.exceptions import ISINValidationError

logger = logging.getLogger(__name__)


@dataclass
class ISINInfo:
    """Information parsed from an ISIN code."""

    isin: str
    country_code: str
    national_code: str
    check_digit: str
    country_name: str
    is_valid: bool
    validation_error: str | None = None


@dataclass
class ISINMapping:
    """ISIN to ticker mapping result."""

    isin: str
    ticker: str
    exchange_code: str
    exchange_name: str
    security_name: str
    currency: str
    source: str
    confidence: float = 1.0
    is_active: bool = True


class ISINUtils:
    """Core ISIN utility functions with caching and database integration."""

    # ISO 3166-1 alpha-2 country codes for financial markets
    COUNTRY_CODES = {
        "AD": "Andorra",
        "AE": "United Arab Emirates",
        "AR": "Argentina",
        "AT": "Austria",
        "AU": "Australia",
        "BE": "Belgium",
        "BG": "Bulgaria",
        "BH": "Bahrain",
        "BR": "Brazil",
        "CA": "Canada",
        "CH": "Switzerland",
        "CL": "Chile",
        "CN": "China",
        "CO": "Colombia",
        "CZ": "Czech Republic",
        "DE": "Germany",
        "DK": "Denmark",
        "EG": "Egypt",
        "ES": "Spain",
        "FI": "Finland",
        "FR": "France",
        "GB": "United Kingdom",
        "GR": "Greece",
        "HK": "Hong Kong",
        "HU": "Hungary",
        "ID": "Indonesia",
        "IE": "Ireland",
        "IL": "Israel",
        "IN": "India",
        "IT": "Italy",
        "JP": "Japan",
        "KR": "South Korea",
        "LU": "Luxembourg",
        "MX": "Mexico",
        "MY": "Malaysia",
        "NL": "Netherlands",
        "NO": "Norway",
        "NZ": "New Zealand",
        "PH": "Philippines",
        "PL": "Poland",
        "PT": "Portugal",
        "QA": "Qatar",
        "RO": "Romania",
        "RU": "Russia",
        "SA": "Saudi Arabia",
        "SE": "Sweden",
        "SG": "Singapore",
        "TH": "Thailand",
        "TR": "Turkey",
        "TW": "Taiwan",
        "US": "United States",
        "ZA": "South Africa",
        "XS": "International Securities",
        "EU": "European Union Securities",
    }

    # Exchange code mappings for better ticker resolution
    EXCHANGE_MAPPINGS = {
        "DE": ["GX", "GF", "GD", "GY", "GS", "GM", "GB"],  # German exchanges
        "US": ["UQ", "UN", "UW"],  # US exchanges
        "GB": ["LN", "L"],  # UK exchanges
        "FR": ["FP", "FR"],  # French exchanges
        "IT": ["IM", "IT"],  # Italian exchanges
        "ES": ["MC", "ES"],  # Spanish exchanges
        "NL": ["AS", "NA"],  # Dutch exchanges
        "CH": ["SW", "CH"],  # Swiss exchanges
        "CA": ["TO", "CN"],  # Canadian exchanges
        "AU": ["AX", "AU"],  # Australian exchanges
        "JP": ["JP", "T"],  # Japanese exchanges
        "HK": ["HK"],  # Hong Kong exchanges
        "SG": ["SI", "SG"],  # Singapore exchanges
    }

    @classmethod
    def is_isin_format(cls, identifier: str) -> bool:
        """Check if a string matches ISIN format pattern.

        Args:
            identifier: String to check

        Returns:
            True if matches ISIN format, False otherwise
        """
        if not identifier or len(identifier) != 12:
            return False

        # ISIN format: 2 letters + 9 alphanumeric + 1 digit
        pattern = r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$"
        return bool(re.match(pattern, identifier.upper()))

    @classmethod
    def validate_isin_checksum(cls, isin: str) -> tuple[bool, int]:
        """Validate ISIN checksum using the Luhn algorithm.

        Args:
            isin: ISIN code to validate

        Returns:
            Tuple of (is_valid, expected_check_digit)
        """
        if len(isin) != 12:
            return False, -1

        # Convert letters to numbers (A=10, B=11, ..., Z=35)
        converted = ""
        for char in isin[:-1]:  # Exclude check digit
            if char.isalpha():
                converted += str(ord(char.upper()) - ord("A") + 10)
            else:
                converted += char

        # Apply Luhn algorithm
        total = 0
        for i, digit in enumerate(reversed(converted)):
            n = int(digit)
            if i % 2 == 0:  # Every second digit from right
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n

        check_digit = (10 - (total % 10)) % 10
        return str(check_digit) == isin[11], check_digit

    @classmethod
    def parse_isin(cls, isin: str) -> ISINInfo:
        """Parse ISIN code and extract components.

        Args:
            isin: ISIN code to parse

        Returns:
            ISINInfo object with parsed components
        """
        isin = isin.upper().strip()

        # Basic format validation
        if not cls.is_isin_format(isin):
            return ISINInfo(
                isin=isin,
                country_code="",
                national_code="",
                check_digit="",
                country_name="",
                is_valid=False,
                validation_error="Invalid ISIN format",
            )

        # Extract components
        country_code = isin[:2]
        national_code = isin[2:11]
        check_digit = isin[11]
        country_name = cls.COUNTRY_CODES.get(country_code, "Unknown Country")

        # Validate checksum
        is_checksum_valid, expected_check = cls.validate_isin_checksum(isin)

        validation_error = None
        if not is_checksum_valid:
            validation_error = (
                f"Invalid checksum (expected {expected_check}, got {check_digit})"
            )

        return ISINInfo(
            isin=isin,
            country_code=country_code,
            national_code=national_code,
            check_digit=check_digit,
            country_name=country_name,
            is_valid=is_checksum_valid,
            validation_error=validation_error,
        )

    @classmethod
    def validate_isin(
        cls, isin: str, use_cache: bool = True
    ) -> tuple[bool, str | None]:
        """Validate ISIN code completely with optional database caching.

        Args:
            isin: ISIN code to validate
            use_cache: Whether to use database cache for validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isin:
            return False, "ISIN cannot be empty"

        isin = isin.upper().strip()

        # Check cache first if enabled
        if use_cache:
            try:
                from backend.database import get_db_session
                from backend.models.isin import ISINValidationCache

                with get_db_session() as db:
                    cached = (
                        db.query(ISINValidationCache)
                        .filter(ISINValidationCache.isin == isin)
                        .first()
                    )

                    if cached and cached.is_fresh(24):
                        logger.debug(f"Using cached ISIN validation for {isin}")
                        return cached.is_valid, cached.validation_error

            except Exception as e:
                logger.warning(f"Cache lookup failed for ISIN {isin}: {e}")

        # Perform validation
        isin_info = cls.parse_isin(isin)

        # Cache the result if caching is enabled
        if use_cache:
            try:
                from backend.database import get_db_session
                from backend.models.isin import ISINValidationCache

                with get_db_session() as db:
                    # Delete old cache entry if exists
                    db.query(ISINValidationCache).filter(
                        ISINValidationCache.isin == isin
                    ).delete()

                    # Create new cache entry
                    cache_entry = ISINValidationCache.create_from_validation(
                        isin=isin,
                        is_valid=isin_info.is_valid,
                        country_code=(
                            isin_info.country_code if isin_info.is_valid else None
                        ),
                        country_name=(
                            isin_info.country_name if isin_info.is_valid else None
                        ),
                        national_code=(
                            isin_info.national_code if isin_info.is_valid else None
                        ),
                        check_digit=(
                            isin_info.check_digit if isin_info.is_valid else None
                        ),
                        validation_error=isin_info.validation_error,
                    )

                    db.add(cache_entry)
                    db.commit()
                    logger.debug(f"Cached ISIN validation result for {isin}")

            except Exception as e:
                logger.warning(f"Failed to cache ISIN validation for {isin}: {e}")

        return isin_info.is_valid, isin_info.validation_error

    @classmethod
    def get_preferred_exchanges(cls, country_code: str) -> list[str]:
        """Get preferred exchange codes for a country.

        Args:
            country_code: 2-letter country code

        Returns:
            List of exchange codes in order of preference
        """
        return cls.EXCHANGE_MAPPINGS.get(country_code, [])

    @classmethod
    def suggest_ticker_formats(cls, isin: str, base_ticker: str) -> list[str]:
        """Suggest possible ticker formats based on ISIN country.

        Args:
            isin: ISIN code
            base_ticker: Base ticker symbol

        Returns:
            List of suggested ticker formats
        """
        isin_info = cls.parse_isin(isin)
        if not isin_info.is_valid:
            return [base_ticker]

        suggestions = [base_ticker]  # Start with base ticker

        # Add country-specific formats
        country = isin_info.country_code

        if country == "DE":
            suggestions.extend(
                [
                    f"{base_ticker}.DE",  # XETRA
                    f"{base_ticker}.F",  # Frankfurt
                    f"{base_ticker}.BE",  # Berlin
                    f"{base_ticker}.DU",  # Düsseldorf
                    f"{base_ticker}.HM",  # Hamburg
                    f"{base_ticker}.MU",  # Munich
                    f"{base_ticker}.SG",  # Stuttgart
                ]
            )
        elif country == "GB":
            suggestions.extend(
                [
                    f"{base_ticker}.L",  # London
                    f"{base_ticker}.LN",  # London (alternative)
                ]
            )
        elif country == "FR":
            suggestions.extend(
                [
                    f"{base_ticker}.PA",  # Paris
                    f"{base_ticker}.FR",  # France
                ]
            )
        elif country == "IT":
            suggestions.extend(
                [
                    f"{base_ticker}.MI",  # Milan
                    f"{base_ticker}.IT",  # Italy
                ]
            )
        elif country == "ES":
            suggestions.extend(
                [
                    f"{base_ticker}.MC",  # Madrid
                    f"{base_ticker}.ES",  # Spain
                ]
            )
        elif country == "NL":
            suggestions.extend(
                [
                    f"{base_ticker}.AS",  # Amsterdam
                    f"{base_ticker}.NL",  # Netherlands
                ]
            )
        elif country == "CH":
            suggestions.extend(
                [
                    f"{base_ticker}.SW",  # Swiss
                    f"{base_ticker}.CH",  # Switzerland
                ]
            )
        elif country == "CA":
            suggestions.extend(
                [
                    f"{base_ticker}.TO",  # Toronto
                    f"{base_ticker}.V",  # TSX Venture
                ]
            )
        elif country == "AU":
            suggestions.extend(
                [
                    f"{base_ticker}.AX",  # Australia
                ]
            )
        elif country == "JP":
            suggestions.extend(
                [
                    f"{base_ticker}.T",  # Tokyo
                ]
            )
        elif country == "HK":
            suggestions.extend(
                [
                    f"{base_ticker}.HK",  # Hong Kong
                ]
            )

        return suggestions


class ISINMappingService:
    """Service for managing ISIN to ticker mappings with database persistence."""

    def __init__(self):
        self.rate_limit_delay = 2.0  # Seconds between external API calls
        self.last_call_time = 0

    def _respect_rate_limit(self):
        """Ensure we don't exceed API rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            time.sleep(sleep_time)
        self.last_call_time = time.time()

    def get_mappings_from_db(
        self,
        db: Session,
        isin: str,
        exchange_code: str | None = None,
        active_only: bool = True,
    ) -> list[ISINMapping]:
        """Get ISIN mappings from database.

        Args:
            db: Database session
            isin: ISIN code
            exchange_code: Optional exchange code filter
            active_only: Whether to return only active mappings

        Returns:
            List of ISINMapping objects
        """
        try:
            from backend.models.isin import ISINTickerMapping

            query = db.query(ISINTickerMapping).filter(
                ISINTickerMapping.isin == isin.upper()
            )

            if active_only:
                query = query.filter(ISINTickerMapping.is_active)

            if exchange_code:
                query = query.filter(ISINTickerMapping.exchange_code == exchange_code)

            # Order by confidence (highest first) and creation date (newest first)
            query = query.order_by(
                ISINTickerMapping.confidence.desc(), ISINTickerMapping.created_at.desc()
            )

            mappings = []
            for mapping in query.all():
                mappings.append(
                    ISINMapping(
                        isin=mapping.isin,
                        ticker=mapping.ticker,
                        exchange_code=mapping.exchange_code or "",
                        exchange_name=mapping.exchange_name or "",
                        security_name=mapping.security_name or "",
                        currency=mapping.currency or "",
                        source=mapping.source,
                        confidence=mapping.confidence,
                        is_active=mapping.is_active,
                    )
                )

            return mappings

        except Exception as e:
            logger.error(f"Error getting ISIN mappings from database for {isin}: {e}")
            return []

    def save_mapping_to_db(
        self, db: Session, mapping: ISINMapping, update_existing: bool = True
    ) -> bool:
        """Save ISIN mapping to database.

        Args:
            db: Database session
            mapping: ISINMapping to save
            update_existing: Whether to update existing mappings

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            from backend.models.isin import ISINTickerMapping

            # Check if mapping already exists
            existing = (
                db.query(ISINTickerMapping)
                .filter(
                    and_(
                        ISINTickerMapping.isin == mapping.isin,
                        ISINTickerMapping.ticker == mapping.ticker,
                        ISINTickerMapping.exchange_code == mapping.exchange_code,
                    )
                )
                .first()
            )

            if existing:
                if update_existing:
                    # Update existing mapping
                    existing.security_name = mapping.security_name
                    existing.currency = mapping.currency
                    existing.source = mapping.source
                    existing.confidence = mapping.confidence
                    existing.is_active = mapping.is_active
                    existing.last_updated = datetime.utcnow()
                    logger.debug(
                        f"Updated existing ISIN mapping: {mapping.isin} -> {mapping.ticker}"
                    )
                else:
                    logger.debug(
                        f"ISIN mapping already exists: {mapping.isin} -> {mapping.ticker}"
                    )
                    return True
            else:
                # Create new mapping
                new_mapping = ISINTickerMapping()
                new_mapping.isin = mapping.isin
                new_mapping.ticker = mapping.ticker
                new_mapping.exchange_code = mapping.exchange_code
                new_mapping.exchange_name = mapping.exchange_name
                new_mapping.security_name = mapping.security_name
                new_mapping.currency = mapping.currency
                new_mapping.source = mapping.source
                new_mapping.confidence = mapping.confidence
                new_mapping.is_active = mapping.is_active

                db.add(new_mapping)
                logger.debug(
                    f"Created new ISIN mapping: {mapping.isin} -> {mapping.ticker}"
                )

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Error saving ISIN mapping to database: {e}")
            db.rollback()
            return False

    def get_best_ticker_for_exchange(
        self, db: Session, isin: str, preferred_exchange: str | None = None
    ) -> str | None:
        """Get the best ticker symbol for an ISIN, optionally preferring a specific exchange.

        Args:
            db: Database session
            isin: ISIN code
            preferred_exchange: Preferred exchange code

        Returns:
            Best ticker symbol or None if not found
        """
        # First, try to get from database
        mappings = self.get_mappings_from_db(db, isin)

        if not mappings:
            # No database mappings, could try external APIs here
            logger.debug(f"No database mappings found for ISIN {isin}")
            return None

        # If we have a preferred exchange, try to find it first
        if preferred_exchange:
            for mapping in mappings:
                if mapping.exchange_code == preferred_exchange:
                    logger.debug(
                        f"Found preferred exchange mapping: {mapping.ticker} ({preferred_exchange})"
                    )
                    return mapping.ticker

        # Fall back to highest confidence mapping
        best_mapping = max(mappings, key=lambda m: m.confidence)
        logger.debug(
            f"Using best confidence mapping: {best_mapping.ticker} (confidence: {best_mapping.confidence})"
        )
        return best_mapping.ticker

    def resolve_isin_to_ticker(
        self, db: Session, isin: str, preferred_country: str | None = None
    ) -> str | None:
        """Resolve ISIN to the most appropriate ticker symbol.

        Args:
            db: Database session
            isin: ISIN code to resolve
            preferred_country: Preferred country for exchange selection

        Returns:
            Resolved ticker symbol or None
        """
        # Validate ISIN first
        is_valid, error = ISINUtils.validate_isin(isin)
        if not is_valid:
            logger.warning(f"Invalid ISIN provided: {isin} - {error}")
            return None

        # Parse ISIN to get country information
        isin_info = ISINUtils.parse_isin(isin)
        country_code = preferred_country or isin_info.country_code

        # Get preferred exchanges for the country
        preferred_exchanges = ISINUtils.get_preferred_exchanges(country_code)

        # Try each preferred exchange in order
        for exchange in preferred_exchanges:
            ticker = self.get_best_ticker_for_exchange(db, isin, exchange)
            if ticker:
                return ticker

        # Fall back to any available mapping
        return self.get_best_ticker_for_exchange(db, isin)


class ISINService:
    """Main ISIN service combining validation, mapping, and resolution functionality."""

    def __init__(self):
        self.mapping_service = ISINMappingService()

    def resolve_identifier(
        self, db: Session, identifier: str
    ) -> tuple[str, str, ISINInfo | None]:
        """Resolve an identifier that could be either a ticker or ISIN.

        Args:
            db: Database session
            identifier: Ticker symbol or ISIN code

        Returns:
            Tuple of (resolved_ticker, identifier_type, isin_info)
            identifier_type is either 'ticker' or 'isin'
        """
        identifier = identifier.upper().strip()

        # Check if it's an ISIN
        if ISINUtils.is_isin_format(identifier):
            is_valid, error = ISINUtils.validate_isin(identifier)
            if is_valid:
                isin_info = ISINUtils.parse_isin(identifier)

                # Try to resolve ISIN to ticker
                ticker = self.mapping_service.resolve_isin_to_ticker(db, identifier)

                if ticker:
                    return ticker, "isin", isin_info
                # Return the ISIN itself if no ticker mapping found
                # The calling code can decide how to handle this
                return identifier, "isin", isin_info
            raise ISINValidationError(f"Invalid ISIN: {error}")

        # Assume it's a ticker
        return identifier, "ticker", None

    def add_manual_mapping(
        self,
        db: Session,
        isin: str,
        ticker: str,
        exchange_code: str | None = None,
        exchange_name: str | None = None,
        security_name: str | None = None,
        currency: str | None = None,
    ) -> bool:
        """Manually add an ISIN to ticker mapping.

        Args:
            db: Database session
            isin: ISIN code
            ticker: Ticker symbol
            exchange_code: Exchange code
            exchange_name: Exchange name
            security_name: Security name
            currency: Currency code

        Returns:
            True if mapping was added successfully
        """
        # Validate ISIN
        is_valid, error = ISINUtils.validate_isin(isin)
        if not is_valid:
            raise ISINValidationError(f"Invalid ISIN: {error}")

        # Create mapping
        mapping = ISINMapping(
            isin=isin,
            ticker=ticker,
            exchange_code=exchange_code or "",
            exchange_name=exchange_name or "",
            security_name=security_name or "",
            currency=currency or "",
            source="manual",
            confidence=1.0,  # High confidence for manual mappings
            is_active=True,
        )

        return self.mapping_service.save_mapping_to_db(db, mapping)

    def get_ticker_for_isin(self, isin: str) -> str | None:
        """Get ticker symbol for a given ISIN.

        Args:
            isin: ISIN code

        Returns:
            Ticker symbol if found, None otherwise
        """
        from backend.models import get_db

        db = next(get_db())
        return self.mapping_service.resolve_isin_to_ticker(db, isin)

    def get_asset_info(self, db: Session, identifier: str) -> dict[str, Any]:
        """Get comprehensive asset information from identifier.

        Args:
            db: Database session
            identifier: Ticker symbol or ISIN code

        Returns:
            Dictionary with asset information
        """
        try:
            resolved_ticker, id_type, isin_info = self.resolve_identifier(
                db, identifier
            )

            result = {
                "original_identifier": identifier,
                "resolved_ticker": resolved_ticker,
                "identifier_type": id_type,
                "success": True,
            }

            # Add ISIN information if we resolved from ISIN
            if id_type == "isin" and isin_info:
                result.update(
                    {
                        "isin": identifier,
                        "country_code": isin_info.country_code,
                        "country_name": isin_info.country_name,
                        "national_code": isin_info.national_code,
                        "check_digit": isin_info.check_digit,
                    }
                )

                # Get available mappings from database
                mappings = self.mapping_service.get_mappings_from_db(db, identifier)
                if mappings:
                    result["available_tickers"] = [
                        {
                            "ticker": m.ticker,
                            "exchange_code": m.exchange_code,
                            "exchange_name": m.exchange_name,
                            "currency": m.currency,
                            "confidence": m.confidence,
                            "source": m.source,
                        }
                        for m in mappings
                    ]

            return result

        except ISINValidationError as e:
            return {
                "original_identifier": identifier,
                "success": False,
                "error": str(e),
                "error_type": "validation",
            }
        except Exception as e:
            logger.error(f"Error getting asset info for {identifier}: {e}")
            return {
                "original_identifier": identifier,
                "success": False,
                "error": str(e),
                "error_type": "general",
            }


# Global service instance
isin_service = ISINService()


def get_isin_service() -> ISINService:
    """Get the global ISIN service instance."""
    return isin_service
