"""ISIN Analytics and Summary Dashboard.

This module provides comprehensive analytics and insights for the ISIN system
including coverage metrics, data quality analysis, and performance monitoring.
"""

import streamlit as st

# Import components from specialized modules
from .isin_analytics_charts import (
    exchange_analysis_widget,
    geographical_analysis_widget,
    sync_activity_analysis,
)
from .isin_analytics_quality import data_quality_analysis
from .isin_analytics_widgets import (
    dashboard_footer,
    overview_metrics_widget,
    quick_actions_sidebar,
    system_health_dashboard,
)


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
        quick_actions_sidebar()

    # Footer with actions
    dashboard_footer()


# Export all functions for backward compatibility
__all__ = [
    "isin_analytics_dashboard",
    # Widget functions
    "overview_metrics_widget",
    "system_health_dashboard",
    "quick_actions_sidebar",
    "dashboard_footer",
    # Chart functions
    "geographical_analysis_widget",
    "exchange_analysis_widget",
    "sync_activity_analysis",
    # Quality functions
    "data_quality_analysis",
]


if __name__ == "__main__":
    isin_analytics_dashboard()
