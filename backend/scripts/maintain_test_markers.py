#!/usr/bin/env python3
"""
Test Marker Maintenance Script

Maintains test marker compliance across the codebase by:
- Auto-suggesting markers for unmarked tests
- Validating marker usage patterns
- Generating maintenance reports
- Providing CI/CD integration hooks

Usage:
    python scripts/maintain_test_markers.py --suggest-markers
    python scripts/maintain_test_markers.py --validate-markers
    python scripts/maintain_test_markers.py --generate-report
    python scripts/maintain_test_markers.py --ci-check
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import json

@dataclass
class MarkerSuggestion:
    """Suggestion for adding a marker to a test."""
    file_path: str
    test_function: str
    suggested_marker: str
    confidence: float
    reasoning: str

@dataclass
class MarkerValidation:
    """Validation result for a test marker."""
    file_path: str
    test_function: str
    marker: str
    is_valid: bool
    issues: List[str]

class TestMarkerMaintainer:
    """Maintains test marker compliance and provides suggestions."""

    VALID_MARKERS = {
        'real_data': {
            'description': 'Uses real database/services',
            'patterns': [
                r'get_session\(\)',
                r'\.query\(',
                r'\.add\(',
                r'\.commit\(\)',
                r'DatabaseTestManager',
                r'real_db',
                r'actual.*database'
            ]
        },
        'external_service': {
            'description': 'Mocks external APIs only',
            'patterns': [
                r'@patch\(.*(?:openai|anthropic|google|external)',
                r'mock.*(?:api|external|llm)',
                r'httpx.*mock',
                r'responses.*mock'
            ]
        },
        'mock_data': {
            'description': 'Uses mocks for all dependencies',
            'patterns': [
                r'@patch\(.*app\.',
                r'mock.*service',
                r'pytest\.fixture',
                r'MagicMock',
                r'unit.*test'
            ]
        }
    }

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
        self.suggestions: List[MarkerSuggestion] = []
        self.validations: List[MarkerValidation] = []

    def analyze_test_content(self, content: str, test_function: str) -> str:
        """Analyze test content to suggest appropriate marker."""
        content_lower = content.lower()

        # Check for real database patterns
        for pattern in self.VALID_MARKERS['real_data']['patterns']:
            if re.search(pattern, content, re.IGNORECASE):
                return 'real_data'

        # Check for external service patterns
        for pattern in self.VALID_MARKERS['external_service']['patterns']:
            if re.search(pattern, content, re.IGNORECASE):
                return 'external_service'

        # Check for mock data patterns
        for pattern in self.VALID_MARKERS['mock_data']['patterns']:
            if re.search(pattern, content, re.IGNORECASE):
                return 'mock_data'

        # Default to mock_data for unit tests
        if 'unit' in str(self.base_path).lower() or 'test_' in test_function:
            return 'mock_data'

        return 'real_data'  # Default for integration tests

    def suggest_markers_for_file(self, file_path: Path) -> List[MarkerSuggestion]:
        """Generate marker suggestions for a test file."""
        suggestions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return suggestions

        # Find all test functions
        test_functions = re.findall(r'def (test_\w+)\s*\(', content)

        for test_func in test_functions:
            # Check if already has marker
            func_start = content.find(f'def {test_func}(')
            if func_start == -1:
                continue

            # Look for existing marker
            marker_section = content[:func_start].split('\n')[-5:]  # Last 5 lines
            has_marker = any(re.search(r'@pytest\.mark\.(real_data|external_service|mock_data)', line)
                           for line in marker_section)

            if not has_marker:
                # Get test function content
                func_end = content.find('\n\n', func_start)
                if func_end == -1:
                    func_end = len(content)
                test_content = content[func_start:func_end]

                # Suggest marker
                suggested_marker = self.analyze_test_content(test_content, test_func)

                # Calculate confidence
                confidence = self._calculate_confidence(test_content, suggested_marker)

                suggestions.append(MarkerSuggestion(
                    file_path=str(file_path),
                    test_function=test_func,
                    suggested_marker=suggested_marker,
                    confidence=confidence,
                    reasoning=self._generate_reasoning(test_content, suggested_marker)
                ))

        return suggestions

    def _calculate_confidence(self, content: str, marker: str) -> float:
        """Calculate confidence score for marker suggestion."""
        if marker not in self.VALID_MARKERS:
            return 0.0

        patterns = self.VALID_MARKERS[marker]['patterns']
        matches = sum(1 for pattern in patterns if re.search(pattern, content, re.IGNORECASE))

        # Base confidence
        confidence = 0.5

        # Increase confidence based on pattern matches
        confidence += min(matches * 0.2, 0.4)

        # Increase confidence for clear indicators
        if 'database' in content.lower() and marker == 'real_data':
            confidence += 0.2
        elif 'mock' in content.lower() and marker == 'mock_data':
            confidence += 0.2
        elif 'external' in content.lower() and marker == 'external_service':
            confidence += 0.2

        return min(confidence, 1.0)

    def _generate_reasoning(self, content: str, marker: str) -> str:
        """Generate reasoning for marker suggestion."""
        if marker == 'real_data':
            return "Test appears to use real database operations or service calls"
        elif marker == 'external_service':
            return "Test mocks external APIs or services"
        elif marker == 'mock_data':
            return "Test uses mocked dependencies for unit testing"
        else:
            return "Default marker suggestion based on test structure"

    def validate_markers_in_file(self, file_path: Path) -> List[MarkerValidation]:
        """Validate existing markers in a test file."""
        validations = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return validations

        # Find all test functions with markers
        marker_pattern = r'@pytest\.mark\.(real_data|external_service|mock_data)\s*\n\s*def (test_\w+)\s*\('
        matches = re.findall(marker_pattern, content, re.MULTILINE)

        for marker, test_func in matches:
            # Get test function content
            func_start = content.find(f'def {test_func}(')
            func_end = content.find('\n\n', func_start)
            if func_end == -1:
                func_end = len(content)
            test_content = content[func_start:func_end]

            # Validate marker appropriateness
            is_valid, issues = self._validate_marker_appropriateness(test_content, marker)

            validations.append(MarkerValidation(
                file_path=str(file_path),
                test_function=test_func,
                marker=marker,
                is_valid=is_valid,
                issues=issues
            ))

        return validations

    def _validate_marker_appropriateness(self, content: str, marker: str) -> Tuple[bool, List[str]]:
        """Validate if a marker is appropriate for the test content."""
        issues = []

        if marker not in self.VALID_MARKERS:
            return False, ["Invalid marker type"]

        # Check for conflicting patterns
        if marker == 'real_data':
            # Should not have extensive mocking
            mock_count = len(re.findall(r'@patch|@mock', content))
            if mock_count > 3:
                issues.append("High number of mocks in real_data test")
        elif marker == 'mock_data':
            # Should not have real database calls
            if re.search(r'get_session\(\)|\.query\(|\.add\(|\.commit\(\)', content):
                issues.append("Real database operations in mock_data test")
        elif marker == 'external_service':
            # Should not mock internal services
            if re.search(r'@patch\(.*app\.services', content):
                issues.append("Mocking internal services in external_service test")

        return len(issues) == 0, issues

    def generate_maintenance_report(self, suggestions: List[MarkerSuggestion],
                                  validations: List[MarkerValidation]) -> str:
        """Generate a comprehensive maintenance report."""
        report = []
        report.append("# Test Marker Maintenance Report")
        report.append("")

        # Summary
        total_suggestions = len(suggestions)
        total_validations = len(validations)
        invalid_markers = len([v for v in validations if not v.is_valid])

        report.append("## Summary")
        report.append("")
        report.append(f"- **Marker Suggestions**: {total_suggestions}")
        report.append(f"- **Marker Validations**: {total_validations}")
        report.append(f"- **Invalid Markers**: {invalid_markers}")
        report.append("")

        # Suggestions by confidence
        if suggestions:
            report.append("## Marker Suggestions")
            report.append("")

            # Group by confidence
            high_conf = [s for s in suggestions if s.confidence >= 0.8]
            medium_conf = [s for s in suggestions if 0.6 <= s.confidence < 0.8]
            low_conf = [s for s in suggestions if s.confidence < 0.6]

            if high_conf:
                report.append("### High Confidence (>80%)")
                for suggestion in high_conf:
                    report.append(f"- **{suggestion.test_function}** in {Path(suggestion.file_path).name}")
                    report.append(f"  - Suggested: `{suggestion.suggested_marker}`")
                    report.append(".1f")
                    report.append(f"  - Reasoning: {suggestion.reasoning}")
                    report.append("")

            if medium_conf:
                report.append("### Medium Confidence (60-80%)")
                for suggestion in medium_conf:
                    report.append(f"- **{suggestion.test_function}** in {Path(suggestion.file_path).name}")
                    report.append(f"  - Suggested: `{suggestion.suggested_marker}`")
                    report.append(".1f")
                    report.append("")

            if low_conf:
                report.append("### Low Confidence (<60%)")
                for suggestion in low_conf:
                    report.append(f"- **{suggestion.test_function}** in {Path(suggestion.file_path).name}")
                    report.append(f"  - Suggested: `{suggestion.suggested_marker}`")
                    report.append(".1f")
                    report.append("")

        # Validation Issues
        if invalid_markers > 0:
            report.append("## Validation Issues")
            report.append("")

            for validation in validations:
                if not validation.is_valid:
                    report.append(f"### {validation.test_function}")
                    report.append(f"- **File**: {Path(validation.file_path).name}")
                    report.append(f"- **Current Marker**: `{validation.marker}`")
                    report.append("- **Issues**:")
                    for issue in validation.issues:
                        report.append(f"  - {issue}")
                    report.append("")

        # Recommendations
        report.append("## Recommendations")
        report.append("")
        report.append("### Immediate Actions")
        if total_suggestions > 0:
            report.append(f"- Review and apply {total_suggestions} marker suggestions")
        if invalid_markers > 0:
            report.append(f"- Fix {invalid_markers} invalid marker usages")
        report.append("")
        report.append("### Process Improvements")
        report.append("- Integrate marker validation into CI/CD pipeline")
        report.append("- Set up automated marker suggestion reviews")
        report.append("- Create marker usage guidelines documentation")
        report.append("")
        report.append("### Quality Gates")
        report.append("- Require marker validation before merge")
        report.append("- Automate marker compliance checks")
        report.append("- Monitor marker usage trends")

        return "\n".join(report)

    def apply_suggestion(self, suggestion: MarkerSuggestion) -> bool:
        """Apply a marker suggestion to the test file."""
        try:
            with open(suggestion.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the test function
            func_pattern = rf'(def {suggestion.test_function}\s*\()'
            match = re.search(func_pattern, content)

            if not match:
                return False

            func_start = match.start()
            # Look for existing decorators
            lines_before = content[:func_start].split('\n')
            decorator_lines = []

            # Find decorator lines (lines starting with @)
            for i in range(len(lines_before) - 1, max(-1, len(lines_before) - 10), -1):
                line = lines_before[i].strip()
                if line.startswith('@'):
                    decorator_lines.insert(0, line)
                elif line and not line.startswith('#'):
                    break

            # Add the marker
            marker_line = f"@pytest.mark.{suggestion.suggested_marker}"
            if marker_line not in decorator_lines:
                decorator_lines.insert(0, marker_line)

            # Reconstruct the content
            decorator_text = '\n'.join(decorator_lines)
            if decorator_text:
                decorator_text += '\n'

            new_content = (
                content[:func_start - len('\n'.join(lines_before[-len(decorator_lines):])) - 1] +
                decorator_text +
                content[func_start:]
            )

            with open(suggestion.file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return True

        except Exception as e:
            print(f"Error applying suggestion: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Maintain test marker compliance")
    parser.add_argument("--suggest-markers", action="store_true",
                       help="Generate marker suggestions for unmarked tests")
    parser.add_argument("--validate-markers", action="store_true",
                       help="Validate existing marker usage")
    parser.add_argument("--generate-report", action="store_true",
                       help="Generate maintenance report")
    parser.add_argument("--ci-check", action="store_true",
                       help="Run CI validation checks")
    parser.add_argument("--apply-suggestions", action="store_true",
                       help="Apply high-confidence marker suggestions")
    parser.add_argument("--file", type=str,
                       help="Process specific test file")
    parser.add_argument("--output", type=str, default="marker-maintenance-report.md",
                       help="Output file for reports")

    args = parser.parse_args()

    maintainer = TestMarkerMaintainer()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File {file_path} does not exist")
            sys.exit(1)

        if args.suggest_markers:
            suggestions = maintainer.suggest_markers_for_file(file_path)
            maintainer.suggestions.extend(suggestions)

        if args.validate_markers:
            validations = maintainer.validate_markers_in_file(file_path)
            maintainer.validations.extend(validations)

    else:
        # Process all test files
        backend_tests = Path("../backend/tests")
        frontend_tests = Path("../frontend/tests")

        test_dirs = []
        if backend_tests.exists():
            test_dirs.append(backend_tests)
        if frontend_tests.exists():
            test_dirs.append(frontend_tests)

        for test_dir in test_dirs:
            for test_file in test_dir.rglob('test_*.py'):
                if args.suggest_markers:
                    suggestions = maintainer.suggest_markers_for_file(test_file)
                    maintainer.suggestions.extend(suggestions)

                if args.validate_markers:
                    validations = maintainer.validate_markers_in_file(test_file)
                    maintainer.validations.extend(validations)

    # Apply suggestions if requested
    if args.apply_suggestions:
        applied_count = 0
        for suggestion in maintainer.suggestions:
            if suggestion.confidence >= 0.8:  # Only apply high-confidence suggestions
                if maintainer.apply_suggestion(suggestion):
                    applied_count += 1
                    print(f"Applied marker to {suggestion.test_function}")
                else:
                    print(f"Failed to apply marker to {suggestion.test_function}")

        print(f"Applied {applied_count} high-confidence marker suggestions")

    # Generate report
    if args.generate_report or args.suggest_markers or args.validate_markers:
        report = maintainer.generate_maintenance_report(
            maintainer.suggestions,
            maintainer.validations
        )

        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Maintenance report saved to {args.output}")

    # CI Check
    if args.ci_check:
        invalid_count = len([v for v in maintainer.validations if not v.is_valid])
        unmarked_count = len(maintainer.suggestions)

        if invalid_count > 0 or unmarked_count > 0:
            print(f"❌ CI Check Failed: {invalid_count} invalid markers, {unmarked_count} unmarked tests")
            print("See marker-maintenance-report.md for details")
            sys.exit(1)
        else:
            print("✅ CI Check Passed: All markers are valid and properly applied")
            sys.exit(0)

    # Print summary
    if maintainer.suggestions or maintainer.validations:
        print("\nSummary:")
        print(f"  Suggestions generated: {len(maintainer.suggestions)}")
        print(f"  Validations performed: {len(maintainer.validations)}")
        invalid_count = len([v for v in maintainer.validations if not v.is_valid])
        print(f"  Invalid markers found: {invalid_count}")

if __name__ == "__main__":
    main()
