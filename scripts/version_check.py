#!/usr/bin/env python3
"""Simple Version Check Script for Financial Dashboard MCP

This script prevents confusion between Financial Dashboard application version
and Python version specifications by validating and fixing version consistency.

Usage:
    python scripts/version_check.py --check    # Check version consistency
    python scripts/version_check.py --fix      # Fix version issues
    python scripts/version_check.py --bump <type>  # Bump version (major/minor/patch)
"""

import argparse
from pathlib import Path
import re
import sys


class VersionChecker:
    """Simple version management for Financial Dashboard."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.app_version = "1.5.1"  # Current Financial Dashboard version
        self.python_version = "3.11"  # Python runtime version
        self.python_target = "py311"  # Python target for tools

    def check_pyproject_toml(self) -> dict[str, bool]:
        """Check pyproject.toml for version consistency."""
        results = {}
        pyproject_path = self.project_root / "pyproject.toml"

        if not pyproject_path.exists():
            results["pyproject_exists"] = False
            return results

        content = pyproject_path.read_text()

        # Check project version
        project_version_match = re.search(
            r'\[project\].*?version\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL
        )
        results["project_version_correct"] = (
            project_version_match and project_version_match.group(1) == self.app_version
        )

        # Check mypy python_version (should be 3.11, not app version)
        mypy_version_match = re.search(
            r'python_version\s*=\s*["\']([^"\']+)["\']', content
        )
        results["mypy_version_correct"] = (
            mypy_version_match and mypy_version_match.group(1) == self.python_version
        )

        # Check black target-version (should be py311, not app version)
        black_version_match = re.search(
            r'target-version\s*=\s*\[["\']([^"\']+)["\']\]', content
        )
        results["black_version_correct"] = (
            black_version_match and black_version_match.group(1) == self.python_target
        )

        # Check for incorrect app version in Python specs
        results["no_app_version_in_python_specs"] = not bool(
            re.search(r'python_version\s*=\s*["\']1\.[56]\.[0-9]+["\']', content)
            or re.search(r'target-version.*["\']1\.[56]\.[0-9]+["\']', content)
        )

        return results

    def check_backend_init(self) -> dict[str, bool]:
        """Check backend/__init__.py version."""
        results = {}
        backend_init = self.project_root / "backend" / "__init__.py"

        if not backend_init.exists():
            results["backend_init_exists"] = False
            return results

        content = backend_init.read_text()

        # Check __version__
        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        results["backend_version_correct"] = (
            version_match and version_match.group(1) == self.app_version
        )

        # Check it's not Python version
        results["backend_not_python_version"] = not bool(
            re.search(r'__version__\s*=\s*["\']3\.[0-9]+["\']', content)
        )

        return results

    def check_all_versions(self) -> dict[str, dict[str, bool]]:
        """Check all version specifications."""
        return {
            "pyproject_toml": self.check_pyproject_toml(),
            "backend_init": self.check_backend_init(),
        }

    def fix_pyproject_toml(self) -> bool:
        """Fix pyproject.toml version specifications."""
        pyproject_path = self.project_root / "pyproject.toml"

        if not pyproject_path.exists():
            print("❌ pyproject.toml not found")
            return False

        content = pyproject_path.read_text()
        original_content = content

        # Fix project version (ensure it's the app version)
        content = re.sub(
            r'(\[project\].*?version\s*=\s*["\'])[^"\']+(["\'])',
            rf"\g<1>{self.app_version}\g<2>",
            content,
            flags=re.DOTALL,
        )

        # Fix mypy python_version (ensure it's Python version, not app version)
        content = re.sub(
            r'python_version\s*=\s*["\'][^"\']*["\']',
            f'python_version = "{self.python_version}"',
            content,
        )

        # Fix black target-version (ensure it's Python target, not app version)
        content = re.sub(
            r'target-version\s*=\s*\[["\'][^"\']*["\']\]',
            f'target-version = ["{self.python_target}"]',
            content,
        )

        # Fix ruff target-version
        content = re.sub(
            r'(\[tool\.ruff\].*?)target-version\s*=\s*["\'][^"\']*["\']',
            rf'\g<1>target-version = "{self.python_target}"',
            content,
            flags=re.DOTALL,
        )

        if content != original_content:
            pyproject_path.write_text(content)
            print("✅ Fixed pyproject.toml version specifications")
            return True
        print("✅ pyproject.toml already correct")
        return False

    def fix_backend_init(self) -> bool:
        """Fix backend/__init__.py version."""
        backend_init = self.project_root / "backend" / "__init__.py"

        if not backend_init.exists():
            print("❌ backend/__init__.py not found")
            return False

        content = backend_init.read_text()
        original_content = content

        # Fix __version__ (ensure it's app version, not Python version)
        content = re.sub(
            r'__version__\s*=\s*["\'][^"\']*["\']',
            f'__version__ = "{self.app_version}"',
            content,
        )

        if content != original_content:
            backend_init.write_text(content)
            print("✅ Fixed backend/__init__.py version")
            return True
        print("✅ backend/__init__.py already correct")
        return False

    def fix_all_versions(self) -> bool:
        """Fix all version issues."""
        print("🔧 Fixing Financial Dashboard version specifications...")
        print(f"📱 App Version: {self.app_version}")
        print(f"🐍 Python Version: {self.python_version}")
        print(f"🎯 Python Target: {self.python_target}")
        print()

        changes_made = False

        if self.fix_pyproject_toml():
            changes_made = True

        if self.fix_backend_init():
            changes_made = True

        return changes_made

    def bump_version(self, bump_type: str) -> str:
        """Bump the application version."""
        major, minor, patch = map(int, self.app_version.split("."))

        if bump_type == "major":
            new_version = f"{major + 1}.0.0"
        elif bump_type == "minor":
            new_version = f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            new_version = f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        # Update app_version and fix files
        old_version = self.app_version
        self.app_version = new_version

        self.fix_all_versions()

        print(f"🚀 Version bumped from {old_version} to {new_version}")
        return new_version

    def print_status(self) -> None:
        """Print current version status."""
        print("📊 Financial Dashboard Version Status")
        print("=" * 50)

        results = self.check_all_versions()

        print(f"📱 Expected App Version: {self.app_version}")
        print(f"🐍 Expected Python Version: {self.python_version}")
        print(f"🎯 Expected Python Target: {self.python_target}")
        print()

        # pyproject.toml status
        print("📄 pyproject.toml:")
        pyproject_results = results.get("pyproject_toml", {})
        for check, passed in pyproject_results.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check.replace('_', ' ').title()}")

        print()

        # backend/__init__.py status
        print("🐍 backend/__init__.py:")
        backend_results = results.get("backend_init", {})
        for check, passed in backend_results.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check.replace('_', ' ').title()}")

        print()

        # Overall status
        all_passed = all(all(checks.values()) for checks in results.values() if checks)

        if all_passed:
            print("🎉 All version specifications are correct!")
        else:
            print("⚠️  Version issues detected. Run with --fix to resolve.")


def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(
        description="Financial Dashboard Version Management"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Check version consistency")
    group.add_argument("--fix", action="store_true", help="Fix version issues")
    group.add_argument(
        "--bump", choices=["major", "minor", "patch"], help="Bump version"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    checker = VersionChecker(project_root)

    try:
        if args.check:
            checker.print_status()

        elif args.fix:
            if checker.fix_all_versions():
                print("\n✅ Version issues have been fixed!")
                print("💡 Remember to commit these changes")
            else:
                print("\n✅ No version issues found")

        elif args.bump:
            new_version = checker.bump_version(args.bump)
            print(f"\n✅ Version bumped to {new_version}")
            print("💡 Remember to:")
            print("   1. Commit the changes")
            print(f"   2. Tag the release: git tag v{new_version}")
            print("   3. Push with tags: git push --tags")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
