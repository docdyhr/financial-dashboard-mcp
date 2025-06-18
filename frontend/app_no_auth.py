"""Non-authenticated version of the Financial Dashboard for development/demo."""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import streamlit as st

from frontend.components.backup_export import backup_export_page
from frontend.components.enhanced_charts import enhanced_analytics_page
from frontend.components.enhanced_portfolio import enhanced_portfolio_page
from frontend.components.isin_analytics_dashboard import isin_analytics_dashboard
from frontend.components.isin_input import isin_management_page
from frontend.components.isin_sync_monitor import isin_sync_monitor_page
from frontend.components.portfolio import (
    asset_allocation_chart,
    holdings_table,
    performance_metrics_widget,
    portfolio_overview_widget,
    portfolio_value_chart,
    refresh_data_button,
)
from frontend.components.tasks import (
    submit_task_widget,
    system_status_widget,
    task_history_widget,
    task_monitoring_widget,
)

# Page config
st.set_page_config(
    page_title="Financial Dashboard (Demo)",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Backend URL configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def check_backend_health():
    """Check if backend is healthy."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def dashboard_page():
    """Main dashboard page with portfolio overview."""
    st.title("💰 Portfolio Dashboard")
    st.markdown("*Real-time portfolio monitoring and analysis*")

    # Refresh data controls
    refresh_data_button(BACKEND_URL)
    st.divider()

    # Main portfolio metrics
    portfolio_overview_widget(BACKEND_URL)
    st.divider()

    # Performance metrics
    performance_metrics_widget(BACKEND_URL)
    st.divider()

    # Two-column layout for charts
    col1, col2 = st.columns(2)

    with col1:
        asset_allocation_chart(BACKEND_URL)

    with col2:
        portfolio_value_chart(BACKEND_URL)

    st.divider()

    # Holdings table
    holdings_table(BACKEND_URL)


def portfolio_page():
    """Portfolio management page."""
    st.title("📊 Portfolio Management")

    tab1, tab2, tab3 = st.tabs(
        ["Current Holdings", "Add Position", "Transaction History"]
    )

    with tab1:
        holdings_table(BACKEND_URL)

    with tab2:
        st.subheader("Add New Position")

        # Simple form for adding positions
        with st.form("add_position"):
            col1, col2 = st.columns(2)

            with col1:
                ticker = st.text_input("Ticker Symbol", placeholder="e.g., AAPL")
                quantity = st.number_input("Quantity", min_value=0.0001, step=0.1)

            with col2:
                purchase_price = st.number_input(
                    "Purchase Price", min_value=0.01, step=0.01
                )
                purchase_date = st.date_input("Purchase Date")

            if st.form_submit_button("Add Position", type="primary"):
                if ticker and quantity and purchase_price:
                    st.success(
                        f"Added {quantity} shares of {ticker} at ${purchase_price}"
                    )
                    st.info(
                        "Note: Authentication is required for actual portfolio updates"
                    )
                else:
                    st.error("Please fill all fields")

    with tab3:
        st.subheader("Transaction History")
        st.info("Transaction history will be available when authentication is enabled")


def tasks_page():
    """Task monitoring page."""
    st.title("🛠️ Task Management")

    # System status
    system_status_widget(BACKEND_URL)
    st.divider()

    # Task submission
    submit_task_widget(BACKEND_URL)
    st.divider()

    # Task monitoring
    task_monitoring_widget(BACKEND_URL)
    st.divider()

    # Task history
    task_history_widget(BACKEND_URL)


def analytics_page():
    """Analytics and reporting page."""
    enhanced_analytics_page()


def settings_page():
    """Settings and configuration page."""
    st.title("⚙️ Settings")
    st.markdown("Configuration options for your dashboard")

    with st.expander("🔒 Authentication Status", expanded=True):
        st.warning(
            """
        **Demo Mode Active**

        Authentication is implemented but currently disabled for demo purposes.

        **Features:**
        - ✅ JWT token-based authentication
        - ✅ Password hashing with bcrypt
        - ✅ Protected API endpoints
        - ✅ User session management
        - ✅ Login/logout functionality

        **To enable authentication:**
        1. Fix bcrypt version compatibility in Docker
        2. Replace `frontend/app_no_auth.py` with `frontend/app.py`
        3. Restart the frontend container
        """
        )

    st.markdown(
        "🔧 Advanced configuration options will be available in a future update."
    )


def main():
    """Main application function."""
    # Initialize session state for navigation
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    # Header
    st.markdown("# 💰 Financial Dashboard (Demo Mode)")
    st.markdown("*Powered by real-time task queue system*")

    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        page = st.selectbox(
            "Choose a page",
            [
                "Dashboard",
                "Portfolio",
                "Enhanced Portfolio",
                "ISIN Management",
                "ISIN Sync Monitor",
                "ISIN Analytics",
                "Tasks",
                "Enhanced Analytics",
                "Backup & Export",
                "Settings",
            ],
            key="page",
        )

        st.divider()

        # Backend status
        st.subheader("🔧 System Status")
        backend_status = check_backend_health()
        if backend_status:
            st.success("✅ Backend: Online")
        else:
            st.error("❌ Backend: Offline")

        # Quick links
        st.divider()
        st.subheader("🔗 Quick Links")
        st.markdown("- [Flower UI](http://localhost:5555)")
        st.markdown("- [API Docs](http://localhost:8000/docs)")
        st.markdown("- [GitHub](https://github.com/docdyhr/financial-dashboard-mcp)")

        # Demo note
        st.divider()
        st.warning("**Demo Mode**: Authentication disabled for development")

        # Last updated
        st.divider()
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    # Main content based on selected page
    if page == "Dashboard":
        dashboard_page()
    elif page == "Portfolio":
        portfolio_page()
    elif page == "Enhanced Portfolio":
        enhanced_portfolio_page()
    elif page == "ISIN Management":
        isin_management_page()
    elif page == "ISIN Sync Monitor":
        isin_sync_monitor_page()
    elif page == "ISIN Analytics":
        isin_analytics_dashboard()
    elif page == "Tasks":
        tasks_page()
    elif page == "Enhanced Analytics":
        analytics_page()
    elif page == "Backup & Export":
        backup_export_page()
    elif page == "Settings":
        settings_page()


if __name__ == "__main__":
    main()
