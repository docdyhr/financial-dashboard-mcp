"""ISIN (International Securities Identification Number) prototype utility.

This module provides core ISIN functionality including validation, parsing,
and basic ticker mapping capabilities for the Financial Dashboard.
"""

import logging
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class ISINValidationError(Exception):
    """Exception raised for ISIN validation errors."""

    pass


@dataclass
class ISINInfo:
    """Information parsed from an ISIN code."""

    isin: str
    country_code: str
    national_code: str
    check_digit: str
    country_name: str
    is_valid: bool
    validation_error: Optional[str] = None


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


class ISINUtils:
    """Core ISIN utility functions."""

    # ISO 3166-1 alpha-2 country codes (subset for common financial markets)
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
    }

    @classmethod
    def is_isin_format(cls, identifier: str) -> bool:
        """
        Check if a string matches ISIN format pattern.

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
    def validate_isin_checksum(cls, isin: str) -> Tuple[bool, int]:
        """
        Validate ISIN checksum using the Luhn algorithm.

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
            if i % 2 == 0:  # Every second digit from right (starting with first)
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n

        check_digit = (10 - (total % 10)) % 10
        return str(check_digit) == isin[11], check_digit

    @classmethod
    def parse_isin(cls, isin: str) -> ISINInfo:
        """
        Parse ISIN code and extract components.

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
    def validate_isin(cls, isin: str) -> Tuple[bool, Optional[str]]:
        """
        Validate ISIN code completely.

        Args:
            isin: ISIN code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isin:
            return False, "ISIN cannot be empty"

        isin_info = cls.parse_isin(isin)
        return isin_info.is_valid, isin_info.validation_error


class ISINMappingService:
    """Service for mapping ISIN codes to ticker symbols."""

    def __init__(self, openfigi_api_key: Optional[str] = None):
        self.openfigi_api_key = openfigi_api_key
        self.rate_limit_delay = 2.0  # Seconds between API calls
        self.last_call_time = 0
        self.cache: Dict[str, List[ISINMapping]] = {}

    def _respect_rate_limit(self):
        """Ensure we don't exceed API rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            time.sleep(sleep_time)
        self.last_call_time = time.time()

    def lookup_isin_openfigi(
        self, isin: str, exchange_code: Optional[str] = None
    ) -> List[ISINMapping]:
        """
        Lookup ISIN using OpenFIGI API.

        Args:
            isin: ISIN code to lookup
            exchange_code: Optional exchange code filter (e.g., 'GX' for XETRA)

        Returns:
            List of ISINMapping objects
        """
        try:
            self._respect_rate_limit()

            url = "https://api.openfigi.com/v3/mapping"
            headers = {"Content-Type": "application/json"}

            # Add API key if available
            if self.openfigi_api_key:
                headers["X-OPENFIGI-APIKEY"] = self.openfigi_api_key

            payload = [{"idType": "ID_ISIN", "idValue": isin}]

            # Add exchange filter if specified
            if exchange_code:
                payload[0]["exchCode"] = exchange_code

            response = requests.post(url, json=payload, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                mappings = []

                if data and len(data) > 0 and "data" in data[0]:
                    for item in data[0]["data"]:
                        mapping = ISINMapping(
                            isin=isin,
                            ticker=item.get("ticker", ""),
                            exchange_code=item.get("exchCode", ""),
                            exchange_name=item.get("name", ""),
                            security_name=item.get("name", ""),
                            currency=item.get("currency", ""),
                            source="OpenFIGI",
                            confidence=0.9,  # High confidence for OpenFIGI
                        )
                        mappings.append(mapping)

                return mappings
            else:
                logger.warning(
                    f"OpenFIGI API error for {isin}: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"Error looking up ISIN {isin} via OpenFIGI: {e}")
            return []

    def lookup_isin_cached(
        self, isin: str, exchange_code: Optional[str] = None
    ) -> List[ISINMapping]:
        """
        Lookup ISIN with caching.

        Args:
            isin: ISIN code to lookup
            exchange_code: Optional exchange code filter

        Returns:
            List of ISINMapping objects
        """
        cache_key = f"{isin}:{exchange_code or 'all'}"

        # Check cache first
        if cache_key in self.cache:
            logger.debug(f"Found cached ISIN mapping for {isin}")
            return self.cache[cache_key]

        # Lookup via APIs
        mappings = self.lookup_isin_openfigi(isin, exchange_code)

        # Cache results
        if mappings:
            self.cache[cache_key] = mappings
            logger.info(f"Cached {len(mappings)} ISIN mappings for {isin}")

        return mappings

    def get_best_ticker_for_exchange(
        self, isin: str, preferred_exchange: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the best ticker symbol for an ISIN, optionally preferring a specific exchange.

        Args:
            isin: ISIN code
            preferred_exchange: Preferred exchange code (e.g., 'GX' for XETRA)

        Returns:
            Best ticker symbol or None if not found
        """
        mappings = self.lookup_isin_cached(isin, preferred_exchange)

        if not mappings:
            return None

        # If we have a preferred exchange, try to find it first
        if preferred_exchange:
            for mapping in mappings:
                if mapping.exchange_code == preferred_exchange:
                    return mapping.ticker

        # Fall back to first available mapping
        return mappings[0].ticker if mappings else None


class ISINService:
    """Main ISIN service combining validation and mapping functionality."""

    def __init__(self, openfigi_api_key: Optional[str] = None):
        self.mapping_service = ISINMappingService(openfigi_api_key)

    def resolve_identifier(self, identifier: str) -> Tuple[str, str]:
        """
        Resolve an identifier that could be either a ticker or ISIN.

        Args:
            identifier: Ticker symbol or ISIN code

        Returns:
            Tuple of (resolved_ticker, identifier_type)
            identifier_type is either 'ticker' or 'isin'
        """
        identifier = identifier.upper().strip()

        # Check if it's an ISIN
        if ISINUtils.is_isin_format(identifier):
            is_valid, error = ISINUtils.validate_isin(identifier)
            if is_valid:
                # Try to map ISIN to ticker
                isin_info = ISINUtils.parse_isin(identifier)

                # Determine preferred exchange based on country
                preferred_exchange = None
                if isin_info.country_code == "DE":
                    preferred_exchange = "GX"  # XETRA
                elif isin_info.country_code == "US":
                    preferred_exchange = "UQ"  # NASDAQ
                elif isin_info.country_code == "GB":
                    preferred_exchange = "LN"  # London

                ticker = self.mapping_service.get_best_ticker_for_exchange(
                    identifier, preferred_exchange
                )

                if ticker:
                    return ticker, "isin"
                else:
                    # Return the ISIN itself if no ticker mapping found
                    return identifier, "isin"
            else:
                raise ISINValidationError(f"Invalid ISIN: {error}")

        # Assume it's a ticker
        return identifier, "ticker"

    def get_asset_info(self, identifier: str) -> Dict[str, any]:
        """
        Get comprehensive asset information from identifier.

        Args:
            identifier: Ticker symbol or ISIN code

        Returns:
            Dictionary with asset information
        """
        try:
            resolved_ticker, id_type = self.resolve_identifier(identifier)

            result = {
                "original_identifier": identifier,
                "resolved_ticker": resolved_ticker,
                "identifier_type": id_type,
                "success": True,
            }

            # Add ISIN information if we resolved from ISIN
            if id_type == "isin":
                isin_info = ISINUtils.parse_isin(identifier)
                result.update(
                    {
                        "isin": identifier,
                        "country_code": isin_info.country_code,
                        "country_name": isin_info.country_name,
                        "national_code": isin_info.national_code,
                    }
                )

                # Get available mappings
                mappings = self.mapping_service.lookup_isin_cached(identifier)
                if mappings:
                    result["available_tickers"] = [
                        {
                            "ticker": m.ticker,
                            "exchange": m.exchange_code,
                            "exchange_name": m.exchange_name,
                            "currency": m.currency,
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
            return {
                "original_identifier": identifier,
                "success": False,
                "error": str(e),
                "error_type": "general",
            }


# Test functions for demonstration
def test_isin_validation():
    """Test ISIN validation functionality."""
    test_cases = [
        ("DE000A35JS40", True, "Click Digital"),
        ("US0378331005", True, "Apple Inc."),
        ("GB0002162385", True, "BP plc"),
        ("INVALID12345", False, "Invalid format"),
        ("DE000A35JS41", False, "Wrong checksum"),
    ]

    print("🧪 ISIN Validation Tests")
    print("=" * 50)

    for isin, expected_valid, description in test_cases:
        is_valid, error = ISINUtils.validate_isin(isin)
        status = "✅" if is_valid == expected_valid else "❌"

        print(f"{status} {isin} ({description})")
        if is_valid:
            isin_info = ISINUtils.parse_isin(isin)
            print(f"   Country: {isin_info.country_name} ({isin_info.country_code})")
        else:
            print(f"   Error: {error}")
        print()


def test_click_digital_case():
    """Test the specific Click Digital case."""
    print("🎯 Click Digital (CLIQ.DE) Test Case")
    print("=" * 50)

    isin = "DE000A35JS40"
    service = ISINService()

    print(f"Testing ISIN: {isin}")

    # Validate ISIN
    is_valid, error = ISINUtils.validate_isin(isin)
    print(f"Valid ISIN: {is_valid}")
    if error:
        print(f"Error: {error}")

    # Parse ISIN
    isin_info = ISINUtils.parse_isin(isin)
    print(f"Country: {isin_info.country_name}")
    print(f"National Code: {isin_info.national_code}")

    # Try to resolve
    try:
        asset_info = service.get_asset_info(isin)
        print(f"Resolution Success: {asset_info['success']}")
        if asset_info["success"]:
            print(f"Resolved Ticker: {asset_info['resolved_ticker']}")
            if "available_tickers" in asset_info:
                print("Available Tickers:")
                for ticker_info in asset_info["available_tickers"]:
                    print(f"  • {ticker_info['ticker']} ({ticker_info['exchange']})")
        else:
            print(f"Error: {asset_info['error']}")
    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    # Run tests
    test_isin_validation()
    test_click_digital_case()

    print("\n🏁 ISIN Prototype Complete")
    print("=" * 50)
    print("This prototype demonstrates:")
    print("✅ ISIN format validation")
    print("✅ ISIN checksum verification")
    print("✅ ISIN parsing and country detection")
    print("✅ Basic ISIN-to-ticker mapping via OpenFIGI")
    print("✅ Caching mechanism for API responses")
    print("✅ Smart identifier resolution (ISIN vs ticker)")
    print()
    print("Ready for integration into Financial Dashboard!")
