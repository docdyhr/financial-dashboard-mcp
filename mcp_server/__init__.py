"""Financial Dashboard MCP Server Package.

This package provides MCP (Model Context Protocol) server functionality
for AI-powered financial analysis and portfolio management.
"""

__version__ = "1.3.0"
__author__ = "Financial Dashboard Team"
__description__ = "MCP Server for Financial Dashboard AI Integration"

from .main import FinancialDashboardMCP, main

__all__ = ["FinancialDashboardMCP", "main"]
