#!/bin/bash
# Financial Dashboard MCP Server Startup Script
# This script ensures the MCP server starts with the correct Python environment

set -euo pipefail

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    log_error "Virtual environment not found at .venv"
    log_info "Please create a virtual environment first:"
    log_info "  python -m venv .venv"
    log_info "  source .venv/bin/activate"
    log_info "  pip install -e ."
    exit 1
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source .venv/bin/activate

# Verify Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
log_info "Using Python version: $PYTHON_VERSION"

# Check if required packages are installed
log_info "Checking dependencies..."
if ! python -c "import mcp" 2>/dev/null; then
    log_error "MCP package not found. Installing dependencies..."
    pip install -e .
fi

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    log_warning ".env file not found, copying from .env.example"
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        log_info "Copied .env.example to .env"
    else
        log_error ".env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Load environment variables
if [[ -f ".env" ]]; then
    log_info "Loading environment variables from .env"
    set -a
    source .env
    set +a
fi

# Set default environment variables if not set
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
export MCP_SERVER_HOST="${MCP_SERVER_HOST:-localhost}"
export MCP_SERVER_PORT="${MCP_SERVER_PORT:-8502}"
export BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

log_info "Starting Financial Dashboard MCP Server..."
log_info "Project root: $PROJECT_ROOT"
log_info "Python path: $PYTHONPATH"
log_info "Backend URL: $BACKEND_URL"
log_info "MCP Server: ${MCP_SERVER_HOST}:${MCP_SERVER_PORT}"

# Start the MCP server
log_info "Executing: python -m mcp_server.run"

# Trap signals for graceful shutdown
trap 'log_info "Received interrupt signal, shutting down MCP server..."; exit 0' INT TERM

# Execute the MCP server
exec python -m mcp_server.run "$@"
