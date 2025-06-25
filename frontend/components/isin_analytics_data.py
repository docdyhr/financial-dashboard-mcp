"""ISIN Analytics data fetching services."""

import logging
from typing import Any

import pandas as pd
import requests
import streamlit as st

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"


def call_api(endpoint: str, method: str = "GET", data: dict = None) -> dict | None:
    """Call API with error handling."""
    try:
        url = f"{BACKEND_URL}{endpoint}"

        if method == "GET":
            response = requests.get(url, timeout=15)
        elif method == "POST":
            response = requests.post(url, json=data or {}, timeout=15)
        else:
            return None

        if response.status_code == 200:
            return response.json()
        st.error(f"API Error {response.status_code}: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def get_isin_statistics() -> dict | None:
    """Get comprehensive ISIN statistics."""
    try:
        # This would call the ISIN statistics endpoint
        stats_data = call_api("/isin/statistics")
        if stats_data and stats_data.get("success"):
            return stats_data.get("data", {})

        # Mock data for development
        return {
            "total_isins": 125000,
            "valid_isins": 118500,
            "invalid_isins": 6500,
            "coverage_percentage": 94.8,
            "countries_covered": 67,
            "exchanges_covered": 143,
            "last_sync": "2024-12-08T10:30:00Z",
        }
    except Exception as e:
        logger.error(f"Error getting ISIN statistics: {e}")
        return None


def get_country_distribution() -> pd.DataFrame:
    """Get ISIN distribution by country."""
    try:
        # This would call the country distribution endpoint
        country_data = call_api("/isin/distribution/country")
        if country_data and country_data.get("success"):
            return pd.DataFrame(country_data.get("data", []))

        # Mock data for development
        countries = [
            {
                "country_code": "US",
                "country_name": "United States",
                "count": 45000,
                "percentage": 36.0,
            },
            {
                "country_code": "GB",
                "country_name": "United Kingdom",
                "count": 15000,
                "percentage": 12.0,
            },
            {
                "country_code": "DE",
                "country_name": "Germany",
                "count": 12000,
                "percentage": 9.6,
            },
            {
                "country_code": "FR",
                "country_name": "France",
                "count": 10000,
                "percentage": 8.0,
            },
            {
                "country_code": "JP",
                "country_name": "Japan",
                "count": 8500,
                "percentage": 6.8,
            },
            {
                "country_code": "CA",
                "country_name": "Canada",
                "count": 7500,
                "percentage": 6.0,
            },
            {
                "country_code": "CH",
                "country_name": "Switzerland",
                "count": 5000,
                "percentage": 4.0,
            },
            {
                "country_code": "AU",
                "country_name": "Australia",
                "count": 4500,
                "percentage": 3.6,
            },
            {
                "country_code": "NL",
                "country_name": "Netherlands",
                "count": 4000,
                "percentage": 3.2,
            },
            {
                "country_code": "IT",
                "country_name": "Italy",
                "count": 3500,
                "percentage": 2.8,
            },
            {
                "country_code": "Others",
                "country_name": "Other Countries",
                "count": 10000,
                "percentage": 8.0,
            },
        ]
        return pd.DataFrame(countries)
    except Exception as e:
        logger.error(f"Error getting country distribution: {e}")
        return pd.DataFrame()


def get_exchange_distribution() -> pd.DataFrame:
    """Get ISIN distribution by exchange."""
    try:
        # This would call the exchange distribution endpoint
        exchange_data = call_api("/isin/distribution/exchange")
        if exchange_data and exchange_data.get("success"):
            return pd.DataFrame(exchange_data.get("data", []))

        # Mock data for development
        exchanges = [
            {
                "exchange_code": "XNAS",
                "exchange_name": "NASDAQ",
                "country": "US",
                "count": 18000,
                "percentage": 14.4,
            },
            {
                "exchange_code": "XNYS",
                "exchange_name": "NYSE",
                "country": "US",
                "count": 15000,
                "percentage": 12.0,
            },
            {
                "exchange_code": "XLON",
                "exchange_name": "London Stock Exchange",
                "country": "GB",
                "count": 12000,
                "percentage": 9.6,
            },
            {
                "exchange_code": "XETR",
                "exchange_name": "XETRA",
                "country": "DE",
                "count": 8500,
                "percentage": 6.8,
            },
            {
                "exchange_code": "XPAR",
                "exchange_name": "Euronext Paris",
                "country": "FR",
                "count": 7500,
                "percentage": 6.0,
            },
            {
                "exchange_code": "XTKS",
                "exchange_name": "Tokyo Stock Exchange",
                "country": "JP",
                "count": 7000,
                "percentage": 5.6,
            },
            {
                "exchange_code": "XTSE",
                "exchange_name": "Toronto Stock Exchange",
                "country": "CA",
                "count": 6000,
                "percentage": 4.8,
            },
            {
                "exchange_code": "XSWX",
                "exchange_name": "SIX Swiss Exchange",
                "country": "CH",
                "count": 4500,
                "percentage": 3.6,
            },
            {
                "exchange_code": "XASX",
                "exchange_name": "Australian Securities Exchange",
                "country": "AU",
                "count": 4000,
                "percentage": 3.2,
            },
            {
                "exchange_code": "XAMS",
                "exchange_name": "Euronext Amsterdam",
                "country": "NL",
                "count": 3500,
                "percentage": 2.8,
            },
            {
                "exchange_code": "Others",
                "exchange_name": "Other Exchanges",
                "country": "Multiple",
                "count": 39000,
                "percentage": 31.2,
            },
        ]
        return pd.DataFrame(exchanges)
    except Exception as e:
        logger.error(f"Error getting exchange distribution: {e}")
        return pd.DataFrame()


def get_quality_metrics() -> dict[str, Any]:
    """Get data quality metrics."""
    try:
        quality_data = call_api("/isin/quality/metrics")
        if quality_data and quality_data.get("success"):
            return quality_data.get("data", {})

        # Mock data for development
        return {
            "overall_score": 92.5,
            "validation_accuracy": 97.8,
            "completeness": 94.2,
            "timeliness": 89.5,
            "consistency": 96.1,
        }
    except Exception as e:
        logger.error(f"Error getting quality metrics: {e}")
        return {}


def get_sync_activity() -> pd.DataFrame:
    """Get synchronization activity data."""
    try:
        sync_data = call_api("/isin/sync/activity")
        if sync_data and sync_data.get("success"):
            return pd.DataFrame(sync_data.get("data", []))

        # Mock data for development
        from datetime import datetime, timedelta

        import numpy as np

        dates = pd.date_range(
            start=datetime.now() - timedelta(days=30), end=datetime.now(), freq="D"
        )

        # Generate realistic sync activity data
        np.random.seed(42)
        base_syncs = 1000
        activity_data = []

        for date in dates:
            daily_syncs = base_syncs + np.random.normal(0, 200)
            success_rate = 0.95 + np.random.normal(0, 0.03)
            success_rate = max(0.85, min(0.99, success_rate))

            activity_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "total_syncs": int(max(500, daily_syncs)),
                    "successful_syncs": int(daily_syncs * success_rate),
                    "failed_syncs": int(daily_syncs * (1 - success_rate)),
                    "success_rate": success_rate * 100,
                    "avg_duration_ms": 150 + np.random.normal(0, 30),
                }
            )

        return pd.DataFrame(activity_data)
    except Exception as e:
        logger.error(f"Error getting sync activity: {e}")
        return pd.DataFrame()


def get_system_health() -> dict[str, Any]:
    """Get system health metrics."""
    try:
        health_data = call_api("/isin/health")
        if health_data and health_data.get("success"):
            return health_data.get("data", {})

        # Mock data for development
        return {
            "cache_hit_rate": 87.5,
            "avg_response_time": 125.3,
            "memory_usage": 68.2,
            "cpu_usage": 45.1,
            "active_connections": 23,
            "queue_length": 12,
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {}
