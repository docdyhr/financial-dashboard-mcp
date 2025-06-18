"""Enhanced charting and visualization components."""

import random
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def create_mock_historical_data(symbol: str, days: int = 90) -> pd.DataFrame:
    """Create mock historical price data for demonstration."""
    dates = pd.date_range(end=datetime.now(), periods=days, freq="D")

    # Start with a base price
    base_prices = {
        "AAPL": 180.0,
        "MSFT": 350.0,
        "VOO": 380.0,
        "BTC-USD": 42000.0,
    }

    base_price = base_prices.get(symbol, 100.0)
    prices = []
    current_price = base_price

    for _ in range(days):
        # Random walk with slight upward bias
        change = random.gauss(0.01, 0.02)  # Small upward bias
        current_price *= 1 + change
        prices.append(current_price)

    return pd.DataFrame(
        {
            "Date": dates,
            "Close": prices,
            "Volume": [random.randint(1000000, 10000000) for _ in range(days)],
        }
    )


def portfolio_performance_chart(backend_url: str):
    """Display portfolio performance over time chart."""
    st.subheader("📈 Portfolio Performance")

    # Create mock portfolio performance data
    dates = pd.date_range(end=datetime.now(), periods=90, freq="D")

    # Simulate portfolio value growth
    portfolio_values = []
    sp500_values = []
    base_portfolio = 50000
    base_sp500 = 50000

    for i, date in enumerate(dates):
        # Portfolio with some volatility but general upward trend
        portfolio_change = random.gauss(0.0008, 0.015)  # Slightly better than market
        sp500_change = random.gauss(0.0005, 0.012)  # Market return

        base_portfolio *= 1 + portfolio_change
        base_sp500 *= 1 + sp500_change

        portfolio_values.append(base_portfolio)
        sp500_values.append(base_sp500)

    df = pd.DataFrame(
        {"Date": dates, "Portfolio": portfolio_values, "S&P 500": sp500_values}
    )

    # Calculate returns
    portfolio_return = (df["Portfolio"].iloc[-1] / df["Portfolio"].iloc[0] - 1) * 100
    sp500_return = (df["S&P 500"].iloc[-1] / df["S&P 500"].iloc[0] - 1) * 100

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Portfolio"],
            mode="lines",
            name="Your Portfolio",
            line=dict(color="#1f77b4", width=3),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["S&P 500"],
            mode="lines",
            name="S&P 500 Benchmark",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
        )
    )

    fig.update_layout(
        title="Portfolio vs S&P 500 Performance (90 Days)",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Portfolio Return",
            f"{portfolio_return:.2f}%",
            delta=f"{portfolio_return - sp500_return:.2f}% vs S&P 500",
        )

    with col2:
        volatility = df["Portfolio"].pct_change().std() * (252**0.5) * 100
        st.metric("Volatility (Annualized)", f"{volatility:.1f}%")

    with col3:
        max_dd = ((df["Portfolio"] / df["Portfolio"].cummax()) - 1).min() * 100
        st.metric("Max Drawdown", f"{max_dd:.1f}%")

    with col4:
        current_value = df["Portfolio"].iloc[-1]
        st.metric("Current Value", f"${current_value:,.0f}")


def individual_stock_charts(backend_url: str):
    """Display individual stock price charts."""
    st.subheader("📊 Individual Asset Performance")

    # Sample tickers from portfolio
    tickers = ["AAPL", "MSFT", "VOO", "BTC-USD"]

    # Create tabs for each asset
    tabs = st.tabs(tickers)

    for i, (tab, ticker) in enumerate(zip(tabs, tickers, strict=False)):
        with tab:
            # Create mock data
            df = create_mock_historical_data(ticker)

            # Create candlestick-style chart
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df["Close"],
                    mode="lines",
                    name=f"{ticker} Price",
                    line=dict(width=2),
                )
            )

            # Add moving averages
            df["MA20"] = df["Close"].rolling(window=20).mean()
            df["MA50"] = df["Close"].rolling(window=50).mean()

            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df["MA20"],
                    mode="lines",
                    name="20-day MA",
                    line=dict(color="orange", width=1, dash="dot"),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df["MA50"],
                    mode="lines",
                    name="50-day MA",
                    line=dict(color="red", width=1, dash="dash"),
                )
            )

            fig.update_layout(
                title=f"{ticker} Price Chart with Moving Averages",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                hovermode="x unified",
                height=350,
            )

            st.plotly_chart(fig, use_container_width=True)

            # Price metrics
            current_price = df["Close"].iloc[-1]
            price_change = df["Close"].pct_change().iloc[-1] * 100

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${current_price:.2f}")
            with col2:
                st.metric("1-Day Change", f"{price_change:.2f}%")
            with col3:
                total_return = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
                st.metric("90-Day Return", f"{total_return:.2f}%")


def risk_metrics_dashboard(backend_url: str):
    """Display risk analysis metrics."""
    st.subheader("⚠️ Risk Analysis")

    # Create mock portfolio data
    assets = ["AAPL", "MSFT", "VOO", "BTC-USD"]
    weights = [0.3, 0.25, 0.35, 0.1]  # Portfolio allocation

    # Generate mock returns for correlation matrix
    returns_data = {}
    for asset in assets:
        returns_data[asset] = [random.gauss(0.001, 0.02) for _ in range(90)]

    returns_df = pd.DataFrame(returns_data)

    # Correlation matrix heatmap
    corr_matrix = returns_df.corr()

    fig_corr = px.imshow(
        corr_matrix,
        title="Asset Correlation Matrix",
        color_continuous_scale="RdBu",
        aspect="auto",
    )

    fig_corr.update_layout(height=400)
    st.plotly_chart(fig_corr, use_container_width=True)

    # Risk metrics
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Portfolio Risk Metrics")

        # Calculate portfolio volatility (simplified)
        portfolio_vol = sum(
            w * returns_df[asset].std()
            for w, asset in zip(weights, assets, strict=False)
        )
        portfolio_vol_annualized = portfolio_vol * (252**0.5) * 100

        st.metric("Portfolio Volatility", f"{portfolio_vol_annualized:.1f}%")

        # Value at Risk (simplified)
        var_95 = returns_df.sum(axis=1).quantile(0.05) * 100
        st.metric("VaR (95%, 1-day)", f"{var_95:.2f}%")

        # Sharpe ratio (simplified)
        excess_return = returns_df.mean().mean() * 252
        sharpe = excess_return / (portfolio_vol * (252**0.5))
        st.metric("Sharpe Ratio", f"{sharpe:.2f}")

    with col2:
        st.subheader("Asset Allocation")

        # Pie chart for allocation
        fig_pie = px.pie(
            values=weights, names=assets, title="Current Portfolio Allocation"
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)


def sector_analysis_chart(backend_url: str):
    """Display sector allocation and analysis."""
    st.subheader("🏭 Sector Analysis")

    # Mock sector data
    sectors = {
        "Technology": 55,
        "Financial Services": 20,
        "Healthcare": 10,
        "Consumer Cyclical": 8,
        "Alternative Investments": 7,
    }

    col1, col2 = st.columns(2)

    with col1:
        # Sector allocation donut chart
        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=list(sectors.keys()), values=list(sectors.values()), hole=0.4
                )
            ]
        )

        fig_donut.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="%{label}<br>%{percent}<br>$%{value}k<extra></extra>",
        )

        fig_donut.update_layout(
            title="Sector Allocation",
            annotations=[
                dict(text="Portfolio", x=0.5, y=0.5, font_size=16, showarrow=False)
            ],
        )

        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        # Sector performance comparison
        sector_returns = {
            "Technology": 8.2,
            "Financial Services": -2.1,
            "Healthcare": 4.7,
            "Consumer Cyclical": 1.3,
            "Alternative Investments": 12.8,
        }

        fig_bar = px.bar(
            x=list(sector_returns.keys()),
            y=list(sector_returns.values()),
            title="Sector Performance (YTD %)",
            color=list(sector_returns.values()),
            color_continuous_scale="RdYlGn",
        )

        fig_bar.update_layout(
            xaxis_title="Sector", yaxis_title="Return (%)", showlegend=False
        )

        st.plotly_chart(fig_bar, use_container_width=True)


def performance_attribution_chart(backend_url: str):
    """Display performance attribution analysis."""
    st.subheader("🎯 Performance Attribution")

    # Mock attribution data
    attribution_data = {
        "Asset": ["AAPL", "MSFT", "VOO", "BTC-USD", "Cash"],
        "Weight (%)": [30, 25, 35, 8, 2],
        "Return (%)": [12.5, 8.3, 9.1, 25.2, 0.5],
        "Contribution (%)": [3.75, 2.08, 3.19, 2.02, 0.01],
    }

    df_attr = pd.DataFrame(attribution_data)

    # Waterfall chart for contribution
    fig_waterfall = go.Figure(
        go.Waterfall(
            name="Performance Attribution",
            orientation="v",
            measure=[
                "relative",
                "relative",
                "relative",
                "relative",
                "relative",
                "total",
            ],
            x=[*df_attr["Asset"].tolist(), "Total"],
            textposition="outside",
            text=[f"+{x:.2f}%" for x in df_attr["Contribution (%)"]]
            + [f"{df_attr['Contribution (%)'].sum():.2f}%"],
            y=[
                *df_attr["Contribution (%)"].tolist(),
                df_attr["Contribution (%)"].sum(),
            ],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        )
    )

    fig_waterfall.update_layout(
        title="Portfolio Return Attribution",
        xaxis_title="Asset",
        yaxis_title="Contribution to Return (%)",
        height=400,
    )

    st.plotly_chart(fig_waterfall, use_container_width=True)

    # Attribution table
    st.subheader("Attribution Details")
    st.dataframe(
        df_attr.style.format(
            {
                "Weight (%)": "{:.1f}%",
                "Return (%)": "{:.1f}%",
                "Contribution (%)": "{:.2f}%",
            }
        ),
        use_container_width=True,
    )


def enhanced_analytics_page():
    """Complete enhanced analytics page."""
    st.title("📊 Enhanced Analytics Dashboard")
    st.markdown("*Advanced portfolio analysis and visualizations*")

    # Performance overview
    portfolio_performance_chart("")
    st.divider()

    # Individual asset charts
    individual_stock_charts("")
    st.divider()

    # Risk analysis
    risk_metrics_dashboard("")
    st.divider()

    # Sector analysis
    sector_analysis_chart("")
    st.divider()

    # Performance attribution
    performance_attribution_chart("")

    st.info(
        "📝 **Note**: These charts use simulated data for demonstration. In production, real market data would be fetched from your portfolio and external APIs."
    )
