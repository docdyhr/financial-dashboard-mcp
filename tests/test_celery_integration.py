import pytest

from backend.tasks.market_data import fetch_market_data


@pytest.mark.skipif(
    "not config.getoption('--run-integration')",
    reason="need --run-integration option to run integration tests",
)
def test_fetch_market_data_task():
    # This test requires a running Celery worker and broker
    symbols = ["AAPL", "GOOG"]
    result = fetch_market_data.delay(symbols)
    output = result.get(timeout=20)
    assert output["status"] in ("success", "completed")  # nosec
    assert "results" in output  # nosec
