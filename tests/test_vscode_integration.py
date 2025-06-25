"""
Simple test file to verify VS Code testing integration.
This file should appear in the VS Code TESTING panel.
"""

import pytest


def test_simple_assertion():
    """Simple test that should always pass."""
    assert 1 + 1 == 2


def test_string_operations():
    """Test basic string operations."""
    text = "Hello, World!"
    assert len(text) == 13
    assert text.upper() == "HELLO, WORLD!"
    assert text.lower() == "hello, world!"


def test_list_operations():
    """Test basic list operations."""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert sum(numbers) == 15
    assert max(numbers) == 5
    assert min(numbers) == 1


class TestBasicMath:
    """Test class for basic mathematical operations."""

    def test_addition(self):
        """Test addition operation."""
        assert 2 + 3 == 5
        assert -1 + 1 == 0
        assert 0 + 0 == 0

    def test_multiplication(self):
        """Test multiplication operation."""
        assert 2 * 3 == 6
        assert 5 * 0 == 0
        assert -2 * 3 == -6

    def test_division(self):
        """Test division operation."""
        assert 10 / 2 == 5
        assert 9 / 3 == 3

    def test_division_by_zero(self):
        """Test that division by zero raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            1 / 0


@pytest.mark.parametrize(
    "input,expected",
    [
        (1, 1),
        (2, 4),
        (3, 9),
        (4, 16),
        (-2, 4),
    ],
)
def test_square_function(input, expected):
    """Test square function with parametrized inputs."""

    def square(x):
        return x * x

    assert square(input) == expected


def test_environment_check():
    """Test that we can access environment and imports."""
    import os
    import sys

    # Basic environment checks
    assert os.path.exists(".")
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 11


if __name__ == "__main__":
    pytest.main([__file__])
