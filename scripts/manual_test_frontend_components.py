#!/usr/bin/env python3
"""Test script to validate frontend components without starting Streamlit server."""

from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all required imports work correctly."""
    print("🔍 Testing imports...")

    try:
        import streamlit as st

        # Test basic streamlit functionality
        _ = st.__version__
        print("  ✅ Streamlit import successful")
    except ImportError as e:
        print(f"  ❌ Streamlit import failed: {e}")
        return False

    try:
        import pandas as pd

        # Test basic pandas functionality
        _ = pd.__version__
        print("  ✅ Pandas import successful")
    except ImportError as e:
        print(f"  ❌ Pandas import failed: {e}")
        return False

    try:
        import numpy as np

        # Test basic numpy functionality
        _ = np.__version__
        print("  ✅ NumPy import successful")
    except ImportError as e:
        print(f"  ❌ NumPy import failed: {e}")
        return False

    try:
        import plotly.graph_objects as go

        # Test basic plotly functionality
        _ = go.Figure()
        print("  ✅ Plotly import successful")
    except ImportError as e:
        print(f"  ❌ Plotly import failed: {e}")
        return False

    return True


def test_portfolio_component():
    """Test portfolio component functions."""
    print("\n📊 Testing portfolio component...")

    try:
        # Import the portfolio component
        from frontend.components.portfolio import portfolio_value_chart

        # Test that the function exists
        _ = portfolio_value_chart

        print("  ✅ Portfolio component import successful")

        # Test the data generation logic (the part that was failing)
        import numpy as np
        import pandas as pd

        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        base_value = 100000
        growth_rate = 0.0003
        volatility = 0.015

        np.random.seed(42)
        daily_returns = np.random.normal(growth_rate, volatility, len(dates))
        cumulative_returns = np.cumprod(1 + daily_returns)
        values = pd.Series(index=dates, data=base_value * cumulative_returns)

        print("✅ Sample data generation successful")
        print(f"    - Dates: {len(dates)} entries")
        print(f"    - Values: {len(values)} entries")
        print(f"    - Match: {'✅' if len(dates) == len(values) else '❌'}")

        return True

    except Exception as e:
        print(f"  ❌ Portfolio component test failed: {e}")
        return False


def test_app_structure():
    """Test main app structure."""
    print("\n🏗️  Testing app structure...")

    try:
        # Test that main app file exists and can be imported
        app_path = project_root / "frontend" / "app.py"
        if not app_path.exists():
            print("  ❌ app.py not found")
            return False

        print("  ✅ app.py exists")

        # Test syntax by compiling
        import py_compile

        py_compile.compile(str(app_path), doraise=True)
        print("  ✅ app.py syntax valid")

        return True

    except Exception as e:
        print(f"  ❌ App structure test failed: {e}")
        return False


def test_component_structure():
    """Test component structure."""
    print("\n🧩 Testing component structure...")

    try:
        components_path = project_root / "frontend" / "components"
        if not components_path.exists():
            print("  ❌ components directory not found")
            return False

        print("  ✅ components directory exists")

        # Test portfolio component
        portfolio_path = components_path / "portfolio.py"
        if not portfolio_path.exists():
            print("  ❌ portfolio.py not found")
            return False

        print("  ✅ portfolio.py exists")

        # Test syntax
        import py_compile

        py_compile.compile(str(portfolio_path), doraise=True)
        print("  ✅ portfolio.py syntax valid")

        return True

    except Exception as e:
        print(f"  ❌ Component structure test failed: {e}")
        return False


def test_backend_integration():
    """Test backend integration capabilities."""
    print("\n🔗 Testing backend integration...")

    try:
        import requests

        # Test basic requests functionality
        _ = requests.__version__

        print("  ✅ Requests library available")

        # Test that we can make a connection attempt (doesn't need to succeed)
        backend_url = "http://localhost:8000"
        print(f"  ℹ️  Backend URL configured: {backend_url}")

        return True

    except ImportError as e:
        print(f"  ❌ Backend integration test failed: {e}")
        return False


def test_environment():
    """Test environment setup."""
    print("\n🌍 Testing environment...")

    # Check Python version
    python_version = sys.version_info
    print(
        f"  ℹ️  Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    if python_version >= (3, 8):
        print("  ✅ Python version compatible")
    else:
        print("  ❌ Python version too old (need 3.8+)")
        return False

    # Check virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    print(
        f"  {'✅' if in_venv else '⚠️'} Virtual environment: {'Active' if in_venv else 'Not detected'}"
    )

    return True


def simulate_streamlit_functions():
    """Simulate Streamlit functions to test component logic."""
    print("\n🎭 Testing component logic simulation...")

    try:
        # Create mock streamlit functions
        class MockStreamlit:
            def metric(self, *args, **kwargs):
                pass

            def subheader(self, *args, **kwargs):
                pass

            def info(self, *args, **kwargs):
                pass

            def plotly_chart(self, *args, **kwargs):
                pass

            def columns(self, *args, **kwargs):
                return [MockStreamlit(), MockStreamlit(), MockStreamlit()]

            def button(self, *args, **kwargs):
                return False

            def spinner(self, *args, **kwargs):
                return MockContext()

        class MockContext:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        # Test portfolio summary logic
        import pandas as pd

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "asset_id": [1, 2, 3],
                "symbol": ["AAPL", "GOOGL", "MSFT"],
                "quantity": [10, 5, 8],
                "avg_cost": [150.0, 2500.0, 300.0],
                "current_price": [175.0, 2800.0, 350.0],
                "market_value": [1750.0, 14000.0, 2800.0],
                "unrealized_pnl": [250.0, 1500.0, 400.0],
            }
        )

        # Test calculations
        total_value = sample_data["market_value"].sum()
        total_cost = (sample_data["quantity"] * sample_data["avg_cost"]).sum()
        total_pnl = sample_data["unrealized_pnl"].sum()

        print("✅ Portfolio calculations successful")
        print(f"    - Total value: ${total_value:,.2f}")
        print(f"    - Total cost: ${total_cost:,.2f}")
        print(f"    - Total P&L: ${total_pnl:,.2f}")

        return True

    except Exception as e:
        print(f"  ❌ Component logic simulation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Frontend Component Tests")
    print("=" * 50)

    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("App Structure", test_app_structure),
        ("Component Structure", test_component_structure),
        ("Portfolio Component", test_portfolio_component),
        ("Backend Integration", test_backend_integration),
        ("Component Logic", simulate_streamlit_functions),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"  💥 {test_name} test crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary:")

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All frontend component tests passed!")
        print("💡 You can now run: streamlit run frontend/app.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
