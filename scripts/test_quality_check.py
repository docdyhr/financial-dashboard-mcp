#!/usr/bin/env python3
"""
Comprehensive test coverage analysis and quality validation script.

This script analyzes test coverage, validates test quality, and provides
actionable recommendations for improving the test suite.
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class CoverageMetrics:
    """Coverage metrics for a module or file."""

    name: str
    statements: int
    missing: int
    excluded: int
    coverage: float
    missing_lines: List[str]


@dataclass
class TestQualityMetrics:
    """Test quality metrics."""

    total_tests: int
    unit_tests: int
    integration_tests: int
    api_tests: int
    performance_tests: int
    test_files: int
    assertions_count: int
    mock_usage: int
    fixture_usage: int
    parametrized_tests: int


@dataclass
class QualityReport:
    """Overall quality report."""

    coverage_metrics: Dict[str, CoverageMetrics]
    test_metrics: TestQualityMetrics
    quality_score: float
    recommendations: List[str]
    warnings: List[str]
    errors: List[str]


class TestCoverageAnalyzer:
    """Analyzes test coverage from coverage reports."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.coverage_xml_path = project_root / "coverage.xml"
        self.coverage_report_path = project_root / "htmlcov"

    def run_coverage_analysis(self) -> bool:
        """Run coverage analysis and generate reports."""
        try:
            # Run tests with coverage
            cmd = [
                "python",
                "-m",
                "pytest",
                "--cov=backend",
                "--cov=frontend",
                "--cov=mcp_server",
                "--cov-report=xml",
                "--cov-report=html",
                "--cov-report=term-missing",
                "-q",
            ]

            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode != 0:
                print(f"Coverage analysis failed: {result.stderr}")
                return False

            return True

        except Exception as e:
            print(f"Error running coverage analysis: {e}")
            return False

    def parse_coverage_xml(self) -> Dict[str, CoverageMetrics]:
        """Parse coverage XML report."""
        if not self.coverage_xml_path.exists():
            return {}

        try:
            tree = ET.parse(self.coverage_xml_path)
            root = tree.getroot()

            metrics = {}

            for package in root.findall(".//package"):
                package_name = package.get("name", "")

                for class_elem in package.findall("classes/class"):
                    filename = class_elem.get("filename", "")

                    # Calculate metrics
                    statements = 0
                    missing = 0
                    covered = 0

                    for line in class_elem.findall("lines/line"):
                        statements += 1
                        hits = int(line.get("hits", "0"))
                        if hits == 0:
                            missing += 1
                        else:
                            covered += 1

                    if statements > 0:
                        coverage = (covered / statements) * 100

                        # Get missing lines
                        missing_lines = [
                            line.get("number", "")
                            for line in class_elem.findall("lines/line")
                            if int(line.get("hits", "0")) == 0
                        ]

                        metrics[filename] = CoverageMetrics(
                            name=filename,
                            statements=statements,
                            missing=missing,
                            excluded=0,
                            coverage=coverage,
                            missing_lines=missing_lines,
                        )

            return metrics

        except Exception as e:
            print(f"Error parsing coverage XML: {e}")
            return {}

    def calculate_overall_coverage(self, metrics: Dict[str, CoverageMetrics]) -> float:
        """Calculate overall coverage percentage."""
        if not metrics:
            return 0.0

        total_statements = sum(m.statements for m in metrics.values())
        total_missing = sum(m.missing for m in metrics.values())

        if total_statements == 0:
            return 0.0

        return ((total_statements - total_missing) / total_statements) * 100


class TestQualityAnalyzer:
    """Analyzes test quality metrics."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"

    def analyze_test_files(self) -> TestQualityMetrics:
        """Analyze test files for quality metrics."""
        if not self.tests_dir.exists():
            return TestQualityMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        test_files = list(self.tests_dir.rglob("test_*.py"))
        test_files.extend(list(self.tests_dir.rglob("*_test.py")))

        total_tests = 0
        unit_tests = 0
        integration_tests = 0
        api_tests = 0
        performance_tests = 0
        assertions_count = 0
        mock_usage = 0
        fixture_usage = 0
        parametrized_tests = 0

        for test_file in test_files:
            try:
                content = test_file.read_text(encoding="utf-8")

                # Count test functions
                file_tests = content.count("def test_")
                total_tests += file_tests

                # Categorize tests based on file path or markers
                if "/unit/" in str(test_file):
                    unit_tests += file_tests
                elif "/integration/" in str(test_file):
                    integration_tests += file_tests
                elif "/api/" in str(test_file):
                    api_tests += file_tests
                elif "/performance/" in str(test_file):
                    performance_tests += file_tests

                # Count assertions
                assertions_count += content.count("assert ")

                # Count mock usage
                mock_usage += content.count("Mock(")
                mock_usage += content.count("@patch")
                mock_usage += content.count("mock_")

                # Count fixture usage
                fixture_usage += content.count("@pytest.fixture")

                # Count parametrized tests
                parametrized_tests += content.count("@pytest.mark.parametrize")

            except Exception as e:
                print(f"Error analyzing {test_file}: {e}")
                continue

        return TestQualityMetrics(
            total_tests=total_tests,
            unit_tests=unit_tests,
            integration_tests=integration_tests,
            api_tests=api_tests,
            performance_tests=performance_tests,
            test_files=len(test_files),
            assertions_count=assertions_count,
            mock_usage=mock_usage,
            fixture_usage=fixture_usage,
            parametrized_tests=parametrized_tests,
        )


class TestQualityValidator:
    """Validates test quality and provides recommendations."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.min_coverage = 80.0
        self.min_test_ratio = 0.5  # Minimum test files to source files ratio

    def validate_coverage(
        self, metrics: Dict[str, CoverageMetrics]
    ) -> Tuple[List[str], List[str]]:
        """Validate coverage metrics and return warnings/errors."""
        warnings = []
        errors = []

        if not metrics:
            errors.append("No coverage data found. Ensure tests are run with coverage.")
            return warnings, errors

        # Check overall coverage
        overall_coverage = sum(
            m.coverage * m.statements for m in metrics.values()
        ) / sum(m.statements for m in metrics.values())

        if overall_coverage < self.min_coverage:
            errors.append(
                f"Overall coverage {overall_coverage:.1f}% is below minimum {self.min_coverage}%"
            )

        # Check individual file coverage
        low_coverage_files = [
            f"{m.name} ({m.coverage:.1f}%)"
            for m in metrics.values()
            if m.coverage < 70.0
        ]

        if low_coverage_files:
            warnings.append(f"Files with low coverage: {', '.join(low_coverage_files)}")

        # Check for completely untested files
        untested_files = [m.name for m in metrics.values() if m.coverage == 0]
        if untested_files:
            errors.append(f"Completely untested files: {', '.join(untested_files)}")

        return warnings, errors

    def validate_test_quality(
        self, test_metrics: TestQualityMetrics
    ) -> Tuple[List[str], List[str]]:
        """Validate test quality metrics."""
        warnings = []
        errors = []

        # Check if tests exist
        if test_metrics.total_tests == 0:
            errors.append("No tests found in the project")
            return warnings, errors

        # Check test distribution
        if test_metrics.unit_tests == 0:
            warnings.append("No unit tests found")

        if test_metrics.integration_tests == 0:
            warnings.append("No integration tests found")

        if test_metrics.api_tests == 0:
            warnings.append("No API tests found")

        # Check assertions ratio
        assertions_per_test = test_metrics.assertions_count / test_metrics.total_tests
        if assertions_per_test < 1.0:
            warnings.append(f"Low assertions per test ratio: {assertions_per_test:.1f}")

        # Check fixture usage
        if test_metrics.fixture_usage == 0:
            warnings.append(
                "No pytest fixtures found - consider using fixtures for test data"
            )

        # Check parametrized tests
        parametrized_ratio = test_metrics.parametrized_tests / test_metrics.total_tests
        if parametrized_ratio < 0.1:
            warnings.append(
                "Consider using more parametrized tests for better coverage"
            )

        return warnings, errors

    def generate_recommendations(
        self,
        coverage_metrics: Dict[str, CoverageMetrics],
        test_metrics: TestQualityMetrics,
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if not coverage_metrics:
            recommendations.append("Set up coverage reporting with pytest-cov")
            return recommendations

        # Coverage recommendations
        overall_coverage = sum(
            m.coverage * m.statements for m in coverage_metrics.values()
        ) / sum(m.statements for m in coverage_metrics.values())

        if overall_coverage < 90:
            recommendations.append(
                f"Increase overall coverage from {overall_coverage:.1f}% to 90%+"
            )

        # Find files that need the most attention
        low_coverage_files = sorted(
            [
                (m.name, m.coverage, m.missing)
                for m in coverage_metrics.values()
                if m.coverage < 80
            ],
            key=lambda x: x[2],  # Sort by missing lines
            reverse=True,
        )

        if low_coverage_files:
            top_files = low_coverage_files[:3]
            recommendations.append(
                f"Priority files for testing: {', '.join([f'{name} ({missing} lines)' for name, _, missing in top_files])}"
            )

        # Test quality recommendations
        if test_metrics.total_tests > 0:
            if test_metrics.unit_tests / test_metrics.total_tests < 0.6:
                recommendations.append(
                    "Increase unit test coverage - aim for 60%+ of tests to be unit tests"
                )

            if test_metrics.performance_tests == 0:
                recommendations.append("Add performance tests for critical components")

            if test_metrics.mock_usage / test_metrics.total_tests < 0.3:
                recommendations.append(
                    "Consider using more mocks to isolate units under test"
                )

        # ISIN-specific recommendations
        isin_files = [f for f in coverage_metrics.keys() if "isin" in f.lower()]
        if isin_files:
            low_isin_coverage = [
                f for f in isin_files if coverage_metrics[f].coverage < 85
            ]
            if low_isin_coverage:
                recommendations.append(
                    f"ISIN components need better coverage: {', '.join(low_isin_coverage)}"
                )

        return recommendations

    def calculate_quality_score(
        self,
        coverage_metrics: Dict[str, CoverageMetrics],
        test_metrics: TestQualityMetrics,
    ) -> float:
        """Calculate overall quality score (0-100)."""
        if not coverage_metrics or test_metrics.total_tests == 0:
            return 0.0

        # Coverage score (40% weight)
        overall_coverage = sum(
            m.coverage * m.statements for m in coverage_metrics.values()
        ) / sum(m.statements for m in coverage_metrics.values())
        coverage_score = min(overall_coverage, 100.0)

        # Test distribution score (30% weight)
        total_tests = test_metrics.total_tests
        distribution_score = 0
        if total_tests > 0:
            unit_ratio = min(test_metrics.unit_tests / total_tests, 0.7) / 0.7
            integration_ratio = (
                min(test_metrics.integration_tests / total_tests, 0.3) / 0.3
            )
            api_ratio = min(test_metrics.api_tests / total_tests, 0.2) / 0.2

            distribution_score = (unit_ratio + integration_ratio + api_ratio) * 100 / 3

        # Test quality score (30% weight)
        quality_score = 0
        if total_tests > 0:
            assertions_ratio = min(
                test_metrics.assertions_count / total_tests / 3.0, 1.0
            )
            fixture_ratio = min(
                test_metrics.fixture_usage / test_metrics.test_files, 1.0
            )
            parametrized_ratio = min(
                test_metrics.parametrized_tests / total_tests / 0.2, 1.0
            )

            quality_score = (
                (assertions_ratio + fixture_ratio + parametrized_ratio) * 100 / 3
            )

        # Combined score
        final_score = (
            coverage_score * 0.4 + distribution_score * 0.3 + quality_score * 0.3
        )
        return min(final_score, 100.0)


class TestQualityReporter:
    """Generates test quality reports."""

    def print_coverage_report(self, metrics: Dict[str, CoverageMetrics]):
        """Print coverage report to console."""
        if not metrics:
            print("❌ No coverage data available")
            return

        print("\n📊 Coverage Report")
        print("=" * 50)

        # Overall stats
        total_statements = sum(m.statements for m in metrics.values())
        total_missing = sum(m.missing for m in metrics.values())
        overall_coverage = ((total_statements - total_missing) / total_statements) * 100

        print(f"Overall Coverage: {overall_coverage:.1f}%")
        print(f"Total Statements: {total_statements}")
        print(f"Missing: {total_missing}")
        print()

        # Per-file breakdown
        sorted_metrics = sorted(metrics.values(), key=lambda m: m.coverage)

        print("File Coverage Breakdown:")
        print(f"{'File':<40} {'Coverage':<10} {'Missing':<8}")
        print("-" * 60)

        for metric in sorted_metrics:
            status = (
                "🟢"
                if metric.coverage >= 90
                else "🟡" if metric.coverage >= 70 else "🔴"
            )
            short_name = metric.name[-37:] if len(metric.name) > 37 else metric.name
            print(
                f"{status} {short_name:<37} {metric.coverage:>6.1f}% {metric.missing:>7}"
            )

    def print_test_quality_report(self, metrics: TestQualityMetrics):
        """Print test quality report to console."""
        print("\n🧪 Test Quality Report")
        print("=" * 50)

        if metrics.total_tests == 0:
            print("❌ No tests found")
            return

        print(f"Total Tests: {metrics.total_tests}")
        print(f"Test Files: {metrics.test_files}")
        print()

        # Test distribution
        print("Test Distribution:")
        print(
            f"  Unit Tests: {metrics.unit_tests} ({metrics.unit_tests/metrics.total_tests*100:.1f}%)"
        )
        print(
            f"  Integration Tests: {metrics.integration_tests} ({metrics.integration_tests/metrics.total_tests*100:.1f}%)"
        )
        print(
            f"  API Tests: {metrics.api_tests} ({metrics.api_tests/metrics.total_tests*100:.1f}%)"
        )
        print(
            f"  Performance Tests: {metrics.performance_tests} ({metrics.performance_tests/metrics.total_tests*100:.1f}%)"
        )
        print()

        # Quality metrics
        print("Quality Metrics:")
        print(
            f"  Assertions per Test: {metrics.assertions_count/metrics.total_tests:.1f}"
        )
        print(f"  Fixtures: {metrics.fixture_usage}")
        print(f"  Parametrized Tests: {metrics.parametrized_tests}")
        print(f"  Mock Usage: {metrics.mock_usage}")

    def print_quality_score(self, score: float):
        """Print overall quality score."""
        print(f"\n🎯 Overall Quality Score: {score:.1f}/100")

        if score >= 90:
            print("🟢 Excellent test quality!")
        elif score >= 80:
            print("🟡 Good test quality with room for improvement")
        elif score >= 60:
            print("🟠 Moderate test quality - needs attention")
        else:
            print("🔴 Poor test quality - significant improvements needed")

    def print_recommendations(self, recommendations: List[str]):
        """Print recommendations."""
        if not recommendations:
            return

        print("\n💡 Recommendations")
        print("=" * 50)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

    def print_warnings_and_errors(self, warnings: List[str], errors: List[str]):
        """Print warnings and errors."""
        if errors:
            print("\n❌ Errors")
            print("=" * 50)
            for error in errors:
                print(f"• {error}")

        if warnings:
            print("\n⚠️  Warnings")
            print("=" * 50)
            for warning in warnings:
                print(f"• {warning}")

    def generate_json_report(self, report: QualityReport, output_path: Path):
        """Generate JSON report."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "quality_score": report.quality_score,
            "coverage": {
                "files": {
                    name: {
                        "statements": m.statements,
                        "missing": m.missing,
                        "coverage": m.coverage,
                        "missing_lines": m.missing_lines,
                    }
                    for name, m in report.coverage_metrics.items()
                }
            },
            "test_metrics": {
                "total_tests": report.test_metrics.total_tests,
                "unit_tests": report.test_metrics.unit_tests,
                "integration_tests": report.test_metrics.integration_tests,
                "api_tests": report.test_metrics.api_tests,
                "performance_tests": report.test_metrics.performance_tests,
                "test_files": report.test_metrics.test_files,
                "assertions_count": report.test_metrics.assertions_count,
                "mock_usage": report.test_metrics.mock_usage,
                "fixture_usage": report.test_metrics.fixture_usage,
                "parametrized_tests": report.test_metrics.parametrized_tests,
            },
            "recommendations": report.recommendations,
            "warnings": report.warnings,
            "errors": report.errors,
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test quality analysis and validation")
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Don't run tests, use existing coverage data",
    )
    parser.add_argument("--json-output", type=str, help="Output JSON report to file")
    parser.add_argument(
        "--fail-under",
        type=float,
        default=80.0,
        help="Fail if coverage is under this threshold",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    project_root = PROJECT_ROOT

    # Initialize analyzers
    coverage_analyzer = TestCoverageAnalyzer(project_root)
    test_analyzer = TestQualityAnalyzer(project_root)
    validator = TestQualityValidator(project_root)
    reporter = TestQualityReporter()

    # Run coverage analysis
    if not args.no_run:
        print("🔄 Running coverage analysis...")
        if not coverage_analyzer.run_coverage_analysis():
            print("❌ Failed to run coverage analysis")
            sys.exit(1)

    # Parse coverage data
    print("📊 Analyzing coverage data...")
    coverage_metrics = coverage_analyzer.parse_coverage_xml()

    # Analyze test quality
    print("🧪 Analyzing test quality...")
    test_metrics = test_analyzer.analyze_test_files()

    # Validate and generate recommendations
    print("🔍 Validating quality...")
    coverage_warnings, coverage_errors = validator.validate_coverage(coverage_metrics)
    test_warnings, test_errors = validator.validate_test_quality(test_metrics)

    all_warnings = coverage_warnings + test_warnings
    all_errors = coverage_errors + test_errors

    recommendations = validator.generate_recommendations(coverage_metrics, test_metrics)
    quality_score = validator.calculate_quality_score(coverage_metrics, test_metrics)

    # Generate report
    report = QualityReport(
        coverage_metrics=coverage_metrics,
        test_metrics=test_metrics,
        quality_score=quality_score,
        recommendations=recommendations,
        warnings=all_warnings,
        errors=all_errors,
    )

    # Print reports
    reporter.print_coverage_report(coverage_metrics)
    reporter.print_test_quality_report(test_metrics)
    reporter.print_quality_score(quality_score)
    reporter.print_recommendations(recommendations)
    reporter.print_warnings_and_errors(all_warnings, all_errors)

    # Generate JSON report if requested
    if args.json_output:
        output_path = Path(args.json_output)
        reporter.generate_json_report(report, output_path)
        print(f"\n📄 JSON report saved to: {output_path}")

    # Check exit conditions
    overall_coverage = coverage_analyzer.calculate_overall_coverage(coverage_metrics)

    if all_errors:
        print(f"\n❌ Quality check failed with {len(all_errors)} errors")
        sys.exit(1)

    if overall_coverage < args.fail_under:
        print(
            f"\n❌ Coverage {overall_coverage:.1f}% is below threshold {args.fail_under}%"
        )
        sys.exit(1)

    if quality_score < 60:
        print(f"\n❌ Quality score {quality_score:.1f} is below acceptable threshold")
        sys.exit(1)

    print("\n✅ Quality check passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()
