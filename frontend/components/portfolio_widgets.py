"""Portfolio widget components for the Financial Dashboard."""

import streamlit as st

from .portfolio_data import get_performance_data, get_portfolio_data, safe_float


def portfolio_overview_widget(backend_url: str):
    """Display portfolio overview with key metrics."""
    st.subheader("📊 Portfolio Overview")

    # Get user settings for currency formatting
    from frontend.services.settings import get_settings_manager

    settings_manager = get_settings_manager(backend_url)

    portfolio_data = get_portfolio_data(backend_url)

    if portfolio_data:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_value = safe_float(portfolio_data.get("total_value"))
            daily_change_pct = safe_float(portfolio_data.get("daily_change_pct"))
            st.metric(
                label="Total Portfolio Value",
                value=settings_manager.format_currency(total_value),
                delta=f"{daily_change_pct:.2f}%" if daily_change_pct != 0 else None,
            )

        with col2:
            cash_position = safe_float(portfolio_data.get("cash_balance"))
            st.metric(
                label="Cash Position",
                value=settings_manager.format_currency(cash_position),
                delta=None,
            )

        with col3:
            total_positions = portfolio_data.get("total_positions", 0)
            st.metric(label="Total Positions", value=total_positions, delta=None)

        with col4:
            ytd_return = safe_float(portfolio_data.get("total_gain_loss_percent"))
            st.metric(label="YTD Return", value=f"{ytd_return:.2f}%", delta=None)
    else:
        st.warning(
            "Unable to load portfolio data. Please check your backend connection."
        )


def performance_metrics_widget(backend_url: str):
    """Display performance metrics for different time periods."""
    st.subheader("📈 Performance Metrics")

    # Time period selector
    period_options = {
        "1D": "1 Day",
        "1W": "1 Week",
        "1M": "1 Month",
        "3M": "3 Months",
        "6M": "6 Months",
        "1Y": "1 Year",
        "YTD": "Year to Date",
    }

    col1, col2 = st.columns([1, 3])

    with col1:
        selected_period = st.selectbox(
            "Time Period",
            options=list(period_options.keys()),
            format_func=lambda x: period_options[x],
            index=2,  # Default to 1M
        )

    performance_data = get_performance_data(backend_url, selected_period or "1M")

    if performance_data:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_return = safe_float(performance_data.get("total_return_pct"))
            st.metric(label="Total Return", value=f"{total_return:.2f}%", delta=None)

        with col2:
            sharpe_ratio = safe_float(performance_data.get("sharpe_ratio"))
            st.metric(label="Sharpe Ratio", value=f"{sharpe_ratio:.3f}", delta=None)

        with col3:
            volatility = safe_float(performance_data.get("volatility"))
            st.metric(label="Volatility", value=f"{volatility:.2f}%", delta=None)

        with col4:
            max_drawdown = safe_float(performance_data.get("max_drawdown"))
            st.metric(label="Max Drawdown", value=f"{max_drawdown:.2f}%", delta=None)
    else:
        period_name = (
            period_options.get(selected_period, "selected period")
            if selected_period
            else "selected period"
        )
        st.info(f"Performance data for {period_name} is not available yet.")


def portfolio_summary_metrics(backend_url: str):
    """Display portfolio summary metrics."""
    import requests

    try:
        from frontend.components.auth import get_auth_headers, is_authenticated

        if not is_authenticated():
            st.error("Please log in to view portfolio summary.")
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
            if data.get("success"):
                summary = data["data"]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    from .portfolio_utils import safe_format_currency

                    total_value = safe_float(summary.get("total_market_value", 0))
                    st.metric(
                        "Total Portfolio Value", safe_format_currency(total_value)
                    )

                with col2:
                    total_cost = safe_float(summary.get("total_cost_basis", 0))
                    st.metric("Total Cost Basis", safe_format_currency(total_cost))

                with col3:
                    total_pnl = safe_float(summary.get("total_unrealized_pnl", 0))
                    pnl_pct = safe_float(summary.get("total_unrealized_pnl_percent", 0))
                    delta_color = "normal" if total_pnl >= 0 else "inverse"
                    st.metric(
                        "Unrealized P&L",
                        safe_format_currency(total_pnl),
                        f"{pnl_pct:.2f}%",
                        delta_color=delta_color,
                    )

                with col4:
                    position_count = summary.get("total_positions", 0)
                    st.metric("Total Positions", f"{position_count}")

                return summary
            st.error("Failed to fetch portfolio summary")
        elif response.status_code == 401:
            st.error("Authentication failed. Please log in again.")
        else:
            st.error(f"Failed to fetch portfolio summary: {response.status_code}")

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching portfolio summary: {e}")

    return None


def refresh_data_button(backend_url: str):
    """Button to refresh data and trigger background tasks."""
    from .portfolio_data import create_portfolio_snapshot, refresh_market_data

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🔄 Refresh Data", type="primary"):
            with st.spinner("Updating market data..."):
                refresh_market_data(backend_url)

    with col2:
        if st.button("💾 Create Snapshot"):
            with st.spinner("Creating portfolio snapshot..."):
                create_portfolio_snapshot(backend_url)

    with col3:
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh every 5 minutes")
        if auto_refresh:
            st.rerun()  # This would need proper implementation with session state
