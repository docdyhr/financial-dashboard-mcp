"""Portfolio overview components for the Financial Dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


def get_portfolio_data(backend_url: str) -> dict | None:
    """Fetch portfolio data from the backend API."""
    try:
        response = requests.get(f"{backend_url}/api/portfolio/summary", timeout=10)
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch portfolio data: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None


def get_positions_data(backend_url: str) -> list[dict] | None:
    """Fetch positions data from the backend API."""
    try:
        response = requests.get(f"{backend_url}/api/portfolio/positions", timeout=10)
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch positions data: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None


def get_performance_data(backend_url: str, period: str = "1M") -> dict | None:
    """Fetch performance data from the backend API."""
    try:
        response = requests.get(
            f"{backend_url}/api/portfolio/performance?period={period}", timeout=10
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch performance data: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None


def portfolio_overview_widget(backend_url: str):
    """Display portfolio overview with key metrics."""
    st.subheader("📊 Portfolio Overview")

    portfolio_data = get_portfolio_data(backend_url)

    if portfolio_data:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_value = portfolio_data.get("total_value", 0)
            st.metric(
                label="Total Portfolio Value",
                value=f"${total_value:,.2f}",
                delta=f"{portfolio_data.get('daily_change_pct', 0):.2f}%",
            )

        with col2:
            cash_position = portfolio_data.get("cash_position", 0)
            st.metric(label="Cash Position", value=f"${cash_position:,.2f}", delta=None)

        with col3:
            total_positions = portfolio_data.get("total_positions", 0)
            st.metric(label="Total Positions", value=total_positions, delta=None)

        with col4:
            ytd_return = portfolio_data.get("ytd_return_pct", 0)
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

    performance_data = get_performance_data(backend_url, selected_period)

    if performance_data:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_return = performance_data.get("total_return_pct", 0)
            st.metric(label="Total Return", value=f"{total_return:.2f}%", delta=None)

        with col2:
            sharpe_ratio = performance_data.get("sharpe_ratio", 0)
            st.metric(label="Sharpe Ratio", value=f"{sharpe_ratio:.3f}", delta=None)

        with col3:
            volatility = performance_data.get("volatility", 0)
            st.metric(label="Volatility", value=f"{volatility:.2f}%", delta=None)

        with col4:
            max_drawdown = performance_data.get("max_drawdown", 0)
            st.metric(label="Max Drawdown", value=f"{max_drawdown:.2f}%", delta=None)
    else:
        st.info(
            f"Performance data for {period_options[selected_period]} is not available yet."
        )


def asset_allocation_chart(backend_url: str):
    """Display asset allocation pie chart."""
    st.subheader("🥧 Asset Allocation")

    positions_data = get_positions_data(backend_url)

    if positions_data and len(positions_data) > 0:
        # Convert to DataFrame
        df = pd.DataFrame(positions_data)

        # Calculate allocation percentages
        total_value = df["market_value"].sum()
        df["allocation_pct"] = (df["market_value"] / total_value) * 100

        # Group by asset type for better visualization
        if "asset_type" in df.columns:
            allocation_by_type = (
                df.groupby("asset_type")["allocation_pct"].sum().reset_index()
            )

            # Create pie chart
            fig = px.pie(
                allocation_by_type,
                values="allocation_pct",
                names="asset_type",
                title="Portfolio Allocation by Asset Type",
                hole=0.4,  # Donut chart
            )

            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(
                showlegend=True, height=400, margin=dict(t=50, b=0, l=0, r=0)
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback to individual positions
            top_positions = df.nlargest(10, "allocation_pct")

            fig = px.pie(
                top_positions,
                values="allocation_pct",
                names="symbol",
                title="Top 10 Holdings",
                hole=0.4,
            )

            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(
                showlegend=True, height=400, margin=dict(t=50, b=0, l=0, r=0)
            )

            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No position data available. Add some positions to see allocation.")


def holdings_table(backend_url: str):
    """Display holdings table with real-time prices."""
    st.subheader("📋 Current Holdings")

    positions_data = get_positions_data(backend_url)

    if positions_data and len(positions_data) > 0:
        # Convert to DataFrame
        df = pd.DataFrame(positions_data)

        # Format the data for display
        display_df = df.copy()

        # Format currency columns
        currency_columns = ["cost_basis", "market_value", "unrealized_pnl"]
        for col in currency_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")

        # Format percentage columns
        pct_columns = ["unrealized_pnl_pct", "allocation_pct"]
        for col in pct_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%")

        # Rename columns for better display
        column_mapping = {
            "symbol": "Symbol",
            "name": "Name",
            "quantity": "Quantity",
            "cost_basis": "Cost Basis",
            "market_value": "Market Value",
            "current_price": "Current Price",
            "unrealized_pnl": "Unrealized P&L",
            "unrealized_pnl_pct": "P&L %",
            "allocation_pct": "Allocation %",
        }

        # Select and rename columns
        available_columns = [
            col for col in column_mapping if col in display_df.columns
        ]
        display_df = display_df[available_columns].rename(columns=column_mapping)

        # Color code P&L columns
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Summary row
        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            total_cost = df["cost_basis"].sum()
            st.metric("Total Cost Basis", f"${total_cost:,.2f}")

        with col2:
            total_value = df["market_value"].sum()
            st.metric("Total Market Value", f"${total_value:,.2f}")

        with col3:
            total_pnl = df["unrealized_pnl"].sum()
            total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
            st.metric(
                "Total Unrealized P&L",
                f"${total_pnl:,.2f}",
                delta=f"{total_pnl_pct:.2f}%",
            )
    else:
        st.info("No holdings found. Add some positions to see your portfolio.")

        if st.button("Add Sample Data"):
            st.info(
                "Feature coming soon! You'll be able to add positions through the UI."
            )


def portfolio_value_chart(backend_url: str):
    """Display portfolio value over time chart."""
    st.subheader("📊 Portfolio Value Over Time")

    # This would need historical data from the backend
    # For now, show a placeholder
    st.info(
        "Historical portfolio value chart will be available once you have portfolio snapshots."
    )

    # Placeholder chart with sample data
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    values = pd.Series(index=dates, data=range(100000, 100000 + len(dates) * 100))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines",
            name="Portfolio Value",
            line=dict(color="blue", width=2),
        )
    )

    fig.update_layout(
        title="Sample Portfolio Growth",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        height=400,
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def refresh_data_button(backend_url: str):
    """Button to refresh data and trigger background tasks."""
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🔄 Refresh Data", type="primary"):
            with st.spinner("Updating market data..."):
                try:
                    # Trigger market data update task
                    response = requests.post(
                        f"{backend_url}/api/tasks/market-data/update-prices", timeout=10
                    )
                    if response.status_code == 200:
                        task_data = response.json()
                        st.success(
                            f"Data refresh started! Task ID: {task_data.get('task_id', 'N/A')}"
                        )
                    else:
                        st.error("Failed to start data refresh")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error triggering data refresh: {e}")

    with col2:
        if st.button("💾 Create Snapshot"):
            with st.spinner("Creating portfolio snapshot..."):
                try:
                    # Trigger portfolio snapshot task
                    response = requests.post(
                        f"{backend_url}/api/tasks/portfolio/snapshot",
                        json={"user_id": 1},  # Default user
                        timeout=10,
                    )
                    if response.status_code == 200:
                        task_data = response.json()
                        st.success(
                            f"Snapshot creation started! Task ID: {task_data.get('task_id', 'N/A')}"
                        )
                    else:
                        st.error("Failed to create snapshot")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error creating snapshot: {e}")

    with col3:
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh every 5 minutes")
        if auto_refresh:
            st.rerun()  # This would need proper implementation with session state
