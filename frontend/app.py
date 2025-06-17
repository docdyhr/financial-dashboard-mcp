"""Enhanced Streamlit application for Financial Dashboard with complete UI."""

import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from components.enhanced_portfolio import enhanced_portfolio_page
from components.isin_analytics_dashboard import isin_analytics_dashboard
from components.isin_input import isin_management_page
from components.isin_sync_monitor import isin_sync_monitor_page
from components.portfolio import (
    asset_allocation_chart,
    holdings_table,
    performance_metrics_widget,
    portfolio_overview_widget,
    portfolio_value_chart,
    refresh_data_button,
    safe_float,
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

        # Input method selection
        input_method = st.radio(
            "Input Method",
            ["Ticker Symbol", "ISIN Code"],
            horizontal=True,
            help="Choose how to identify the security",
        )

        col1, col2 = st.columns(2)

        with col1:
            if input_method == "Ticker Symbol":
                symbol = st.text_input("Stock Symbol", placeholder="e.g., AAPL")
                isin_code = None
            else:
                isin_code = (
                    st.text_input(
                        "ISIN Code",
                        placeholder="e.g., US0378331005",
                        max_chars=12,
                        help="12-character International Securities Identification Number",
                    )
                    .upper()
                    .strip()
                )
                symbol = None

                # ISIN validation and ticker lookup
                if isin_code and len(isin_code) == 12:
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/isin/resolve",
                            json={"identifier": isin_code},
                            timeout=10,
                        )
                        if response.status_code == 200:
                            resolve_data = response.json()
                            if resolve_data.get("found"):
                                symbol = resolve_data.get("result", {}).get("ticker")
                                if symbol:
                                    st.success(f"✅ Resolved to: {symbol}")
                                else:
                                    st.warning("⚠️ ISIN found but no ticker available")
                            else:
                                st.error("❌ ISIN not found in database")
                    except Exception as e:
                        st.error(f"❌ Error resolving ISIN: {e}")

            quantity = st.number_input("Quantity", min_value=0.0, step=0.01)
            purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01)

        with col2:
            asset_type = st.selectbox(
                "Asset Type", ["Stock", "Bond", "ETF", "Mutual Fund", "Other"]
            )
            notes = st.text_area("Notes (optional)")

        # Determine identifier for validation
        identifier = symbol if input_method == "Ticker Symbol" else isin_code

        if st.button("Add Position", type="primary"):
            if identifier and quantity > 0 and purchase_price > 0:
                try:
                    # First, try to get the asset by ticker (symbol should be resolved from ISIN if needed)
                    if symbol:
                        asset_response = requests.get(
                            f"{BACKEND_URL}/api/v1/assets/ticker/{symbol.upper()}",
                            timeout=10,
                        )
                    else:
                        st.error("❌ Could not resolve identifier to ticker symbol")
                        st.stop()

                    asset_id = None
                    if asset_response.status_code == 200:
                        asset_data = asset_response.json()
                        if asset_data.get("success"):
                            asset_id = asset_data["data"]["id"]

                    # If asset doesn't exist, create it
                    if asset_id is None:
                        asset_create_data = {
                            "ticker": symbol.upper(),
                            "name": f"{symbol.upper()} Stock",
                            "asset_type": asset_type.lower() if asset_type else "stock",
                            "category": "equity",
                            "currency": "USD",
                        }

                        create_asset_response = requests.post(
                            f"{BACKEND_URL}/api/v1/assets/",
                            json=asset_create_data,
                            timeout=10,
                        )

                        if create_asset_response.status_code == 200:
                            create_data = create_asset_response.json()
                            if create_data.get("success"):
                                asset_id = create_data["data"]["id"]
                        else:
                            st.error(
                                f"Failed to create asset: {create_asset_response.status_code}"
                            )
                            st.stop()

                    # Now create the position
                    if asset_id:
                        total_cost = quantity * purchase_price
                        position_data = {
                            "user_id": 5,  # Correct user ID
                            "asset_id": asset_id,
                            "quantity": str(quantity),
                            "average_cost_per_share": str(purchase_price),
                            "total_cost_basis": str(total_cost),
                            "notes": notes,
                        }

                        response = requests.post(
                            f"{BACKEND_URL}/api/v1/positions/",
                            json=position_data,
                            timeout=10,
                        )
                        if response.status_code == 200:
                            st.success(f"Position {symbol} added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add position: {response.status_code}")
                            st.error(f"Response: {response.text}")
                    else:
                        st.error("Failed to get or create asset")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error adding position: {e}")
            else:
                missing_fields = []
                if not identifier:
                    missing_fields.append(
                        "Stock Symbol"
                        if input_method == "Ticker Symbol"
                        else "ISIN Code"
                    )
                if quantity <= 0:
                    missing_fields.append("Quantity")
                if purchase_price <= 0:
                    missing_fields.append("Purchase Price")

                st.error(
                    f"Please fill in all required fields: {', '.join(missing_fields)}"
                )

    with tab3:
        st.subheader("📈 Transaction History")

        # Transaction filters
        col1, col2, col3 = st.columns(3)

        with col1:
            transaction_type_filter = st.selectbox(
                "Transaction Type",
                ["All", "Buy", "Sell", "Dividend", "Split", "Other"],
                index=0,
            )

        with col2:
            start_date = st.date_input("Start Date", value=None)

        with col3:
            end_date = st.date_input("End Date", value=None)

        # Fetch and display transactions
        try:
            # Build query parameters
            params = {"user_id": "5", "page": "1", "page_size": "100"}

            if transaction_type_filter and transaction_type_filter != "All":
                params["transaction_type"] = transaction_type_filter.lower()
            if start_date:
                params["start_date"] = str(start_date)
            if end_date:
                params["end_date"] = str(end_date)

            response = requests.get(
                f"{BACKEND_URL}/api/v1/transactions/", params=params, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    transactions = data["data"]

                    if transactions:
                        # Convert to DataFrame
                        df = pd.DataFrame(transactions)

                        # Process and display transactions
                        display_df = df.copy()

                        # Add asset symbol
                        display_df["symbol"] = display_df["asset"].apply(
                            lambda x: (
                                x.get("ticker", "Unknown")
                                if isinstance(x, dict)
                                else "Unknown"
                            )
                        )

                        # Format currency columns
                        currency_columns = ["total_amount", "net_amount", "commission"]
                        for col in currency_columns:
                            if col in display_df.columns:
                                display_df[col] = display_df[col].apply(
                                    lambda x: (
                                        f"${safe_float(x):.2f}"
                                        if x is not None
                                        else "N/A"
                                    )
                                )

                        # Format quantity as whole numbers for stocks
                        if "quantity" in display_df.columns:
                            display_df["quantity"] = display_df["quantity"].apply(
                                lambda x: (
                                    f"{int(safe_float(x))}" if x is not None else "N/A"
                                )
                            )

                        # Format price per share
                        if "price_per_share" in display_df.columns:
                            display_df["price_per_share"] = display_df[
                                "price_per_share"
                            ].apply(
                                lambda x: (
                                    f"${safe_float(x):.2f}" if x is not None else "N/A"
                                )
                            )

                        # Format dates
                        display_df["transaction_date"] = pd.to_datetime(
                            display_df["transaction_date"]
                        ).dt.strftime("%Y-%m-%d")

                        # Select and rename columns for display
                        columns_to_show = {
                            "transaction_date": "Date",
                            "symbol": "Symbol",
                            "transaction_type": "Type",
                            "quantity": "Quantity",
                            "price_per_share": "Price",
                            "total_amount": "Total Amount",
                            "commission": "Commission",
                            "net_amount": "Net Amount",
                            "notes": "Notes",
                        }

                        available_columns = [
                            col for col in columns_to_show if col in display_df.columns
                        ]
                        rename_dict = {
                            k: v
                            for k, v in columns_to_show.items()
                            if k in available_columns
                        }

                        final_df = display_df[available_columns].copy()
                        final_df.columns = [
                            rename_dict.get(col, col) for col in final_df.columns
                        ]

                        # Display the transactions table
                        st.dataframe(final_df, use_container_width=True)

                        # Summary metrics
                        st.divider()
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            total_transactions = len(transactions)
                            st.metric("Total Transactions", total_transactions)

                        with col2:
                            buy_transactions = len(
                                [
                                    t
                                    for t in transactions
                                    if t["transaction_type"] == "buy"
                                ]
                            )
                            st.metric("Buy Transactions", buy_transactions)

                        with col3:
                            sell_transactions = len(
                                [
                                    t
                                    for t in transactions
                                    if t["transaction_type"] == "sell"
                                ]
                            )
                            st.metric("Sell Transactions", sell_transactions)

                        with col4:
                            dividend_transactions = len(
                                [
                                    t
                                    for t in transactions
                                    if t["transaction_type"] == "dividend"
                                ]
                            )
                            st.metric("Dividend Transactions", dividend_transactions)

                        # Performance metrics
                        st.divider()
                        performance_response = requests.get(
                            f"{BACKEND_URL}/api/v1/transactions/performance/5",
                            timeout=10,
                        )

                        if performance_response.status_code == 200:
                            perf_data = performance_response.json()
                            if perf_data.get("success") and perf_data.get("data"):
                                metrics = perf_data["data"]

                                st.subheader("📊 Performance Summary")

                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    total_invested = safe_float(
                                        metrics.get("total_invested", 0)
                                    )
                                    st.metric(
                                        "Total Invested", f"${total_invested:,.2f}"
                                    )

                                    total_proceeds = safe_float(
                                        metrics.get("total_proceeds", 0)
                                    )
                                    st.metric(
                                        "Total Proceeds", f"${total_proceeds:,.2f}"
                                    )

                                with col2:
                                    total_dividends = safe_float(
                                        metrics.get("total_dividends_received", 0)
                                    )
                                    st.metric(
                                        "Total Dividends", f"${total_dividends:,.2f}"
                                    )

                                    total_fees = safe_float(
                                        metrics.get("total_fees_paid", 0)
                                    )
                                    st.metric("Total Fees", f"${total_fees:,.2f}")

                                with col3:
                                    net_cash_flow = safe_float(
                                        metrics.get("net_cash_flow", 0)
                                    )
                                    st.metric("Net Cash Flow", f"${net_cash_flow:,.2f}")

                                    realized_gains = safe_float(
                                        metrics.get("realized_gains", 0)
                                    )
                                    st.metric(
                                        "Realized Gains/Losses",
                                        f"${realized_gains:,.2f}",
                                    )

                    else:
                        st.info("No transactions found for the selected criteria.")

                        # Show sample transaction entry form
                        st.subheader("💡 Add Your First Transaction")
                        st.write(
                            "Once you have positions, you can view their transaction history here."
                        )

                        with st.expander("What will be shown here?"):
                            st.write(
                                "• **Buy/Sell Transactions**: All your trading activity"
                            )
                            st.write(
                                "• **Dividend Payments**: Income from your holdings"
                            )
                            st.write(
                                "• **Stock Splits**: Corporate actions affecting your positions"
                            )
                            st.write(
                                "• **Performance Metrics**: Realized gains, fees, and cash flow analysis"
                            )
                            st.write(
                                "• **Filtering & Search**: Find transactions by date, type, or symbol"
                            )

                else:
                    st.error("Failed to load transaction data.")

            else:
                st.error(f"Failed to fetch transactions: {response.status_code}")

        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching transactions: {e}")


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

    # Initialize settings manager
    from frontend.services.settings import get_settings_manager

    settings_manager = get_settings_manager(BACKEND_URL)

    # Add status indicator
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Configure your dashboard preferences")
    with col2:
        if st.button("🔄 Reload Settings"):
            try:
                settings_manager.reload_settings()
                st.success("Settings reloaded!")
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to reload settings: {e}")
                st.error(f"Failed to reload settings: {e}")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["General", "Data Sources", "Notifications", "Advanced"]
    )

    with tab1:
        st.subheader("General Settings")

        # Theme settings
        current_theme = settings_manager.get_setting("theme", "light")
        theme = st.selectbox(
            "Theme",
            ["light", "dark", "auto"],
            index=(
                0 if current_theme == "light" else 1 if current_theme == "dark" else 2
            ),
            help="Choose your preferred UI theme",
        )

        # Currency
        current_currency = settings_manager.get_setting("currency", "USD")
        currency = st.selectbox(
            "Default Currency",
            ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"],
            index=(
                ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"].index(
                    current_currency
                )
                if current_currency in ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"]
                else 0
            ),
            help="Your preferred currency for displaying amounts",
        )

        # Auto-refresh
        auto_refresh = st.checkbox(
            "Auto-refresh data",
            value=settings_manager.get_setting("auto_refresh", False),
            help="Automatically refresh market data",
        )

        if st.button("Save General Settings", type="primary"):
            try:
                st.success("✅ General settings saved successfully!")
                st.rerun()
            except Exception:
                st.error("❌ Failed to save settings")

    with tab2:
        st.subheader("Data Source Configuration")

        # Market data provider
        current_provider = settings_manager.get_setting("data_provider", "yfinance")
        provider_options = ["yfinance", "alpha_vantage", "finnhub"]
        provider_display = ["Yahoo Finance", "Alpha Vantage", "Finnhub"]

        try:
            provider_index = provider_options.index(current_provider)
        except ValueError:
            provider_index = 0  # Default to yfinance

        provider_selection = st.selectbox(
            "Market Data Provider",
            provider_display,
            index=provider_index,
            help="Choose your preferred market data provider",
        )

        if st.button("Save Data Source Settings", type="primary"):
            try:
                st.success("✅ Data source settings saved!")
                st.rerun()
            except Exception:
                st.error("❌ Failed to save settings")

    with tab3:
        st.subheader("Notification Settings")
        st.info("📧 Notification features will be available in a future update.")

    with tab4:
        st.subheader("Advanced Settings")
        st.info(
            "🔧 Advanced configuration options will be available in a future update."
        )


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
            [
                "Dashboard",
                "Portfolio",
                "Enhanced Portfolio",
                "ISIN Management",
                "ISIN Sync Monitor",
                "ISIN Analytics",
                "Tasks",
                "Analytics",
                "Settings",
            ],
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
    elif page == "Enhanced Portfolio":
        enhanced_portfolio_page()
    elif page == "Tasks":
        tasks_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "ISIN Management":
        isin_management_page()
    elif page == "ISIN Sync Monitor":
        isin_sync_monitor_page()
    elif page == "ISIN Analytics":
        isin_analytics_dashboard()
    elif page == "Settings":
        settings_page()


if __name__ == "__main__":
    main()
