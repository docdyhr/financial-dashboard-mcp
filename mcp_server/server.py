"""MCP Server for Financial Dashboard AI Integration."""

import logging
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app for MCP server
app = FastAPI(
    title="Financial Dashboard MCP Server",
    description="Model Context Protocol server for AI-powered financial insights",
    version="0.1.0",
)

# Configuration
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "development-token")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")  # nosec
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8502"))


def verify_auth_token(authorization: str = Header(None)) -> bool:
    """Verify the authentication token."""
    if not authorization:
        return False

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return False
        return token == MCP_AUTH_TOKEN
    except (ValueError, AttributeError):
        return False


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Financial Dashboard MCP Server",
        "version": "0.1.0",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "mcp_server",
            "version": "0.1.0",
        },
        status_code=200,
    )


@app.post("/tools/list")
async def list_tools(authorization: str = Header(None)) -> dict[str, Any]:
    """List available MCP tools."""
    if not verify_auth_token(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {
        "tools": [
            {
                "name": "get_positions",
                "description": "Retrieve current portfolio positions",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_portfolio_summary",
                "description": "Get portfolio overview and metrics",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_asset_price",
                "description": "Fetch current asset price",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Asset ticker symbol",
                        },
                    },
                    "required": ["ticker"],
                },
            },
            {
                "name": "calculate_performance",
                "description": "Calculate portfolio performance for a period",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "enum": ["1D", "1W", "1M", "3M", "6M", "1Y", "YTD"],
                            "description": "Time period for calculation",
                        },
                    },
                    "required": ["period"],
                },
            },
            {
                "name": "recommend_allocation",
                "description": "Get AI-powered allocation recommendations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "risk_tolerance": {
                            "type": "string",
                            "enum": ["conservative", "moderate", "aggressive"],
                            "description": "Investor risk tolerance",
                        },
                    },
                },
            },
        ],
    }


@app.post("/tools/execute/{tool_name}")
async def execute_tool(
    tool_name: str,
    request_body: dict[str, Any],
    authorization: str = Header(None),
) -> dict[str, Any]:
    """Execute an MCP tool."""
    if not verify_auth_token(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Tool implementations (placeholder - will connect to actual backend)
    if tool_name == "get_positions":
        return {
            "success": True,
            "data": {
                "positions": [
                    {
                        "ticker": "AAPL",
                        "name": "Apple Inc.",
                        "quantity": 100,
                        "current_price": 150.00,
                        "total_value": 15000.00,
                    },
                    {
                        "ticker": "GOOGL",
                        "name": "Alphabet Inc.",
                        "quantity": 50,
                        "current_price": 140.00,
                        "total_value": 7000.00,
                    },
                ],
                "total_value": 22000.00,
            },
        }

    if tool_name == "get_portfolio_summary":
        return {
            "success": True,
            "data": {
                "total_value": 22000.00,
                "daily_change": 350.00,
                "daily_change_percent": 1.62,
                "total_assets": 2,
                "cash_balance": 5000.00,
            },
        }

    if tool_name == "get_asset_price":
        ticker = request_body.get("ticker", "").upper()
        # Placeholder prices
        prices = {
            "AAPL": 150.00,
            "GOOGL": 140.00,
            "MSFT": 380.00,
            "AMZN": 170.00,
        }

        if ticker in prices:
            return {
                "success": True,
                "data": {
                    "ticker": ticker,
                    "price": prices[ticker],
                    "currency": "USD",
                },
            }
        return {
            "success": False,
            "error": f"Price not found for ticker: {ticker}",
        }

    if tool_name == "calculate_performance":
        period = request_body.get("period", "1M")
        # Placeholder performance data
        performance_data = {
            "1D": {"return": 1.62, "value_change": 350.00},
            "1W": {"return": 3.45, "value_change": 735.00},
            "1M": {"return": 5.23, "value_change": 1095.00},
            "YTD": {"return": 12.87, "value_change": 2435.00},
        }

        return {
            "success": True,
            "data": performance_data.get(
                period,
                {"return": 0.0, "value_change": 0.0},
            ),
        }

    if tool_name == "recommend_allocation":
        risk_tolerance = request_body.get("risk_tolerance", "moderate")
        allocations = {
            "conservative": {
                "stocks": 30,
                "bonds": 60,
                "cash": 10,
            },
            "moderate": {
                "stocks": 60,
                "bonds": 30,
                "cash": 10,
            },
            "aggressive": {
                "stocks": 80,
                "bonds": 15,
                "cash": 5,
            },
        }

        return {
            "success": True,
            "data": {
                "recommended_allocation": allocations.get(risk_tolerance),
                "risk_profile": risk_tolerance,
            },
        }

    raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")


if __name__ == "__main__":
    logger.info(f"Starting MCP Server on {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    uvicorn.run(
        "mcp_server.server:app",
        host=MCP_SERVER_HOST,
        port=MCP_SERVER_PORT,
        reload=True,
    )
