"""Authentication components for Streamlit frontend."""

import os
from typing import Any

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """Authenticate user with backend and return token info."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data={
                "username": username,
                "password": password,
                "grant_type": "password",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5,
        )

        if response.status_code == 200:
            token_data = response.json()
            return {
                "access_token": token_data["access_token"],
                "token_type": token_data["token_type"],
            }
        return None

    except requests.exceptions.RequestException:
        return None


def get_user_info(token: str) -> dict[str, Any] | None:
    """Get user information using the access token."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers=headers,
            timeout=5,
        )

        if response.status_code == 200:
            return response.json()
        return None

    except requests.exceptions.RequestException:
        return None


def is_authenticated() -> bool:
    """Check if user is currently authenticated."""
    return (
        "access_token" in st.session_state and st.session_state.access_token is not None
    )


def get_auth_headers() -> dict[str, str]:
    """Get authentication headers for API requests."""
    if is_authenticated():
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}


def logout():
    """Clear authentication session."""
    if "access_token" in st.session_state:
        del st.session_state.access_token
    if "user_info" in st.session_state:
        del st.session_state.user_info
    st.rerun()


def login_form():
    """Display login form and handle authentication."""
    st.markdown("## 🔐 Login to Financial Dashboard")
    st.markdown("*Please enter your credentials to access your portfolio*")

    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            username = st.text_input(
                "Username or Email",
                placeholder="Enter your username or email",
                help="Use your registered username or email address",
            )
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password"
            )

            login_button = st.form_submit_button(
                "🔑 Login", use_container_width=True, type="primary"
            )

    if login_button:
        if not username or not password:
            st.error("Please enter both username and password.")
            return False

        with st.spinner("Authenticating..."):
            token_data = authenticate_user(username, password)

        if token_data:
            # Store authentication data
            st.session_state.access_token = token_data["access_token"]

            # Get user information
            user_info = get_user_info(token_data["access_token"])
            if user_info:
                st.session_state.user_info = user_info
                st.success(f"Welcome back, {user_info.get('full_name', username)}!")
                st.rerun()
            else:
                st.error("Failed to retrieve user information.")
                return False
        else:
            st.error("Invalid username or password. Please try again.")
            return False

    # Demo credentials info
    with st.expander("📝 Demo Credentials", expanded=False):
        st.info(
            """
        **For testing purposes, use:**
        - **Username:** user@example.com
        - **Password:** demo123

        *Note: These are demo credentials for the default user created during database setup.*
        """
        )

    return False


def require_authentication():
    """Decorator-like function to require authentication."""
    if not is_authenticated():
        login_form()
        return False
    return True


def with_authentication(func):
    """Decorator to require authentication for a function."""

    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.error("Please log in to access this feature.")
            login_form()
            return None
        return func(*args, **kwargs)

    return wrapper


def check_auth_or_redirect():
    """Check authentication and show login form if not authenticated."""
    if not is_authenticated():
        st.error("Please log in to access this feature.")
        login_form()
        return False
    return True


def show_user_info():
    """Display current user information in sidebar."""
    if is_authenticated() and "user_info" in st.session_state:
        user_info = st.session_state.user_info

        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Info")
            st.markdown(f"**Name:** {user_info.get('full_name', 'N/A')}")
            st.markdown(f"**Email:** {user_info.get('email', 'N/A')}")

            if st.button("🚪 Logout", use_container_width=True):
                logout()


def protected_request(method: str, url: str, **kwargs) -> requests.Response | None:
    """Make authenticated API request."""
    if not is_authenticated():
        return None

    headers = kwargs.get("headers", {})
    headers.update(get_auth_headers())
    kwargs["headers"] = headers

    try:
        response = getattr(requests, method.lower())(url, **kwargs)

        # Handle token expiration
        if response.status_code == 401:
            st.error("Your session has expired. Please login again.")
            logout()
            return None

        return response

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None
