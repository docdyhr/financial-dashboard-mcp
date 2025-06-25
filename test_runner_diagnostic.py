import pytest


def test_runner():
    result = pytest.main(["-q", "--tb=short"])
    assert result == 0, "Tests did not pass"


if __name__ == "__main__":
    test_runner()
