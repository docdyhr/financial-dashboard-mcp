#!/usr/bin/env bash
# Pytest wrapper script that ensures we use the virtual environment's pytest.
# This script guarantees consistent behavior whether running from command line or VS Code.

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"

# Ensure we're in the project root
cd "${PROJECT_ROOT}"

# Check if virtual environment exists
if [[ ! -f ".venv/bin/pytest" ]]; then
    echo "Error: Virtual environment not found or pytest not installed."
    echo "Please run: python -m venv .venv && .venv/bin/pip install -e ."
    exit 1
fi

# Check if pytest is available in venv
if [[ ! -x ".venv/bin/pytest" ]]; then
    echo "Error: pytest not found in virtual environment."
    echo "Please run: .venv/bin/pip install pytest"
    exit 1
fi

# Set environment variables for consistent testing
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
export ENVIRONMENT="test"

# Run pytest with all passed arguments
exec .venv/bin/pytest "$@"
