"""Integration tests for MCP server connecting to backend API."""

import asyncio
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx
import pytest

from backend.main import app as backend_app
from mcp_server.server import app as mcp_app


@pytest.fixture
def test_user_setup():
    """Set up test user and return authentication details."""
    backend_client = TestClient(backend_app)

    # Register a test user
    register_response = backend_client.post(
        "/api/v1/auth/register",
        json={
            "email": "mcptest@example.com",
            "username": "mcptest",
            "password": "mcppassword123",
            "full_name": "MCP Test User",
        },
    )

    # Login and get token
    login_response = backend_client.post(
        "/api/v1/auth/login",
        data={"username": "mcptest@example.com", "password": "mcppassword123"},
    )

    backend_token = login_response.json()["access_token"]
    backend_auth_headers = {"Authorization": f"Bearer {backend_token}"}

    return {
        "backend_client": backend_client,
        "backend_token": backend_token,
        "backend_auth_headers": backend_auth_headers,
    }


class TestMCPBackendIntegration:
    """Test MCP server integration with backend API."""

    @pytest.fixture(autouse=True)
    def setup_clients(self, test_user_setup):
        """Set up test clients."""
        self.backend_client = test_user_setup["backend_client"]
        self.backend_token = test_user_setup["backend_token"]
        self.backend_auth_headers = test_user_setup["backend_auth_headers"]

        self.mcp_client = TestClient(mcp_app)
        # Use the test MCP auth token from environment
        import os

        mcp_token = os.getenv("MCP_AUTH_TOKEN", "test-mcp-token")
        self.auth_headers = {"Authorization": f"Bearer {mcp_token}"}

    def test_mcp_tools_list_integration(self):
        """Test that MCP server can list available tools."""
        response = self.mcp_client.post("/tools/list", headers=self.auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data

        tool_names = [tool["name"] for tool in data["tools"]]
        expected_tools = [
            "get_positions",
            "get_portfolio_summary",
            "get_asset_price",
            "calculate_performance",
            "recommend_allocation",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @patch("mcp_server.tools.portfolio.PortfolioTools")
    def test_mcp_get_positions_integration(self, mock_portfolio_tools):
        """Test MCP get_positions tool with backend integration."""
        # Mock the portfolio tools to use our test backend
        mock_instance = mock_portfolio_tools.return_value
        mock_instance.execute_tool.return_value = asyncio.Future()
        mock_instance.execute_tool.return_value.set_result(
            [
                {
                    "type": "text",
                    "text": "**Current Portfolio Positions:**\n\n**No positions found in your portfolio.**\n\nTo get started, use the `add_position` tool to add your first investment!",
                }
            ]
        )

        # Test the MCP endpoint
        response = self.mcp_client.post(
            "/tools/execute/get_positions", json={}, headers=self.auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_mcp_backend_connectivity(self):
        """Test that MCP server can connect to backend health endpoint."""
        # Test direct backend connectivity
        backend_health = self.backend_client.get("/health")
        assert backend_health.status_code == 200

        # Test MCP server health
        mcp_health = self.mcp_client.get("/health")
        assert mcp_health.status_code == 200
        assert mcp_health.json()["status"] == "healthy"

    def test_mcp_asset_price_tool(self):
        """Test MCP asset price tool returns expected format."""
        response = self.mcp_client.post(
            "/tools/execute/get_asset_price",
            json={"ticker": "AAPL"},
            headers=self.auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["ticker"] == "AAPL"
        assert "price" in data["data"]

    def test_mcp_calculate_performance_tool(self):
        """Test MCP calculate performance tool."""
        response = self.mcp_client.post(
            "/tools/execute/calculate_performance",
            json={"period": "1M"},
            headers=self.auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "return" in data["data"]
        assert "value_change" in data["data"]

    def test_mcp_recommend_allocation_tool(self):
        """Test MCP allocation recommendation tool."""
        response = self.mcp_client.post(
            "/tools/execute/recommend_allocation",
            json={"risk_tolerance": "moderate"},
            headers=self.auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "recommended_allocation" in data["data"]

        allocation = data["data"]["recommended_allocation"]
        assert "stocks" in allocation
        assert "bonds" in allocation
        assert "cash" in allocation

        # Check that allocations add up to 100%
        total = allocation["stocks"] + allocation["bonds"] + allocation["cash"]
        assert total == 100

    def test_mcp_authorization_required(self):
        """Test that MCP tools require proper authorization."""
        # Test without authorization
        response = self.mcp_client.post("/tools/list")
        assert response.status_code == 401

        response = self.mcp_client.post("/tools/execute/get_positions", json={})
        assert response.status_code == 401

        # Test with invalid authorization
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = self.mcp_client.post("/tools/list", headers=invalid_headers)
        assert response.status_code == 401

    def test_mcp_tool_error_handling(self):
        """Test MCP server error handling for invalid tools."""
        response = self.mcp_client.post(
            "/tools/execute/nonexistent_tool", json={}, headers=self.auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestMCPPortfolioToolsIntegration:
    """Test MCP portfolio tools with async backend integration."""

    async def test_portfolio_tools_initialization(self):
        """Test that portfolio tools can be initialized."""
        from mcp_server.tools.portfolio import PortfolioTools

        tools = PortfolioTools(backend_url="http://localhost:8000")
        assert tools.backend_url == "http://localhost:8000"
        assert tools.http_client is not None

        # Test tool listing
        tool_list = tools.get_tools()
        assert len(tool_list) > 0

        tool_names = [tool.name for tool in tool_list]
        assert "get_positions" in tool_names
        assert "get_portfolio_summary" in tool_names
        assert "add_position" in tool_names

        await tools.close()

    async def test_portfolio_tools_error_handling(self):
        """Test portfolio tools error handling with invalid backend URL."""
        from mcp_server.tools.portfolio import PortfolioTools

        # Use invalid backend URL to test error handling
        tools = PortfolioTools(backend_url="http://invalid-url:9999")

        # This should handle connection errors gracefully
        result = await tools.execute_tool("get_positions", {})
        assert len(result) == 1
        # Should get an authentication error when connecting to invalid URL
        # Either connection error or authentication failure is acceptable
        assert (
            "Error connecting to backend" in result[0].text
            or "Authentication failed" in result[0].text
        )

        await tools.close()

    async def test_portfolio_tools_backend_connectivity(self):
        """Test portfolio tools can handle backend connection errors."""
        from mcp_server.tools.portfolio import PortfolioTools

        # Use invalid backend URL to test error handling
        tools = PortfolioTools(backend_url="http://invalid-url:9999")

        # This should handle connection errors gracefully
        result = await tools.execute_tool("get_positions", {})
        assert len(result) == 1
        # Should get a connection error when connecting to invalid URL
        assert (
            "Error connecting to backend" in result[0].text
            or "Authentication failed" in result[0].text
            or "Error retrieving positions" in result[0].text
        )

        await tools.close()


class TestMCPServerConfiguration:
    """Test MCP server configuration and setup."""

    def test_mcp_server_environment_variables(self):
        """Test MCP server respects environment variables."""

        # Test values in test environment
        from mcp_server.server import BACKEND_URL, MCP_AUTH_TOKEN, MCP_SERVER_PORT

        # Should use test environment values
        assert MCP_AUTH_TOKEN == "test-mcp-token"
        assert BACKEND_URL == "http://localhost:8000"
        assert MCP_SERVER_PORT == 8502

    def test_mcp_auth_token_verification(self):
        """Test MCP server auth token verification."""
        from mcp_server.server import verify_auth_token

        # Test valid token (using test environment token)
        assert verify_auth_token("Bearer test-mcp-token") is True

        # Test invalid tokens
        assert verify_auth_token("Bearer wrong-token") is False
        assert verify_auth_token("InvalidScheme test-mcp-token") is False
        assert verify_auth_token("Bearer") is False
        assert verify_auth_token("") is False
        # For None, we need to call it without parameter to use the default
        assert verify_auth_token() is False
        assert verify_auth_token("malformed") is False

    def test_mcp_server_endpoints_exist(self):
        """Test that all expected MCP server endpoints exist."""
        client = TestClient(mcp_app)

        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200

        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200

        # Test tools endpoints (should require auth)
        response = client.post("/tools/list")
        assert response.status_code == 401


@pytest.mark.integration
class TestMCPFullIntegration:
    """Full integration tests requiring running backend server."""

    @pytest.mark.skipif(
        "not config.getoption('--run-integration')",
        reason="requires --run-integration option and running backend",
    )
    @pytest.mark.asyncio
    async def test_full_mcp_backend_integration(self):
        """Test full MCP integration with running backend server."""
        from mcp_server.tools.portfolio import PortfolioTools

        # This test requires the backend to be running on localhost:8000
        tools = PortfolioTools(backend_url="http://localhost:8000")

        try:
            # Test basic connectivity
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health")
                assert response.status_code == 200

            # Test portfolio tools with real backend
            result = await tools.execute_tool("get_positions", {"include_cash": True})
            assert len(result) == 1
            # Should either show positions or "No positions found"
            assert (
                "Portfolio" in result[0].text or "No positions found" in result[0].text
            )

        except httpx.ConnectError:
            pytest.skip("Backend server not running on localhost:8000")
        finally:
            await tools.close()
