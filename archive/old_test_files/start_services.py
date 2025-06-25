#!/usr/bin/env python3
"""Startup script for Financial Dashboard services.
This script starts both the backend (FastAPI) and frontend (Streamlit) services.
"""

import logging
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 8000
FRONTEND_PORT = 8501
PROJECT_ROOT = Path(__file__).parent
VENV_PATH = PROJECT_ROOT / ".venv"
PYTHON_PATH = VENV_PATH / "bin" / "python"

# Process tracking
processes = []
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    print("\n🛑 Shutdown signal received. Stopping services...")
    shutdown_requested = True
    stop_all_services()
    sys.exit(0)


def check_venv():
    """Check if virtual environment exists and is properly configured."""
    if not VENV_PATH.exists():
        print("❌ Virtual environment not found at .venv/")
        print(
            "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
        )
        return False

    if not PYTHON_PATH.exists():
        print("❌ Python interpreter not found in virtual environment")
        return False

    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        result = subprocess.run(
            [str(PYTHON_PATH), "-c", "import uvicorn, streamlit, fastapi"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False


def start_backend():
    """Start the FastAPI backend service."""
    print(f"🚀 Starting backend on http://{BACKEND_HOST}:{BACKEND_PORT}")

    cmd = [
        str(PYTHON_PATH),
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        BACKEND_HOST,
        "--port",
        str(BACKEND_PORT),
        "--reload",
    ]

    try:
        process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        processes.append(("backend", process))

        # Monitor backend startup
        def monitor_backend():
            for line in iter(process.stdout.readline, ""):
                if shutdown_requested:
                    break
                print(f"[BACKEND] {line.strip()}")
                if "Application startup complete" in line:
                    print(
                        f"✅ Backend started successfully on http://localhost:{BACKEND_PORT}"
                    )
                    print(f"📚 API Documentation: http://localhost:{BACKEND_PORT}/docs")

        threading.Thread(target=monitor_backend, daemon=True).start()
        return process

    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None


def start_frontend():
    """Start the Streamlit frontend service."""
    print(f"🎨 Starting frontend on http://localhost:{FRONTEND_PORT}")

    cmd = [
        str(PYTHON_PATH),
        "-m",
        "streamlit",
        "run",
        "frontend/app.py",
        "--server.port",
        str(FRONTEND_PORT),
        "--server.address",
        "localhost",
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]

    try:
        process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        processes.append(("frontend", process))

        # Monitor frontend startup
        def monitor_frontend():
            for line in iter(process.stdout.readline, ""):
                if shutdown_requested:
                    break
                print(f"[FRONTEND] {line.strip()}")
                if "You can now view your Streamlit app" in line:
                    print(
                        f"✅ Frontend started successfully on http://localhost:{FRONTEND_PORT}"
                    )

        threading.Thread(target=monitor_frontend, daemon=True).start()
        return process

    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None


def wait_for_backend():
    """Wait for backend to be ready."""
    import requests

    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(
                f"http://localhost:{BACKEND_PORT}/health", timeout=2
            )
            if response.status_code == 200:
                return True
        except (
            requests.RequestException,
            requests.ConnectionError,
            requests.Timeout,
        ) as e:
            logger.debug(
                f"Health check attempt {attempt + 1}/{max_attempts} failed: {e}"
            )
        except Exception as e:
            logger.warning(f"Unexpected error during health check: {e}")

        if shutdown_requested:
            return False

        print(f"⏳ Waiting for backend to start... ({attempt + 1}/{max_attempts})")
        time.sleep(2)

    return False


def stop_all_services():
    """Stop all running services."""
    print("🛑 Stopping all services...")

    for service_name, process in processes:
        if process and process.poll() is None:
            print(f"   Stopping {service_name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {service_name}...")
                process.kill()
                process.wait()
            except Exception as e:
                print(f"   Error stopping {service_name}: {e}")

    processes.clear()
    print("✅ All services stopped")


def main():
    """Main startup function."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🏦 Financial Dashboard Startup Script")
    print("=" * 50)

    # Pre-flight checks
    print("🔍 Running pre-flight checks...")

    if not check_venv():
        sys.exit(1)

    if not check_dependencies():
        print("❌ Required dependencies not found")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

    print("✅ All pre-flight checks passed")
    print()

    # Start services
    try:
        # Start backend first
        backend_process = start_backend()
        if not backend_process:
            print("❌ Failed to start backend service")
            sys.exit(1)

        # Wait for backend to be ready
        if not wait_for_backend():
            print("❌ Backend failed to start properly")
            stop_all_services()
            sys.exit(1)

        print()

        # Start frontend
        frontend_process = start_frontend()
        if not frontend_process:
            print("❌ Failed to start frontend service")
            stop_all_services()
            sys.exit(1)

        # Wait a bit for frontend to start
        time.sleep(5)

        print("\n" + "=" * 50)
        print("🎉 FINANCIAL DASHBOARD STARTED SUCCESSFULLY!")
        print("=" * 50)
        print(f"🎨 Frontend:  http://localhost:{FRONTEND_PORT}")
        print(f"🔧 Backend:   http://localhost:{BACKEND_PORT}")
        print(f"📚 API Docs:  http://localhost:{BACKEND_PORT}/docs")
        print(f"🏥 Health:    http://localhost:{BACKEND_PORT}/health")
        print("=" * 50)
        print("📝 Features Available:")
        print("   • Portfolio Dashboard")
        print("   • Position Management (with deletion)")
        print("   • Transaction History")
        print("   • Real-time Market Data")
        print("   • Settings & Configuration")
        print("=" * 50)
        print("Press Ctrl+C to stop all services")
        print()

        # Keep the script running
        try:
            while True:
                time.sleep(1)

                # Check if processes are still running
                for service_name, process in processes:
                    if process.poll() is not None:
                        print(f"⚠️  {service_name} service stopped unexpectedly")
                        stop_all_services()
                        sys.exit(1)

        except KeyboardInterrupt:
            pass

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        stop_all_services()
        sys.exit(1)

    finally:
        stop_all_services()


if __name__ == "__main__":
    main()
