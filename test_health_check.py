#!/usr/bin/env python3
"""Test Health Check Script
Verifies that all tests are passing and provides a summary of the test suite status.
"""

from pathlib import Path
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print("=" * 60)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,  # 5 minutes timeout
        )

        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Command timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Main test health check."""
    print("Financial Dashboard MCP - Test Health Check")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("pytest.ini").exists():
        print(
            "Error: Not in the project root directory. Please run from the project root."
        )
        sys.exit(1)

    # Check if virtual environment is activated
    if not Path(".venv/bin/pytest").exists():
        print(
            "Error: Virtual environment not found. Please activate the virtual environment."
        )
        sys.exit(1)

    tests_to_run = [
        {
            "cmd": ".venv/bin/pytest tests/test_basic.py -v",
            "description": "Basic functionality tests",
        },
        {"cmd": ".venv/bin/pytest tests/unit/ -v", "description": "Unit tests"},
        {"cmd": ".venv/bin/pytest tests/api/ -v", "description": "API tests"},
        {
            "cmd": ".venv/bin/pytest tests/integration/ -v",
            "description": "Integration tests",
        },
        {
            "cmd": ".venv/bin/pytest tests/test_mcp_backend_integration.py -v",
            "description": "MCP Backend Integration tests (recently fixed)",
        },
        {
            "cmd": ".venv/bin/pytest tests/ -x --disable-warnings",
            "description": "Full test suite (fail-fast)",
        },
    ]

    results = []

    for test in tests_to_run:
        success = run_command(test["cmd"], test["description"])
        results.append({"description": test["description"], "success": success})

    # Summary
    print("\n" + "=" * 60)
    print("TEST HEALTH CHECK SUMMARY")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests

    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status} - {result['description']}")

    print(f"\nOverall Status: {passed_tests}/{total_tests} test categories passed")

    if failed_tests == 0:
        print("🎉 All test categories are passing!")
        return 0
    print(f"⚠️  {failed_tests} test categories failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
