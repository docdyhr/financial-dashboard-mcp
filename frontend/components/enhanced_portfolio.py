"""Enhanced portfolio visualization with ISIN-based real-time data.

This component provides advanced portfolio visualization capabilities leveraging
the ISIN infrastructure for comprehensive European market coverage.
"""

import logging
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"


def call_api(endpoint: str, method: str = "GET", data: dict = None) -> dict | None:
    """Call API with error handling."""
    try:
        url = f"{BACKEND_URL}{endpoint}"

        if method == "GET":
            response = requests.get(url, timeout=15)
        elif method == "POST":
            response = requests.post(url, json=data or {}, timeout=15)
        else:
            return None

        if response.status_code == 200:
            return response.json()
        st.error(f"API Error {response.status_code}: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def get_portfolio_data() -> pd.DataFrame | None:
    """Fetch enhanced portfolio data with ISIN information."""
    try:
        # Get portfolio positions
        positions_data = call_api("/api/v1/positions/")

        if not positions_data or not positions_data.get("success"):
            return None

        positions = positions_data.get("data", [])

        if not positions:
            return pd.DataFrame()

        # Convert to DataFrame
        portfolio_df = pd.DataFrame(positions)

        # Extract ISIN information from assets
        portfolio_df["isin"] = portfolio_df["asset"].apply(
            lambda x: x.get("isin") if isinstance(x, dict) else None
        )
        portfolio_df["ticker"] = portfolio_df["asset"].apply(
            lambda x: x.get("ticker") if isinstance(x, dict) else "Unknown"
        )
        portfolio_df["company_name"] = portfolio_df["asset"].apply(
            lambda x: (
                x.get("name", x.get("ticker", "Unknown"))
                if isinstance(x, dict)
                else "Unknown"
            )
        )
        portfolio_df["currency"] = portfolio_df["asset"].apply(
            lambda x: x.get("currency", "EUR") if isinstance(x, dict) else "EUR"
        )

        # Calculate values
        portfolio_df["market_value"] = (
            portfolio_df["quantity"] * portfolio_df["current_price"]
        )
        portfolio_df["unrealized_pnl"] = (
            portfolio_df["current_price"] - portfolio_df["average_cost"]
        ) * portfolio_df["quantity"]
        portfolio_df["unrealized_pnl_percent"] = (
            portfolio_df["unrealized_pnl"]
            / (portfolio_df["average_cost"] * portfolio_df["quantity"])
        ) * 100

        return portfolio_df

    except Exception as e:
        logger.error(f"Error fetching portfolio data: {e}")
        st.error(f"Error loading portfolio: {e}")
        return None


def get_real_time_quotes(isins: list[str]) -> dict[str, dict]:
    """Get real-time quotes for ISINs."""
    try:
        # This would call the enhanced market data service
        quotes_data = call_api(
            "/api/v1/market-data/quotes/batch", "POST", {"isins": isins}
        )

        if quotes_data and quotes_data.get("success"):
            return quotes_data.get("data", {})

        return {}
    except Exception as e:
        logger.error(f"Error fetching real-time quotes: {e}")
        return {}


def enhanced_portfolio_overview():
    """Enhanced portfolio overview with real-time data."""
    st.subheader("📊 Enhanced Portfolio Overview")

    # Get portfolio data
    portfolio_df = get_portfolio_data()

    if portfolio_df is None:
        st.error("Unable to load portfolio data")
        return

    if portfolio_df.empty:
        st.info("No positions in portfolio")
        return

    # Get real-time quotes if ISINs are available
    isins_with_data = (
        portfolio_df[portfolio_df["isin"].notna()]["isin"].unique().tolist()
    )
    real_time_quotes = {}

    if isins_with_data:
        with st.spinner("📡 Fetching real-time quotes..."):
            real_time_quotes = get_real_time_quotes(isins_with_data)

    # Calculate portfolio metrics
    total_value = portfolio_df["market_value"].sum()
    total_unrealized_pnl = portfolio_df["unrealized_pnl"].sum()
    total_unrealized_pnl_percent = (
        total_unrealized_pnl
        / (portfolio_df["average_cost"] * portfolio_df["quantity"]).sum()
    ) * 100

    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Portfolio Value",
            f"€{total_value:,.2f}",
            delta=(
                f"€{total_unrealized_pnl:,.2f}"
                if not np.isnan(total_unrealized_pnl)
                else None
            ),
        )

    with col2:
        st.metric(
            "Total P&L",
            (
                f"{total_unrealized_pnl_percent:.2f}%"
                if not np.isnan(total_unrealized_pnl_percent)
                else "N/A"
            ),
            delta=(
                f"€{total_unrealized_pnl:,.2f}"
                if not np.isnan(total_unrealized_pnl)
                else None
            ),
        )

    with col3:
        st.metric("Positions", len(portfolio_df))

    with col4:
        currencies = portfolio_df["currency"].value_counts()
        primary_currency = currencies.index[0] if len(currencies) > 0 else "EUR"
        st.metric("Primary Currency", primary_currency)

    # Real-time updates indicator
    if real_time_quotes:
        st.success(f"📡 Real-time data: {len(real_time_quotes)} quotes updated")
    else:
        st.info("📊 Using cached market data")


def portfolio_allocation_charts(portfolio_df: pd.DataFrame):
    """Create portfolio allocation charts."""
    if portfolio_df.empty:
        return

    st.subheader("🥧 Portfolio Allocation")

    tab1, tab2, tab3 = st.tabs(["By Position", "By Currency", "By Country"])

    with tab1:
        # Allocation by position
        fig_pie = px.pie(
            portfolio_df,
            values="market_value",
            names="ticker",
            title="Portfolio Allocation by Position",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=500)
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        # Allocation by currency
        currency_allocation = (
            portfolio_df.groupby("currency")["market_value"].sum().reset_index()
        )

        fig_currency = px.pie(
            currency_allocation,
            values="market_value",
            names="currency",
            title="Portfolio Allocation by Currency",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_currency.update_traces(textposition="inside", textinfo="percent+label")
        fig_currency.update_layout(height=500)
        st.plotly_chart(fig_currency, use_container_width=True)

    with tab3:
        # Allocation by country (from ISIN)
        portfolio_df["country"] = portfolio_df["isin"].apply(
            lambda x: x[:2] if x and len(x) >= 2 else "Unknown"
        )

        country_allocation = (
            portfolio_df.groupby("country")["market_value"].sum().reset_index()
        )

        # Map country codes to names
        country_names = {
            "DE": "Germany",
            "US": "United States",
            "GB": "United Kingdom",
            "FR": "France",
            "NL": "Netherlands",
            "CH": "Switzerland",
            "IT": "Italy",
            "ES": "Spain",
            "SE": "Sweden",
            "DK": "Denmark",
            "FI": "Finland",
            "NO": "Norway",
            "AT": "Austria",
            "BE": "Belgium",
        }

        country_allocation["country_name"] = country_allocation["country"].map(
            lambda x: country_names.get(x, x)
        )

        fig_country = px.pie(
            country_allocation,
            values="market_value",
            names="country_name",
            title="Portfolio Allocation by Country",
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        fig_country.update_traces(textposition="inside", textinfo="percent+label")
        fig_country.update_layout(height=500)
        st.plotly_chart(fig_country, use_container_width=True)


def performance_analysis_charts(portfolio_df: pd.DataFrame):
    """Create performance analysis charts."""
    if portfolio_df.empty:
        return

    st.subheader("📈 Performance Analysis")

    # Performance table
    performance_df = portfolio_df[
        [
            "ticker",
            "company_name",
            "quantity",
            "average_cost",
            "current_price",
            "market_value",
            "unrealized_pnl",
            "unrealized_pnl_percent",
        ]
    ].copy()

    # Add performance indicators
    performance_df["performance_indicator"] = performance_df[
        "unrealized_pnl_percent"
    ].apply(lambda x: "🟢" if x > 0 else "🔴" if x < 0 else "⚪")

    # Sort by performance
    performance_df = performance_df.sort_values(
        "unrealized_pnl_percent", ascending=False
    )

    # Format for display
    display_df = performance_df.copy()
    display_df["Market Value"] = display_df["market_value"].apply(
        lambda x: f"€{x:,.2f}"
    )
    display_df["P&L"] = display_df["unrealized_pnl"].apply(lambda x: f"€{x:,.2f}")
    display_df["P&L %"] = display_df["unrealized_pnl_percent"].apply(
        lambda x: f"{x:.2f}%"
    )
    display_df["Avg Cost"] = display_df["average_cost"].apply(lambda x: f"€{x:.2f}")
    display_df["Current Price"] = display_df["current_price"].apply(
        lambda x: f"€{x:.2f}"
    )

    # Display table
    st.dataframe(
        display_df[
            [
                "performance_indicator",
                "ticker",
                "company_name",
                "quantity",
                "Avg Cost",
                "Current Price",
                "Market Value",
                "P&L",
                "P&L %",
            ]
        ],
        column_config={
            "performance_indicator": st.column_config.TextColumn("📊", width="small"),
            "ticker": st.column_config.TextColumn("Ticker", width="small"),
            "company_name": st.column_config.TextColumn("Company", width="medium"),
            "quantity": st.column_config.NumberColumn("Qty", width="small"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # Performance charts
    col1, col2 = st.columns(2)

    with col1:
        # P&L chart
        fig_pnl = px.bar(
            performance_df,
            x="ticker",
            y="unrealized_pnl",
            title="Unrealized P&L by Position",
            color="unrealized_pnl",
            color_continuous_scale=["red", "gray", "green"],
        )
        fig_pnl.update_layout(height=400)
        st.plotly_chart(fig_pnl, use_container_width=True)

    with col2:
        # P&L percentage chart
        fig_pnl_pct = px.bar(
            performance_df,
            x="ticker",
            y="unrealized_pnl_percent",
            title="Unrealized P&L % by Position",
            color="unrealized_pnl_percent",
            color_continuous_scale=["red", "gray", "green"],
        )
        fig_pnl_pct.update_layout(height=400)
        st.plotly_chart(fig_pnl_pct, use_container_width=True)


def risk_analysis_dashboard(portfolio_df: pd.DataFrame):
    """Create risk analysis dashboard."""
    if portfolio_df.empty:
        return

    st.subheader("⚠️ Risk Analysis")

    # Calculate risk metrics
    portfolio_df["weight"] = (
        portfolio_df["market_value"] / portfolio_df["market_value"].sum()
    )
    portfolio_df["concentration_risk"] = portfolio_df["weight"].apply(
        lambda x: "High" if x > 0.2 else "Medium" if x > 0.1 else "Low"
    )

    col1, col2 = st.columns(2)

    with col1:
        # Concentration analysis
        st.write("**Concentration Risk Analysis**")

        # Top 5 positions
        top_positions = portfolio_df.nlargest(5, "market_value")[
            ["ticker", "weight", "concentration_risk"]
        ]
        top_positions["Weight %"] = (top_positions["weight"] * 100).round(2)

        st.dataframe(
            top_positions[["ticker", "Weight %", "concentration_risk"]],
            column_config={
                "ticker": "Ticker",
                "Weight %": st.column_config.NumberColumn("Weight %", format="%.2f%%"),
                "concentration_risk": "Risk Level",
            },
            hide_index=True,
        )

        # Concentration chart
        fig_concentration = px.treemap(
            portfolio_df,
            path=["ticker"],
            values="market_value",
            title="Position Concentration",
            color="weight",
            color_continuous_scale="Reds",
        )
        fig_concentration.update_layout(height=300)
        st.plotly_chart(fig_concentration, use_container_width=True)

    with col2:
        # Diversification metrics
        st.write("**Diversification Metrics**")

        # Calculate diversification scores
        num_positions = len(portfolio_df)
        herfindahl_index = (portfolio_df["weight"] ** 2).sum()
        effective_positions = 1 / herfindahl_index

        # Currency diversification
        currency_count = portfolio_df["currency"].nunique()

        # Country diversification
        portfolio_df["country"] = portfolio_df["isin"].apply(
            lambda x: x[:2] if x and len(x) >= 2 else "Unknown"
        )
        country_count = portfolio_df[portfolio_df["country"] != "Unknown"][
            "country"
        ].nunique()

        metrics_df = pd.DataFrame(
            {
                "Metric": [
                    "Total Positions",
                    "Effective Positions",
                    "Currencies",
                    "Countries",
                    "Herfindahl Index",
                ],
                "Value": [
                    num_positions,
                    f"{effective_positions:.2f}",
                    currency_count,
                    country_count,
                    f"{herfindahl_index:.4f}",
                ],
                "Score": [
                    (
                        "Good"
                        if num_positions >= 10
                        else "Medium" if num_positions >= 5 else "Poor"
                    ),
                    (
                        "Good"
                        if effective_positions >= 8
                        else "Medium" if effective_positions >= 5 else "Poor"
                    ),
                    (
                        "Good"
                        if currency_count >= 3
                        else "Medium" if currency_count >= 2 else "Poor"
                    ),
                    (
                        "Good"
                        if country_count >= 5
                        else "Medium" if country_count >= 3 else "Poor"
                    ),
                    (
                        "Good"
                        if herfindahl_index <= 0.2
                        else "Medium" if herfindahl_index <= 0.4 else "Poor"
                    ),
                ],
            }
        )

        st.dataframe(
            metrics_df,
            column_config={
                "Metric": "Diversification Metric",
                "Value": "Current Value",
                "Score": st.column_config.TextColumn(
                    "Score", help="Good = Well diversified, Poor = Concentrated"
                ),
            },
            hide_index=True,
        )


def real_time_monitoring_widget():
    """Real-time portfolio monitoring widget."""
    st.subheader("📡 Real-Time Monitoring")

    # Auto-refresh toggle
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        auto_refresh = st.checkbox(
            "🔄 Auto-refresh (60s)", value=False, key="portfolio_auto_refresh"
        )

    with col2:
        if st.button("🔄 Refresh Now", key="portfolio_refresh"):
            st.rerun()

    with col3:
        st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")

    # Market status indicators
    market_status = call_api("/api/v1/market-data/status")

    if market_status and market_status.get("success"):
        status_data = market_status["data"]

        col1, col2, col3 = st.columns(3)

        with col1:
            market_state = status_data.get("market_state", "UNKNOWN")
            color = (
                "🟢"
                if market_state == "OPEN"
                else "🔴" if market_state == "CLOSED" else "🟡"
            )
            st.metric("Market Status", f"{color} {market_state}")

        with col2:
            is_trading = status_data.get("is_trading_day", False)
            st.metric("Trading Day", "✅ Yes" if is_trading else "❌ No")

        with col3:
            exchange = status_data.get("exchange", "XETR")
            st.metric("Primary Exchange", exchange)

    # Portfolio alerts
    portfolio_df = get_portfolio_data()

    if portfolio_df is not None and not portfolio_df.empty:
        st.write("**Portfolio Alerts**")

        alerts = []

        # Large position alerts
        large_positions = portfolio_df[
            portfolio_df["market_value"] / portfolio_df["market_value"].sum() > 0.2
        ]
        for _, pos in large_positions.iterrows():
            alerts.append(
                f"⚠️ Large position: {pos['ticker']} ({pos['market_value'] / portfolio_df['market_value'].sum() * 100:.1f}% of portfolio)"
            )

        # Performance alerts
        big_losers = portfolio_df[portfolio_df["unrealized_pnl_percent"] < -10]
        for _, pos in big_losers.iterrows():
            alerts.append(
                f"🔴 Significant loss: {pos['ticker']} ({pos['unrealized_pnl_percent']:.1f}%)"
            )

        big_winners = portfolio_df[portfolio_df["unrealized_pnl_percent"] > 20]
        for _, pos in big_winners.iterrows():
            alerts.append(
                f"🟢 Strong performer: {pos['ticker']} (+{pos['unrealized_pnl_percent']:.1f}%)"
            )

        if alerts:
            for alert in alerts[:5]:  # Show top 5 alerts
                st.write(alert)
        else:
            st.success("✅ No alerts")

    # Auto-refresh implementation
    if auto_refresh:
        import time

        time.sleep(60)
        st.rerun()


def isin_coverage_analysis():
    """Analyze ISIN coverage in the portfolio."""
    st.subheader("🔢 ISIN Coverage Analysis")

    portfolio_df = get_portfolio_data()

    if portfolio_df is None or portfolio_df.empty:
        st.info("No portfolio data available")
        return

    # ISIN coverage metrics
    total_positions = len(portfolio_df)
    positions_with_isin = len(portfolio_df[portfolio_df["isin"].notna()])
    coverage_percent = (
        (positions_with_isin / total_positions) * 100 if total_positions > 0 else 0
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Positions", total_positions)

    with col2:
        st.metric("With ISIN", positions_with_isin)

    with col3:
        st.metric("Coverage", f"{coverage_percent:.1f}%")

    # Missing ISIN analysis
    missing_isin = portfolio_df[portfolio_df["isin"].isna()]

    if not missing_isin.empty:
        st.warning(f"⚠️ {len(missing_isin)} positions missing ISIN codes")

        with st.expander("📋 Positions Missing ISIN", expanded=False):
            st.dataframe(
                missing_isin[["ticker", "company_name", "market_value"]],
                column_config={
                    "ticker": "Ticker",
                    "company_name": "Company",
                    "market_value": st.column_config.NumberColumn(
                        "Market Value", format="€%.2f"
                    ),
                },
                hide_index=True,
            )

            # Suggest ISIN lookup
            if st.button("🔍 Lookup Missing ISINs", key="lookup_missing_isins"):
                st.info("This would trigger ISIN lookup for missing positions")
    else:
        st.success("✅ All positions have ISIN codes")

    # ISIN country distribution
    if positions_with_isin > 0:
        isin_df = portfolio_df[portfolio_df["isin"].notna()].copy()
        isin_df["country_code"] = isin_df["isin"].str[:2]

        country_dist = (
            isin_df.groupby("country_code")
            .agg({"market_value": "sum", "ticker": "count"})
            .reset_index()
        )

        country_dist.columns = ["Country Code", "Market Value", "Position Count"]

        # Map country codes to names
        country_names = {
            "DE": "Germany",
            "US": "United States",
            "GB": "United Kingdom",
            "FR": "France",
            "NL": "Netherlands",
            "CH": "Switzerland",
            "IT": "Italy",
            "ES": "Spain",
            "SE": "Sweden",
            "DK": "Denmark",
        }

        country_dist["Country"] = country_dist["Country Code"].map(
            lambda x: country_names.get(x, x)
        )

        fig_country_dist = px.bar(
            country_dist,
            x="Country",
            y="Market Value",
            title="Portfolio Value by Country (from ISIN)",
            color="Market Value",
            color_continuous_scale="Blues",
        )
        fig_country_dist.update_layout(height=400)
        st.plotly_chart(fig_country_dist, use_container_width=True)


def enhanced_portfolio_page():
    """Main enhanced portfolio page."""
    st.title("💼 Enhanced Portfolio Dashboard")
    st.markdown("*Advanced portfolio analytics with ISIN-powered insights*")

    # Check if portfolio data is available
    portfolio_df = get_portfolio_data()

    if portfolio_df is None:
        st.error("Unable to load portfolio data. Please check the backend connection.")
        return

    if portfolio_df.empty:
        st.info(
            "📝 No positions in your portfolio yet. Add some positions to see analytics!"
        )
        return

    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📊 Overview",
            "🥧 Allocation",
            "📈 Performance",
            "⚠️ Risk Analysis",
            "🔢 ISIN Coverage",
        ]
    )

    with tab1:
        enhanced_portfolio_overview()
        real_time_monitoring_widget()

    with tab2:
        portfolio_allocation_charts(portfolio_df)

    with tab3:
        performance_analysis_charts(portfolio_df)

    with tab4:
        risk_analysis_dashboard(portfolio_df)

    with tab5:
        isin_coverage_analysis()

    # Sidebar with quick stats
    with st.sidebar:
        st.subheader("📊 Quick Stats")

        if portfolio_df is not None and not portfolio_df.empty:
            total_value = portfolio_df["market_value"].sum()
            best_performer = portfolio_df.loc[
                portfolio_df["unrealized_pnl_percent"].idxmax()
            ]
            worst_performer = portfolio_df.loc[
                portfolio_df["unrealized_pnl_percent"].idxmin()
            ]

            st.metric("Portfolio Value", f"€{total_value:,.0f}")
            st.metric("Positions", len(portfolio_df))

            st.write("**Best Performer**")
            st.success(
                f"{best_performer['ticker']}: +{best_performer['unrealized_pnl_percent']:.1f}%"
            )

            st.write("**Worst Performer**")
            st.error(
                f"{worst_performer['ticker']}: {worst_performer['unrealized_pnl_percent']:.1f}%"
            )

        st.divider()

        # Quick actions
        st.subheader("🚀 Quick Actions")

        if st.button("📊 Refresh Data"):
            st.rerun()

        if st.button("📈 Market Update"):
            st.info("Fetching latest market data...")
            # This would trigger a market data refresh

        if st.button("🔍 ISIN Lookup"):
            st.info("Starting ISIN lookup for missing positions...")
            # This would trigger ISIN lookup


if __name__ == "__main__":
    enhanced_portfolio_page()
