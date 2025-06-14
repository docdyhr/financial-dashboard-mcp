"""Task monitoring components for the Financial Dashboard."""

import pandas as pd
import requests
import streamlit as st


def get_active_tasks(backend_url: str) -> list[dict] | None:
    """Fetch active tasks from the backend."""
    try:
        response = requests.get(f"{backend_url}/api/tasks/active", timeout=10)
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch active tasks: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None


def get_task_status(backend_url: str, task_id: str) -> dict | None:
    """Get status of a specific task."""
    try:
        response = requests.get(f"{backend_url}/api/tasks/{task_id}/status", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def task_monitoring_widget(backend_url: str):
    """Display task monitoring widget."""
    st.subheader("⚙️ Background Tasks")

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("🔄 Refresh Tasks"):
            st.rerun()

    with col1:
        active_tasks = get_active_tasks(backend_url)

        if active_tasks:
            if len(active_tasks) == 0:
                st.info("No active tasks running.")
            else:
                # Display active tasks
                df = pd.DataFrame(active_tasks)

                # Format the data for display
                display_df = df.copy()

                # Format timestamp if present
                if "started_at" in display_df.columns:
                    display_df["started_at"] = pd.to_datetime(
                        display_df["started_at"]
                    ).dt.strftime("%H:%M:%S")

                # Rename columns
                column_mapping = {
                    "task_id": "Task ID",
                    "name": "Task Name",
                    "status": "Status",
                    "started_at": "Started At",
                    "progress": "Progress",
                }

                available_columns = [
                    col for col in column_mapping if col in display_df.columns
                ]
                display_df = display_df[available_columns].rename(
                    columns=column_mapping
                )

                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Unable to fetch task information.")


def submit_task_widget(backend_url: str):
    """Widget to submit new tasks."""
    st.subheader("🚀 Submit Tasks")

    task_type = st.selectbox(
        "Task Type", ["Market Data Fetch", "Portfolio Snapshot", "Portfolio Analytics"]
    )

    if task_type == "Market Data Fetch":
        symbols = st.text_input(
            "Symbols (comma-separated)",
            value="AAPL,GOOGL,MSFT",
            help="Enter stock symbols separated by commas",
        )

        if st.button("Submit Market Data Task"):
            if symbols:
                symbol_list = [s.strip().upper() for s in symbols.split(",")]
                try:
                    response = requests.post(
                        f"{backend_url}/api/tasks/market-data/fetch",
                        json={"symbols": symbol_list},
                        timeout=10,
                    )
                    if response.status_code == 200:
                        task_data = response.json()
                        st.success(
                            f"Task submitted! ID: {task_data.get('task_id', 'N/A')}"
                        )
                    else:
                        st.error(f"Failed to submit task: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error submitting task: {e}")
            else:
                st.warning("Please enter at least one symbol.")

    elif task_type == "Portfolio Snapshot":
        user_id = st.number_input("User ID", min_value=1, value=1)

        if st.button("Submit Snapshot Task"):
            try:
                response = requests.post(
                    f"{backend_url}/api/tasks/portfolio/snapshot",
                    json={"user_id": user_id},
                    timeout=10,
                )
                if response.status_code == 200:
                    task_data = response.json()
                    st.success(f"Task submitted! ID: {task_data.get('task_id', 'N/A')}")
                else:
                    st.error(f"Failed to submit task: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error submitting task: {e}")

    elif task_type == "Portfolio Analytics":
        user_id = st.number_input("User ID", min_value=1, value=1, key="analytics_user")

        if st.button("Submit Analytics Task"):
            try:
                response = requests.post(
                    f"{backend_url}/api/tasks/portfolio/analytics",
                    json={"user_id": user_id},
                    timeout=10,
                )
                if response.status_code == 200:
                    task_data = response.json()
                    st.success(f"Task submitted! ID: {task_data.get('task_id', 'N/A')}")
                else:
                    st.error(f"Failed to submit task: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error submitting task: {e}")


def system_status_widget(backend_url: str):
    """Display system status information."""
    st.subheader("🔧 System Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Backend status
        try:
            response = requests.get(f"{backend_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Backend API")
            else:
                st.error("❌ Backend API")
        except Exception:
            st.error("❌ Backend API")

    with col2:
        # Task queue status (through API)
        try:
            response = requests.get(f"{backend_url}/api/tasks/active", timeout=5)
            if response.status_code == 200:
                st.success("✅ Task Queue")
            else:
                st.error("❌ Task Queue")
        except Exception:
            st.error("❌ Task Queue")

    with col3:
        # Database status (through API)
        try:
            response = requests.get(f"{backend_url}/api/portfolio/summary", timeout=5)
            if response.status_code == 200:
                st.success("✅ Database")
            else:
                st.error("❌ Database")
        except Exception:
            st.error("❌ Database")

    # Additional system info
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Services:**")
        st.markdown("- 🌐 Flower UI: http://localhost:5555")
        st.markdown("- 📊 API Docs: http://localhost:8000/docs")
        st.markdown("- 🔄 Redis: localhost:6379")

    with col2:
        st.markdown("**Quick Actions:**")
        if st.button("View Flower Dashboard", key="flower_btn"):
            st.markdown("[Open Flower](http://localhost:5555)")
        if st.button("View API Documentation", key="api_docs_btn"):
            st.markdown("[Open API Docs](http://localhost:8000/docs)")


def task_history_widget(backend_url: str):
    """Display recent task history."""
    st.subheader("📋 Recent Task History")

    # This would need a backend endpoint for task history
    # For now, show placeholder
    st.info("Task history will be available in a future update.")

    # Placeholder data
    sample_data = [
        {
            "Task ID": "abc123",
            "Type": "Market Data",
            "Status": "SUCCESS",
            "Duration": "2.3s",
            "Completed": "10:30:15",
        },
        {
            "Task ID": "def456",
            "Type": "Portfolio Snapshot",
            "Status": "SUCCESS",
            "Duration": "1.8s",
            "Completed": "10:25:42",
        },
        {
            "Task ID": "ghi789",
            "Type": "Analytics",
            "Status": "FAILED",
            "Duration": "0.5s",
            "Completed": "10:20:33",
        },
    ]

    df = pd.DataFrame(sample_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
