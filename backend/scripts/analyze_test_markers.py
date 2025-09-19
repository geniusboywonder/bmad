#!/usr/bin/env python3
"""
Test Marker Analysis Script

Analyzes test files for proper marker classification compliance with Testing Protocol.
Generates comprehensive reports on marker usage and identifies tests needing updates.

Usage:
    python scripts/analyze_test_markers.py --comprehensive
    python scripts/analyze_test_markers.py --file=test_file.py
    python scripts/analyze_test_markers.py --directory=backend/tests
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class TestMarkerAnalysis:
    """Analysis results for a single test file."""
    file_path: str
    total_tests: int
    marked_tests: int
    real_data_tests: int
    external_service_tests: int
    mock_data_tests: int
    unmarked_tests: List[str]
    inappropriate_mocks: List[str]
    compliance_percentage: float

class TestMarkerAnalyzer:
    """Analyzes test files for marker compliance."""

    VALID_MARKERS = {
        'real_data': '@pytest.mark.real_data',
        'external_service': '@pytest.mark.external_service',
        'mock_data': '@pytest.mark.mock_data'
    }

    INAPPROPRIATE_PATTERNS = [
        r'@patch\(["\'](?:app\.database|get_session|database\.get_session)["\']',
        r'@patch\(["\']app\.services\.',
        r'@patch\(["\'](?:app\.models|app\.repositories)["\']'
    ]

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
        self.results: Dict[str, TestMarkerAnalysis] = {}

    def analyze_file(self, file_path: Path) -> TestMarkerAnalysis:
        """Analyze a single test file for marker compliance."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return TestMarkerAnalysis(
                file_path=str(file_path),
                total_tests=0,
                marked_tests=0,
                real_data_tests=0,
                external_service_tests=0,
                mock_data_tests=0,
                unmarked_tests=[],
                inappropriate_mocks=[],
                compliance_percentage=0.0
            )

        # Find all test functions
        test_functions = re.findall(r'def (test_\w+)\s*\(', content)
        total_tests = len(test_functions)

        if total_tests == 0:
            return TestMarkerAnalysis(
                file_path=str(file_path),
                total_tests=0,
                marked_tests=0,
                real_data_tests=0,
                external_service_tests=0,
                mock_data_tests=0,
                unmarked_tests=[],
                inappropriate_mocks=[],
                compliance_percentage=0.0
            )

        # Analyze each test function
        marked_tests = 0
        real_data_tests = 0
        external_service_tests = 0
        mock_data_tests = 0
        unmarked_tests = []
        inappropriate_mocks = []

        for test_func in test_functions:
            # Find the test function with its decorators
            func_pattern = rf'(@pytest\.mark\.(?:real_data|external_service|mock_data)\s*\n\s*)?def {test_func}\s*\('
            func_match = re.search(func_pattern, content, re.MULTILINE | re.DOTALL)

            if func_match:
                marker_match = re.search(r'@pytest\.mark\.(real_data|external_service|mock_data)', func_match.group(0))
                if marker_match:
                    marked_tests += 1
                    marker_type = marker_match.group(1)
                    if marker_type == 'real_data':
                        real_data_tests += 1
                    elif marker_type == 'external_service':
                        external_service_tests += 1
                    elif marker_type == 'mock_data':
                        mock_data_tests += 1
                else:
                    unmarked_tests.append(test_func)
            else:
                unmarked_tests.append(test_func)

            # Check for inappropriate mocking patterns
            func_start = content.find(f'def {test_func}(')
            if func_start != -1:
                # Look for decorators above the function
                decorator_section = content[:func_start].split('\n')[-10:]  # Last 10 lines
                decorator_text = '\n'.join(decorator_section)

                for pattern in self.INAPPROPRIATE_PATTERNS:
                    if re.search(pattern, decorator_text):
                        inappropriate_mocks.append(f"{test_func}: {pattern}")

        compliance_percentage = (marked_tests / total_tests * 100) if total_tests > 0 else 0.0

        return TestMarkerAnalysis(
            file_path=str(file_path),
            total_tests=total_tests,
            marked_tests=marked_tests,
            real_data_tests=real_data_tests,
            external_service_tests=external_service_tests,
            mock_data_tests=mock_data_tests,
            unmarked_tests=unmarked_tests,
            inappropriate_mocks=inappropriate_mocks,
            compliance_percentage=compliance_percentage
        )

    def analyze_directory(self, directory: Path) -> Dict[str, TestMarkerAnalysis]:
        """Analyze all test files in a directory."""
        results = {}

        # Find all Python test files
        test_files = list(directory.rglob('test_*.py'))
        test_files.extend(list(directory.rglob('*_test.py')))

        print(f"Found {len(test_files)} test files in {directory}")

        for test_file in test_files:
            if test_file.is_file():
                print(f"Analyzing {test_file}")
                analysis = self.analyze_file(test_file)
                results[str(test_file)] = analysis

        return results

    def generate_report(self, results: Dict[str, TestMarkerAnalysis]) -> str:
        """Generate a comprehensive analysis report."""
        total_files = len(results)
        total_tests = sum(analysis.total_tests for analysis in results.values())
        total_marked = sum(analysis.marked_tests for analysis in results.values())
        total_unmarked = sum(len(analysis.unmarked_tests) for analysis in results.values())
        total_inappropriate = sum(len(analysis.inappropriate_mocks) for analysis in results.values())

        overall_compliance = (total_marked / total_tests * 100) if total_tests > 0 else 0.0

        report = []
        report.append("# Test Marker Compliance Analysis Report")
        report.append("")
        report.append("## Executive Summary")
        report.append("")
        report.append(f"- **Total Test Files Analyzed**: {total_files}")
        report.append(f"- **Total Tests Found**: {total_tests}")
        report.append(f"- **Tests with Markers**: {total_marked}")
        report.append(f"- **Tests without Markers**: {total_unmarked}")
        report.append(f"- **Inappropriate Mocks Found**: {total_inappropriate}")
        report.append(".1f")
        report.append("")
        report.append("## Marker Distribution")
        report.append("")

        marker_counts = defaultdict(int)
        for analysis in results.values():
            marker_counts['real_data'] += analysis.real_data_tests
            marker_counts['external_service'] += analysis.external_service_tests
            marker_counts['mock_data'] += analysis.mock_data_tests

        report.append("| Marker Type | Count | Percentage |")
        report.append("|-------------|-------|------------|")
        for marker_type, count in marker_counts.items():
            percentage = (count / total_tests * 100) if total_tests > 0 else 0.0
            report.append(f"| {marker_type} | {count} | {percentage:.1f}% |")
        report.append("")

        report.append("## Files Requiring Updates")
        report.append("")

        for file_path, analysis in results.items():
            if analysis.compliance_percentage < 100.0 or analysis.inappropriate_mocks:
                report.append(f"### {Path(file_path).name}")
                report.append(f"- **Location**: {file_path}")
                report.append(".1f")
                report.append(f"- **Total Tests**: {analysis.total_tests}")
                report.append(f"- **Marked Tests**: {analysis.marked_tests}")
                report.append(f"- **Unmarked Tests**: {len(analysis.unmarked_tests)}")
                report.append(f"- **Inappropriate Mocks**: {len(analysis.inappropriate_mocks)}")

                if analysis.unmarked_tests:
                    report.append("")
                    report.append("**Unmarked Tests**:")
                    for test in analysis.unmarked_tests:
                        report.append(f"- {test}")

                if analysis.inappropriate_mocks:
                    report.append("")
                    report.append("**Inappropriate Mocks**:")
                    for mock in analysis.inappropriate_mocks:
                        report.append(f"- {mock}")

                report.append("")

        report.append("## Recommendations")
        report.append("")
        report.append("### Immediate Actions")
        report.append("- Add markers to all unmarked tests")
        report.append("- Replace inappropriate database/service mocks with real implementations")
        report.append("- Implement factory-based test data generation")
        report.append("")
        report.append("### Process Improvements")
        report.append("- Integrate marker validation into CI/CD pipeline")
        report.append("- Create automated marker suggestion tooling")
        report.append("- Establish marker maintenance workflows")
        report.append("")
        report.append("### Quality Gates")
        report.append("- Require 100% marker compliance for all tests")
        report.append("- Block merges with inappropriate mocking patterns")
        report.append("- Automate marker validation in pre-commit hooks")

        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Analyze test marker compliance")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Analyze all test files in the project")
    parser.add_argument("--file", type=str,
                       help="Analyze a specific test file")
    parser.add_argument("--directory", type=str,
                       help="Analyze all test files in a directory")
    parser.add_argument("--output", type=str, default="marker-analysis-report.md",
                       help="Output file for the report")

    args = parser.parse_args()

    analyzer = TestMarkerAnalyzer()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File {file_path} does not exist")
            sys.exit(1)

        print(f"Analyzing {file_path}")
        analysis = analyzer.analyze_file(file_path)
        analyzer.results[str(file_path)] = analysis

    elif args.directory:
        directory = Path(args.directory)
        if not directory.exists():
            print(f"Error: Directory {directory} does not exist")
            sys.exit(1)

        analyzer.results = analyzer.analyze_directory(directory)

    elif args.comprehensive:
        # Analyze backend and frontend test directories
        backend_tests = Path("../backend/tests")
        frontend_tests = Path("../frontend/tests")

        if backend_tests.exists():
            print("Analyzing backend tests...")
            analyzer.results.update(analyzer.analyze_directory(backend_tests))

        if frontend_tests.exists():
            print("Analyzing frontend tests...")
            analyzer.results.update(analyzer.analyze_directory(frontend_tests))

    else:
        print("Please specify --comprehensive, --file, or --directory")
        sys.exit(1)

    # Generate and save report
    report = analyzer.generate_report(analyzer.results)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Analysis complete. Report saved to {args.output}")

    # Print summary
    total_tests = sum(analysis.total_tests for analysis in analyzer.results.values())
    total_marked = sum(analysis.marked_tests for analysis in analyzer.results.values())
    compliance = (total_marked / total_tests * 100) if total_tests > 0 else 0.0

    print("\nSummary:")
    print(f"  Total tests: {total_tests}")
    print(f"  Marked tests: {total_marked}")
    print(f"  Compliance: {compliance:.1f}%")

if __name__ == "__main__":
    main()
