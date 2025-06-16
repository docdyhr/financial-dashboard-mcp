"""Portfolio overview components for the Financial Dashboard."""

from typing import Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
        response = requests.get(f"{backend_url}/api/v1/portfolio/summary/5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("data") if data.get("success") else None
        st.error(f"Failed to fetch portfolio data: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None


def get_positions_data(backend_url: str) -> list[dict] | None:
    """Fetch positions data from the backend API."""
    try:
        response = requests.get(
            f"{backend_url}/api/v1/positions/?user_id=5", timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data") if data.get("success") else None
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
                options=["Select a position..."] + position_options,
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

                st.subheader(f"📊 Position Details")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Symbol", position_detail["asset"]["ticker"])
                    st.metric(
                        "Quantity", f"{int(safe_float(position_detail['quantity']))}"
                    )
                    st.metric(
                        "Average Cost",
                        f"${position_detail['average_cost_per_share']:.2f}",
                    )

                with col2:
                    st.metric(
                        "Total Cost Basis",
                        f"${position_detail['total_cost_basis']:.2f}",
                    )
                    if position_detail.get("current_value"):
                        st.metric(
                            "Current Value", f"${position_detail['current_value']:.2f}"
                        )
                    if position_detail.get("unrealized_gain_loss"):
                        pnl = position_detail["unrealized_gain_loss"]
                        pnl_pct = position_detail.get("unrealized_gain_loss_percent", 0)
                        st.metric("Unrealized P&L", f"${pnl:.2f}", f"{pnl_pct:.2f}%")

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

    col1, col2 = st.columns(2)

    with col1:
        new_quantity = st.number_input(
            "Quantity", value=int(float(position["quantity"])), min_value=0, step=1
        )

        new_avg_cost = st.number_input(
            "Average Cost per Share",
            value=float(position["average_cost_per_share"]),
            min_value=0.0,
            step=0.01,
        )

    with col2:
        new_account = st.text_input(
            "Account Name", value=position.get("account_name", "") or ""
        )

        new_notes = st.text_area("Notes", value=position.get("notes", "") or "")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Update Position", type="primary", key="update_position_final"):
            try:
                update_data = {
                    "quantity": str(int(new_quantity)),  # Ensure whole numbers
                    "average_cost_per_share": str(new_avg_cost),
                    "total_cost_basis": str(int(new_quantity) * new_avg_cost),
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
                                f"${safe_float(x):.2f}" if x is not None else "N/A"
                            )
                        )

                    # Format quantity - whole numbers for stocks
                    if "quantity" in display_df.columns:
                        display_df["quantity"] = display_df["quantity"].apply(
                            lambda x: (
                                f"{int(safe_float(x))}" if x is not None else "N/A"
                            )
                        )

                    # Select and rename columns for display
                    columns_to_show = {
                        "transaction_date": "Date",
                        "transaction_type": "Type",
                        "quantity": "Quantity",
                        "price_per_share": "Price",
                        "total_amount": "Gross Amount",
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

                    final_df = display_df[available_columns].rename(columns=rename_dict)

                    # Display the transactions table
                    st.dataframe(final_df, use_container_width=True)

                    # Transaction summary
                    st.divider()
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        buy_count = len(
                            [t for t in transactions if t["transaction_type"] == "buy"]
                        )
                        st.metric("Buy Transactions", buy_count)

                    with col2:
                        sell_count = len(
                            [t for t in transactions if t["transaction_type"] == "sell"]
                        )
                        st.metric("Sell Transactions", sell_count)

                    with col3:
                        dividend_count = len(
                            [
                                t
                                for t in transactions
                                if t["transaction_type"] == "dividend"
                            ]
                        )
                        st.metric("Dividend Payments", dividend_count)

                    # Calculate totals
                    total_invested = sum(
                        safe_float(t.get("total_amount", 0))
                        for t in transactions
                        if t["transaction_type"] == "buy"
                    )
                    total_proceeds = sum(
                        safe_float(t.get("total_amount", 0))
                        for t in transactions
                        if t["transaction_type"] == "sell"
                    )
                    total_dividends = sum(
                        safe_float(t.get("total_amount", 0))
                        for t in transactions
                        if t["transaction_type"] == "dividend"
                    )
                    total_fees = sum(
                        safe_float(t.get("commission", 0)) for t in transactions
                    )

                    st.divider()
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Invested", f"${total_invested:,.2f}")

                    with col2:
                        st.metric("Total Proceeds", f"${total_proceeds:,.2f}")

                    with col3:
                        st.metric("Total Dividends", f"${total_dividends:,.2f}")

                    with col4:
                        st.metric("Total Fees", f"${total_fees:,.2f}")

                else:
                    st.info("No transactions found for this position.")
                    st.write("Transactions will appear here when you:")
                    st.write("• Buy or sell shares of this asset")
                    st.write("• Receive dividend payments")
                    st.write("• Experience stock splits or other corporate actions")

            else:
                st.error("Failed to load transaction data.")

        else:
            st.error(f"Failed to fetch transactions: {response.status_code}")

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching transactions: {e}")
        st.info(
            "The transaction history feature requires the backend API to be running."
        )


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
