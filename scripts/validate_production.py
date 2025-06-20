#!/usr/bin/env python3
"""
Production Environment Validation Script

This script validates that the production environment is properly configured
and secure before deployment.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{GREEN}=== {text} ==={NC}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{GREEN}✓ {text}{NC}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{NC}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{RED}✗ {text}{NC}")


def check_env_file() -> Tuple[bool, List[str]]:
    """Check if .env file exists and validate its contents."""
    issues = []

    if not Path(".env").exists():
        issues.append(".env file not found - run ./scripts/setup_production.sh first")
        return False, issues

    # Read .env file
    with open(".env", "r") as f:
        env_content = f.read()

    # Check for required variables
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "MCP_AUTH_TOKEN",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "ENVIRONMENT",
        "DEBUG",
    ]

    for var in required_vars:
        if f"{var}=" not in env_content:
            issues.append(f"Missing required variable: {var}")

    # Check for insecure values
    insecure_patterns = [
        (r"SECRET_KEY=.*CHANGE_ME", "SECRET_KEY contains placeholder value"),
        (r"PASSWORD=.*CHANGE_ME", "Password contains placeholder value"),
        (r"DEBUG=True", "DEBUG is set to True in production"),
        (r"ENVIRONMENT=development", "ENVIRONMENT is set to development"),
        (r"PASSWORD=password", "Weak password detected"),
        (r"PASSWORD=admin", "Weak password detected"),
        (r"SECRET_KEY=dev-", "Development secret key detected"),
    ]

    for pattern, message in insecure_patterns:
        if re.search(pattern, env_content, re.IGNORECASE):
            issues.append(message)

    # Check for exposed email addresses
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(email_pattern, env_content)
    real_emails = [e for e in emails if not e.endswith("@example.com")]
    if real_emails:
        issues.append(f"Real email addresses found: {', '.join(real_emails)}")

    # Check secret strength
    secret_key_match = re.search(r"SECRET_KEY=(.+?)(?:\n|$)", env_content)
    if secret_key_match:
        secret_key = secret_key_match.group(1)
        if len(secret_key) < 50:
            issues.append("SECRET_KEY is too short (should be at least 50 characters)")

    return len(issues) == 0, issues


def check_docker_files() -> Tuple[bool, List[str]]:
    """Check Docker configuration files for security issues."""
    issues = []

    # Check docker-compose.yml
    if Path("docker-compose.yml").exists():
        with open("docker-compose.yml", "r") as f:
            compose_content = f.read()

        # Check for hardcoded passwords
        if "password:-" in compose_content or "PASSWORD:-" in compose_content:
            issues.append("docker-compose.yml contains default passwords")

    # Check production compose file
    prod_compose = "docker/docker-compose.prod.yml"
    if not Path(prod_compose).exists():
        issues.append("Production docker-compose file not found")

    return len(issues) == 0, issues


def check_gitignore() -> Tuple[bool, List[str]]:
    """Verify .gitignore properly excludes sensitive files."""
    issues = []

    if not Path(".gitignore").exists():
        issues.append(".gitignore file not found")
        return False, issues

    with open(".gitignore", "r") as f:
        gitignore_content = f.read()

    required_patterns = [".env", "*.pem", "*.key", "secrets/", "*.secret"]

    for pattern in required_patterns:
        if pattern not in gitignore_content:
            issues.append(f".gitignore missing pattern: {pattern}")

    return len(issues) == 0, issues


def check_file_permissions() -> Tuple[bool, List[str]]:
    """Check file permissions for sensitive files."""
    issues = []

    if Path(".env").exists():
        stat_info = os.stat(".env")
        mode = oct(stat_info.st_mode)[-3:]
        if mode != "600":
            issues.append(f".env file has insecure permissions: {mode} (should be 600)")

    return len(issues) == 0, issues


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check for dependency security issues."""
    issues = []

    # This is a basic check - in production, use tools like safety or snyk
    if Path("requirements.txt").exists():
        with open("requirements.txt", "r") as f:
            deps = f.read()

        # Check for known vulnerable versions (examples)
        vulnerable_patterns = [
            (r"django==2\.[0-1]", "Django version has known vulnerabilities"),
            (r"flask==0\.", "Flask version is outdated"),
            (r"requests==2\.1[0-9]", "Requests version may have vulnerabilities"),
        ]

        for pattern, message in vulnerable_patterns:
            if re.search(pattern, deps, re.IGNORECASE):
                issues.append(message)

    return len(issues) == 0, issues


def main():
    """Run all validation checks."""
    print(f"{GREEN}Financial Dashboard - Production Validation{NC}")
    print("=" * 50)

    all_passed = True

    # Run checks
    checks = [
        ("Environment Configuration", check_env_file),
        ("Docker Configuration", check_docker_files),
        ("Git Ignore Configuration", check_gitignore),
        ("File Permissions", check_file_permissions),
        ("Dependencies", check_dependencies),
    ]

    for check_name, check_func in checks:
        print_header(check_name)
        passed, issues = check_func()

        if passed:
            print_success(f"{check_name} validation passed")
        else:
            all_passed = False
            for issue in issues:
                print_error(issue)

    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print_success("All production validation checks passed!")
        print("\nNext steps:")
        print("1. Set up SSL/TLS certificates")
        print("2. Configure firewall rules")
        print("3. Set up monitoring and alerting")
        print("4. Deploy with: docker-compose -f docker/docker-compose.prod.yml up -d")
        return 0
    else:
        print_error("Production validation failed!")
        print_warning("Fix the issues above before deploying to production")
        return 1


if __name__ == "__main__":
    sys.exit(main())
