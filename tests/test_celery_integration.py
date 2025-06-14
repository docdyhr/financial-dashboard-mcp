from backend.tasks.market_data import fetch_market_data


def test_fetch_market_data_task():
    # This test requires a running Celery worker and broker
    symbols = ["AAPL", "GOOG"]
    result = fetch_market_data.delay(symbols)
    output = result.get(timeout=20)
    assert output["status"] in ("success", "completed")  # nosec
    assert "results" in output  # nosec
