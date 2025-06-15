#!/bin/bash
# Safe Claude Desktop Configuration Updater for Financial Dashboard
# This script safely adds or updates ONLY the financial-dashboard MCP server
# while preserving all other existing MCP servers in Claude Desktop

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

# Show help
show_help() {
    cat << EOF
Safe Claude Desktop Configuration Updater for Financial Dashboard

This script safely adds or updates ONLY the financial-dashboard MCP server
while preserving all your other existing MCP servers.

Usage: $0 [options]

Options:
    --help, -h      Show this help message
    --test          Test MCP server only (safe, no changes)
    --restore       Restore from backup
    --force         Update even if Claude Desktop is running
    --dry-run       Show what would be changed without making changes

Examples:
    $0              # Safely update configuration
    $0 --test       # Test MCP server functionality only
    $0 --dry-run    # Preview changes without applying them
    $0 --restore    # Restore previous configuration

Safety Features:
    ✅ Preserves all existing MCP servers
    ✅ Creates automatic backup before changes
    ✅ Validates configuration before applying
    ✅ Can restore from backup if needed
    ✅ Shows exactly what will be changed

EOF
}

# Preview changes
show_preview() {
    log_info "Preview of changes that would be made:"
    echo "========================================"
    echo "Action: Add or update 'financial-dashboard' MCP server"
    echo "Effect: Preserve all other existing MCP servers"
    echo "Backup: Automatic backup will be created"
    echo
    echo "New financial-dashboard configuration:"
    echo "  Command: $PROJECT_ROOT/.venv/bin/python"
    echo "  Args: -m mcp_server"
    echo "  Working Directory: $PROJECT_ROOT"
    echo "  Environment:"
    echo "    BACKEND_URL: http://localhost:8000"
    echo "    PYTHONPATH: $PROJECT_ROOT"
    echo "========================================"
}

# Main function
main() {
    local action="update"
    local force=false
    local dry_run=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --test)
                action="test"
                shift
                ;;
            --restore)
                action="restore"
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    echo "🛡️  Safe Claude Desktop Configuration Updater"
    echo "=============================================="
    echo "Purpose: Add/update ONLY financial-dashboard MCP server"
    echo "Safety:  Preserves all other existing MCP servers"
    echo

    case $action in
        test)
            log_info "Testing MCP server functionality (safe - no changes)..."
            cd "$PROJECT_ROOT"
            python scripts/add_to_claude_config.py --test
            ;;
        restore)
            log_warning "This will restore your Claude Desktop configuration from backup"
            echo
            read -p "Are you sure you want to restore from backup? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cd "$PROJECT_ROOT"
                python scripts/add_to_claude_config.py --restore
            else
                log_info "Restore cancelled"
            fi
            ;;
        update)
            if [[ "$dry_run" == "true" ]]; then
                show_preview
                echo
                log_info "This was a dry-run. No changes were made."
                log_info "Run without --dry-run to apply changes."
                exit 0
            fi

            # Check if Claude is running
            if check_claude_running && [[ "$force" != "true" ]]; then
                log_warning "Claude Desktop is currently running"
                log_warning "It's recommended to quit Claude Desktop first for a clean update"
                echo
                read -p "Do you want to continue anyway? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "Update cancelled. Quit Claude Desktop and try again, or use --force"
                    exit 1
                fi
            fi

            # Show what will be changed
            show_preview
            echo

            # Confirm action
            read -p "Proceed with safe configuration update? (Y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Nn]$ ]]; then
                log_info "Update cancelled by user"
                exit 0
            fi

            # Perform the safe update
            log_info "Performing safe configuration update..."
            cd "$PROJECT_ROOT"

            if python scripts/add_to_claude_config.py; then
                echo
                log_success "✅ Configuration safely updated!"
                echo
                log_warning "🔄 Next step: Restart Claude Desktop"
                echo
                log_info "Instructions:"
                log_info "1. Quit Claude Desktop completely (Cmd+Q)"
                log_info "2. Wait 5 seconds"
                log_info "3. Restart Claude Desktop"
                log_info "4. Test by asking: 'What financial tools do you have available?'"
                echo
                log_info "💡 If there are any issues, you can restore with:"
                log_info "   $0 --restore"
            else
                log_error "Configuration update failed"
                exit 1
            fi
            ;;
    esac
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${BLUE}[INFO]${NC} Operation cancelled by user"; exit 0' INT

# Check that Python script exists
if [[ ! -f "$PROJECT_ROOT/scripts/add_to_claude_config.py" ]]; then
    log_error "Required script not found: scripts/add_to_claude_config.py"
    log_error "Please ensure you're running this from the project root"
    exit 1
fi

# Run main function with all arguments
main "$@"
