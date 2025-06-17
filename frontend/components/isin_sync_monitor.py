"""ISIN Sync Service Monitor component for frontend dashboard.

This component provides real-time monitoring and management of the ISIN
synchronization service including job status, conflict resolution, and
service health monitoring.
"""

import logging
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"


def call_sync_api(endpoint: str, method: str = "GET", data: dict = None) -> dict | None:
    """Call ISIN sync API endpoint with error handling.

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, DELETE)
        data: Request data for POST requests

    Returns:
        API response data or None if error
    """
    try:
        url = f"{BACKEND_URL}/isin/sync/{endpoint}"

        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data or {}, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None

        if response.status_code == 200:
            return response.json()
        st.error(f"API Error {response.status_code}: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def format_datetime(dt_string: str) -> str:
    """Format datetime string for display."""
    if not dt_string:
        return "N/A"

    try:
        dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return dt_string


def sync_service_status_widget():
    """Display sync service status and controls."""
    st.subheader("🔄 Sync Service Status")

    # Get service status
    status_data = call_sync_api("status")

    if status_data and status_data.get("success"):
        stats = status_data["data"]

        # Status metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            service_running = stats.get("service_running", False)
            status_color = "🟢" if service_running else "🔴"
            st.metric(
                "Service Status",
                f"{status_color} {'Running' if service_running else 'Stopped'}",
            )

        with col2:
            st.metric("Queue Size", stats.get("queue_size", 0))

        with col3:
            st.metric("Active Jobs", stats.get("running_jobs", 0))

        with col4:
            st.metric("Unresolved Conflicts", stats.get("unresolved_conflicts", 0))

        # Additional metrics
        col5, col6, col7 = st.columns(3)

        with col5:
            st.metric("Total Jobs", stats.get("total_jobs", 0))

        with col6:
            st.metric("Completed Jobs", stats.get("completed_jobs", 0))

        with col7:
            st.metric("Failed Jobs", stats.get("failed_jobs", 0))

        # Service controls
        st.subheader("⚙️ Service Controls")

        col1, col2, col3 = st.columns([2, 2, 4])

        with col1:
            if st.button("🟢 Start Service", disabled=service_running):
                with st.spinner("Starting sync service..."):
                    result = call_sync_api("service/start", "POST")
                    if result and result.get("success"):
                        st.success("✅ Sync service started")
                        st.rerun()
                    else:
                        st.error("❌ Failed to start sync service")

        with col2:
            if st.button("🔴 Stop Service", disabled=not service_running):
                with st.spinner("Stopping sync service..."):
                    result = call_sync_api("service/stop", "POST")
                    if result and result.get("success"):
                        st.success("✅ Sync service stopped")
                        st.rerun()
                    else:
                        st.error("❌ Failed to stop sync service")

        with col3:
            if st.button("🔄 Refresh Status"):
                st.rerun()

    else:
        st.error("❌ Unable to fetch sync service status")


def sync_jobs_management_widget():
    """Manage sync jobs."""
    st.subheader("📋 Sync Jobs Management")

    # Create new sync job
    with st.expander("➕ Create New Sync Job", expanded=False):
        with st.form("create_sync_job"):
            st.write("**Add ISINs for synchronization**")

            # ISIN input methods
            input_method = st.radio(
                "Input Method",
                ["Manual Entry", "File Upload", "Bulk Criteria"],
                horizontal=True,
            )

            isins = []
            country_codes = []
            exchanges = []
            max_isins = 100

            if input_method == "Manual Entry":
                isin_text = st.text_area(
                    "ISINs (one per line)",
                    placeholder="US0378331005\nGB0002162385\nDE0007164600",
                    height=100,
                )
                if isin_text:
                    isins = [
                        line.strip().upper()
                        for line in isin_text.split("\n")
                        if line.strip()
                    ]

            elif input_method == "File Upload":
                uploaded_file = st.file_uploader(
                    "Upload ISIN list", type=["txt", "csv"]
                )
                if uploaded_file:
                    content = uploaded_file.read().decode("utf-8")
                    isins = [
                        line.strip().upper()
                        for line in content.split("\n")
                        if line.strip()
                    ]

            elif input_method == "Bulk Criteria":
                col1, col2 = st.columns(2)

                with col1:
                    country_codes = st.multiselect(
                        "Country Codes",
                        [
                            "DE",
                            "GB",
                            "FR",
                            "NL",
                            "IT",
                            "ES",
                            "CH",
                            "AT",
                            "SE",
                            "DK",
                            "FI",
                            "NO",
                        ],
                        help="Select countries to sync",
                    )

                with col2:
                    exchanges = st.multiselect(
                        "Exchanges",
                        [
                            "XETR",
                            "XFRA",
                            "XLON",
                            "XPAR",
                            "XAMS",
                            "XMIL",
                            "XMAD",
                            "XSWX",
                        ],
                        help="Select exchanges to sync",
                    )

                max_isins = st.number_input(
                    "Max ISINs", min_value=1, max_value=5000, value=100
                )

            # Job configuration
            col1, col2 = st.columns(2)

            with col1:
                source = st.selectbox(
                    "Data Source",
                    ["german_data_providers", "european_mappings", "manual"],
                    help="Source for sync data",
                )

            with col2:
                priority = st.selectbox("Priority", ["low", "normal", "high"])

            create_button = st.form_submit_button("🚀 Create Sync Job")

            if create_button:
                if input_method == "Bulk Criteria":
                    # Create bulk sync job
                    bulk_data = {
                        "country_codes": country_codes if country_codes else None,
                        "exchanges": exchanges if exchanges else None,
                        "max_isins": max_isins,
                        "source": source,
                    }

                    with st.spinner("Creating bulk sync job..."):
                        result = call_sync_api("bulk", "POST", bulk_data)
                        if result and result.get("success"):
                            job_data = result["data"]
                            st.success(
                                f"✅ Bulk sync job created: {job_data['job_id']} ({job_data['isin_count']} ISINs)"
                            )
                        else:
                            st.error("❌ Failed to create bulk sync job")

                elif isins:
                    # Create regular sync job
                    job_data = {"isins": isins, "source": source, "priority": priority}

                    with st.spinner(f"Creating sync job for {len(isins)} ISINs..."):
                        result = call_sync_api("jobs", "POST", job_data)
                        if result and result.get("success"):
                            job_info = result["data"]
                            st.success(f"✅ Sync job created: {job_info['job_id']}")
                        else:
                            st.error("❌ Failed to create sync job")

                else:
                    st.error("Please provide ISINs to sync")

    # List existing jobs
    st.subheader("📊 Active Jobs")

    # Job filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "running", "completed", "failed", "cancelled"],
        )

    with col2:
        limit = st.number_input("Max Jobs", min_value=10, max_value=200, value=50)

    with col3:
        if st.button("🔄 Refresh Jobs"):
            st.rerun()

    # Get jobs list
    jobs_endpoint = f"jobs?limit={limit}"
    if status_filter != "All":
        jobs_endpoint += f"&status={status_filter}"

    jobs_data = call_sync_api(jobs_endpoint)

    if jobs_data and jobs_data.get("success"):
        jobs = jobs_data["data"]["jobs"]

        if jobs:
            # Create jobs dataframe
            jobs_df = []
            for job in jobs:
                jobs_df.append(
                    {
                        "Job ID": job["job_id"],
                        "Status": f"{'🟡' if job['status'] == 'pending' else '🟢' if job['status'] == 'running' else '✅' if job['status'] == 'completed' else '❌'} {job['status'].title()}",
                        "Progress": (
                            f"{job['progress']}/{job['total']}"
                            if job["total"] > 0
                            else "N/A"
                        ),
                        "Source": job["source"],
                        "Created": format_datetime(job["created_at"]),
                        "Started": format_datetime(job["started_at"]),
                        "Completed": format_datetime(job["completed_at"]),
                        "Errors": len(job.get("errors", [])),
                    }
                )

            df = pd.DataFrame(jobs_df)

            # Display jobs table
            st.dataframe(df, use_container_width=True)

            # Job details
            if jobs_df:
                selected_job_id = st.selectbox(
                    "Select job for details",
                    [job["Job ID"] for job in jobs_df],
                    key="job_details_select",
                )

                if selected_job_id:
                    selected_job = next(
                        job for job in jobs if job["job_id"] == selected_job_id
                    )

                    with st.expander(
                        f"📋 Job Details: {selected_job_id}", expanded=False
                    ):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Status:** {selected_job['status']}")
                            st.write(f"**Source:** {selected_job['source']}")
                            st.write(
                                f"**Progress:** {selected_job['progress']}/{selected_job['total']}"
                            )

                        with col2:
                            st.write(
                                f"**Created:** {format_datetime(selected_job['created_at'])}"
                            )
                            st.write(
                                f"**Started:** {format_datetime(selected_job['started_at'])}"
                            )
                            st.write(
                                f"**Completed:** {format_datetime(selected_job['completed_at'])}"
                            )

                        # Show errors if any
                        if selected_job.get("errors"):
                            st.write("**Errors:**")
                            for error in selected_job["errors"][
                                :10
                            ]:  # Show first 10 errors
                                st.error(f"• {error}")

                        # Job actions
                        if selected_job["status"] in ["pending", "running"]:
                            if st.button(f"❌ Cancel Job {selected_job_id}"):
                                with st.spinner("Cancelling job..."):
                                    result = call_sync_api(
                                        f"jobs/{selected_job_id}", "DELETE"
                                    )
                                    if result and result.get("success"):
                                        st.success("✅ Job cancelled")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to cancel job")

        else:
            st.info("No sync jobs found")

    else:
        st.error("❌ Unable to fetch sync jobs")


def conflicts_resolution_widget():
    """Handle mapping conflicts."""
    st.subheader("⚠️ Mapping Conflicts")

    # Get pending conflicts
    conflicts_data = call_sync_api("conflicts")

    if conflicts_data and conflicts_data.get("success"):
        conflicts = conflicts_data["data"]["conflicts"]

        if conflicts:
            st.write(f"**{len(conflicts)} conflicts require manual resolution**")

            # Display conflicts
            for i, conflict in enumerate(conflicts):
                with st.expander(
                    f"🔍 Conflict {i+1}: {conflict['isin']}", expanded=False
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Existing Mapping:**")
                        st.write(f"• Ticker: `{conflict['existing_ticker']}`")
                        st.write(f"• Exchange: `{conflict['existing_exchange']}`")
                        st.write(f"• Confidence: {conflict['existing_confidence']:.1%}")

                    with col2:
                        st.write("**New Mapping:**")
                        st.write(f"• Ticker: `{conflict['new_ticker']}`")
                        st.write(f"• Exchange: `{conflict['new_exchange']}`")
                        st.write(f"• Confidence: {conflict['new_confidence']:.1%}")

                    st.write(f"**Conflict Type:** {conflict['conflict_type']}")

                    # Resolution options
                    st.write("**Resolution:**")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if st.button("✅ Keep Existing", key=f"keep_{i}"):
                            resolve_conflict(
                                conflict["isin"],
                                "keep_existing",
                                "User chose to keep existing mapping",
                            )

                    with col2:
                        if st.button("🆕 Use New", key=f"new_{i}"):
                            resolve_conflict(
                                conflict["isin"],
                                "use_new",
                                "User chose to use new mapping",
                            )

                    with col3:
                        if st.button("🔀 Merge", key=f"merge_{i}"):
                            resolve_conflict(
                                conflict["isin"],
                                "merge",
                                "User chose to merge mappings",
                            )

                    with col4:
                        if st.button("❌ Skip", key=f"skip_{i}"):
                            st.info("Conflict skipped - will remain unresolved")

        else:
            st.success("✅ No pending conflicts")

    else:
        st.error("❌ Unable to fetch conflicts")


def resolve_conflict(isin: str, resolution: str, reason: str):
    """Resolve a mapping conflict."""
    resolve_data = {"isin": isin, "resolution": resolution, "reason": reason}

    with st.spinner(f"Resolving conflict for {isin}..."):
        result = call_sync_api("conflicts/resolve", "POST", resolve_data)
        if result and result.get("success"):
            st.success(f"✅ Conflict resolved: {resolution}")
            st.rerun()
        else:
            st.error("❌ Failed to resolve conflict")


def sync_health_monitor():
    """Monitor sync service health."""
    st.subheader("🏥 Service Health")

    health_data = call_sync_api("health")

    if health_data and health_data.get("success"):
        health = health_data["data"]

        # Overall health status
        overall_healthy = health.get("healthy", False)
        health_color = "🟢" if overall_healthy else "🔴"

        st.metric(
            "Overall Health",
            f"{health_color} {'Healthy' if overall_healthy else 'Unhealthy'}",
        )

        # Health metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Service Running",
                "✅ Yes" if health.get("service_running") else "❌ No",
            )
            st.metric("Queue Size", health.get("queue_size", 0))

        with col2:
            st.metric("Active Jobs", health.get("active_jobs", 0))
            st.metric("Recent Failures", health.get("recent_failures", 0))

        with col3:
            st.metric("Unresolved Conflicts", health.get("unresolved_conflicts", 0))
            st.write(f"**Last Check:** {format_datetime(health.get('last_check', ''))}")

        # Health recommendations
        if not overall_healthy:
            st.warning("⚠️ **Health Issues Detected:**")

            if not health.get("service_running"):
                st.error("• Sync service is not running")

            if health.get("recent_failures", 0) > 0:
                st.error(f"• {health['recent_failures']} recent job failures")

            if health.get("unresolved_conflicts", 0) > 10:
                st.warning(f"• {health['unresolved_conflicts']} unresolved conflicts")

    else:
        st.error("❌ Unable to fetch health status")


def isin_sync_monitor_page():
    """Complete ISIN sync monitoring page."""
    st.title("🔄 ISIN Sync Monitor")
    st.markdown("*Real-time ISIN mapping synchronization management*")

    # Auto-refresh toggle
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(
            "Monitor and manage ISIN synchronization jobs, resolve conflicts, and track service health."
        )

    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)

    if auto_refresh:
        # Auto-refresh every 30 seconds
        time.sleep(30)
        st.rerun()

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Status", "🔄 Jobs", "⚠️ Conflicts", "🏥 Health"]
    )

    with tab1:
        sync_service_status_widget()

    with tab2:
        sync_jobs_management_widget()

    with tab3:
        conflicts_resolution_widget()

    with tab4:
        sync_health_monitor()

    # Quick actions sidebar
    with st.sidebar:
        st.subheader("🚀 Quick Actions")

        # Quick sync for popular ISINs
        if st.button("🇩🇪 Sync German DAX"):
            dax_isins = [
                "DE0007164600",  # SAP
                "DE0008404005",  # Allianz
                "DE0005190003",  # BMW
                "DE0007236101",  # Siemens
                "DE0008469008",  # Deutsche Bank
            ]

            job_data = {
                "isins": dax_isins,
                "source": "quick_dax_sync",
                "priority": "high",
            }

            with st.spinner("Creating DAX sync job..."):
                result = call_sync_api("jobs", "POST", job_data)
                if result and result.get("success"):
                    st.success("✅ DAX sync started")
                else:
                    st.error("❌ Failed to start DAX sync")

        if st.button("🇬🇧 Sync UK FTSE"):
            ftse_isins = [
                "GB0002374006",  # Shell
                "GB0007980591",  # BP
                "GB00B03MLX29",  # Royal Dutch Shell
                "GB0008706128",  # HSBC
                "GB0031348658",  # Vodafone
            ]

            job_data = {
                "isins": ftse_isins,
                "source": "quick_ftse_sync",
                "priority": "high",
            }

            with st.spinner("Creating FTSE sync job..."):
                result = call_sync_api("jobs", "POST", job_data)
                if result and result.get("success"):
                    st.success("✅ FTSE sync started")
                else:
                    st.error("❌ Failed to start FTSE sync")

        # Emergency actions
        st.divider()
        st.subheader("🚨 Emergency")

        if st.button("🛑 Stop All Jobs", type="secondary"):
            if st.button("⚠️ Confirm Stop All", type="secondary"):
                # This would require additional API endpoint
                st.warning("Feature not implemented - stop service instead")


if __name__ == "__main__":
    isin_sync_monitor_page()
