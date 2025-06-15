#!/bin/bash
# Monitor Claude Desktop MCP Server Logs
# This script monitors the Claude Desktop logs for the Financial Dashboard MCP server
# and provides real-time feedback on connection status

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
LOG_FILE="$HOME/Library/Logs/Claude/mcp-server-financial-dashboard.log"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

log_highlight() {
    echo -e "${PURPLE}[HIGHLIGHT]${NC} $1"
}

# Check if log file exists
check_log_file() {
    if [[ ! -f "$LOG_FILE" ]]; then
        log_warning "Log file not found: $LOG_FILE"
        log_info "This may be normal if Claude Desktop hasn't been restarted yet"
        return 1
    fi
    return 0
}

# Show recent logs
show_recent_logs() {
    if check_log_file; then
        log_info "Recent Claude Desktop MCP logs (last 20 lines):"
        echo "=================================================================="
        tail -20 "$LOG_FILE" | while IFS= read -r line; do
            if [[ "$line" == *"error"* ]] || [[ "$line" == *"ERROR"* ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ "$line" == *"Loaded"* ]] || [[ "$line" == *"tools"* ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ "$line" == *"Starting"* ]] || [[ "$line" == *"Initializing"* ]]; then
                echo -e "${BLUE}$line${NC}"
            else
                echo "$line"
            fi
        done
        echo "=================================================================="
    fi
}

# Monitor logs in real-time
monitor_logs() {
    if ! check_log_file; then
        log_info "Waiting for log file to be created..."
        while [[ ! -f "$LOG_FILE" ]]; do
            sleep 2
            echo -n "."
        done
        echo
        log_success "Log file created!"
    fi

    log_info "Monitoring Claude Desktop MCP logs in real-time..."
    log_info "Press Ctrl+C to stop monitoring"
    echo "=================================================================="

    tail -f "$LOG_FILE" | while IFS= read -r line; do
        timestamp=$(echo "$line" | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}T[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}' || echo "")

        if [[ "$line" == *"spawn python ENOENT"* ]]; then
            log_error "❌ ENOENT Error detected - Python path issue"
        elif [[ "$line" == *"error"* ]] || [[ "$line" == *"ERROR"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ "$line" == *"Initializing server"* ]]; then
            log_highlight "🚀 MCP Server initializing..."
        elif [[ "$line" == *"Loaded"* ]] && [[ "$line" == *"tools"* ]]; then
            tool_count=$(echo "$line" | grep -o '[0-9]\+ tools' || echo "tools")
            log_success "✅ MCP Server loaded $tool_count successfully!"
        elif [[ "$line" == *"Starting financial-dashboard-mcp"* ]]; then
            log_success "✅ Financial Dashboard MCP Server started!"
        elif [[ "$line" == *"Server transport closed unexpectedly"* ]]; then
            log_warning "⚠️ Server transport closed unexpectedly"
        elif [[ "$line" == *"Starting"* ]] || [[ "$line" == *"Initializing"* ]]; then
            echo -e "${BLUE}$line${NC}"
        elif [[ "$line" == *"info"* ]]; then
            echo -e "${CYAN}$line${NC}"
        else
            echo "$line"
        fi
    done
}

# Analyze logs for common issues
analyze_logs() {
    if ! check_log_file; then
        return 1
    fi

    log_info "Analyzing logs for common issues..."
    echo "=================================================================="

    local enoent_count=$(grep -c "ENOENT" "$LOG_FILE" 2>/dev/null || echo "0")
    local success_count=$(grep -c "Loaded.*tools" "$LOG_FILE" 2>/dev/null || echo "0")
    local init_count=$(grep -c "Initializing server" "$LOG_FILE" 2>/dev/null || echo "0")

    echo "📊 Log Analysis Results:"
    echo "  • Initialization attempts: $init_count"
    echo "  • Successful tool loads: $success_count"
    echo "  • ENOENT errors: $enoent_count"
    echo

    if [[ "$enoent_count" -gt 0 ]] && [[ "$success_count" -eq 0 ]]; then
        log_error "❌ Configuration Issue Detected"
        echo "  Problem: Python path errors (ENOENT)"
        echo "  Solution: Update Claude Desktop configuration"
        echo "  Command: ./scripts/update_claude_config.sh --force"
    elif [[ "$success_count" -gt 0 ]]; then
        log_success "✅ MCP Server Working Correctly"
        echo "  Status: Tools loading successfully"
        echo "  Last success: $(grep "Loaded.*tools" "$LOG_FILE" | tail -1 | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}T[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}' || echo "Unknown")"
    elif [[ "$init_count" -gt 0 ]]; then
        log_warning "⚠️ Partial Success"
        echo "  Status: Server initializing but not completing"
        echo "  Check: Ensure all services are running"
    else
        log_info "ℹ️ No Recent Activity"
        echo "  Status: No recent MCP server activity detected"
        echo "  Action: Try restarting Claude Desktop"
    fi

    echo "=================================================================="
}

# Check if services are running
check_services() {
    log_info "Checking Financial Dashboard services..."

    if [[ -f "$PROJECT_ROOT/scripts/services.sh" ]]; then
        cd "$PROJECT_ROOT"
        ./scripts/services.sh status
    else
        log_warning "Service management script not found"
    fi
}

# Clear logs
clear_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        log_info "Clearing Claude Desktop MCP logs..."
        > "$LOG_FILE"
        log_success "Logs cleared"
    else
        log_info "No log file to clear"
    fi
}

# Show help
show_help() {
    cat << EOF
Claude Desktop MCP Server Log Monitor

Usage: $0 [command]

Commands:
    monitor     Monitor logs in real-time (default)
    recent      Show recent log entries
    analyze     Analyze logs for common issues
    clear       Clear the log file
    services    Check service status
    help        Show this help

Examples:
    $0                  # Monitor logs in real-time
    $0 recent          # Show recent entries
    $0 analyze         # Analyze for issues

Log file location: $LOG_FILE

EOF
}

# Test Claude Desktop integration
test_integration() {
    log_info "Testing Claude Desktop MCP integration..."
    echo "=================================================================="

    # Check if Claude is running
    if pgrep -f "Claude" > /dev/null; then
        log_success "✅ Claude Desktop is running"
    else
        log_warning "⚠️ Claude Desktop is not running"
        log_info "Please start Claude Desktop to test MCP integration"
        return 1
    fi

    # Check configuration
    local config_file="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    if [[ -f "$config_file" ]]; then
        log_success "✅ Claude Desktop configuration found"
        if grep -q "financial-dashboard" "$config_file"; then
            log_success "✅ Financial Dashboard MCP server configured"
        else
            log_warning "⚠️ Financial Dashboard not found in configuration"
        fi
    else
        log_error "❌ Claude Desktop configuration not found"
        log_info "Run: ./scripts/update_claude_config.sh"
        return 1
    fi

    # Check services
    check_services

    # Show recent logs
    show_recent_logs

    echo "=================================================================="
    log_info "💡 To test the integration:"
    log_info "1. Open Claude Desktop"
    log_info "2. Ask: 'What financial tools do you have available?'"
    log_info "3. You should see 13 financial dashboard tools listed"
}

# Main function
main() {
    local command=${1:-monitor}

    case $command in
        monitor)
            show_recent_logs
            echo
            monitor_logs
            ;;
        recent)
            show_recent_logs
            ;;
        analyze)
            analyze_logs
            ;;
        clear)
            clear_logs
            ;;
        services)
            check_services
            ;;
        test)
            test_integration
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${BLUE}[INFO]${NC} Monitoring stopped."; exit 0' INT

# Run main function
main "$@"
