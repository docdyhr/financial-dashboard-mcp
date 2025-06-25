"""Test to verify VS Code testing integration is working."""

import os

import pytest


def test_vs_code_testing_integration():
    """Test that VS Code testing integration is working."""
    assert True, "VS Code testing integration should work"


def test_environment_variables_loaded():
    """Test that environment variables are properly loaded."""
    # Check that our test environment variables are set
    assert os.environ.get("TESTING") == "true"
    assert os.environ.get("ENVIRONMENT") == "test"


@pytest.mark.fast
def test_fast_marker_works():
    """Test that pytest markers are working."""
    assert True, "Fast marker should work in VS Code"


class TestVSCodeTesting:
    """Test class for VS Code testing."""

    def test_class_based_test(self):
        """Test that class-based tests work in VS Code."""
        assert 1 + 1 == 2

    def test_backend_configuration_loads(self):
        """Test that backend configuration loads without errors."""
        from backend.config import get_settings

        settings = get_settings()
        assert settings.environment == "test"
        assert settings.debug is True
