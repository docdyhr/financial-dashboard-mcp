from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200  # nosec
    assert "Welcome" in response.text  # nosec


# Add more endpoint tests as needed
