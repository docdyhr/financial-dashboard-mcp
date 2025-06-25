"""Backup and export functionality for portfolio data."""

from datetime import datetime
import json

import pandas as pd
import streamlit as st


def export_portfolio_to_csv(backend_url: str) -> str:
    """Export portfolio data to CSV format."""
    # In a real implementation, this would fetch data from the API
    # For demo, we'll create sample data

    sample_data = {
        "Symbol": ["AAPL", "MSFT", "VOO", "BTC-USD"],
        "Name": [
            "Apple Inc.",
            "Microsoft Corporation",
            "Vanguard S&P 500 ETF",
            "Bitcoin USD",
        ],
        "Quantity": [50.0, 30.0, 25.0, 0.5],
        "Purchase_Price": [150.00, 320.00, 400.00, 45000.00],
        "Current_Price": [200.64, 493.82, 411.22, 45134.16],
        "Total_Cost": [7500.00, 9600.00, 10000.00, 22500.00],
        "Current_Value": [10032.00, 14814.60, 10280.50, 22567.08],
        "Gain_Loss": [2532.00, 5214.60, 280.50, 67.08],
        "Gain_Loss_Percent": [33.76, 54.32, 2.81, 0.30],
        "Purchase_Date": ["2024-01-15", "2024-02-01", "2024-01-05", "2024-03-01"],
        "Asset_Type": ["Stock", "Stock", "ETF", "Crypto"],
        "Sector": ["Technology", "Technology", "Broad Market", "Alternative"],
    }

    df = pd.DataFrame(sample_data)
    return df.to_csv(index=False)


def export_portfolio_to_json(backend_url: str) -> str:
    """Export portfolio data to JSON format."""
    portfolio_data = {
        "export_metadata": {
            "export_date": datetime.now().isoformat(),
            "source": "Financial Dashboard",
            "version": "1.0",
            "user": "demo@financial-dashboard.com",
        },
        "portfolio_summary": {
            "total_value": 57694.18,
            "total_cost": 49600.00,
            "total_gain_loss": 8094.18,
            "total_gain_loss_percent": 16.31,
            "number_of_positions": 4,
            "last_updated": datetime.now().isoformat(),
        },
        "positions": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "asset_type": "stock",
                "sector": "Technology",
                "quantity": 50.0,
                "purchase_price": 150.00,
                "current_price": 200.64,
                "purchase_date": "2024-01-15",
                "total_cost": 7500.00,
                "current_value": 10032.00,
                "gain_loss": 2532.00,
                "gain_loss_percent": 33.76,
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "asset_type": "stock",
                "sector": "Technology",
                "quantity": 30.0,
                "purchase_price": 320.00,
                "current_price": 493.82,
                "purchase_date": "2024-02-01",
                "total_cost": 9600.00,
                "current_value": 14814.60,
                "gain_loss": 5214.60,
                "gain_loss_percent": 54.32,
            },
            {
                "symbol": "VOO",
                "name": "Vanguard S&P 500 ETF",
                "asset_type": "etf",
                "sector": "Broad Market",
                "quantity": 25.0,
                "purchase_price": 400.00,
                "current_price": 411.22,
                "purchase_date": "2024-01-05",
                "total_cost": 10000.00,
                "current_value": 10280.50,
                "gain_loss": 280.50,
                "gain_loss_percent": 2.81,
            },
            {
                "symbol": "BTC-USD",
                "name": "Bitcoin USD",
                "asset_type": "crypto",
                "sector": "Alternative",
                "quantity": 0.5,
                "purchase_price": 45000.00,
                "current_price": 45134.16,
                "purchase_date": "2024-03-01",
                "total_cost": 22500.00,
                "current_value": 22567.08,
                "gain_loss": 67.08,
                "gain_loss_percent": 0.30,
            },
        ],
        "allocation_by_sector": {
            "Technology": 56.9,
            "Broad Market": 17.8,
            "Alternative": 39.1,
        },
        "allocation_by_asset_type": {"Stock": 43.1, "ETF": 17.8, "Crypto": 39.1},
    }

    return json.dumps(portfolio_data, indent=2)


def create_backup_database(backend_url: str) -> str:
    """Create a complete database backup in JSON format."""
    backup_data = {
        "backup_metadata": {
            "created_at": datetime.now().isoformat(),
            "database_version": "1.0",
            "backup_type": "full",
            "application": "Financial Dashboard MCP",
            "description": "Complete portfolio database backup",
        },
        "users": [
            {
                "id": 6,
                "email": "user@example.com",
                "username": "testuser",
                "full_name": "Test User",
                "is_active": True,
                "is_verified": True,
                "preferred_currency": "USD",
                "timezone": "UTC",
                "created_at": "2025-06-13T13:29:23.447204",
                "last_login": None,
            }
        ],
        "assets": [
            {
                "id": 1,
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "asset_type": "stock",
                "category": "equity",
                "currency": "USD",
                "current_price": 200.64,
                "is_active": True,
            },
            {
                "id": 2,
                "ticker": "MSFT",
                "name": "Microsoft Corporation",
                "asset_type": "stock",
                "category": "equity",
                "currency": "USD",
                "current_price": 493.82,
                "is_active": True,
            },
            {
                "id": 3,
                "ticker": "VOO",
                "name": "Vanguard S&P 500 ETF",
                "asset_type": "etf",
                "category": "equity",
                "currency": "USD",
                "current_price": 411.22,
                "is_active": True,
            },
            {
                "id": 4,
                "ticker": "BTC-USD",
                "name": "Bitcoin USD",
                "asset_type": "crypto",
                "category": "alternative",
                "currency": "USD",
                "current_price": 45134.16,
                "is_active": True,
            },
        ],
        "positions": [
            {
                "id": 1,
                "user_id": 6,
                "asset_id": 1,
                "quantity": 50.0,
                "average_cost_per_share": 150.00,
                "total_cost_basis": 7500.00,
                "is_active": True,
            },
            {
                "id": 2,
                "user_id": 6,
                "asset_id": 2,
                "quantity": 30.0,
                "average_cost_per_share": 320.00,
                "total_cost_basis": 9600.00,
                "is_active": True,
            },
            {
                "id": 3,
                "user_id": 6,
                "asset_id": 3,
                "quantity": 25.0,
                "average_cost_per_share": 400.00,
                "total_cost_basis": 10000.00,
                "is_active": True,
            },
            {
                "id": 4,
                "user_id": 6,
                "asset_id": 4,
                "quantity": 0.5,
                "average_cost_per_share": 45000.00,
                "total_cost_basis": 22500.00,
                "is_active": True,
            },
        ],
        "settings": {
            "default_currency": "USD",
            "risk_tolerance": "moderate",
            "auto_rebalance": False,
            "notification_preferences": {
                "price_alerts": True,
                "portfolio_reports": True,
                "market_news": False,
            },
        },
    }

    return json.dumps(backup_data, indent=2)


def backup_export_page():
    """Main backup and export page."""
    st.title("💾 Backup & Export")
    st.markdown("*Secure your portfolio data with exports and backups*")

    # Export section
    st.subheader("📊 Export Portfolio Data")
    st.markdown(
        "Download your portfolio data in various formats for analysis or record keeping."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 Export as CSV", type="primary", use_container_width=True):
            csv_data = export_portfolio_to_csv("")
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.success("✅ CSV export ready for download!")

    with col2:
        if st.button("📄 Export as JSON", type="secondary", use_container_width=True):
            json_data = export_portfolio_to_json("")
            st.download_button(
                label="💾 Download JSON",
                data=json_data,
                file_name=f"portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
            st.success("✅ JSON export ready for download!")

    with col3:
        if st.button("📈 Export Report", use_container_width=True):
            # Generate a comprehensive report
            report_data = f"""
FINANCIAL DASHBOARD PORTFOLIO REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=====================================

PORTFOLIO SUMMARY
-----------------
Total Value: $57,694.18
Total Cost: $49,600.00
Total Gain/Loss: $8,094.18 (+16.31%)
Number of Positions: 4

POSITIONS
---------
AAPL: 50 shares @ $200.64 = $10,032.00 (+33.76%)
MSFT: 30 shares @ $493.82 = $14,814.60 (+54.32%)
VOO: 25 shares @ $411.22 = $10,280.50 (+2.81%)
BTC-USD: 0.5 shares @ $45,134.16 = $22,567.08 (+0.30%)

ALLOCATION
----------
Technology: 43.1%
Broad Market: 17.8%
Alternative: 39.1%

This report contains demo data for illustration purposes.
"""

            st.download_button(
                label="💾 Download Report",
                data=report_data,
                file_name=f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
            st.success("✅ Portfolio report ready for download!")

    st.divider()

    # Backup section
    st.subheader("🛡️ Database Backup")
    st.markdown("Create complete backups of your financial dashboard database.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Full Database Backup")
        st.markdown("Includes all users, assets, positions, and settings.")

        if st.button("🗄️ Create Full Backup", type="primary", use_container_width=True):
            backup_data = create_backup_database("")
            st.download_button(
                label="💾 Download Backup",
                data=backup_data,
                file_name=f"financial_dashboard_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
            st.success("✅ Database backup created successfully!")

    with col2:
        st.markdown("### Scheduled Backups")
        st.markdown("Configure automatic backup schedules.")

        backup_frequency = st.selectbox(
            "Backup Frequency", ["Disabled", "Daily", "Weekly", "Monthly"], index=0
        )

        backup_time = st.time_input("Backup Time", value=datetime.now().time())

        if st.button("⚙️ Configure Auto-Backup", use_container_width=True):
            if backup_frequency != "Disabled":
                st.success(
                    f"✅ Scheduled {backup_frequency.lower()} backups at {backup_time}"
                )
                st.info(
                    "Note: This is a demo. In production, backups would be configured in the backend."
                )
            else:
                st.info("Automatic backups disabled.")

    st.divider()

    # Import section
    st.subheader("📥 Import Data")
    st.markdown("Restore data from previous exports or backups.")

    uploaded_file = st.file_uploader(
        "Choose a backup file",
        type=["json", "csv"],
        help="Upload a previously exported portfolio file or database backup",
    )

    if uploaded_file is not None:
        file_details = {
            "filename": uploaded_file.name,
            "filetype": uploaded_file.type,
            "filesize": uploaded_file.size,
        }
        st.write(file_details)

        if uploaded_file.type == "application/json":
            # Try to parse JSON
            try:
                data = json.loads(uploaded_file.getvalue().decode("utf-8"))
                st.success("✅ JSON file parsed successfully")

                if "backup_metadata" in data:
                    st.info("🗄️ Database backup file detected")
                    backup_info = data["backup_metadata"]
                    st.markdown(
                        f"**Created:** {backup_info.get('created_at', 'Unknown')}"
                    )
                    st.markdown(
                        f"**Type:** {backup_info.get('backup_type', 'Unknown')}"
                    )

                elif "export_metadata" in data:
                    st.info("📊 Portfolio export file detected")
                    export_info = data["export_metadata"]
                    st.markdown(
                        f"**Exported:** {export_info.get('export_date', 'Unknown')}"
                    )
                    st.markdown(f"**Source:** {export_info.get('source', 'Unknown')}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔍 Preview Import", type="secondary"):
                        st.json(data)

                with col2:
                    if st.button("📥 Import Data", type="primary"):
                        st.warning(
                            "⚠️ Import functionality requires authentication and admin privileges."
                        )
                        st.info(
                            "In production, this would restore the data to your database."
                        )

            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file")

        elif uploaded_file.type == "text/csv":
            try:
                df = pd.read_csv(uploaded_file)
                st.success("✅ CSV file parsed successfully")
                st.dataframe(df.head())

                if st.button("📥 Import CSV Data", type="primary"):
                    st.warning(
                        "⚠️ CSV import requires authentication and proper validation."
                    )
                    st.info(
                        "In production, this would validate and import the portfolio data."
                    )

            except Exception as e:
                st.error(f"❌ Error reading CSV: {e}")

    st.divider()

    # Security notes
    st.subheader("🔒 Security & Privacy")

    with st.expander("Data Security Information", expanded=False):
        st.markdown(
            """
        **Your Data Security:**
        - All exports are generated locally and not transmitted to external servers
        - Backup files contain sensitive financial information - store securely
        - Use strong encryption when storing backup files
        - Regularly test backup restoration procedures

        **Best Practices:**
        - Create backups before major changes
        - Store backups in multiple secure locations
        - Use encrypted storage for backup files
        - Regularly verify backup integrity
        - Keep export files confidential

        **Demo Note:**
        This is demonstration data. In production:
        - All data would be encrypted in transit and at rest
        - Access logs would track all export/import activities
        - Multi-factor authentication would be required for sensitive operations
        """
        )

    st.info(
        "📝 **Note**: This backup/export system uses demo data. In production, it would integrate with your live portfolio database and include additional security measures."
    )
