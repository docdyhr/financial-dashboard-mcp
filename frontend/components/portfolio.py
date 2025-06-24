"""Portfolio overview components for the Financial Dashboard."""

import pandas as pd
import plotly.express as px
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


def asset_allocation_chart(backend_url: str):
    """Display asset allocation pie chart."""
    st.subheader("🥧 Asset Allocation")

    positions_data = get_positions_data(backend_url)

    if positions_data and len(positions_data) > 0:
        # Convert to DataFrame
        df = pd.DataFrame(positions_data)

        # Calculate allocation percentages using cost basis since current_value might be None
        if "current_value" in df.columns and len(df[df["current_value"].notna()]) > 0:
            df["current_value_float"] = df["current_value"].apply(safe_float)
            total_value = df["current_value_float"].sum()
            df["allocation_pct"] = (
                (df["current_value_float"] / total_value) * 100
                if total_value > 0
                else 0
            )
        elif "total_cost_basis" in df.columns:
            df["total_cost_basis_float"] = df["total_cost_basis"].apply(safe_float)
            total_value = df["total_cost_basis_float"].sum()
            df["allocation_pct"] = (
                (df["total_cost_basis_float"] / total_value) * 100
                if total_value > 0
                else 0
            )
        else:
            st.warning(
                "Unable to calculate allocation percentages - no value data available"
            )
            return

        # Group by asset type for better visualization
        if "asset" in df.columns and len(df) > 0:
            # Extract asset_type from nested asset object
            df["asset_type"] = df["asset"].apply(
                lambda x: (
                    x.get("asset_type", "Unknown") if isinstance(x, dict) else "Unknown"
                )
            )
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
            # Fallback to individual positions using ticker from asset
            df["symbol"] = df["asset"].apply(
                lambda x: (
                    x.get("ticker", "Unknown") if isinstance(x, dict) else "Unknown"
                )
            )
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

    # Get user settings for currency formatting
    from frontend.services.settings import get_settings_manager

    settings_manager = get_settings_manager(backend_url)

    positions_data = get_positions_data(backend_url)

    if positions_data and len(positions_data) > 0:
        # Convert to DataFrame
        df = pd.DataFrame(positions_data)

        # Format the data for display
        display_df = df.copy()

        # Format currency columns
        currency_columns = ["total_cost_basis", "current_value", "unrealized_gain_loss"]
        for col in currency_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: (
                        settings_manager.format_currency(safe_float(x))
                        if x is not None
                        else "N/A"
                    )
                )

        # Format percentage columns
        pct_columns = ["unrealized_gain_loss_percent", "weight_in_portfolio"]
        for col in pct_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{safe_float(x):.2f}%" if x is not None else "N/A"
                )

        # Format quantity column to show whole numbers for stocks
        if "quantity" in display_df.columns:
            display_df["quantity"] = display_df["quantity"].apply(
                lambda x: f"{int(safe_float(x))}" if x is not None else "0"
            )

        # Add symbol column from asset data
        display_df["symbol"] = display_df["asset"].apply(
            lambda x: x.get("ticker", "Unknown") if isinstance(x, dict) else "Unknown"
        )
        display_df["name"] = display_df["asset"].apply(
            lambda x: x.get("name", "Unknown") if isinstance(x, dict) else "Unknown"
        )

        # Rename columns for better display
        column_mapping = {
            "symbol": "Symbol",
            "name": "Name",
            "quantity": "Quantity",
            "total_cost_basis": "Cost Basis",
            "current_value": "Market Value",
            "unrealized_gain_loss": "Unrealized P&L",
            "unrealized_gain_loss_percent": "P&L %",
            "weight_in_portfolio": "Allocation %",
        }

        # Select and rename columns
        # Select and rename columns for display
        available_columns = [col for col in column_mapping if col in display_df.columns]

        # Create a new DataFrame with renamed columns
        renamed_df = display_df[available_columns].copy()
        renamed_df.columns = [
            column_mapping.get(col, col) for col in renamed_df.columns
        ]
        display_df = renamed_df

        # Display the table
        st.dataframe(display_df, use_container_width=True)

        # Position management UI
        st.divider()
        st.subheader("Position Management")

        # Initialize session state
        if "show_delete" not in st.session_state:
            st.session_state.show_delete = False
        if "show_details" not in st.session_state:
            st.session_state.show_details = False
        if "show_edit" not in st.session_state:
            st.session_state.show_edit = False
        if "show_transactions" not in st.session_state:
            st.session_state.show_transactions = False
        if "selected_position_index" not in st.session_state:
            st.session_state.selected_position_index = None

        # Position selection for management
        # Create position options using the original asset data
        position_options = []
        for _, row in df.iterrows():
            asset_data = row["asset"] if isinstance(row["asset"], dict) else {}
            symbol = asset_data.get("ticker", "Unknown")
            quantity = int(safe_float(row["quantity"]))
            position_options.append(f"{symbol} - {quantity} shares")

        if position_options:
            selected_position_display = st.selectbox(
                "Select a position to manage:",
                options=["Select a position...", *position_options],
                index=0,
            )

            if selected_position_display != "Select a position...":
                selected_index = position_options.index(selected_position_display)

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button(
                        "🗑️ Delete Position",
                        type="secondary",
                        key=f"delete_{selected_index}",
                    ):
                        st.session_state.show_delete = True
                        st.session_state.selected_position_index = selected_index
                        st.session_state.show_details = False
                        st.session_state.show_edit = False
                        st.session_state.show_transactions = False

                with col2:
                    if st.button(
                        "📊 View Details",
                        type="secondary",
                        key=f"details_{selected_index}",
                    ):
                        st.session_state.show_details = True
                        st.session_state.selected_position_index = selected_index
                        st.session_state.show_delete = False
                        st.session_state.show_edit = False
                        st.session_state.show_transactions = False

                with col3:
                    if st.button(
                        "✏️ Edit Position",
                        type="secondary",
                        key=f"edit_{selected_index}",
                    ):
                        st.session_state.show_edit = True
                        st.session_state.selected_position_index = selected_index
                        st.session_state.show_delete = False
                        st.session_state.show_details = False
                        st.session_state.show_transactions = False

                with col4:
                    if st.button(
                        "📈 View Transactions",
                        type="secondary",
                        key=f"transactions_{selected_index}",
                    ):
                        st.session_state.show_transactions = True
                        st.session_state.selected_position_index = selected_index
                        st.session_state.show_delete = False
                        st.session_state.show_details = False
                        st.session_state.show_edit = False

        # Handle the different actions based on session state
        if (
            st.session_state.get("show_delete", False)
            and st.session_state.selected_position_index is not None
        ):
            delete_positions(
                backend_url, df, [st.session_state.selected_position_index]
            )

        if (
            st.session_state.get("show_details", False)
            and st.session_state.selected_position_index is not None
        ):
            view_position_details(
                backend_url, df, [st.session_state.selected_position_index]
            )

        if (
            st.session_state.get("show_edit", False)
            and st.session_state.selected_position_index is not None
        ):
            edit_position(backend_url, df, [st.session_state.selected_position_index])

        if (
            st.session_state.get("show_transactions", False)
            and st.session_state.selected_position_index is not None
        ):
            view_position_transactions(
                backend_url, df, [st.session_state.selected_position_index]
            )

        # Summary row
        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            total_cost = df["total_cost_basis"].apply(lambda x: safe_float(x)).sum()
            st.metric("Total Cost Basis", settings_manager.format_currency(total_cost))

        with col2:
            current_values = df["current_value"].apply(
                lambda x: safe_float(x) if x is not None else 0.0
            )
            total_value = current_values.sum()
            has_valid_prices = any(df["current_value"].notna())

            if total_value > 0 and has_valid_prices:
                st.metric(
                    "Total Market Value", settings_manager.format_currency(total_value)
                )
            else:
                st.metric("Total Market Value", "N/A (No current prices)")

        with col3:
            pnl_values = df["unrealized_gain_loss"].apply(
                lambda x: safe_float(x) if x is not None else 0.0
            )
            total_pnl = pnl_values.sum()
            has_valid_pnl = any(df["unrealized_gain_loss"].notna())

            if has_valid_pnl and total_cost > 0:
                total_pnl_pct = (total_pnl / total_cost) * 100
                st.metric(
                    "Total Unrealized P&L",
                    settings_manager.format_currency(total_pnl),
                    delta=f"{total_pnl_pct:.2f}%",
                )
            else:
                st.metric("Total Unrealized P&L", "N/A (No current prices)")
    else:
        st.info("No holdings found. Add some positions to see your portfolio.")

        if st.button("Add Sample Data"):
            st.info(
                "Feature coming soon! You'll be able to add positions through the UI."
            )


def delete_positions(backend_url: str, df: pd.DataFrame, selected_indices: list[int]):
    """Delete selected positions with confirmation."""
    import requests

    if not selected_indices:
        st.warning("No positions selected for deletion.")
        return

    # Get selected position
    position = df.iloc[selected_indices[0]]
    symbol = (
        position["asset"]["ticker"]
        if isinstance(position["asset"], dict)
        else "Unknown"
    )
    quantity = int(safe_float(position["quantity"]))

    # Show confirmation dialog
    st.warning("⚠️ **Position Deletion Confirmation**")
    st.write(
        f"Are you sure you want to delete position **{symbol}** ({quantity} shares)?"
    )

    col1, col2 = st.columns(2)

    with col1:
        soft_delete = st.checkbox(
            "Soft delete (keep in history)",
            value=True,
            help="Soft delete keeps the position in transaction history",
        )

    with col2:
        confirm_delete = st.checkbox("I confirm deletion", value=False)

    if confirm_delete:
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "🗑️ Confirm Delete", type="primary", key="confirm_delete_final"
            ):
                position_id = position["id"]

                try:
                    response = requests.delete(
                        f"{backend_url}/api/v1/positions/{position_id}",
                        params={"soft_delete": soft_delete},
                        timeout=10,
                    )

                    if response.status_code == 200:
                        st.success(f"Successfully deleted position {symbol}")
                        # Clear session state
                        if "show_delete" in st.session_state:
                            del st.session_state["show_delete"]
                        if "selected_position_index" in st.session_state:
                            del st.session_state["selected_position_index"]
                        st.rerun()
                    else:
                        st.error(f"Failed to delete position: {response.status_code}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error deleting position: {e}")

        with col2:
            if st.button("❌ Cancel", type="secondary", key="cancel_delete_final"):
                # Clear session state
                if "show_delete" in st.session_state:
                    del st.session_state["show_delete"]
                if "selected_position_index" in st.session_state:
                    del st.session_state["selected_position_index"]
                st.rerun()


def view_position_details(
    backend_url: str, df: pd.DataFrame, selected_indices: list[int]
):
    """Show detailed information for selected positions."""
    import requests

    if not selected_indices or len(selected_indices) != 1:
        st.warning("Please select exactly one position to view details.")
        return

    position = df.iloc[selected_indices[0]]
    position_id = position["id"]

    try:
        response = requests.get(
            f"{backend_url}/api/v1/positions/{position_id}", timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                position_detail = data["data"]

                st.subheader("📊 Position Details")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Symbol", position_detail["asset"]["ticker"])
                    st.metric(
                        "Quantity", f"{int(safe_float(position_detail['quantity']))}"
                    )
                    avg_cost = safe_float(
                        position_detail.get("average_cost_per_share", 0)
                    )
                    st.metric(
                        "Average Cost",
                        f"${avg_cost:.2f}",
                    )

                with col2:
                    total_cost = safe_float(position_detail.get("total_cost_basis", 0))
                    st.metric(
                        "Total Cost Basis",
                        f"${total_cost:.2f}",
                    )
                    current_value = safe_float(position_detail.get("current_value"))
                    if current_value > 0:
                        st.metric("Current Value", f"${current_value:.2f}")
                    pnl = safe_float(position_detail.get("unrealized_gain_loss"))
                    if pnl != 0:
                        pnl_pct = safe_float(
                            position_detail.get("unrealized_gain_loss_percent", 0)
                        )
                        delta_color = "normal" if pnl >= 0 else "inverse"
                        st.metric(
                            "Unrealized P&L",
                            f"${pnl:.2f}",
                            f"{pnl_pct:.2f}%",
                            delta_color=delta_color,
                        )

                if position_detail.get("notes"):
                    st.text_area("Notes", value=position_detail["notes"], disabled=True)

        else:
            st.error(f"Failed to fetch position details: {response.status_code}")

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching position details: {e}")


def edit_position(backend_url: str, df: pd.DataFrame, selected_indices: list[int]):
    """Edit selected position."""
    import requests

    if not selected_indices or len(selected_indices) != 1:
        st.warning("Please select exactly one position to edit.")
        return

    position = df.iloc[selected_indices[0]]
    position_id = position["id"]

    st.subheader("✏️ Edit Position")

    # Fetch current position details including asset info
    try:
        response = requests.get(
            f"{backend_url}/api/v1/positions/{position_id}", timeout=10
        )

        if response.status_code != 200:
            st.error(f"Failed to fetch position details: {response.status_code}")
            return

        data = response.json()
        if not data.get("success"):
            st.error("Failed to fetch position details")
            return

        position_detail = data["data"]
        current_asset = position_detail["asset"]

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching position details: {e}")
        return

    # Create tabs for different editing options
    tab1, tab2 = st.tabs(["📊 Position Details", "🏷️ Asset Information"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            new_quantity = st.number_input(
                "Quantity",
                value=safe_float(position_detail.get("quantity", 0)),
                min_value=0.0,
                step=0.1,
                format="%.4f",
            )

            new_avg_cost = st.number_input(
                "Average Cost per Share",
                value=safe_float(position_detail.get("average_cost_per_share", 0)),
                min_value=0.0,
                step=0.01,
                format="%.4f",
            )

        with col2:
            new_account = st.text_input(
                "Account Name", value=position_detail.get("account_name", "") or ""
            )

            new_notes = st.text_area(
                "Notes", value=position_detail.get("notes", "") or ""
            )

    with tab2:
        st.write("**Current Asset Information:**")
        col1, col2 = st.columns(2)

        with col1:
            st.text_input(
                "Current Ticker", value=current_asset["ticker"], disabled=True
            )
            st.text_input("Current Name", value=current_asset["name"], disabled=True)
            st.text_input(
                "Current Exchange",
                value=current_asset.get("exchange", "N/A"),
                disabled=True,
            )

        with col2:
            st.text_input(
                "Current Currency",
                value=current_asset.get("currency", "USD"),
                disabled=True,
            )
            st.text_input(
                "Current Sector",
                value=current_asset.get("sector", "N/A"),
                disabled=True,
            )
            st.text_input(
                "Current Country",
                value=current_asset.get("country", "N/A"),
                disabled=True,
            )

        st.divider()
        st.write("**Edit Asset Information:**")

        col1, col2 = st.columns(2)

        with col1:
            new_ticker = st.text_input(
                "New Ticker Symbol",
                value=current_asset["ticker"],
                help="For European stocks, use format like ASML.PA, VODAFONE.L, SAP.DE",
            )

            new_name = st.text_input("Asset Name", value=current_asset["name"])

            new_exchange = st.text_input(
                "Exchange",
                value=current_asset.get("exchange", ""),
                help="e.g., London Stock Exchange, Euronext Paris, NASDAQ",
            )

        with col2:
            new_currency = st.selectbox(
                "Currency",
                options=[
                    "USD",
                    "EUR",
                    "GBP",
                    "CHF",
                    "SEK",
                    "NOK",
                    "DKK",
                    "CAD",
                    "AUD",
                    "JPY",
                ],
                index=(
                    [
                        "USD",
                        "EUR",
                        "GBP",
                        "CHF",
                        "SEK",
                        "NOK",
                        "DKK",
                        "CAD",
                        "AUD",
                        "JPY",
                    ].index(current_asset.get("currency", "USD"))
                    if current_asset.get("currency", "USD")
                    in [
                        "USD",
                        "EUR",
                        "GBP",
                        "CHF",
                        "SEK",
                        "NOK",
                        "DKK",
                        "CAD",
                        "AUD",
                        "JPY",
                    ]
                    else 0
                ),
            )

            new_sector = st.text_input("Sector", value=current_asset.get("sector", ""))

            new_country = st.text_input(
                "Country Code",
                value=current_asset.get("country", ""),
                help="2-letter country code (e.g., US, GB, DE, FR)",
            )

        # Ticker validation and suggestion
        if new_ticker and new_ticker != current_asset["ticker"]:
            try:
                from backend.services.ticker_utils import TickerUtils

                is_valid, error_msg = TickerUtils.validate_ticker_format(new_ticker)
                if not is_valid:
                    st.error(f"Invalid ticker format: {error_msg}")
                else:
                    ticker_info = TickerUtils.parse_ticker(new_ticker)
                    st.info("✓ Valid ticker format detected")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Exchange:** {ticker_info.exchange_name}")
                        st.write(
                            f"**Currency:** {ticker_info.default_currency or 'Unknown'}"
                        )
                    with col2:
                        st.write(
                            f"**Country:** {ticker_info.country_code or 'Unknown'}"
                        )
                        st.write(
                            f"**European:** {'Yes' if TickerUtils.is_european_ticker(new_ticker) else 'No'}"
                        )
            except ImportError:
                st.warning(
                    "Ticker validation service not available. Please ensure the ticker format is correct."
                )

    # Update buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "💾 Update Position Only", type="primary", key="update_position_only"
        ):
            try:
                update_data = {
                    "quantity": str(new_quantity),
                    "average_cost_per_share": str(new_avg_cost),
                    "total_cost_basis": str(new_quantity * new_avg_cost),
                    "account_name": new_account if new_account else None,
                    "notes": new_notes if new_notes else None,
                }

                response = requests.put(
                    f"{backend_url}/api/v1/positions/{position_id}",
                    json=update_data,
                    timeout=10,
                )

                if response.status_code == 200:
                    st.success("Position updated successfully!")
                    # Clear session state
                    if "show_edit" in st.session_state:
                        del st.session_state["show_edit"]
                    if "selected_position_index" in st.session_state:
                        del st.session_state["selected_position_index"]
                    st.rerun()
                else:
                    st.error(f"Failed to update position: {response.status_code}")
                    st.error(f"Response: {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"Error updating position: {e}")

    with col2:
        # Check if asset information has changed
        asset_changed = any(
            [
                new_ticker != current_asset["ticker"],
                new_name != current_asset["name"],
                new_exchange != current_asset.get("exchange", ""),
                new_currency != current_asset.get("currency", "USD"),
                new_sector != current_asset.get("sector", ""),
                new_country != current_asset.get("country", ""),
            ]
        )

        if asset_changed:
            if st.button(
                "🔄 Update Asset & Position", type="primary", key="update_both"
            ):
                try:
                    # First update the asset
                    asset_update_data = {
                        "name": new_name,
                        "exchange": new_exchange if new_exchange else None,
                        "currency": new_currency,
                        "sector": new_sector if new_sector else None,
                        "country": new_country if new_country else None,
                    }

                    # Only update ticker if it has actually changed
                    if new_ticker and new_ticker != current_asset["ticker"]:
                        # For ticker changes, we need to validate first
                        try:
                            from backend.services.ticker_utils import TickerUtils

                            is_valid, error_msg = TickerUtils.validate_ticker_format(
                                new_ticker
                            )
                            if not is_valid:
                                st.error(
                                    f"Cannot update: Invalid ticker format - {error_msg}"
                                )
                                st.stop()
                        except ImportError:
                            st.warning(
                                "Ticker validation not available, proceeding with update..."
                            )

                    asset_response = requests.put(
                        f"{backend_url}/api/v1/assets/{current_asset['id']}",
                        json=asset_update_data,
                        timeout=10,
                    )

                    if asset_response.status_code == 200:
                        # If ticker changed, we need to handle it specially
                        if new_ticker != current_asset["ticker"]:
                            # Check if an asset with new ticker already exists
                            search_response = requests.get(
                                f"{backend_url}/api/v1/assets/search",
                                params={"query": new_ticker},
                                timeout=10,
                            )

                            if search_response.status_code == 200:
                                search_data = search_response.json()
                                existing_assets = [
                                    asset
                                    for asset in search_data.get("data", [])
                                    if asset["ticker"] == new_ticker
                                ]

                                if existing_assets:
                                    # Asset with new ticker exists, need to merge/reassign
                                    st.warning(
                                        f"Asset with ticker {new_ticker} already exists. Please use the existing asset or choose a different ticker."
                                    )
                                    st.stop()
                                else:
                                    # Create new asset with new ticker
                                    new_asset_data = {
                                        "ticker": new_ticker,
                                        "name": new_name,
                                        "asset_type": current_asset["asset_type"],
                                        "category": current_asset["category"],
                                        "exchange": (
                                            new_exchange if new_exchange else None
                                        ),
                                        "currency": new_currency,
                                        "sector": new_sector if new_sector else None,
                                        "country": new_country if new_country else None,
                                    }

                                    create_response = requests.post(
                                        f"{backend_url}/api/v1/assets",
                                        json=new_asset_data,
                                        timeout=10,
                                    )

                                    if create_response.status_code == 201:
                                        new_asset = create_response.json()["data"]
                                        # Update position to use new asset
                                        position_update_data = {
                                            "asset_id": new_asset["id"],
                                            "quantity": str(new_quantity),
                                            "average_cost_per_share": str(new_avg_cost),
                                            "total_cost_basis": str(
                                                new_quantity * new_avg_cost
                                            ),
                                            "account_name": (
                                                new_account if new_account else None
                                            ),
                                            "notes": new_notes if new_notes else None,
                                        }
                                    else:
                                        st.error(
                                            f"Failed to create new asset: {create_response.status_code}"
                                        )
                                        st.stop()
                            else:
                                st.error("Failed to search for existing assets")
                                st.stop()
                        else:
                            # No ticker change, just update position
                            position_update_data = {
                                "quantity": str(new_quantity),
                                "average_cost_per_share": str(new_avg_cost),
                                "total_cost_basis": str(new_quantity * new_avg_cost),
                                "account_name": new_account if new_account else None,
                                "notes": new_notes if new_notes else None,
                            }

                        # Update position
                        position_response = requests.put(
                            f"{backend_url}/api/v1/positions/{position_id}",
                            json=position_update_data,
                            timeout=10,
                        )

                        if position_response.status_code == 200:
                            st.success("Asset and position updated successfully!")
                            # Clear session state
                            if "show_edit" in st.session_state:
                                del st.session_state["show_edit"]
                            if "selected_position_index" in st.session_state:
                                del st.session_state["selected_position_index"]
                            st.rerun()
                        else:
                            st.error(
                                f"Asset updated but failed to update position: {position_response.status_code}"
                            )
                    else:
                        st.error(
                            f"Failed to update asset: {asset_response.status_code}"
                        )
                        st.error(f"Response: {asset_response.text}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error updating asset and position: {e}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
        else:
            st.write("*No asset changes detected*")

    with col3:
        if st.button("❌ Cancel Edit", type="secondary", key="cancel_edit_final"):
            # Clear session state
            if "show_edit" in st.session_state:
                del st.session_state["show_edit"]
            if "selected_position_index" in st.session_state:
                del st.session_state["selected_position_index"]
            st.rerun()


def view_position_transactions(
    backend_url: str, df: pd.DataFrame, selected_indices: list[int]
):
    """View transaction history for selected position."""
    import pandas as pd
    import requests

    if not selected_indices or len(selected_indices) != 1:
        st.warning("Please select exactly one position to view transactions.")
        return

    position = df.iloc[selected_indices[0]]
    position_id = position["id"]
    asset_id = position["asset"]["id"] if isinstance(position["asset"], dict) else None
    symbol = (
        position["asset"]["ticker"]
        if isinstance(position["asset"], dict)
        else "Unknown"
    )

    st.subheader(f"📈 Transaction History - {symbol}")

    try:
        # Fetch transactions for this position
        response = requests.get(
            f"{backend_url}/api/v1/transactions/position/{position_id}", timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                transactions = data["data"]

                if transactions:
                    # Convert to DataFrame
                    df_trans = pd.DataFrame(transactions)

                    # Format data for display
                    display_df = df_trans.copy()

                    # Format dates
                    display_df["transaction_date"] = pd.to_datetime(
                        display_df["transaction_date"]
                    ).dt.strftime("%Y-%m-%d")

                    # Format currency columns
                    currency_columns = ["total_amount", "net_amount", "commission"]
                    for col in currency_columns:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(
                                lambda x: (
                                    f"${safe_float(x):.2f}" if x is not None else "N/A"
                                )
                            )

                    # Format price per share separately
                    if "price_per_share" in display_df.columns:
                        display_df["price_per_share"] = display_df[
                            "price_per_share"
                        ].apply(
                            lambda x: (
                                f"${safe_float(x):.4f}" if x is not None else "N/A"
                            )
                        )

                    # Rename columns for better display
                    column_mapping = {
                        "transaction_date": "Date",
                        "transaction_type": "Type",
                        "quantity": "Quantity",
                        "price_per_share": "Price/Share",
                        "total_amount": "Total Amount",
                        "commission": "Commission",
                        "net_amount": "Net Amount",
                    }

                    display_df = display_df.rename(columns=column_mapping)

                    # Display the table
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No transactions found for this position.")
            else:
                st.error("No transaction data available.")
        else:
            st.error(f"Failed to fetch transactions: {response.status_code}")

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching transactions: {e}")


def safe_format_currency(value, default="$0.00"):
    """Safely format a value as currency."""
    try:
        if value is None:
            return default
        return f"${float(value):.2f}"
    except (ValueError, TypeError):
        return default


def validate_ticker_input(ticker: str) -> tuple[bool, str]:
    """Validate ticker input and provide helpful feedback."""
    if not ticker or not ticker.strip():
        return False, "Ticker cannot be empty"

    ticker = ticker.upper().strip()

    # Import validation function
    try:
        from backend.services.ticker_utils import TickerUtils

        is_valid, error_msg = TickerUtils.validate_ticker_format(ticker)
        return is_valid, error_msg or "Valid format"
    except ImportError:
        # Fallback validation if utils not available
        import re

        if not re.match(r"^[A-Z0-9.-]+$", ticker):
            return False, "Ticker can only contain letters, numbers, dots, and hyphens"

        if len(ticker) > 20:
            return False, "Ticker too long (max 20 characters)"

        return True, "Valid format"


def get_ticker_suggestions(ticker: str, exchange_hint: str = None) -> list[str]:
    """Get ticker format suggestions."""
    try:
        from backend.services.ticker_utils import TickerUtils

        suggestions = []

        if exchange_hint:
            suggested = TickerUtils.suggest_ticker_format(ticker, exchange_hint)
            if suggested != ticker:
                suggestions.append(suggested)

        # Add common European formats if base ticker provided
        if "." not in ticker and len(ticker) <= 10:
            common_formats = [
                f"{ticker}.L",  # London
                f"{ticker}.PA",  # Paris
                f"{ticker}.DE",  # Frankfurt
                f"{ticker}.MI",  # Milan
                f"{ticker}.AS",  # Amsterdam
            ]
            suggestions.extend(common_formats)

        return suggestions[:5]  # Limit to 5 suggestions
    except ImportError:
        return []


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


def portfolio_value_chart(backend_url: str):
    """Display portfolio value over time chart."""
    st.subheader("📊 Portfolio Value Over Time")

    try:
        # This would need historical data from the backend
        # For now, show a placeholder
        st.info(
            "Historical portfolio value chart will be available once you have portfolio snapshots."
        )

        # Placeholder chart with sample data
        import pandas as pd
        import plotly.graph_objects as go

        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")

        # Validate date range
        if len(dates) == 0:
            st.error("Invalid date range for portfolio chart")
            return

        # Create values that grow over time with some realistic variation
        import numpy as np

        base_value = 100000
        growth_rate = 0.0003  # ~11% annual growth
        volatility = 0.015  # Daily volatility

        # Generate realistic portfolio growth with random walks
        np.random.seed(42)  # For reproducible results
        daily_returns = np.random.normal(growth_rate, volatility, len(dates))
        cumulative_returns = np.cumprod(1 + daily_returns)

        # Ensure data lengths match
        if len(cumulative_returns) != len(dates):
            st.error("Data length mismatch in portfolio chart generation")
            return

        values = pd.Series(index=dates, data=base_value * cumulative_returns)

        # Validate the series was created successfully
        if values.empty or values.isna().all():
            st.error("Failed to generate portfolio data")
            return

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

    except ImportError as e:
        st.error(f"Missing required library: {e}")
    except Exception as e:
        st.error(f"Error generating portfolio chart: {e}")
        st.info("Please check the logs for more details.")


def refresh_data_button(backend_url: str):
    """Button to refresh data and trigger background tasks."""
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🔄 Refresh Data", type="primary"):
            with st.spinner("Updating market data..."):
                try:
                    # Trigger market data update task
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
                        f"{backend_url}/api/v1/tasks/portfolio-snapshot",
                        json={"user_id": 5},  # Correct user ID
                        headers={"Content-Type": "application/json"},
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
