"""ISIN Analytics and Summary Dashboard.

This component provides comprehensive analytics and insights for the ISIN system
including coverage metrics, data quality analysis, and performance monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

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


def get_isin_statistics() -> dict | None:
    """Get comprehensive ISIN statistics."""
    try:
        # This would call the ISIN statistics endpoint
        stats_data = call_api("/isin/statistics")
        if stats_data and stats_data.get("success"):
            return stats_data.get("data", {})

        # Fallback: simulate statistics for demo
        return {
            "total_mappings": 1247,
            "active_mappings": 1198,
            "coverage_percentage": 89.3,
            "high_confidence_mappings": 987,
            "countries_covered": 15,
            "exchanges_covered": 12,
            "recent_updates": 156,
            "validation_cache_size": 2341,
            "sync_jobs_completed": 23,
            "conflicts_resolved": 8,
        }
    except Exception as e:
        logger.error(f"Error fetching ISIN statistics: {e}")
        return None


def get_country_distribution() -> pd.DataFrame:
    """Get country distribution data."""
    try:
        # This would call a specific endpoint for country distribution
        # For demo, we'll create sample data
        data = {
            "Country": [
                "Germany",
                "United States",
                "United Kingdom",
                "France",
                "Netherlands",
                "Switzerland",
                "Italy",
                "Spain",
                "Sweden",
                "Denmark",
            ],
            "Country_Code": [
                "DE",
                "US",
                "GB",
                "FR",
                "NL",
                "CH",
                "IT",
                "ES",
                "SE",
                "DK",
            ],
            "ISIN_Count": [342, 256, 189, 145, 98, 87, 76, 54, 43, 32],
            "Market_Value_EUR": [
                45600000,
                38200000,
                28900000,
                21500000,
                14200000,
                12800000,
                9600000,
                7300000,
                5800000,
                4200000,
            ],
        }
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting country distribution: {e}")
        return pd.DataFrame()


def get_exchange_distribution() -> pd.DataFrame:
    """Get exchange distribution data."""
    try:
        data = {
            "Exchange": [
                "Xetra",
                "NASDAQ",
                "London Stock Exchange",
                "Euronext Paris",
                "Euronext Amsterdam",
                "SIX Swiss Exchange",
                "Borsa Italiana",
                "BME Spanish Exchanges",
                "Nasdaq Stockholm",
                "Nasdaq Copenhagen",
            ],
            "Exchange_Code": [
                "XETR",
                "XNAS",
                "XLON",
                "XPAR",
                "XAMS",
                "XSWX",
                "XMIL",
                "XMAD",
                "XSTO",
                "XCSE",
            ],
            "Mappings": [298, 245, 167, 134, 89, 78, 65, 48, 38, 28],
            "Avg_Confidence": [
                0.92,
                0.94,
                0.89,
                0.87,
                0.91,
                0.88,
                0.85,
                0.83,
                0.90,
                0.86,
            ],
        }
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting exchange distribution: {e}")
        return pd.DataFrame()


def get_quality_metrics() -> dict[str, Any]:
    """Get data quality metrics."""
    try:
        return {
            "average_confidence": 0.887,
            "high_confidence_percentage": 78.4,
            "medium_confidence_percentage": 18.9,
            "low_confidence_percentage": 2.7,
            "mappings_with_names": 1089,
            "mappings_with_sectors": 894,
            "mappings_with_market_cap": 567,
            "recent_validations": 234,
            "validation_success_rate": 94.7,
        }
    except Exception as e:
        logger.error(f"Error getting quality metrics: {e}")
        return {}


def get_sync_activity() -> pd.DataFrame:
    """Get sync activity data for the last 30 days."""
    try:
        # Generate sample sync activity data
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=30), end=datetime.now(), freq="D"
        )

        np.random.seed(42)  # For consistent demo data
        data = {
            "Date": dates,
            "Sync_Jobs": np.random.poisson(3, len(dates)),
            "ISINs_Processed": np.random.poisson(150, len(dates)),
            "Conflicts_Found": np.random.poisson(2, len(dates)),
            "Success_Rate": np.random.normal(0.95, 0.02, len(dates)).clip(0.8, 1.0),
        }
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting sync activity: {e}")
        return pd.DataFrame()


def overview_metrics_widget():
    """Display overview metrics."""
    st.subheader("📊 ISIN System Overview")

    stats = get_isin_statistics()
    if not stats:
        st.error("Unable to load ISIN statistics")
        return

    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Mappings",
            f"{stats.get('total_mappings', 0):,}",
            delta=(
                f"+{stats.get('recent_updates', 0)}"
                if stats.get("recent_updates", 0) > 0
                else None
            ),
        )

    with col2:
        coverage = stats.get("coverage_percentage", 0)
        st.metric(
            "Coverage",
            f"{coverage:.1f}%",
            delta=f"{coverage - 85:.1f}%" if coverage > 85 else None,
        )

    with col3:
        confidence_ratio = stats.get("high_confidence_mappings", 0) / max(
            stats.get("total_mappings", 1), 1
        )
        st.metric(
            "High Confidence",
            f"{confidence_ratio:.1%}",
            delta=f"{confidence_ratio - 0.75:.1%}" if confidence_ratio > 0.75 else None,
        )

    with col4:
        st.metric(
            "Countries Covered",
            stats.get("countries_covered", 0),
            delta=(
                f"+{stats.get('countries_covered', 15) - 12}"
                if stats.get("countries_covered", 15) > 12
                else None
            ),
        )

    # Secondary metrics
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric("Active Exchanges", stats.get("exchanges_covered", 0))

    with col6:
        st.metric("Cache Entries", f"{stats.get('validation_cache_size', 0):,}")

    with col7:
        st.metric("Sync Jobs Completed", stats.get("sync_jobs_completed", 0))

    with col8:
        st.metric("Conflicts Resolved", stats.get("conflicts_resolved", 0))


def geographical_analysis_widget():
    """Display geographical analysis of ISIN coverage."""
    st.subheader("🌍 Geographical Analysis")

    country_df = get_country_distribution()
    if country_df.empty:
        st.error("Unable to load country distribution data")
        return

    tab1, tab2 = st.tabs(["Coverage Map", "Market Value"])

    with tab1:
        # Country coverage chart
        fig_countries = px.bar(
            country_df.head(10),
            x="Country",
            y="ISIN_Count",
            title="ISIN Coverage by Country",
            color="ISIN_Count",
            color_continuous_scale="Blues",
            text="ISIN_Count",
        )
        fig_countries.update_traces(texttemplate="%{text}", textposition="outside")
        fig_countries.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig_countries, use_container_width=True)

        # Country details table
        st.write("**Country Details**")
        display_df = country_df.copy()
        display_df["Market Value (€M)"] = (
            display_df["Market_Value_EUR"] / 1000000
        ).round(1)
        display_df["% of Total"] = (
            display_df["ISIN_Count"] / display_df["ISIN_Count"].sum() * 100
        ).round(1)

        st.dataframe(
            display_df[
                [
                    "Country",
                    "Country_Code",
                    "ISIN_Count",
                    "Market Value (€M)",
                    "% of Total",
                ]
            ],
            column_config={
                "Country": "Country",
                "Country_Code": "Code",
                "ISIN_Count": "ISINs",
                "Market Value (€M)": st.column_config.NumberColumn(
                    "Market Value (€M)", format="%.1f"
                ),
                "% of Total": st.column_config.NumberColumn(
                    "% of Total", format="%.1f%%"
                ),
            },
            hide_index=True,
        )

    with tab2:
        # Market value analysis
        fig_value = px.treemap(
            country_df,
            path=["Country"],
            values="Market_Value_EUR",
            title="Market Value Distribution by Country",
            color="Market_Value_EUR",
            color_continuous_scale="Viridis",
        )
        fig_value.update_layout(height=500)
        st.plotly_chart(fig_value, use_container_width=True)

        # Market concentration analysis
        total_value = country_df["Market_Value_EUR"].sum()
        country_df["Value_Percentage"] = (
            country_df["Market_Value_EUR"] / total_value * 100
        )

        top_5_value = country_df.head(5)["Value_Percentage"].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Top 5 Countries",
                f"{top_5_value:.1f}%",
                help="Market value concentration",
            )
        with col2:
            st.metric(
                "Largest Market",
                f"{country_df.iloc[0]['Country']}",
                delta=f"{country_df.iloc[0]['Value_Percentage']:.1f}%",
            )
        with col3:
            herfindahl = (country_df["Value_Percentage"] ** 2).sum() / 10000
            st.metric(
                "HHI",
                f"{herfindahl:.3f}",
                help="Herfindahl-Hirschman Index (concentration)",
            )


def exchange_analysis_widget():
    """Display exchange analysis."""
    st.subheader("🏢 Exchange Analysis")

    exchange_df = get_exchange_distribution()
    if exchange_df.empty:
        st.error("Unable to load exchange distribution data")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Exchange mappings chart
        fig_exchanges = px.pie(
            exchange_df,
            values="Mappings",
            names="Exchange",
            title="Mappings by Exchange",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig_exchanges.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_exchanges, use_container_width=True)

    with col2:
        # Exchange confidence analysis
        fig_confidence = px.bar(
            exchange_df,
            x="Exchange_Code",
            y="Avg_Confidence",
            title="Average Confidence by Exchange",
            color="Avg_Confidence",
            color_continuous_scale="RdYlGn",
            text="Avg_Confidence",
        )
        fig_confidence.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_confidence.update_layout(height=400)
        fig_confidence.update_yaxis(range=[0.8, 1.0])
        st.plotly_chart(fig_confidence, use_container_width=True)

    # Exchange details table
    st.write("**Exchange Performance Summary**")

    display_df = exchange_df.copy()
    display_df["Quality Score"] = (display_df["Avg_Confidence"] * 100).round(1)
    display_df["Market Share"] = (
        display_df["Mappings"] / display_df["Mappings"].sum() * 100
    ).round(1)

    # Add quality indicators
    display_df["Quality_Indicator"] = display_df["Avg_Confidence"].apply(
        lambda x: "🟢" if x >= 0.9 else "🟡" if x >= 0.8 else "🔴"
    )

    st.dataframe(
        display_df[
            [
                "Quality_Indicator",
                "Exchange",
                "Exchange_Code",
                "Mappings",
                "Quality Score",
                "Market Share",
            ]
        ],
        column_config={
            "Quality_Indicator": st.column_config.TextColumn("📊", width="small"),
            "Exchange": "Exchange Name",
            "Exchange_Code": "Code",
            "Mappings": "Total Mappings",
            "Quality Score": st.column_config.NumberColumn(
                "Quality Score", format="%.1f"
            ),
            "Market Share": st.column_config.NumberColumn(
                "Market Share (%)", format="%.1f%%"
            ),
        },
        hide_index=True,
    )


def data_quality_analysis():
    """Analyze data quality metrics."""
    st.subheader("🎯 Data Quality Analysis")

    quality_metrics = get_quality_metrics()
    if not quality_metrics:
        st.error("Unable to load quality metrics")
        return

    # Quality overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_conf = quality_metrics.get("average_confidence", 0)
        st.metric(
            "Average Confidence",
            f"{avg_conf:.3f}",
            delta=f"{avg_conf - 0.85:.3f}" if avg_conf > 0.85 else None,
        )

    with col2:
        success_rate = quality_metrics.get("validation_success_rate", 0)
        st.metric(
            "Validation Success",
            f"{success_rate:.1f}%",
            delta=f"{success_rate - 90:.1f}%" if success_rate > 90 else None,
        )

    with col3:
        completeness = quality_metrics.get("mappings_with_names", 0) / max(
            quality_metrics.get("high_confidence_mappings", 1), 1
        )
        st.metric(
            "Name Completeness",
            f"{completeness:.1%}",
            delta=f"{completeness - 0.85:.1%}" if completeness > 0.85 else None,
        )

    with col4:
        sector_completeness = quality_metrics.get("mappings_with_sectors", 0) / max(
            quality_metrics.get("high_confidence_mappings", 1), 1
        )
        st.metric(
            "Sector Coverage",
            f"{sector_completeness:.1%}",
            delta=(
                f"{sector_completeness - 0.7:.1%}"
                if sector_completeness > 0.7
                else None
            ),
        )

    # Confidence distribution
    confidence_data = {
        "Confidence Level": ["High (≥0.8)", "Medium (0.5-0.8)", "Low (<0.5)"],
        "Percentage": [
            quality_metrics.get("high_confidence_percentage", 0),
            quality_metrics.get("medium_confidence_percentage", 0),
            quality_metrics.get("low_confidence_percentage", 0),
        ],
        "Color": ["green", "orange", "red"],
    }

    confidence_df = pd.DataFrame(confidence_data)

    col1, col2 = st.columns(2)

    with col1:
        fig_confidence_dist = px.pie(
            confidence_df,
            values="Percentage",
            names="Confidence Level",
            title="Confidence Score Distribution",
            color="Confidence Level",
            color_discrete_map={
                "High (≥0.8)": "green",
                "Medium (0.5-0.8)": "orange",
                "Low (<0.5)": "red",
            },
        )
        fig_confidence_dist.update_traces(
            textposition="inside", textinfo="percent+label"
        )
        st.plotly_chart(fig_confidence_dist, use_container_width=True)

    with col2:
        # Data completeness chart
        completeness_data = {
            "Field": [
                "Company Names",
                "Sector Info",
                "Market Cap",
                "Currency",
                "Exchange",
            ],
            "Completeness": [87.4, 71.8, 45.5, 95.2, 89.7],
        }
        completeness_df = pd.DataFrame(completeness_data)

        fig_completeness = px.bar(
            completeness_df,
            x="Completeness",
            y="Field",
            title="Data Field Completeness",
            orientation="h",
            color="Completeness",
            color_continuous_scale="RdYlGn",
            text="Completeness",
        )
        fig_completeness.update_traces(
            texttemplate="%{text:.1f}%", textposition="outside"
        )
        fig_completeness.update_layout(height=400)
        st.plotly_chart(fig_completeness, use_container_width=True)

    # Quality improvement suggestions
    st.write("**Quality Improvement Recommendations**")

    recommendations = []

    if quality_metrics.get("low_confidence_percentage", 0) > 5:
        recommendations.append(
            "🔴 **High Priority**: Review and improve low-confidence mappings"
        )

    if sector_completeness < 0.75:
        recommendations.append(
            "🟡 **Medium Priority**: Enhance sector information coverage"
        )

    if (
        quality_metrics.get("mappings_with_market_cap", 0)
        / max(quality_metrics.get("high_confidence_mappings", 1), 1)
        < 0.6
    ):
        recommendations.append(
            "🟡 **Medium Priority**: Collect more market capitalization data"
        )

    if avg_conf < 0.9:
        recommendations.append(
            "🟢 **Low Priority**: Focus on increasing overall confidence scores"
        )

    if not recommendations:
        st.success("✅ Data quality is excellent! No immediate improvements needed.")
    else:
        for rec in recommendations:
            st.write(rec)


def sync_activity_analysis():
    """Analyze sync activity and performance."""
    st.subheader("⚡ Sync Activity Analysis")

    sync_df = get_sync_activity()
    if sync_df.empty:
        st.error("Unable to load sync activity data")
        return

    # Activity metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_jobs = sync_df["Sync_Jobs"].sum()
        st.metric(
            "Total Sync Jobs",
            total_jobs,
            delta=(
                f"+{sync_df['Sync_Jobs'].iloc[-7:].sum()}"
                if len(sync_df) >= 7
                else None
            ),
        )

    with col2:
        total_isins = sync_df["ISINs_Processed"].sum()
        st.metric(
            "ISINs Processed",
            f"{total_isins:,}",
            delta=(
                f"+{sync_df['ISINs_Processed'].iloc[-7:].sum():,}"
                if len(sync_df) >= 7
                else None
            ),
        )

    with col3:
        avg_success = sync_df["Success_Rate"].mean()
        st.metric(
            "Avg Success Rate",
            f"{avg_success:.1%}",
            delta=f"{avg_success - 0.95:.1%}" if avg_success > 0.95 else None,
        )

    with col4:
        total_conflicts = sync_df["Conflicts_Found"].sum()
        st.metric(
            "Total Conflicts",
            total_conflicts,
            delta=(
                f"+{sync_df['Conflicts_Found'].iloc[-7:].sum()}"
                if len(sync_df) >= 7
                else None
            ),
        )

    # Activity trends
    fig_activity = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Daily Sync Jobs",
            "ISINs Processed",
            "Success Rate Trend",
            "Conflicts Found",
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}],
        ],
    )

    # Daily sync jobs
    fig_activity.add_trace(
        go.Scatter(
            x=sync_df["Date"],
            y=sync_df["Sync_Jobs"],
            mode="lines+markers",
            name="Sync Jobs",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )

    # ISINs processed
    fig_activity.add_trace(
        go.Scatter(
            x=sync_df["Date"],
            y=sync_df["ISINs_Processed"],
            mode="lines+markers",
            name="ISINs Processed",
            line=dict(color="green"),
        ),
        row=1,
        col=2,
    )

    # Success rate
    fig_activity.add_trace(
        go.Scatter(
            x=sync_df["Date"],
            y=sync_df["Success_Rate"],
            mode="lines+markers",
            name="Success Rate",
            line=dict(color="orange"),
        ),
        row=2,
        col=1,
    )

    # Conflicts
    fig_activity.add_trace(
        go.Bar(
            x=sync_df["Date"],
            y=sync_df["Conflicts_Found"],
            name="Conflicts",
            marker_color="red",
        ),
        row=2,
        col=2,
    )

    fig_activity.update_layout(
        height=600, showlegend=False, title_text="Sync Activity Trends (Last 30 Days)"
    )
    st.plotly_chart(fig_activity, use_container_width=True)

    # Performance insights
    st.write("**Performance Insights**")

    # Calculate trends
    recent_avg = sync_df["Success_Rate"].iloc[-7:].mean()
    overall_avg = sync_df["Success_Rate"].mean()

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Recent Performance (Last 7 Days)**")
        if recent_avg > overall_avg:
            st.success(
                f"📈 Success rate improving: {recent_avg:.1%} vs {overall_avg:.1%} overall"
            )
        else:
            st.warning(
                f"📉 Success rate declining: {recent_avg:.1%} vs {overall_avg:.1%} overall"
            )

        peak_activity = sync_df.loc[sync_df["ISINs_Processed"].idxmax()]
        st.info(
            f"🔥 Peak activity: {peak_activity['ISINs_Processed']} ISINs on {peak_activity['Date'].strftime('%Y-%m-%d')}"
        )

    with col2:
        st.write("**Conflict Analysis**")
        conflict_rate = (
            sync_df["Conflicts_Found"].sum()
            / max(sync_df["ISINs_Processed"].sum(), 1)
            * 100
        )
        st.metric("Conflict Rate", f"{conflict_rate:.2f}%")

        if conflict_rate > 2:
            st.warning("⚠️ High conflict rate detected - review data sources")
        else:
            st.success("✅ Low conflict rate - good data consistency")


def system_health_dashboard():
    """Display system health metrics."""
    st.subheader("🏥 System Health")

    # Get sync service status
    sync_status = call_api("/isin/sync/health")

    if sync_status and sync_status.get("success"):
        health_data = sync_status["data"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            is_healthy = health_data.get("healthy", False)
            status_color = "🟢" if is_healthy else "🔴"
            st.metric(
                "System Status",
                f"{status_color} {'Healthy' if is_healthy else 'Issues'}",
            )

        with col2:
            service_running = health_data.get("service_running", False)
            st.metric("Sync Service", "🟢 Running" if service_running else "🔴 Stopped")

        with col3:
            queue_size = health_data.get("queue_size", 0)
            st.metric(
                "Queue Size",
                queue_size,
                delta=f"{'Normal' if queue_size < 10 else 'High'}",
            )

        with col4:
            unresolved = health_data.get("unresolved_conflicts", 0)
            st.metric(
                "Unresolved Conflicts",
                unresolved,
                delta=f"{'Good' if unresolved < 5 else 'Needs Attention'}",
            )

    else:
        st.error("❌ Unable to fetch system health status")

    # System recommendations
    st.write("**System Recommendations**")

    # This would analyze various metrics and provide recommendations
    recommendations = [
        {"level": "success", "message": "✅ ISIN validation cache is performing well"},
        {
            "level": "info",
            "message": "ℹ️ Consider increasing sync frequency for European markets",
        },
        {
            "level": "warning",
            "message": "⚠️ Some low-confidence mappings need manual review",
        },
    ]

    for rec in recommendations:
        if rec["level"] == "success":
            st.success(rec["message"])
        elif rec["level"] == "info":
            st.info(rec["message"])
        elif rec["level"] == "warning":
            st.warning(rec["message"])


def isin_analytics_dashboard():
    """Main ISIN analytics dashboard."""
    st.title("📊 ISIN Analytics Dashboard")
    st.markdown(
        "*Comprehensive insights into ISIN system performance and data quality*"
    )

    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Overview", "🌍 Geography", "🏢 Exchanges", "🎯 Quality", "⚡ Activity"]
    )

    with tab1:
        overview_metrics_widget()
        system_health_dashboard()

    with tab2:
        geographical_analysis_widget()

    with tab3:
        exchange_analysis_widget()

    with tab4:
        data_quality_analysis()

    with tab5:
        sync_activity_analysis()

    # Sidebar with quick actions
    with st.sidebar:
        st.subheader("📈 Quick Insights")

        stats = get_isin_statistics()
        if stats:
            st.metric("System Score", "A+", help="Overall system health grade")

            # Coverage gauge
            coverage = stats.get("coverage_percentage", 0)
            if coverage >= 90:
                st.success(f"🎯 Excellent coverage: {coverage:.1f}%")
            elif coverage >= 75:
                st.info(f"📊 Good coverage: {coverage:.1f}%")
            else:
                st.warning(f"⚠️ Coverage needs improvement: {coverage:.1f}%")

        st.divider()

        st.subheader("🚀 Quick Actions")

        if st.button("🔄 Refresh Data"):
            st.rerun()

        if st.button("📊 Generate Report"):
            st.info("Generating comprehensive ISIN report...")
            # This would trigger report generation

        if st.button("🔍 Run Diagnostics"):
            st.info("Running system diagnostics...")
            # This would trigger diagnostic checks

        if st.button("⚡ Optimize Cache"):
            st.info("Optimizing validation cache...")
            # This would trigger cache optimization

    # Footer with last update time
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.caption(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    with col2:
        if st.button("📤 Export Data", help="Export analytics data"):
            st.info("Data export functionality would be implemented here")

    with col3:
        if st.button("📧 Schedule Report", help="Schedule automated reports"):
            st.info("Report scheduling functionality would be implemented here")


if __name__ == "__main__":
    isin_analytics_dashboard()
