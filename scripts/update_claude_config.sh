#!/bin/bash
# Automated Claude Desktop Configuration Updater for Financial Dashboard MCP Server
# This script updates Claude Desktop's configuration to use the correct MCP server setup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
BACKUP_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json.backup"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Claude Desktop is running
check_claude_running() {
    if pgrep -f "Claude" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Create backup of existing configuration
backup_config() {
    if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
        log_info "Creating backup of existing configuration..."
        cp "$CLAUDE_CONFIG_FILE" "$BACKUP_FILE"
        log_success "Backup created at: $BACKUP_FILE"

        # Show what MCP servers currently exist
        log_info "Current MCP servers in configuration:"
        python3 -c "
import json
try:
    with open('$CLAUDE_CONFIG_FILE', 'r') as f:
        config = json.load(f)
    servers = config.get('mcpServers', {})
    if servers:
        for server_name in servers.keys():
            print(f'  • {server_name}')
    else:
        print('  • No MCP servers configured')
except:
    print('  • Unable to parse configuration')
"
    else
        log_info "No existing configuration found - will create new one"
    fi
}

# Verify project paths exist
verify_paths() {
    log_info "Verifying project paths..."

    if [[ ! -d "$PROJECT_ROOT" ]]; then
        log_error "Project root not found: $PROJECT_ROOT"
        return 1
    fi

    if [[ ! -f "$PROJECT_ROOT/.venv/bin/python" ]]; then
        log_error "Python virtual environment not found: $PROJECT_ROOT/.venv/bin/python"
        log_error "Please ensure the virtual environment is set up"
        return 1
    fi

    if [[ ! -f "$PROJECT_ROOT/mcp_server/__main__.py" ]]; then
        log_error "MCP server module not found: $PROJECT_ROOT/mcp_server/__main__.py"
        return 1
    fi

    log_success "All project paths verified"
    return 0
}

# Test MCP server functionality
test_mcp_server() {
    log_info "Testing MCP server functionality..."

    cd "$PROJECT_ROOT"
    if .venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from mcp_server.main import FinancialDashboardMCP
mcp = FinancialDashboardMCP()
print(f'✅ MCP server loaded {len(mcp.all_tools)} tools')
" 2>/dev/null; then
        log_success "MCP server test passed"
        return 0
    else
        log_error "MCP server test failed"
        return 1
    fi
}

# Generate Claude Desktop configuration
generate_config() {
    log_info "Updating Claude Desktop configuration..."

    # Ensure Claude config directory exists
    mkdir -p "$CLAUDE_CONFIG_DIR"

    # Create or update the configuration preserving existing servers
    if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
        # Configuration exists, update it
        log_info "Existing configuration found, preserving other MCP servers..."

        # Use Python to safely update the JSON
        python3 << EOF
import json
import sys

config_file = "$CLAUDE_CONFIG_FILE"
project_root = "$PROJECT_ROOT"

try:
    # Load existing configuration
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Ensure mcpServers section exists
    if 'mcpServers' not in config:
        config['mcpServers'] = {}

    # Add or update financial-dashboard server
    config['mcpServers']['financial-dashboard'] = {
        "command": f"{project_root}/.venv/bin/python",
        "args": ["-m", "mcp_server"],
        "cwd": project_root,
        "env": {
            "BACKEND_URL": "http://localhost:8000",
            "PYTHONPATH": project_root
        }
    }

    # Write back the configuration
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print("Configuration updated successfully")

except Exception as e:
    print(f"Error updating configuration: {e}")
    sys.exit(1)
EOF
    else
        # No existing configuration, create new one
        log_info "No existing configuration found, creating new one..."
        cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "$PROJECT_ROOT/.venv/bin/python",
      "args": ["-m", "mcp_server"],
      "cwd": "$PROJECT_ROOT",
      "env": {
        "BACKEND_URL": "http://localhost:8000",
        "PYTHONPATH": "$PROJECT_ROOT"
      }
    }
  }
}
EOF
    fi

    log_success "Configuration written to: $CLAUDE_CONFIG_FILE"
}

# Validate JSON configuration
validate_config() {
    log_info "Validating JSON configuration..."

    if python3 -m json.tool "$CLAUDE_CONFIG_FILE" > /dev/null 2>&1; then
        log_success "Configuration JSON is valid"
        return 0
    else
        log_error "Configuration JSON is invalid"
        return 1
    fi
}

# Display configuration
show_config() {
    log_info "Current Claude Desktop configuration:"
    echo "=================================="
    cat "$CLAUDE_CONFIG_FILE"
    echo "=================================="
}

# Warn about Claude Desktop restart
warn_restart() {
    echo
    log_warning "IMPORTANT: You must restart Claude Desktop for changes to take effect"
    echo
    log_info "Steps to restart Claude Desktop:"
    log_info "1. Quit Claude Desktop completely (Cmd+Q)"
    log_info "2. Wait 5 seconds"
    log_info "3. Restart Claude Desktop"
    log_info "4. Test by asking: 'What financial tools do you have available?'"
    echo
}

# Check Claude Desktop logs
check_logs() {
    local log_file="$HOME/Library/Logs/Claude/mcp-server-financial-dashboard.log"

    if [[ -f "$log_file" ]]; then
        log_info "Recent Claude Desktop MCP logs:"
        echo "=================================="
        tail -10 "$log_file" 2>/dev/null || echo "No logs available"
        echo "=================================="
    else
        log_info "No Claude Desktop logs found yet"
    fi
}

# Test the configuration works
test_configuration() {
    log_info "Testing the exact command Claude Desktop will use..."

    cd "$PROJECT_ROOT"

    # Test the command that will be executed
    if timeout 5s "$PROJECT_ROOT/.venv/bin/python" -c "
import sys
sys.path.insert(0, '.')
from mcp_server.main import FinancialDashboardMCP
mcp = FinancialDashboardMCP()
print(f'✅ Claude Desktop command test: {len(mcp.all_tools)} tools available')
" 2>/dev/null; then
        log_success "Configuration command test passed"
        return 0
    else
        log_warning "Configuration command test had issues (may be normal)"
        return 0  # Don't fail on this
    fi
}

# Restore backup configuration
restore_backup() {
    if [[ -f "$BACKUP_FILE" ]]; then
        log_info "Restoring backup configuration..."
        cp "$BACKUP_FILE" "$CLAUDE_CONFIG_FILE"
        log_success "Backup restored"
    else
        log_error "No backup file found to restore"
    fi
}

# Show help
show_help() {
    cat << EOF
Claude Desktop Configuration Updater for Financial Dashboard

Usage: $0 [options]

Options:
    --help, -h      Show this help message
    --backup        Create backup only
    --restore       Restore from backup
    --test          Test MCP server only
    --show          Show current configuration
    --force         Update even if Claude is running

Examples:
    $0              # Update Claude Desktop configuration
    $0 --test       # Test MCP server functionality
    $0 --show       # Show current configuration
    $0 --restore    # Restore backup configuration

EOF
}

# Main function
main() {
    local action="update"
    local force=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --backup)
                action="backup"
                shift
                ;;
            --restore)
                action="restore"
                shift
                ;;
            --test)
                action="test"
                shift
                ;;
            --show)
                action="show"
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    log_info "Financial Dashboard - Claude Desktop Configuration Updater"
    echo "============================================================"

    case $action in
        backup)
            backup_config
            ;;
        restore)
            restore_backup
            ;;
        test)
            if verify_paths && test_mcp_server; then
                log_success "MCP server is ready for Claude Desktop"
            else
                log_error "MCP server has issues"
                exit 1
            fi
            ;;
        show)
            if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
                show_config
            else
                log_info "No Claude Desktop configuration found"
            fi
            ;;
        update)
            # Check if Claude is running
            if check_claude_running && [[ "$force" != "true" ]]; then
                log_warning "Claude Desktop is currently running"
                log_warning "Please quit Claude Desktop first, or use --force to continue"
                echo
                log_info "To quit Claude Desktop: Press Cmd+Q in Claude Desktop"
                echo
                exit 1
            fi

            # Verify everything is ready
            if ! verify_paths; then
                exit 1
            fi

            if ! test_mcp_server; then
                log_error "MCP server test failed. Please fix issues before updating Claude Desktop config."
                exit 1
            fi

            # Create backup
            backup_config

            # Generate new configuration
            generate_config

            # Validate the configuration
            if ! validate_config; then
                log_error "Generated configuration is invalid. Restoring backup..."
                restore_backup
                exit 1
            fi

            # Test the configuration
            test_configuration

            # Show the new configuration
            show_config

            # Show restart instructions
            warn_restart

            # Show logs for reference
            check_logs

            log_success "Claude Desktop configuration updated successfully!"
            echo
            log_info "Configuration summary:"
            python3 -c "
import json
try:
    with open('$CLAUDE_CONFIG_FILE', 'r') as f:
        config = json.load(f)
    servers = config.get('mcpServers', {})
    print(f'  • Total MCP servers: {len(servers)}')
    for server_name in servers.keys():
        status = '✅ Updated' if server_name == 'financial-dashboard' else '✅ Preserved'
        print(f'  • {server_name}: {status}')
except:
    print('  • Unable to parse configuration')
"
            echo
            log_info "Next steps:"
            log_info "1. Restart Claude Desktop (Cmd+Q, then reopen)"
            log_info "2. Ask Claude: 'What financial tools do you have available?'"
            log_info "3. Start using your AI-powered financial dashboard!"
            ;;
    esac
}

# Run main function with all arguments
main "$@"
