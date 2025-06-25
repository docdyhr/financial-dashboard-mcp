"""
Test file to validate VS Code testing integration and new testing tools.
"""

import os
from pathlib import Path
import sys

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestVSCodeIntegration:
    """Test class to validate VS Code testing features."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_basic_assertion(self):
        """Simple test to verify basic pytest functionality."""
        assert True
        assert 1 + 1 == 2
        assert "hello" in "hello world"

    @pytest.mark.unit
    @pytest.mark.fast
    def test_environment_setup(self):
        """Test that environment is properly configured."""
        # Check that we can import from our project
        try:
            from backend.core.config import get_settings

            assert get_settings() is not None
        except ImportError:
            pytest.skip("Backend not available - this is expected in some environments")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_python_path_configuration(self):
        """Test that Python path is correctly configured."""
        assert str(project_root) in sys.path or any(
            str(project_root) in path for path in sys.path
        )

    @pytest.mark.unit
    @pytest.mark.fast
    def test_environment_variables(self):
        """Test that environment variables are accessible."""
        # These should be available from .env file
        env_vars = ["DATABASE_URL", "SECRET_KEY", "ENVIRONMENT"]

        # At least some environment variables should be set
        available_vars = [var for var in env_vars if os.getenv(var)]
        assert (
            len(available_vars) > 0
        ), f"No environment variables found from {env_vars}"

    @pytest.mark.integration
    def test_file_structure(self):
        """Test that required project files exist."""
        required_files = [
            project_root / "pyproject.toml",
            project_root / "pytest.ini",
            project_root / ".env",
            project_root / "backend",
            project_root / "tests",
        ]

        for file_path in required_files:
            assert file_path.exists(), f"Required file/directory missing: {file_path}"


@pytest.mark.parametrize(
    "test_value,expected", [(1, 1), (2, 2), ("test", "test"), ([1, 2, 3], [1, 2, 3])]
)
@pytest.mark.unit
@pytest.mark.fast
def test_parametrized_values(test_value, expected):
    """Test parametrized test functionality for VS Code."""
    assert test_value == expected


class TestVSCodeFeatures:
    """Test class for new VS Code testing features."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_breakpoint_functionality(self):
        """Test that allows checking breakpoint functionality."""
        value = 42
        result = value * 2  # Set breakpoint here to test debugging
        assert result == 84

    @pytest.mark.unit
    @pytest.mark.fast
    def test_test_explorer_compatibility(self):
        """Test designed to verify Test Explorer compatibility."""
        # This test should appear in VS Code Test Explorer
        items = [1, 2, 3, 4, 5]
        assert len(items) == 5
        assert sum(items) == 15

    @pytest.mark.unit
    @pytest.mark.fast
    def test_inline_test_results(self):
        """Test for checking inline test result display."""
        # VS Code should show results inline
        calculations = {"add": 2 + 3, "multiply": 4 * 5, "divide": 10 / 2}

        assert calculations["add"] == 5
        assert calculations["multiply"] == 20
        assert calculations["divide"] == 5.0


if __name__ == "__main__":
    # Allow running this file directly for testing
    pytest.main([__file__, "-v"])
