import requests


def test_mcp_server_health():
    response = requests.get("http://localhost:8000/health", timeout=10)
    assert response.status_code == 200  # nosec
    assert response.json().get("status") in ("ok", "healthy")  # nosec
    # Add more MCP server integration tests as needed
