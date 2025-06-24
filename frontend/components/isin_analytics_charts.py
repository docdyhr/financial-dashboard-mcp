"""ISIN Analytics chart components."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from .isin_analytics_data import (
    get_country_distribution,
    get_exchange_distribution, 
    get_sync_activity,
)


def geographical_analysis_widget():
    """Display geographical analysis of ISIN coverage."""
    st.subheader("🌍 Geographical Analysis")

    country_df = get_country_distribution()
    if country_df.empty:
        st.error("Unable to load country distribution data")
        return

    tab1, tab2 = st.tabs(["Coverage Map", "Market Distribution"])

    with tab1:
        # Country coverage chart
        fig_countries = px.bar(
            country_df.head(10),
            x="country_name",
            y="count",
            title="ISIN Coverage by Country",
            color="count",
            color_continuous_scale="Blues",
            text="count",
        )
        fig_countries.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_countries.update_layout(height=500, showlegend=False)
        fig_countries.update_xaxes(title="Country")
        fig_countries.update_yaxes(title="Number of ISINs")
        st.plotly_chart(fig_countries, use_container_width=True)

        # Country details table
        st.write("**Country Details**")
        display_df = country_df.copy()
        display_df["% of Total"] = display_df["percentage"]

        st.dataframe(
            display_df[
                [
                    "country_name",
                    "country_code",
                    "count",
                    "% of Total",
                ]
            ],
            column_config={
                "country_name": "Country",
                "country_code": "Code",
                "count": "ISINs",
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
            path=["country_name"],
            values="count",
            title="ISIN Distribution by Country",
            color="count",
            color_continuous_scale="Viridis",
        )
        fig_value.update_layout(height=500)
        st.plotly_chart(fig_value, use_container_width=True)

        # Market concentration analysis
        top_5_percentage = country_df.head(5)["percentage"].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Top 5 Countries",
                f"{top_5_percentage:.1f}%",
                help="Coverage concentration",
            )
        with col2:
            st.metric(
                "Largest Market",
                f"{country_df.iloc[0]['country_name']}",
                delta=f"{country_df.iloc[0]['percentage']:.1f}%",
            )
        with col3:
            herfindahl = (country_df["percentage"] ** 2).sum() / 10000
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
            values="count",
            names="exchange_name",
            title="ISINs by Exchange",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig_exchanges.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_exchanges, use_container_width=True)

    with col2:
        # Exchange distribution bar chart
        fig_exchange_bar = px.bar(
            exchange_df.head(10),
            x="exchange_code",
            y="count",
            title="ISIN Count by Exchange",
            color="count",
            color_continuous_scale="Viridis",
            text="count",
        )
        fig_exchange_bar.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_exchange_bar.update_layout(height=400)
        fig_exchange_bar.update_xaxes(title="Exchange Code")
        fig_exchange_bar.update_yaxes(title="Number of ISINs")
        st.plotly_chart(fig_exchange_bar, use_container_width=True)

    # Exchange details table
    st.write("**Exchange Performance Summary**")

    display_df = exchange_df.copy()
    display_df["Market Share"] = display_df["percentage"]

    # Add quality indicators based on count
    display_df["Quality_Indicator"] = display_df["count"].apply(
        lambda x: "🟢" if x >= 5000 else "🟡" if x >= 1000 else "🔴"
    )

    st.dataframe(
        display_df[
            [
                "Quality_Indicator",
                "exchange_name",
                "exchange_code",
                "country",
                "count",
                "Market Share",
            ]
        ],
        column_config={
            "Quality_Indicator": st.column_config.TextColumn("📊", width="small"),
            "exchange_name": "Exchange Name",
            "exchange_code": "Code",
            "country": "Country",
            "count": "Total ISINs",
            "Market Share": st.column_config.NumberColumn(
                "Market Share (%)", format="%.1f%%"
            ),
        },
        hide_index=True,
    )


def sync_activity_analysis():
    """Display synchronization activity analysis."""
    st.subheader("⚡ Sync Activity Analysis")

    sync_df = get_sync_activity()
    if sync_df.empty:
        st.error("Unable to load sync activity data")
        return

    # Convert date column to datetime
    sync_df['date'] = pd.to_datetime(sync_df['date'])
    
    # Create subplot with secondary y-axis
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Daily Sync Volume",
            "Success Rate Trend",
            "Performance Metrics",
            "Activity Distribution"
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": True}],
            [{"secondary_y": False}, {"type": "pie"}]
        ]
    )

    # Daily sync volume
    fig.add_trace(
        go.Scatter(
            x=sync_df['date'],
            y=sync_df['total_syncs'],
            mode='lines+markers',
            name='Total Syncs',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )

    # Success rate trend
    fig.add_trace(
        go.Scatter(
            x=sync_df['date'],
            y=sync_df['success_rate'],
            mode='lines+markers',
            name='Success Rate (%)',
            line=dict(color='green', width=2)
        ),
        row=1, col=2
    )

    # Performance metrics (response time)
    fig.add_trace(
        go.Scatter(
            x=sync_df['date'],
            y=sync_df['avg_duration_ms'],
            mode='lines+markers',
            name='Avg Duration (ms)',
            line=dict(color='orange', width=2)
        ),
        row=2, col=1
    )

    # Activity distribution pie chart
    total_successful = sync_df['successful_syncs'].sum()
    total_failed = sync_df['failed_syncs'].sum()
    
    fig.add_trace(
        go.Pie(
            labels=['Successful', 'Failed'],
            values=[total_successful, total_failed],
            name='Sync Results',
            marker_colors=['green', 'red']
        ),
        row=2, col=2
    )

    fig.update_layout(
        height=800,
        title_text="ISIN Sync Activity Dashboard",
        showlegend=False
    )

    # Update axes labels
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Number of Syncs", row=1, col=1)
    
    fig.update_xaxes(title_text="Date", row=1, col=2)
    fig.update_yaxes(title_text="Success Rate (%)", row=1, col=2)
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Duration (ms)", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_syncs = sync_df['total_syncs'].mean()
        st.metric("Avg Daily Syncs", f"{avg_syncs:,.0f}")

    with col2:
        avg_success = sync_df['success_rate'].mean()
        st.metric("Avg Success Rate", f"{avg_success:.1f}%")

    with col3:
        avg_duration = sync_df['avg_duration_ms'].mean()
        st.metric("Avg Duration", f"{avg_duration:.0f}ms")

    with col4:
        total_processed = sync_df['total_syncs'].sum()
        st.metric("Total Processed", f"{total_processed:,}")


def create_quality_charts(quality_metrics):
    """Create quality analysis charts."""
    if not quality_metrics:
        st.error("No quality metrics available")
        return

    # Quality scores radar chart
    categories = ['Overall Score', 'Validation Accuracy', 'Completeness', 'Timeliness', 'Consistency']
    values = [
        quality_metrics.get('overall_score', 0),
        quality_metrics.get('validation_accuracy', 0),
        quality_metrics.get('completeness', 0),
        quality_metrics.get('timeliness', 0),
        quality_metrics.get('consistency', 0),
    ]

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Quality Metrics'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title="Data Quality Score Breakdown"
    )

    st.plotly_chart(fig, use_container_width=True)

    return fig