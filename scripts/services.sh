#!/bin/bash
# Financial Dashboard Service Management Script
# Simplified management for all required services

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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
LOGS_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/.pids"

# Service port mapping (compatible with older bash)
# Service configurations
get_service_port() {
    case $1 in
        postgres) echo "5432" ;;
        redis) echo "6379" ;;
        backend) echo "8000" ;;
        flower) echo "5555" ;;
        frontend) echo "8501" ;;
        *) echo "" ;;
    esac
}

# Get Flower credentials from Settings or defaults
get_flower_credentials() {
    cd "$PROJECT_ROOT"
    local credentials=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from backend.config import get_settings
    settings = get_settings()
    print(f'{settings.flower_username}:{settings.flower_password}')
except:
    print('admin:admin')
")
    echo "$credentials"
}

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

log_service() {
    echo -e "${PURPLE}[SERVICE]${NC} $1"
}

# Utility functions
create_directories() {
    mkdir -p "$DATA_DIR/postgres" "$LOGS_DIR" "$PID_DIR"
}

load_environment() {
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        log_info "Loading environment variables from .env"
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    else
        log_warning ".env file not found, using defaults"
        export DATABASE_URL="postgresql://financial_user:dev_password@localhost:5432/financial_dashboard"
        export REDIS_URL="redis://localhost:6379/0"
        export CELERY_BROKER_URL="redis://localhost:6379/0"
        export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing=()

    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi

    # Check PostgreSQL
    if ! command -v initdb &> /dev/null && ! command -v pg_ctl &> /dev/null; then
        missing+=("postgresql (initdb/pg_ctl)")
    fi

    # Check Redis
    if ! command -v redis-server &> /dev/null; then
        missing+=("redis-server")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required dependencies:"
        for dep in "${missing[@]}"; do
            log_error "  - $dep"
        done
        log_error "Please install missing dependencies:"
        log_error "  macOS: brew install postgresql redis python"
        log_error "  Ubuntu: sudo apt-get install postgresql redis-server python3"
        return 1
    fi

    log_success "All prerequisites available"
    return 0
}

check_port() {
    local port=$1
    if [[ -n "$port" ]]; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

get_service_pid() {
    local service=$1
    local pid_file="$PID_DIR/$service.pid"

    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    return 1
}

kill_service() {
    local service=$1
    local timeout=${2:-30}

    if pid=$(get_service_pid "$service"); then
        log_info "Stopping $service (PID: $pid)"

        # Try graceful shutdown
        kill -TERM "$pid" 2>/dev/null || true

        # Wait for graceful shutdown
        for i in $(seq 1 $timeout); do
            if ! kill -0 "$pid" 2>/dev/null; then
                rm -f "$PID_DIR/$service.pid"
                return 0
            fi
            sleep 1
        done

        # Force kill if still running
        log_warning "Force killing $service"
        kill -KILL "$pid" 2>/dev/null || true
        rm -f "$PID_DIR/$service.pid"
    fi

    # Kill by port if applicable
    local port=$(get_service_port "$service")
    if [[ -n "$port" ]]; then
        local port_pids=$(lsof -ti:$port 2>/dev/null || true)
        if [[ -n "$port_pids" ]]; then
            log_info "Killing processes on port $port"
            echo "$port_pids" | xargs kill -TERM 2>/dev/null || true
            sleep 2
            echo "$port_pids" | xargs kill -KILL 2>/dev/null || true
        fi
    fi
}

setup_postgres() {
    local data_dir="$DATA_DIR/postgres"

    if [[ ! -f "$data_dir/PG_VERSION" ]]; then
        log_info "Initializing PostgreSQL database..."

        # Try different initdb commands
        if command -v initdb &> /dev/null; then
            initdb -D "$data_dir" -U financial_user --pwfile=<(echo "dev_password") --auth-local=md5 --auth-host=md5
        elif command -v pg_ctl &> /dev/null; then
            pg_ctl initdb -D "$data_dir" -o "-U financial_user --pwfile=<(echo 'dev_password')"
        else
            log_error "Neither initdb nor pg_ctl found"
            return 1
        fi

        # Create postgresql.conf with basic settings
        cat >> "$data_dir/postgresql.conf" << EOF

# Custom settings for development
port = 5432
listen_addresses = 'localhost'
max_connections = 100
shared_buffers = 128MB
dynamic_shared_memory_type = posix
log_statement = 'all'
log_destination = 'stderr'
logging_collector = on
log_directory = '$LOGS_DIR'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
EOF

        # Setup pg_hba.conf for local connections
        cat > "$data_dir/pg_hba.conf" << EOF
# Local connections
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
EOF

        log_success "PostgreSQL initialized"
    fi
}

start_postgres() {
    local data_dir="$DATA_DIR/postgres"

    if check_port 5432; then
        log_info "PostgreSQL already running"
        return 0
    fi

    setup_postgres || return 1

    log_service "Starting PostgreSQL..."

    if command -v pg_ctl &> /dev/null; then
        pg_ctl -D "$data_dir" -l "$LOGS_DIR/postgres.log" start
    elif command -v postgres &> /dev/null; then
        nohup postgres -D "$data_dir" > "$LOGS_DIR/postgres.log" 2>&1 &
        echo $! > "$PID_DIR/postgres.pid"
    else
        log_error "PostgreSQL server not found"
        return 1
    fi

    # Wait for PostgreSQL to start
    for i in {1..30}; do
        if check_port 5432; then
            log_success "PostgreSQL started on port 5432"

            # Create database and user if needed
            sleep 2
            if ! psql -h localhost -U financial_user -d postgres -c '\q' 2>/dev/null; then
                log_info "Setting up database and user..."
                psql -h localhost -U financial_user -d postgres -c "
                    CREATE DATABASE financial_dashboard;
                    GRANT ALL PRIVILEGES ON DATABASE financial_dashboard TO financial_user;
                " 2>/dev/null || true
            fi
            return 0
        fi
        sleep 1
    done

    log_error "PostgreSQL failed to start"
    return 1
}

start_redis() {
    if check_port 6379; then
        log_info "Redis already running"
        return 0
    fi

    log_service "Starting Redis..."

    nohup redis-server --port 6379 --save 60 1 --dir "$DATA_DIR" \
        --logfile "$LOGS_DIR/redis.log" --daemonize no > /dev/null 2>&1 &

    echo $! > "$PID_DIR/redis.pid"

    # Wait for Redis to start
    for i in {1..15}; do
        if redis-cli ping &>/dev/null; then
            log_success "Redis started on port 6379"
            return 0
        fi
        sleep 1
    done

    log_error "Redis failed to start"
    return 1
}

start_backend() {
    if check_port 8000; then
        log_info "Backend already running"
        return 0
    fi

    log_service "Starting FastAPI Backend..."

    cd "$PROJECT_ROOT"
    nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload \
        > "$LOGS_DIR/backend.log" 2>&1 &

    echo $! > "$PID_DIR/backend.pid"

    # Wait for backend to start
    for i in {1..60}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Backend started on port 8000"
            return 0
        fi
        sleep 1
    done

    log_error "Backend failed to start"
    return 1
}

start_celery() {
    if get_service_pid "celery" >/dev/null; then
        log_info "Celery worker already running"
        return 0
    fi

    log_service "Starting Celery Worker..."

    cd "$PROJECT_ROOT"
    nohup python3 -m celery -A backend.tasks worker --loglevel=info --concurrency=2 \
        > "$LOGS_DIR/celery.log" 2>&1 &

    echo $! > "$PID_DIR/celery.pid"

    sleep 3
    if get_service_pid "celery" >/dev/null; then
        log_success "Celery worker started"
        return 0
    else
        log_error "Celery worker failed to start"
        return 1
    fi
}

start_celery_beat() {
    if get_service_pid "celery-beat" >/dev/null; then
        log_info "Celery Beat already running"
        return 0
    fi

    log_service "Starting Celery Beat..."

    cd "$PROJECT_ROOT"
    # Remove old beat schedule if exists
    rm -f celerybeat-schedule.db

    nohup python3 -m celery -A backend.tasks beat --loglevel=info \
        > "$LOGS_DIR/celery-beat.log" 2>&1 &

    echo $! > "$PID_DIR/celery-beat.pid"

    sleep 3
    if get_service_pid "celery-beat" >/dev/null; then
        log_success "Celery Beat started"
        return 0
    else
        log_error "Celery Beat failed to start"
        return 1
    fi
}

start_flower() {
    if check_port 5555; then
        log_info "Flower already running"
        return 0
    fi

    log_service "Starting Flower..."

    cd "$PROJECT_ROOT"
    local flower_auth=$(get_flower_credentials)
    nohup python3 -m celery -A backend.tasks flower --port=5555 --basic_auth="$flower_auth" \
        > "$LOGS_DIR/flower.log" 2>&1 &

    echo $! > "$PID_DIR/flower.pid"

    # Wait for Flower to start
    for i in {1..30}; do
        if check_port 5555; then
            local flower_auth=$(get_flower_credentials)
            log_success "Flower started on port 5555 ($flower_auth)"
            return 0
        fi
        sleep 1
    done

    log_error "Flower failed to start"
    return 1
}

start_frontend() {
    if check_port 8501; then
        log_info "Frontend already running"
        return 0
    fi

    log_service "Starting Streamlit Frontend..."

    cd "$PROJECT_ROOT"
    nohup python3 -m streamlit run frontend/app.py --server.port 8501 --server.address localhost \
        > "$LOGS_DIR/frontend.log" 2>&1 &

    echo $! > "$PID_DIR/frontend.pid"

    # Wait for frontend to start
    for i in {1..60}; do
        if check_port 8501; then
            log_success "Frontend started on port 8501"
            return 0
        fi
        sleep 1
    done

    log_error "Frontend failed to start"
    return 1
}

start_mcp() {
    log_service "Preparing MCP Server (on-demand service)..."

    # Test MCP server can start properly
    cd "$PROJECT_ROOT"
    python3 "$PROJECT_ROOT/scripts/start_mcp_server.py" --test 2>/dev/null &
    local test_pid=$!

    sleep 2
    if kill -0 $test_pid 2>/dev/null; then
        kill $test_pid 2>/dev/null
        log_success "MCP Server ready (starts on Claude Desktop connection)"
        return 0
    else
        log_info "MCP Server configured (runs on-demand when Claude connects)"
        return 0
    fi
}

start_service() {
    local service=$1

    case $service in
        postgres) start_postgres ;;
        redis) start_redis ;;
        backend) start_backend ;;
        celery) start_celery ;;
        celery-beat) start_celery_beat ;;
        flower) start_flower ;;
        frontend) start_frontend ;;
        mcp) start_mcp ;;
        *) log_error "Unknown service: $service"; return 1 ;;
    esac
}

stop_service() {
    local service=$1

    case $service in
        postgres)
            if command -v pg_ctl &> /dev/null; then
                pg_ctl -D "$DATA_DIR/postgres" stop -m fast 2>/dev/null || true
            fi
            kill_service postgres
            ;;
        *)
            kill_service "$service"
            ;;
    esac

    log_success "$service stopped"
}

show_status() {
    log_info "Service Status:"
    echo "=================================="

    for service in postgres redis backend celery celery-beat flower frontend mcp; do
        local port=$(get_service_port "$service")
        local status="❌ STOPPED"

        if [[ "$service" == "mcp" ]]; then
            # MCP is on-demand service
            if [[ -f "$PROJECT_ROOT/scripts/start_mcp_server.py" ]]; then
                status="✅ READY (on-demand)"
            else
                status="❌ NOT CONFIGURED"
            fi
        elif [[ -n "$port" ]] && check_port "$port"; then
            status="✅ RUNNING (port $port)"
        elif get_service_pid "$service" >/dev/null; then
            status="✅ RUNNING"
        fi

        printf "%-12s %s\n" "$service:" "$status"
    done
}

show_urls() {
    echo
    log_info "Service URLs:"
    echo "=================================="
    echo "Frontend:     http://localhost:8501"
    echo "Backend API:  http://localhost:8000"
    echo "API Docs:     http://localhost:8000/docs"
    local flower_auth=$(get_flower_credentials)
    echo "Flower UI:    http://localhost:5555 ($flower_auth)"
    echo "PostgreSQL:   postgresql://financial_user:dev_password@localhost:5432/financial_dashboard"
    echo "Redis:        redis://localhost:6379/0"
    echo "MCP Server:   On-demand (starts when Claude Desktop connects)"
}

run_migrations() {
    log_info "Running database migrations..."
    cd "$PROJECT_ROOT"

    if ! python3 -m alembic upgrade head; then
        log_warning "Migrations failed, creating tables directly..."
        python3 -c "
from backend.database import engine, Base
from backend.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
    fi

    log_success "Database setup complete"
}

start_all() {
    log_info "Starting all Financial Dashboard services..."

    create_directories
    load_environment

    if ! check_prerequisites; then
        return 1
    fi

    # Start services in dependency order
    local services=(postgres redis backend celery celery-beat flower frontend mcp)
    local failed_services=()

    for service in "${services[@]}"; do
        if [[ "$service" == "mcp" ]]; then
            # MCP is on-demand, just verify it's ready
            start_service "$service"
        else
            if ! start_service "$service"; then
                failed_services+=("$service")
            fi
        fi
        sleep 1  # Brief pause between services
    done

    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "Failed to start services: ${failed_services[*]}"
        return 1
    fi

    # Run migrations after backend is up
    sleep 5
    run_migrations

    echo
    log_success "All services started successfully!"
    show_urls
}

stop_all() {
    log_info "Stopping all services..."

    # Stop in reverse order
    local services=(mcp frontend flower celery-beat celery backend redis postgres)

    for service in "${services[@]}"; do
        stop_service "$service"
    done

    # Clean up PID files
    rm -rf "$PID_DIR"

    log_success "All services stopped"
}

restart_all() {
    log_info "Restarting all services..."
    stop_all
    sleep 3
    start_all
}

health_check() {
    log_info "Running health checks..."

    local healthy=true

    # Check PostgreSQL
    if psql -h localhost -U financial_user -d financial_dashboard -c '\q' 2>/dev/null; then
        log_success "PostgreSQL: Healthy"
    else
        log_error "PostgreSQL: Unhealthy"
        healthy=false
    fi

    # Check Redis
    if redis-cli ping | grep -q PONG; then
        log_success "Redis: Healthy"
    else
        log_error "Redis: Unhealthy"
        healthy=false
    fi

    # Check Backend
    if curl -sf http://localhost:8000/health > /dev/null; then
        log_success "Backend: Healthy"
    else
        log_error "Backend: Unhealthy"
        healthy=false
    fi

    # Check Frontend
    if curl -sf http://localhost:8501/_stcore/health > /dev/null; then
        log_success "Frontend: Healthy"
    else
        log_error "Frontend: Unhealthy"
        healthy=false
    fi

    # Check Flower (with basic auth)
    local flower_auth=$(get_flower_credentials)
    if curl -sf -u "$flower_auth" http://localhost:5555 > /dev/null; then
        log_success "Flower: Healthy"
    else
        log_error "Flower: Unhealthy"
        healthy=false
    fi

    if $healthy; then
        log_success "All services are healthy!"
        return 0
    else
        log_error "Some services are unhealthy"
        return 1
    fi
}

show_logs() {
    local service=${1:-"all"}

    if [[ "$service" == "all" ]]; then
        log_info "Showing all service logs (last 50 lines each):"
        for log_file in "$LOGS_DIR"/*.log; do
            if [[ -f "$log_file" ]]; then
                echo -e "\n${CYAN}=== $(basename "$log_file") ===${NC}"
                tail -n 50 "$log_file"
            fi
        done
    else
        local log_file="$LOGS_DIR/$service.log"
        if [[ -f "$log_file" ]]; then
            log_info "Showing logs for $service:"
            tail -f "$log_file"
        else
            log_error "Log file not found: $log_file"
        fi
    fi
}

show_help() {
    cat << EOF
Financial Dashboard Service Manager

Usage: $0 <command> [options]

Commands:
    start [service]     Start service(s)
    stop [service]      Stop service(s)
    restart [service]   Restart service(s)
    status              Show service status
    health              Run health checks
    logs [service]      Show logs (tail -f for specific service)
    urls                Show service URLs
    migrate             Run database migrations
    help                Show this help

Services:
    all, postgres, redis, backend, celery, celery-beat, flower, frontend, mcp

Examples:
    $0 start all           # Start all services
    $0 stop postgres       # Stop PostgreSQL
    $0 restart backend     # Restart backend
    $0 logs celery        # Follow Celery logs
    $0 status             # Show status of all services
    $0 health             # Run health checks

EOF
}

# Main script logic
main() {
    local command=${1:-help}
    local service=${2:-all}

    case $command in
        start)
            if [[ "$service" == "all" ]]; then
                start_all
            else
                create_directories
                load_environment
                start_service "$service"
            fi
            ;;
        stop)
            if [[ "$service" == "all" ]]; then
                stop_all
            else
                stop_service "$service"
            fi
            ;;
        restart)
            if [[ "$service" == "all" ]]; then
                restart_all
            else
                stop_service "$service"
                sleep 2
                create_directories
                load_environment
                start_service "$service"
            fi
            ;;
        status)
            show_status
            ;;
        health)
            health_check
            ;;
        logs)
            show_logs "$service"
            ;;
        urls)
            show_urls
            ;;
        migrate)
            load_environment
            run_migrations
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

# Trap signals for graceful shutdown
trap 'log_info "Interrupted, stopping services..."; stop_all; exit 0' INT TERM

# Run main function
main "$@"
