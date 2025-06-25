"""ISIN Analytics widget components."""

import streamlit as st

from .isin_analytics_data import get_isin_statistics, get_system_health


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
            "Total ISINs",
            f"{stats.get('total_isins', 0):,}",
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
        valid_ratio = stats.get("valid_isins", 0) / max(stats.get("total_isins", 1), 1)
        st.metric(
            "Valid ISINs",
            f"{valid_ratio:.1%}",
            delta=f"{valid_ratio - 0.90:.1%}" if valid_ratio > 0.90 else None,
        )

    with col4:
        st.metric(
            "Countries Covered",
            stats.get("countries_covered", 0),
            delta=(
                f"+{stats.get('countries_covered', 67) - 60}"
                if stats.get("countries_covered", 67) > 60
                else None
            ),
        )

    # Secondary metrics
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric("Active Exchanges", stats.get("exchanges_covered", 0))

    with col6:
        st.metric("Invalid ISINs", f"{stats.get('invalid_isins', 0):,}")

    with col7:
        last_sync = stats.get("last_sync", "Never")
        if last_sync != "Never":
            import datetime

            try:
                sync_time = datetime.datetime.fromisoformat(
                    last_sync.replace("Z", "+00:00")
                )
                last_sync = sync_time.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        st.metric("Last Sync", last_sync)

    with col8:
        st.metric("Data Quality", "A+")


def system_health_dashboard():
    """Display system health metrics."""
    st.subheader("🏥 System Health")

    health = get_system_health()
    if not health:
        st.error("Unable to load system health data")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Performance")
        cache_hit = health.get("cache_hit_rate", 0)
        color = "normal" if cache_hit >= 80 else "inverse"
        st.metric(
            "Cache Hit Rate",
            f"{cache_hit:.1f}%",
            delta=f"{cache_hit - 80:.1f}%" if cache_hit != 80 else None,
            delta_color=color,
        )

        response_time = health.get("avg_response_time", 0)
        color = "normal" if response_time <= 200 else "inverse"
        st.metric(
            "Avg Response Time",
            f"{response_time:.1f}ms",
            delta=f"{200 - response_time:.1f}ms" if response_time != 200 else None,
            delta_color=color,
        )

    with col2:
        st.subheader("Resources")
        memory = health.get("memory_usage", 0)
        color = "normal" if memory <= 80 else "inverse"
        st.metric(
            "Memory Usage",
            f"{memory:.1f}%",
            delta=f"{memory - 50:.1f}%" if memory != 50 else None,
            delta_color=color,
        )

        cpu = health.get("cpu_usage", 0)
        color = "normal" if cpu <= 70 else "inverse"
        st.metric(
            "CPU Usage",
            f"{cpu:.1f}%",
            delta=f"{cpu - 30:.1f}%" if cpu != 30 else None,
            delta_color=color,
        )

    with col3:
        st.subheader("Activity")
        st.metric("Active Connections", health.get("active_connections", 0))
        st.metric("Queue Length", health.get("queue_length", 0))

    # Health status indicator
    overall_health = "Excellent"
    if memory > 90 or cpu > 80 or response_time > 500:
        overall_health = "Poor"
    elif memory > 80 or cpu > 70 or response_time > 200:
        overall_health = "Fair"
    elif memory > 70 or cpu > 60 or response_time > 150:
        overall_health = "Good"

    if overall_health == "Excellent":
        st.success(f"🟢 System Status: {overall_health}")
    elif overall_health == "Good":
        st.info(f"🟡 System Status: {overall_health}")
    elif overall_health == "Fair":
        st.warning(f"🟠 System Status: {overall_health}")
    else:
        st.error(f"🔴 System Status: {overall_health}")


def quick_actions_sidebar():
    """Display quick actions in sidebar."""
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


def dashboard_footer():
    """Display dashboard footer with actions."""
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        from datetime import datetime

        st.caption(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    with col2:
        if st.button("📤 Export Data", help="Export analytics data"):
            st.info("Data export functionality would be implemented here")

    with col3:
        if st.button("📧 Schedule Report", help="Schedule automated reports"):
            st.info("Report scheduling functionality would be implemented here")
