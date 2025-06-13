"""Main Streamlit application for Financial Dashboard."""
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
                    "purchase_date": purchase_date.isoformat(),
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
    st.title("� Portfolio Analytics")

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

    tab1, tab2, tab3 = st.tabs(["General", "Data Sources", "Notifications"])

    with tab1:
        st.subheader("General Settings")

        # Theme
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])

        # Currency
        currency = st.selectbox("Default Currency", ["USD", "EUR", "GBP", "JPY"])

        # Date format
        date_format = st.selectbox(
            "Date Format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"]
        )

        if st.button("Save General Settings"):
            st.success("Settings saved!")

    with tab2:
        st.subheader("Data Source Configuration")

        # Market data provider
        provider = st.selectbox(
            "Market Data Provider", ["yfinance", "Alpha Vantage", "Custom"]
        )

        if provider == "Alpha Vantage":
            api_key = st.text_input("API Key", type="password")

        # Update frequency
        frequency = st.select_slider(
            "Update Frequency (minutes)",
            options=[1, 5, 15, 30, 60],
            value=15,
        )

        if st.button("Save Data Settings"):
            st.success("Data source settings saved!")

    with tab3:
        st.subheader("Notification Preferences")

        # Email notifications
        email_enabled = st.checkbox("Enable Email Notifications")
        if email_enabled:
            email = st.text_input("Email Address")

        # Alert types
        st.write("Alert Types:")
        price_alerts = st.checkbox("Price Alerts")
        performance_alerts = st.checkbox("Performance Alerts")
        news_alerts = st.checkbox("News Alerts")

        if st.button("Save Notification Settings"):
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

        # Current time
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Main content area
    if page == "Dashboard":
        show_dashboard()
    elif page == "Portfolio":
        show_portfolio()
    elif page == "Assets":
        show_assets()
    elif page == "Analytics":
        show_analytics()
    elif page == "Settings":
        show_settings()


def show_dashboard():
    """Show main dashboard page."""
    st.header("Dashboard Overview")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Portfolio Value",
            value="$0.00",
            delta="+0.00%",
        )

    with col2:
        st.metric(
            label="Today's Change",
            value="$0.00",
            delta="+0.00%",
        )

    with col3:
        st.metric(
            label="Total Assets",
            value="0",
        )

    with col4:
        st.metric(
            label="YTD Performance",
            value="+0.00%",
        )

    st.divider()

    # Placeholder for charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Portfolio Value Over Time")
        st.info("📊 Chart will be displayed here once data is available")

    with col2:
        st.subheader("Asset Allocation")
        st.info("🥧 Pie chart will be displayed here once data is available")

    # Recent activity
    st.subheader("Recent Activity")
    st.info("📋 Recent transactions and updates will appear here")


def show_portfolio():
    """Show portfolio page."""
    st.header("Portfolio Management")

    # Add position button
    if st.button("➕ Add New Position"):
        st.info("Position creation form will be implemented here")

    # Portfolio table
    st.subheader("Current Positions")
    st.info("📈 Your portfolio positions will be displayed here")


def show_assets():
    """Show assets page."""
    st.header("Asset Explorer")

    # Search bar
    search_term = st.text_input("🔍 Search for assets (stocks, bonds, etc.)")

    if search_term:
        st.info(f"Searching for: {search_term}")

    # Asset categories
    st.subheader("Browse by Category")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📈 Stocks", use_container_width=True):
            st.info("Stock listings will appear here")

    with col2:
        if st.button("📊 Bonds", use_container_width=True):
            st.info("Bond listings will appear here")

    with col3:
        if st.button("💵 Cash", use_container_width=True):
            st.info("Cash positions will appear here")

    with col4:
        if st.button("🏦 Other", use_container_width=True):
            st.info("Other assets will appear here")


def show_analytics():
    """Show analytics page."""
    st.header("Portfolio Analytics")

    # Analysis options
    analysis_type = st.selectbox(
        "Select Analysis Type",
        [
            "Performance Analysis",
            "Risk Metrics",
            "Allocation Analysis",
            "Historical Trends",
        ],
    )

    if analysis_type == "Performance Analysis":
        st.subheader("Performance Metrics")
        st.info("📊 Performance analytics will be displayed here")
    elif analysis_type == "Risk Metrics":
        st.subheader("Risk Analysis")
        st.info("⚠️ Risk metrics will be displayed here")
    elif analysis_type == "Allocation Analysis":
        st.subheader("Portfolio Allocation")
        st.info("🥧 Allocation analysis will be displayed here")
    elif analysis_type == "Historical Trends":
        st.subheader("Historical Performance")
        st.info("📈 Historical trends will be displayed here")


def show_settings():
    """Show settings page."""
    st.header("Settings")

    # Settings tabs
    tab1, tab2, tab3 = st.tabs(["General", "Data Sources", "Notifications"])

    with tab1:
        st.subheader("General Settings")

        # Theme
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])

        # Currency
        currency = st.selectbox("Default Currency", ["USD", "EUR", "GBP", "JPY"])

        # Date format
        date_format = st.selectbox(
            "Date Format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"]
        )

        if st.button("Save General Settings"):
            st.success("Settings saved!")

    with tab2:
        st.subheader("Data Source Configuration")

        # Market data provider
        provider = st.selectbox(
            "Market Data Provider", ["yfinance", "Alpha Vantage", "Custom"]
        )

        if provider == "Alpha Vantage":
            api_key = st.text_input("API Key", type="password")

        # Update frequency
        frequency = st.select_slider(
            "Update Frequency (minutes)",
            options=[1, 5, 15, 30, 60],
            value=15,
        )

        if st.button("Save Data Settings"):
            st.success("Data source settings saved!")

    with tab3:
        st.subheader("Notification Preferences")

        # Email notifications
        email_enabled = st.checkbox("Enable Email Notifications")
        if email_enabled:
            email = st.text_input("Email Address")

        # Alert types
        st.write("Alert Types:")
        price_alerts = st.checkbox("Price Alerts")
        performance_alerts = st.checkbox("Performance Alerts")
        news_alerts = st.checkbox("News Alerts")

        if st.button("Save Notification Settings"):
            st.success("Notification settings saved!")


if __name__ == "__main__":
    main()
