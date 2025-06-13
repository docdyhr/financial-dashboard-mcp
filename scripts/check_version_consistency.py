#!/usr/bin/env python3
"""
Script to check version consistency across project files.

This script ensures that version numbers are consistent between:
- pyproject.toml
- backend/__init__.py

Used by pre-commit hooks and CI/CD pipeline.
"""

import re
import sys
from pathlib import Path


def extract_version_from_pyproject() -> str:
    """Extract version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    content = pyproject_path.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    
    return match.group(1)


def extract_version_from_backend() -> str:
    """Extract version from backend/__init__.py."""
    backend_init_path = Path("backend/__init__.py")
    if not backend_init_path.exists():
        raise FileNotFoundError("backend/__init__.py not found")
    
    content = backend_init_path.read_text()
    match = re.search(r'^__version__ = "([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("__version__ not found in backend/__init__.py")
    
    return match.group(1)


def validate_semver(version: str) -> bool:
    """Validate that version follows semantic versioning."""
    pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*)?(?:\+[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*)?$'
    return bool(re.match(pattern, version))


def main() -> int:
    """Main function to check version consistency."""
    try:
        print("🔍 Checking version consistency...")
        
        # Extract versions
        pyproject_version = extract_version_from_pyproject()
        backend_version = extract_version_from_backend()
        
        print(f"📄 pyproject.toml: {pyproject_version}")
        print(f"🐍 backend/__init__.py: {backend_version}")
        
        # Check consistency
        if pyproject_version != backend_version:
            print("❌ Version mismatch detected!")
            print(f"   pyproject.toml: {pyproject_version}")
            print(f"   backend/__init__.py: {backend_version}")
            print()
            print("💡 To fix this, run:")
            print(f"   sed -i 's/__version__ = \".*\"/__version__ = \"{pyproject_version}\"/' backend/__init__.py")
            return 1
        
        # Validate semantic versioning
        if not validate_semver(pyproject_version):
            print(f"❌ Version '{pyproject_version}' does not follow semantic versioning!")
            print("   Expected format: MAJOR.MINOR.PATCH (e.g., 1.0.0, 2.1.3)")
            return 1
        
        print(f"✅ All versions are consistent: {pyproject_version}")
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1
    except ValueError as e:
        print(f"❌ Version extraction error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())