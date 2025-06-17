#!/usr/bin/env python3
"""Test script to validate the Streamlit frontend components"""

import os
import sys

import requests

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_backend_connection():
    """Test backend API connection."""
    backend_url = "http://localhost:8000"

    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is accessible")
            return True
        print(f"❌ Backend API returned status {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend API connection failed: {e}")
        return False


def test_frontend_components():
    """Test that frontend components can be imported."""
    try:
        # Testing import availability - unused imports are expected
        from frontend.components.portfolio import (  # noqa: F401
            portfolio_overview_widget,
        )
        from frontend.components.tasks import task_monitoring_widget  # noqa: F401

        print("✅ Frontend components imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Frontend component import failed: {e}")
        return False


def test_streamlit_import():
    """Test that Streamlit can be imported."""
    try:
        import streamlit as st

        print(f"✅ Streamlit {st.__version__} is available")
        return True
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False


def test_plotly_import():
    """Test that Plotly can be imported."""
    try:
        # Testing import availability - unused imports are expected
        import plotly.express as px  # noqa: F401
        import plotly.graph_objects as go  # noqa: F401

        print("✅ Plotly is available for charts")
        return True
    except ImportError as e:
        print(f"❌ Plotly import failed: {e}")
        print("💡 Install with: pip install plotly")
        return False


def main():
    """Run all frontend tests."""
    print("🧪 Testing Financial Dashboard Frontend")
    print("=" * 40)

    tests = [
        ("Streamlit Import", test_streamlit_import),
        ("Plotly Import", test_plotly_import),
        ("Frontend Components", test_frontend_components),
        ("Backend Connection", test_backend_connection),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 40)
    print("📊 Test Results Summary")
    print("=" * 40)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Frontend is ready.")
        print("\n💡 To start the dashboard:")
        print("   ./scripts/start_dashboard.sh")
        print("\n🌐 Or start manually:")
        print("   1. docker-compose up -d")
        print("   2. cd frontend && streamlit run app.py")
    else:
        print(
            f"\n⚠️  {total - passed} test(s) failed. Please fix issues before starting."
        )

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
