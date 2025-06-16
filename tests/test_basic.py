"""Basic tests to verify testing setup works."""

import pytest


def test_basic_math() -> None:
    """Test basic arithmetic to verify pytest is working."""
    assert 1 + 1 == 2  # nosec
    assert 2 * 3 == 6  # nosec
    assert 10 / 2 == 5.0  # nosec


def test_string_operations() -> None:
    """Test string operations."""
    test_string = "Financial Dashboard"
    assert len(test_string) > 0  # nosec
    assert "Dashboard" in test_string  # nosec
    assert test_string.lower() == "financial dashboard"  # nosec


@pytest.mark.unit()
def test_list_operations() -> None:
    """Test list operations with unit marker."""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5  # nosec
    assert sum(test_list) == 15  # nosec
    assert max(test_list) == 5  # nosec


@pytest.mark.financial()
def test_financial_calculations() -> None:
    """Test basic financial calculations."""
    principal = 1000.0
    rate = 0.05
    time = 2

    # Simple interest calculation
    simple_interest = principal * rate * time
    assert simple_interest == 100.0  # nosec

    # Compound interest calculation
    compound_amount = principal * (1 + rate) ** time
    assert abs(compound_amount - 1102.5) < 0.01  # nosec


@pytest.mark.slow()
def test_slow_operation() -> None:
    """Test marked as slow."""
    import time

    start_time = time.time()
    time.sleep(0.1)  # Simulate slow operation
    end_time = time.time()
    assert (end_time - start_time) >= 0.1  # nosec


def test_environment_variable() -> None:
    """Test environment variable access."""
    import os

    # Should be set by conftest.py
    assert os.environ.get("ENVIRONMENT") == "test"  # nosec
