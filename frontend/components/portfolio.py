"""Portfolio overview components for the Financial Dashboard.

This module provides a simplified interface to portfolio functionality,
importing from specialized sub-modules for better organization.
"""

# Import all functions from sub-modules for backward compatibility
from .portfolio_charts import asset_allocation_chart, portfolio_value_chart
from .portfolio_data import (
    create_portfolio_snapshot,
    get_performance_data,
    get_portfolio_data,
    get_positions_data,
    refresh_market_data,
    safe_float,
)
from .portfolio_tables import (
    delete_positions,
    edit_position,
    holdings_table,
    view_position_details,
    view_position_transactions,
)
from .portfolio_utils import (
    get_ticker_suggestions,
    safe_format_currency,
    validate_ticker_input,
)
from .portfolio_widgets import (
    performance_metrics_widget,
    portfolio_overview_widget,
    portfolio_summary_metrics,
    refresh_data_button,
)

# Export all functions for backward compatibility
__all__ = [
    # Data functions
    "safe_float",
    "get_portfolio_data",
    "get_positions_data",
    "get_performance_data",
    "refresh_market_data",
    "create_portfolio_snapshot",
    # Widget functions
    "portfolio_overview_widget",
    "performance_metrics_widget",
    "portfolio_summary_metrics",
    "refresh_data_button",
    # Chart functions
    "asset_allocation_chart",
    "portfolio_value_chart",
    # Table functions
    "holdings_table",
    "delete_positions",
    "view_position_details",
    "edit_position",
    "view_position_transactions",
    # Utility functions
    "safe_format_currency",
    "validate_ticker_input",
    "get_ticker_suggestions",
]
