"""Tests for MCP Server."""

from fastapi.testclient import TestClient

from mcp_server.server import app

client = TestClient(app)


def test_mcp_root_endpoint():
    """Test the MCP server root endpoint."""
    response = client.get("/")
    assert response.status_code == 200  # nosec
    data = response.json()
    assert "message" in data  # nosec
    assert data["status"] == "operational"  # nosec


def test_mcp_health_check():
    """Test the MCP server health check."""
    response = client.get("/health")
    assert response.status_code == 200  # nosec
    data = response.json()
    assert data["status"] == "healthy"  # nosec
    assert data["service"] == "mcp_server"  # nosec


def test_list_tools_unauthorized():
    """Test that listing tools requires authorization."""
    response = client.post("/tools/list")
    assert response.status_code == 401  # nosec


def test_list_tools_authorized():
    """Test listing tools with proper authorization."""
    headers = {"Authorization": "Bearer development-token"}
    response = client.post("/tools/list", headers=headers)
    assert response.status_code == 200  # nosec
    data = response.json()
    assert "tools" in data  # nosec
    assert len(data["tools"]) > 0  # nosec

    # Check that essential tools are present
    tool_names = [tool["name"] for tool in data["tools"]]
    assert "get_positions" in tool_names  # nosec
    assert "get_portfolio_summary" in tool_names  # nosec
    assert "get_asset_price" in tool_names  # nosec


def test_execute_tool_unauthorized():
    """Test that executing tools requires authorization."""
    response = client.post("/tools/execute/get_positions", json={})
    assert response.status_code == 401  # nosec


def test_execute_get_positions():
    """Test executing the get_positions tool."""
    headers = {"Authorization": "Bearer development-token"}
    response = client.post("/tools/execute/get_positions", json={}, headers=headers)
    assert response.status_code == 200  # nosec
    data = response.json()
    assert data["success"] is True  # nosec
    assert "data" in data  # nosec
    assert "positions" in data["data"]  # nosec


def test_execute_get_asset_price():
    """Test executing the get_asset_price tool."""
    headers = {"Authorization": "Bearer development-token"}
    payload = {"ticker": "AAPL"}
    response = client.post(
        "/tools/execute/get_asset_price", json=payload, headers=headers
    )
    assert response.status_code == 200  # nosec
    data = response.json()
    assert data["success"] is True  # nosec
    assert "data" in data  # nosec
    assert data["data"]["ticker"] == "AAPL"  # nosec


def test_execute_nonexistent_tool():
    """Test executing a non-existent tool."""
    headers = {"Authorization": "Bearer development-token"}
    response = client.post("/tools/execute/nonexistent_tool", json={}, headers=headers)
    assert response.status_code == 404  # nosec
