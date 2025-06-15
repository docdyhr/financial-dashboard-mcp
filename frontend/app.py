"""Enhanced Streamlit application for Financial Dashboard with complete UI."""

import os
from datetime import datetime

import requests
import streamlit as st
from components.portfolio import (
    asset_allocation_chart,
    holdings_table,
    performance_metrics_widget,
    portfolio_overview_widget,
    portfolio_value_chart,
    refresh_data_button,
)
from components.tasks import (
    submit_task_widget,
    system_status_widget,
    task_history_widget,
    task_monitoring_widget,
)

# Page config
st.set_page_config(
    page_title="Financial Dashboard",
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

        col1, col2 = st.columns(2)

        with col1:
            symbol = st.text_input("Stock Symbol", placeholder="e.g., AAPL")
            quantity = st.number_input("Quantity", min_value=0.0, step=0.01)
            purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01)

        with col2:
            purchase_date = st.date_input("Purchase Date")
            asset_type = st.selectbox(
                "Asset Type", ["Stock", "Bond", "ETF", "Mutual Fund", "Other"]
            )
            notes = st.text_area("Notes (optional)")

        if st.button("Add Position", type="primary"):
            if symbol and quantity > 0 and purchase_price > 0:
                position_data = {
                    "symbol": symbol.upper(),
                    "quantity": quantity,
                    "purchase_price": purchase_price,
                    "purchase_date": str(purchase_date),
                    "asset_type": asset_type,
                    "notes": notes,
                }

                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/portfolio/positions",
                        json=position_data,
                        timeout=10,
                    )
                    if response.status_code == 200:
                        st.success(f"Position {symbol} added successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to add position: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error adding position: {e}")
            else:
                st.warning("Please fill in all required fields.")

    with tab3:
        st.info("Transaction history will be available in a future update.")


def tasks_page():
    """Task management and monitoring page."""
    st.title("⚙️ Task Management")

    # System status overview
    system_status_widget(BACKEND_URL)
    st.divider()

    # Two-column layout
    col1, col2 = st.columns([2, 1])

    with col1:
        task_monitoring_widget(BACKEND_URL)
        st.divider()
        task_history_widget(BACKEND_URL)

    with col2:
        submit_task_widget(BACKEND_URL)


def analytics_page():
    """Advanced analytics and insights page."""
    st.title("📈 Portfolio Analytics")

    tab1, tab2, tab3 = st.tabs(["Performance Analysis", "Risk Metrics", "Benchmarking"])

    with tab1:
        st.subheader("Performance Analysis")
        performance_metrics_widget(BACKEND_URL)

        st.divider()
        portfolio_value_chart(BACKEND_URL)

    with tab2:
        st.subheader("Risk Metrics")
        st.info(
            "Advanced risk metrics (VaR, Beta, Correlation) will be available soon."
        )

        # Placeholder for risk metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Portfolio Beta", "1.15", delta="0.05")
        with col2:
            st.metric("Value at Risk (95%)", "-$2,450", delta="-$120")
        with col3:
            st.metric("Max Drawdown", "-8.5%", delta="-1.2%")

    with tab3:
        st.subheader("Benchmark Comparison")
        st.info("Benchmark comparison features will be available soon.")

        # Placeholder for benchmark comparison
        benchmark_options = ["S&P 500", "NASDAQ", "Dow Jones", "Custom"]
        selected_benchmark = st.selectbox("Select Benchmark", benchmark_options)
        st.write(f"Comparing portfolio against {selected_benchmark}...")


def settings_page():
    """Settings and configuration page."""
    st.title("⚙️ Settings")

    # Initialize settings in session state if not present
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "theme": "Light",
            "currency": "USD",
            "date_format": "MM/DD/YYYY",
            "provider": "yfinance",
            "api_key": "",
            "frequency": 15,
            "email_enabled": False,
            "email": "",
            "price_alerts": False,
            "performance_alerts": False,
            "news_alerts": False,
        }

    tab1, tab2, tab3 = st.tabs(["General", "Data Sources", "Notifications"])

    with tab1:
        st.subheader("General Settings")

        # Theme
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark", "Auto"],
            index=["Light", "Dark", "Auto"].index(st.session_state.settings["theme"]),
        )

        # Currency
        currency = st.selectbox(
            "Default Currency",
            ["USD", "EUR", "GBP", "JPY"],
            index=["USD", "EUR", "GBP", "JPY"].index(
                st.session_state.settings["currency"]
            ),
        )

        # Date format
        date_format = st.selectbox(
            "Date Format",
            ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
            index=["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"].index(
                st.session_state.settings["date_format"]
            ),
        )

        if st.button("Save General Settings"):
            st.session_state.settings["theme"] = theme
            st.session_state.settings["currency"] = currency
            st.session_state.settings["date_format"] = date_format
            st.success("Settings saved!")

    with tab2:
        st.subheader("Data Source Configuration")

        # Market data provider
        provider = st.selectbox(
            "Market Data Provider",
            ["yfinance", "Alpha Vantage", "Custom"],
            index=["yfinance", "Alpha Vantage", "Custom"].index(
                st.session_state.settings["provider"]
            ),
        )

        api_key = ""
        if provider == "Alpha Vantage":
            api_key = st.text_input(
                "API Key", type="password", value=st.session_state.settings["api_key"]
            )

        # Update frequency
        frequency = st.select_slider(
            "Update Frequency (minutes)",
            options=[1, 5, 15, 30, 60],
            value=st.session_state.settings["frequency"],
        )

        if st.button("Save Data Settings"):
            st.session_state.settings["provider"] = provider
            st.session_state.settings["api_key"] = api_key
            st.session_state.settings["frequency"] = frequency
            st.success("Data source settings saved!")

    with tab3:
        st.subheader("Notification Preferences")

        # Email notifications
        email_enabled = st.checkbox(
            "Enable Email Notifications",
            value=st.session_state.settings["email_enabled"],
        )

        email = ""
        if email_enabled:
            email = st.text_input(
                "Email Address", value=st.session_state.settings["email"]
            )

        # Alert types
        st.write("Alert Types:")
        price_alerts = st.checkbox(
            "Price Alerts", value=st.session_state.settings["price_alerts"]
        )
        performance_alerts = st.checkbox(
            "Performance Alerts", value=st.session_state.settings["performance_alerts"]
        )
        news_alerts = st.checkbox(
            "News Alerts", value=st.session_state.settings["news_alerts"]
        )

        if st.button("Save Notification Settings"):
            st.session_state.settings["email_enabled"] = email_enabled
            st.session_state.settings["email"] = email
            st.session_state.settings["price_alerts"] = price_alerts
            st.session_state.settings["performance_alerts"] = performance_alerts
            st.session_state.settings["news_alerts"] = news_alerts
            st.success("Notification settings saved!")


def main():
    """Main application function."""
    # Header
    st.markdown("# 💰 Financial Dashboard")
    st.markdown("*Powered by real-time task queue system*")

    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        page = st.selectbox(
            "Choose a page",
            ["Dashboard", "Portfolio", "Tasks", "Analytics", "Settings"],
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

        # Last updated
        st.divider()
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    # Main content based on selected page
    if page == "Dashboard":
        dashboard_page()
    elif page == "Portfolio":
        portfolio_page()
    elif page == "Tasks":
        tasks_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "Settings":
        settings_page()


if __name__ == "__main__":
    main()
