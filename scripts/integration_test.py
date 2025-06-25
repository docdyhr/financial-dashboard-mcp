#!/usr/bin/env python3
"""Integration test for the complete Financial Dashboard system."""

from datetime import datetime
import sys
import time

import pytest
import requests

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8501"
FLOWER_URL = "http://localhost:5555"


def check_service(name, url, endpoint="", headers=None):
    """Check if a service is accessible."""
    try:
        response = requests.get(f"{url}{endpoint}", timeout=5, headers=headers or {})
        if response.status_code == 200:
            print(f"✅ {name}: Accessible")
            return True
        print(f"❌ {name}: HTTP {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: {e}")
        return False


@pytest.mark.integration
def test_api_endpoints():
    """Test key API endpoints."""
    # Get authentication token
    auth_headers = {}
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data={"username": "demo", "password": "demo123"},
            timeout=5,
        )
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            auth_headers = {"Authorization": f"Bearer {token}"}
    except Exception:
        pass  # Continue without auth for basic endpoints

    endpoints = [
        ("/health", "Health Check", None),
        ("/api/v1/portfolio/summary/47", "Portfolio Summary", auth_headers),
        ("/api/v1/positions/summary/47", "Portfolio Positions", auth_headers),
        ("/api/v1/tasks/active", "Active Tasks", auth_headers),
    ]

    print("\n🔍 Testing API Endpoints:")
    print("-" * 40)

    for endpoint, name, headers in endpoints:
        success = check_service(name, BACKEND_URL, endpoint, headers)
        if not success:
            assert False, f"API endpoint {name} failed"

    assert True


@pytest.mark.integration
def test_task_submission():
    """Test task submission and monitoring."""
    print("\n🔄 Testing Task System:")
    print("-" * 40)

    # Get authentication token
    auth_headers = {}
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data={"username": "demo", "password": "demo123"},
            timeout=5,
        )
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            auth_headers = {"Authorization": f"Bearer {token}"}
    except Exception:
        pass

    # Submit a market data task
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/tasks/market-data",
            json={"symbols": ["AAPL"]},
            headers=auth_headers,
            timeout=10,
        )

        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get("task_id")
            print(f"✅ Task submitted: {task_id}")

            # Wait and check status
            time.sleep(2)

            status_response = requests.get(
                f"{BACKEND_URL}/api/v1/tasks/status/{task_id}",
                headers=auth_headers,
                timeout=5,
            )

            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ Task status: {status_data.get('status', 'Unknown')}")
                assert True
                return
            print("❌ Could not check task status")
            assert False, "Could not check task status"
        print(f"❌ Task submission failed: {response.status_code}")
        assert False, f"Task submission failed: {response.status_code}"

    except requests.exceptions.RequestException as e:
        print(f"❌ Task submission error: {e}")
        assert False, f"Task submission error: {e}"


@pytest.mark.integration
def test_frontend_components():
    """Test frontend component functionality."""
    print("\n🎨 Testing Frontend Integration:")
    print("-" * 40)

    # Test if Streamlit is accessible
    if not check_service("Streamlit Frontend", FRONTEND_URL):
        print("❌ Frontend is not accessible")
        assert False, "Frontend is not accessible"

    # Get authentication token
    auth_headers = {}
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data={"username": "demo", "password": "demo123"},
            timeout=5,
        )
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            auth_headers = {"Authorization": f"Bearer {token}"}
    except Exception:
        pass

    # Test component data sources
    data_tests = [
        ("Portfolio Data", f"{BACKEND_URL}/api/v1/portfolio/summary/47"),
        ("Positions Data", f"{BACKEND_URL}/api/v1/positions/summary/47"),
        ("Tasks Data", f"{BACKEND_URL}/api/v1/tasks/active"),
    ]

    for name, url in data_tests:
        try:
            response = requests.get(url, headers=auth_headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: Available ({type(data).__name__})")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: {e}")

    assert True


def run_full_system_test():
    """Run complete system integration test."""
    print("🚀 Financial Dashboard Integration Test")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test service accessibility
    print("\n🌐 Checking Service Accessibility:")
    print("-" * 40)

    services = [
        ("Backend API", BACKEND_URL, "/health"),
        ("Streamlit Frontend", FRONTEND_URL, ""),
        ("Flower Monitor", FLOWER_URL, ""),
    ]

    services_ok = True
    for name, url, endpoint in services:
        if not check_service(name, url, endpoint):
            services_ok = False

    if not services_ok:
        print("\n❌ Some services are not accessible!")
        print("Make sure all services are running:")
        print("  docker-compose up -d")
        print("  streamlit run frontend/app.py")
        return False

    # Test API functionality
    if not test_api_endpoints():
        print("\n❌ API tests failed!")
        return False

    # Test task system
    if not test_task_submission():
        print("\n❌ Task system tests failed!")
        return False

    # Test frontend integration
    if not test_frontend_components():
        print("\n❌ Frontend integration tests failed!")
        return False

    # Final success message
    print("\n🎉 All Tests Passed!")
    print("=" * 50)
    print("✅ System Status: HEALTHY")
    print("\n🌐 Access Points:")
    print(f"  • Dashboard: {FRONTEND_URL}")
    print(f"  • API Docs: {BACKEND_URL}/docs")
    print(f"  • Task Monitor: {FLOWER_URL}")

    print("\n💡 Next Steps:")
    print("  1. Open the dashboard in your browser")
    print("  2. Run demo setup: python scripts/demo_setup.py")
    print("  3. Explore the different pages and features")

    return True


def main():
    """Main test function."""
    success = run_full_system_test()

    if success:
        print("\n🌟 Integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Integration test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
