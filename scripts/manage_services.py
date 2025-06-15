#!/usr/bin/env python3
"""
Financial Dashboard Service Manager

This script provides comprehensive management for all services required by the
Financial Dashboard application, including PostgreSQL, Redis, Celery, Flower,
FastAPI backend, Streamlit frontend, and MCP server.

Usage:
    python scripts/manage_services.py --help
    python scripts/manage_services.py start --all
    python scripts/manage_services.py stop --all
    python scripts/manage_services.py status
    python scripts/manage_services.py restart --service redis
"""

import argparse
import logging
import os
import signal
import subprocess  # nosec B404 - subprocess needed for service management
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import psutil
import redis
import requests
from sqlalchemy import create_engine, text

# Project configuration
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "service_manager.log"),
    ],
)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enumeration."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ServiceConfig:
    """Configuration for a service."""

    name: str
    command: List[str]
    port: Optional[int] = None
    health_check_url: Optional[str] = None
    health_check_command: Optional[List[str]] = None
    working_directory: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    depends_on: Optional[List[str]] = None
    startup_delay: int = 2
    shutdown_timeout: int = 30
    max_startup_time: int = 60


class ServiceManager:
    """Manages all Financial Dashboard services."""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.processes: Dict[str, subprocess.Popen] = {}
        self.service_configs = self._load_service_configs()
        self.running = True

        # Ensure logs directory exists
        (self.project_root / "logs").mkdir(exist_ok=True)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_service_configs(self) -> Dict[str, ServiceConfig]:
        """Load service configurations."""
        return {
            "postgres": ServiceConfig(
                name="PostgreSQL Database",
                command=[
                    "postgres",
                    "-D",
                    str(self.project_root / "data" / "postgres"),
                ],
                port=5432,
                health_check_command=["pg_isready", "-h", "localhost", "-p", "5432"],
                startup_delay=3,
                max_startup_time=30,
            ),
            "redis": ServiceConfig(
                name="Redis Server",
                command=["redis-server", "--port", "6379", "--save", "60", "1"],
                port=6379,
                health_check_command=["redis-cli", "ping"],
                startup_delay=2,
                max_startup_time=15,
            ),
            "backend": ServiceConfig(
                name="FastAPI Backend",
                command=[
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.main:app",
                    "--reload",
                    "--host",
                    "0.0.0.0",  # nosec B104 - binding to all interfaces for development
                    "--port",
                    "8000",
                ],
                port=8000,
                health_check_url="http://localhost:8000/health",
                working_directory=str(self.project_root),
                depends_on=["postgres", "redis"],
                startup_delay=5,
                max_startup_time=45,
            ),
            "celery": ServiceConfig(
                name="Celery Worker",
                command=[
                    sys.executable,
                    "-m",
                    "celery",
                    "-A",
                    "backend.tasks",
                    "worker",
                    "--loglevel=info",
                    "--concurrency=2",
                ],
                working_directory=str(self.project_root),
                depends_on=["postgres", "redis"],
                startup_delay=3,
                max_startup_time=30,
            ),
            "celery-beat": ServiceConfig(
                name="Celery Beat Scheduler",
                command=[
                    sys.executable,
                    "-m",
                    "celery",
                    "-A",
                    "backend.tasks",
                    "beat",
                    "--loglevel=info",
                ],
                working_directory=str(self.project_root),
                depends_on=["postgres", "redis"],
                startup_delay=3,
                max_startup_time=30,
            ),
            "flower": ServiceConfig(
                name="Flower Monitoring",
                command=[
                    sys.executable,
                    "-m",
                    "celery",
                    "-A",
                    "backend.tasks",
                    "flower",
                    "--port=5555",
                    "--basic_auth=admin:admin",
                ],
                port=5555,
                health_check_url="http://localhost:5555",
                working_directory=str(self.project_root),
                depends_on=["redis"],
                startup_delay=3,
                max_startup_time=30,
            ),
            "frontend": ServiceConfig(
                name="Streamlit Frontend",
                command=[
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    "frontend/app.py",
                    "--server.port",
                    "8501",
                    "--server.address",
                    "localhost",
                ],
                port=8501,
                health_check_url="http://localhost:8501/_stcore/health",
                working_directory=str(self.project_root),
                depends_on=["backend"],
                startup_delay=5,
                max_startup_time=45,
            ),
            "mcp": ServiceConfig(
                name="MCP Server",
                command=[sys.executable, "-m", "mcp_server"],
                working_directory=str(self.project_root),
                depends_on=["backend"],
                startup_delay=3,
                max_startup_time=30,
            ),
        }

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)

    def _setup_postgres(self) -> bool:
        """Setup PostgreSQL database if not exists."""
        try:
            data_dir = self.project_root / "data" / "postgres"

            if not data_dir.exists():
                logger.info("Initializing PostgreSQL data directory...")
                data_dir.mkdir(parents=True, exist_ok=True)

                # Initialize database
                result = subprocess.run(  # nosec B603,B607 - controlled PostgreSQL initialization
                    [
                        "initdb",
                        "-D",
                        str(data_dir),
                        "-U",
                        "financial_user",
                        "--pwfile=/dev/stdin",
                    ],
                    input="dev_password\n",
                    text=True,
                    capture_output=True,
                )

                if result.returncode != 0:
                    # Try with different method if initdb fails
                    try:
                        result = subprocess.run(  # nosec B603,B607 - controlled PostgreSQL initialization
                            ["pg_ctl", "initdb", "-D", str(data_dir)],
                            capture_output=True,
                            text=True,
                        )
                    except FileNotFoundError:
                        logger.error(
                            "PostgreSQL not found. Please install PostgreSQL first."
                        )
                        return False

            return True

        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL: {e}")
            return False

    def _check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed."""
        required_commands = {
            "postgres": "PostgreSQL server",
            "redis-server": "Redis server",
            "redis-cli": "Redis client",
            "python": "Python interpreter",
        }

        missing = []
        for cmd, desc in required_commands.items():
            try:
                subprocess.run(  # nosec B603 - version checking for dependency validation
                    [cmd, "--version"], capture_output=True, check=True, timeout=5
                )
            except (
                subprocess.CalledProcessError,
                FileNotFoundError,
                subprocess.TimeoutExpired,
            ):
                # Special handling for postgres
                if cmd == "postgres":
                    try:
                        subprocess.run(  # nosec B603,B607 - version checking for dependency validation
                            ["pg_ctl", "--version"],
                            capture_output=True,
                            check=True,
                            timeout=5,
                        )
                        continue
                    except (
                        subprocess.SubprocessError,
                        FileNotFoundError,
                        subprocess.TimeoutExpired,
                    ):
                        pass
                missing.append(f"{cmd} ({desc})")

        if missing:
            logger.error("Missing required dependencies:")
            for item in missing:
                logger.error(f"  - {item}")
            logger.error("Please install missing dependencies and try again.")
            return False

        return True

    def _load_environment(self):
        """Load environment variables from .env file."""
        env_file = self.project_root / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())

    def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get the status of a specific service."""
        if service_name not in self.service_configs:
            return ServiceStatus.UNKNOWN

        config = self.service_configs[service_name]

        # Check if we have a process running
        if service_name in self.processes:
            proc = self.processes[service_name]
            if proc.poll() is None:  # Process is still running
                # Check health if possible
                if config.health_check_url:
                    try:
                        response = requests.get(config.health_check_url, timeout=5)
                        if response.status_code == 200:
                            return ServiceStatus.RUNNING
                    except (requests.RequestException, requests.Timeout):
                        pass
                elif config.health_check_command:
                    try:
                        result = subprocess.run(  # nosec B603 - controlled health check commands
                            config.health_check_command, capture_output=True, timeout=5
                        )
                        if result.returncode == 0:
                            return ServiceStatus.RUNNING
                    except (
                        subprocess.SubprocessError,
                        FileNotFoundError,
                        subprocess.TimeoutExpired,
                    ):
                        pass

                return ServiceStatus.RUNNING
            else:
                # Process terminated
                del self.processes[service_name]
                return ServiceStatus.STOPPED

        # Check if service is running externally
        if config.port:
            try:
                for conn in psutil.net_connections():
                    if (
                        conn.laddr
                        and conn.laddr.port == config.port
                        and conn.status == "LISTEN"
                    ):
                        return ServiceStatus.RUNNING
            except (psutil.Error, AttributeError):
                pass

        return ServiceStatus.STOPPED

    def start_service(self, service_name: str) -> bool:
        """Start a specific service."""
        if service_name not in self.service_configs:
            logger.error(f"Unknown service: {service_name}")
            return False

        config = self.service_configs[service_name]

        # Check if already running
        if self.get_service_status(service_name) == ServiceStatus.RUNNING:
            logger.info(f"{config.name} is already running")
            return True

        # Check dependencies
        if config.depends_on:
            for dep in config.depends_on:
                if self.get_service_status(dep) != ServiceStatus.RUNNING:
                    logger.info(f"Starting dependency: {dep}")
                    if not self.start_service(dep):
                        logger.error(
                            f"Failed to start dependency {dep} for {service_name}"
                        )
                        return False

        # Special setup for postgres
        if service_name == "postgres" and not self._setup_postgres():
            return False

        logger.info(f"Starting {config.name}...")

        try:
            # Prepare environment
            env = os.environ.copy()
            if config.environment:
                env.update(config.environment)

            # Start the process
            proc = subprocess.Popen(  # nosec B603 - controlled service startup
                config.command,
                cwd=config.working_directory or self.project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.processes[service_name] = proc

            # Wait for startup
            time.sleep(config.startup_delay)

            # Wait for service to be healthy
            start_time = time.time()
            while time.time() - start_time < config.max_startup_time:
                if self.get_service_status(service_name) == ServiceStatus.RUNNING:
                    logger.info(f"{config.name} started successfully")
                    return True

                if proc.poll() is not None:
                    # Process died
                    stdout, stderr = proc.communicate()
                    logger.error(f"{config.name} failed to start:")
                    if stderr:
                        logger.error(f"STDERR: {stderr}")
                    if stdout:
                        logger.error(f"STDOUT: {stdout}")
                    del self.processes[service_name]
                    return False

                time.sleep(1)

            logger.error(
                f"{config.name} failed to become healthy within {config.max_startup_time}s"
            )
            self.stop_service(service_name)
            return False

        except Exception as e:
            logger.error(f"Failed to start {config.name}: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service."""
        if service_name not in self.service_configs:
            logger.error(f"Unknown service: {service_name}")
            return False

        config = self.service_configs[service_name]

        if service_name not in self.processes:
            logger.info(f"{config.name} is not running (or not managed by this script)")
            return True

        proc = self.processes[service_name]
        logger.info(f"Stopping {config.name}...")

        try:
            # Try graceful shutdown first
            proc.terminate()

            # Wait for graceful shutdown
            try:
                proc.wait(timeout=config.shutdown_timeout)
                logger.info(f"{config.name} stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if needed
                logger.warning(
                    f"{config.name} didn't stop gracefully, force killing..."
                )
                proc.kill()
                proc.wait()
                logger.info(f"{config.name} force stopped")

            del self.processes[service_name]
            return True

        except Exception as e:
            logger.error(f"Failed to stop {config.name}: {e}")
            return False

    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service."""
        logger.info(f"Restarting {service_name}...")
        if not self.stop_service(service_name):
            return False
        time.sleep(2)  # Brief pause between stop and start
        return self.start_service(service_name)

    def start_all_services(self) -> bool:
        """Start all services in dependency order."""
        logger.info("Starting all services...")

        if not self._check_prerequisites():
            return False

        self._load_environment()

        # Define startup order based on dependencies
        startup_order = [
            "postgres",
            "redis",  # Infrastructure
            "backend",  # Core API
            "celery",
            "celery-beat",
            "flower",  # Task processing
            "frontend",
            "mcp",  # User interfaces
        ]

        failed_services = []

        for service_name in startup_order:
            if not self.start_service(service_name):
                failed_services.append(service_name)

        if failed_services:
            logger.error(f"Failed to start services: {', '.join(failed_services)}")
            return False

        logger.info("All services started successfully!")
        self._show_service_urls()
        return True

    def stop_all_services(self) -> bool:
        """Stop all services."""
        logger.info("Stopping all services...")

        # Stop in reverse dependency order
        shutdown_order = [
            "mcp",
            "frontend",  # User interfaces
            "flower",
            "celery-beat",
            "celery",  # Task processing
            "backend",  # Core API
            "redis",
            "postgres",  # Infrastructure
        ]

        failed_services = []

        for service_name in shutdown_order:
            if service_name in self.processes:
                if not self.stop_service(service_name):
                    failed_services.append(service_name)

        if failed_services:
            logger.error(f"Failed to stop services: {', '.join(failed_services)}")
            return False

        logger.info("All services stopped successfully!")
        return True

    def restart_all_services(self) -> bool:
        """Restart all services."""
        logger.info("Restarting all services...")
        if not self.stop_all_services():
            return False
        time.sleep(3)  # Brief pause
        return self.start_all_services()

    def show_status(self):
        """Show status of all services."""
        logger.info("Service Status Report:")
        logger.info("=" * 50)

        for service_name, config in self.service_configs.items():
            status = self.get_service_status(service_name)
            status_symbol = {
                ServiceStatus.RUNNING: "✅",
                ServiceStatus.STOPPED: "❌",
                ServiceStatus.FAILED: "💥",
                ServiceStatus.STARTING: "🔄",
                ServiceStatus.STOPPING: "⏹️",
                ServiceStatus.UNKNOWN: "❓",
            }.get(status, "❓")

            port_info = f" (:{config.port})" if config.port else ""
            logger.info(f"{status_symbol} {config.name}{port_info}: {status.value}")

    def _show_service_urls(self):
        """Show URLs for accessible services."""
        urls = {
            "Frontend (Streamlit)": "http://localhost:8501",
            "Backend API": "http://localhost:8000",
            "API Documentation": "http://localhost:8000/docs",
            "Flower (Celery Monitor)": "http://localhost:5555",
            "PostgreSQL": "postgresql://financial_user:dev_password@localhost:5432/financial_dashboard",
            "Redis": "redis://localhost:6379/0",
        }

        logger.info("\n🌐 Service URLs:")
        logger.info("=" * 40)
        for name, url in urls.items():
            logger.info(f"{name}: {url}")

    def run_health_checks(self) -> Dict[str, bool]:
        """Run comprehensive health checks on all services."""
        logger.info("Running health checks...")
        results = {}

        for service_name, config in self.service_configs.items():
            logger.info(f"Checking {config.name}...")

            status = self.get_service_status(service_name)
            if status == ServiceStatus.RUNNING:
                # Additional health checks
                if service_name == "postgres":
                    results[service_name] = self._check_postgres_health()
                elif service_name == "redis":
                    results[service_name] = self._check_redis_health()
                elif service_name == "backend":
                    results[service_name] = self._check_backend_health()
                else:
                    results[service_name] = True
            else:
                results[service_name] = False

        # Show results
        logger.info("\n🏥 Health Check Results:")
        logger.info("=" * 30)
        for service, healthy in results.items():
            symbol = "✅" if healthy else "❌"
            logger.info(f"{symbol} {service}: {'Healthy' if healthy else 'Unhealthy'}")

        return results

    def _check_postgres_health(self) -> bool:
        """Check PostgreSQL health."""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                return False
            engine = create_engine(database_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
                return row is not None and row[0] == 1
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False

    def _check_redis_health(self) -> bool:
        """Check Redis health."""
        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            return r.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    def _check_backend_health(self) -> bool:
        """Check backend health."""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Backend health check failed: {e}")
            return False

    def monitor_services(self, interval: int = 30):
        """Monitor services continuously."""
        logger.info(f"Starting service monitoring (interval: {interval}s)")
        logger.info("Press Ctrl+C to stop monitoring")

        try:
            while self.running:
                self.show_status()

                # Check for failed services and attempt restart
                for service_name in self.service_configs:
                    status = self.get_service_status(service_name)
                    if status == ServiceStatus.FAILED:
                        logger.warning(
                            f"Service {service_name} failed, attempting restart..."
                        )
                        self.restart_service(service_name)

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Financial Dashboard Service Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manage_services.py start --all
  python scripts/manage_services.py stop --service redis
  python scripts/manage_services.py restart --service backend
  python scripts/manage_services.py status
  python scripts/manage_services.py health
  python scripts/manage_services.py monitor
        """,
    )

    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status", "health", "monitor"],
        help="Action to perform",
    )

    parser.add_argument(
        "--service",
        choices=[
            "postgres",
            "redis",
            "backend",
            "celery",
            "celery-beat",
            "flower",
            "frontend",
            "mcp",
        ],
        help="Specific service to manage",
    )

    parser.add_argument(
        "--all", action="store_true", help="Apply action to all services"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Monitoring interval in seconds (default: 30)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.action in ["start", "stop", "restart"] and not (args.service or args.all):
        parser.error("Must specify either --service or --all")

    # Create service manager
    manager = ServiceManager()

    try:
        if args.action == "start":
            if args.all:
                success = manager.start_all_services()
            else:
                success = manager.start_service(args.service)
            sys.exit(0 if success else 1)

        elif args.action == "stop":
            if args.all:
                success = manager.stop_all_services()
            else:
                success = manager.stop_service(args.service)
            sys.exit(0 if success else 1)

        elif args.action == "restart":
            if args.all:
                success = manager.restart_all_services()
            else:
                success = manager.restart_service(args.service)
            sys.exit(0 if success else 1)

        elif args.action == "status":
            manager.show_status()

        elif args.action == "health":
            results = manager.run_health_checks()
            all_healthy = all(results.values())
            sys.exit(0 if all_healthy else 1)

        elif args.action == "monitor":
            manager.monitor_services(args.interval)

    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        manager.stop_all_services()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
