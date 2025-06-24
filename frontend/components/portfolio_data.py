"""Portfolio data fetching services for the Financial Dashboard."""

import requests
import streamlit as st


def safe_float(value, default=0.0):
    """Safely convert a value to float, handling None and invalid values."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_portfolio_data(backend_url: str) -> dict | None:
    """Fetch portfolio data from the backend API."""
    try:
        from frontend.components.auth import check_auth_or_redirect, get_auth_headers

        if not check_auth_or_redirect():
            return None

        # Get current user info to get user ID
        if "user_info" not in st.session_state:
            st.error("User information not available. Please log in again.")
            return None

        user_id = st.session_state.user_info.get("id")
        if not user_id:
            st.error("User ID not found. Please log in again.")
            return None

        response = requests.get(
            f"{backend_url}/api/v1/portfolio/summary/{user_id}",
            headers=get_auth_headers(),
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data") if data.get("success") else None
        if response.status_code == 401:
            st.error("Authentication failed. Please log in again.")
            return None
        st.error(f"Failed to fetch portfolio data: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None


def get_positions_data(backend_url: str) -> list[dict] | None:
    """Fetch positions data from the backend API."""
    try:
        from frontend.components.auth import get_auth_headers, is_authenticated

        if not is_authenticated():
            st.error("Please log in to view positions data.")
            return None

        user_id = st.session_state.user_info.get("id")
        if not user_id:
            st.error("User ID not found. Please log in again.")
            return None

        response = requests.get(
            f"{backend_url}/api/v1/positions/?user_id={user_id}",
            headers=get_auth_headers(),
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data") if data.get("success") else None
        if response.status_code == 401:
            st.error("Authentication failed. Please log in again.")
            return None
        st.error(f"Failed to fetch positions data: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None


def get_performance_data(backend_url: str, period: str = "1M") -> dict | None:
    """Fetch performance data from the backend API."""
    try:
        response = requests.get(
            f"{backend_url}/api/v1/portfolio/performance/5?period={period}", timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data") if data.get("success") else None
        st.error(f"Failed to fetch performance data: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None


def refresh_market_data(backend_url: str) -> bool:
    """Trigger market data refresh task."""
    try:
        response = requests.post(
            f"{backend_url}/api/v1/tasks/portfolio-prices",
            json={"user_id": 5},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code == 200:
            task_data = response.json()
            st.success(
                f"Data refresh started! Task ID: {task_data.get('task_id', 'N/A')}"
            )
            return True
        st.error("Failed to start data refresh")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Error triggering data refresh: {e}")
        return False


def create_portfolio_snapshot(backend_url: str) -> bool:
    """Create portfolio snapshot task."""
    try:
        response = requests.post(
            f"{backend_url}/api/v1/tasks/portfolio-snapshot",
            json={"user_id": 5},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code == 200:
            task_data = response.json()
            st.success(
                f"Snapshot creation started! Task ID: {task_data.get('task_id', 'N/A')}"
            )
            return True
        st.error("Failed to create snapshot")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating snapshot: {e}")
        return False
