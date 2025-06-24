"""Portfolio chart components for the Financial Dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .portfolio_data import get_positions_data, safe_float


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
        import numpy as np

        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")

        # Validate date range
        if len(dates) == 0:
            st.error("Invalid date range for portfolio chart")
            return

        # Create values that grow over time with some realistic variation
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
