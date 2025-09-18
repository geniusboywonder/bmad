#!/usr/bin/env python3
"""
Automatically Add Test Markers to Existing Test Files

This script analyzes existing test files and adds appropriate @pytest.mark.mock_data
or @pytest.mark.real_data markers based on the test content.
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Set


class TestMarkerAnalyzer:
    """Analyzes test files to determine appropriate markers."""

    def __init__(self, tests_directory: str):
        self.tests_directory = Path(tests_directory)
        self.mock_indicators = {
            'mock', 'Mock', 'MagicMock', 'AsyncMock', '@patch', 'patch(',
            'mock_db', 'mock_session', 'Mock()', 'return_value', 'side_effect'
        }
        self.real_db_indicators = {
            'db_manager', 'get_session', 'session.add', 'session.commit',
            'DatabaseTestManager', 'real_database', '_real_db', 'session.query'
        }
        self.external_service_indicators = {
            'mock_smtp', 'mock_redis', 'mock_http', 'mock_api', 'mock_file',
            'requests', 'httpx', 'aiofiles', 'smtplib'
        }

    def analyze_test_file(self, file_path: Path) -> Dict[str, any]:
        """Analyze a test file to determine appropriate markers."""
        try:
            content = file_path.read_text()
        except Exception as e:
            return {'error': str(e)}

        analysis = {
            'file': str(file_path.relative_to(self.tests_directory)),
            'has_mock_indicators': False,
            'has_real_db_indicators': False,
            'has_external_service_indicators': False,
            'mock_count': 0,
            'real_db_count': 0,
            'external_service_count': 0,
            'functions': [],
            'needs_markers': True
        }

        # Check if file already has classification markers
        if '@pytest.mark.mock_data' in content or '@pytest.mark.real_data' in content:
            analysis['needs_markers'] = False
            return analysis

        # Count indicators
        for indicator in self.mock_indicators:
            count = content.count(indicator)
            analysis['mock_count'] += count
            if count > 0:
                analysis['has_mock_indicators'] = True

        for indicator in self.real_db_indicators:
            count = content.count(indicator)
            analysis['real_db_count'] += count
            if count > 0:
                analysis['has_real_db_indicators'] = True

        for indicator in self.external_service_indicators:
            count = content.count(indicator)
            analysis['external_service_count'] += count
            if count > 0:
                analysis['has_external_service_indicators'] = True

        # Extract test functions
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    function_analysis = self._analyze_function(node, content)
                    analysis['functions'].append(function_analysis)
        except:
            pass  # Continue even if AST parsing fails

        # Determine primary classification
        if analysis['real_db_count'] > analysis['mock_count']:
            analysis['primary_classification'] = 'real_data'
        elif analysis['mock_count'] > 0:
            analysis['primary_classification'] = 'mock_data'
        else:
            analysis['primary_classification'] = 'mock_data'  # Default to mock for safety

        return analysis

    def _analyze_function(self, func_node: ast.FunctionDef, content: str) -> Dict[str, any]:
        """Analyze individual test function."""
        func_start = func_node.lineno
        func_end = func_node.end_lineno if hasattr(func_node, 'end_lineno') else func_start + 10

        # Get function content
        lines = content.split('\n')
        func_content = '\n'.join(lines[func_start-1:func_end])

        # Check for specific patterns
        has_mock = any(indicator in func_content for indicator in self.mock_indicators)
        has_real_db = any(indicator in func_content for indicator in self.real_db_indicators)

        return {
            'name': func_node.name,
            'line': func_start,
            'has_mock': has_mock,
            'has_real_db': has_real_db
        }

    def add_markers_to_file(self, file_path: Path, analysis: Dict[str, any]) -> bool:
        """Add appropriate markers to a test file."""
        if not analysis.get('needs_markers', True):
            return False

        try:
            content = file_path.read_text()
            lines = content.split('\n')

            # Find test classes and functions to add markers
            modified_lines = []
            i = 0
            added_markers = False

            while i < len(lines):
                line = lines[i]

                # Check if this is a test function or class
                if self._is_test_function_or_class(line):
                    # Check if it already has markers
                    if not self._has_pytest_markers(modified_lines[-5:] if len(modified_lines) >= 5 else []):
                        # Add appropriate marker
                        indent = len(line) - len(line.lstrip())
                        marker = self._get_marker_for_content(line, lines[i:i+10])
                        marker_line = ' ' * indent + marker

                        modified_lines.append(marker_line)
                        added_markers = True

                modified_lines.append(line)
                i += 1

            if added_markers:
                # Write back to file
                file_path.write_text('\n'.join(modified_lines))
                return True

        except Exception as e:
            print(f"Error modifying {file_path}: {e}")

        return False

    def _is_test_function_or_class(self, line: str) -> bool:
        """Check if line contains a test function or class definition."""
        stripped = line.strip()
        return (stripped.startswith('def test_') or
                stripped.startswith('async def test_') or
                (stripped.startswith('class Test') and ':' in stripped))

    def _has_pytest_markers(self, recent_lines: List[str]) -> bool:
        """Check if recent lines contain pytest markers."""
        for line in recent_lines:
            if '@pytest.mark.' in line:
                return True
        return False

    def _get_marker_for_content(self, definition_line: str, following_lines: List[str]) -> str:
        """Determine appropriate marker based on content."""
        content = '\n'.join(following_lines[:20])  # Look ahead 20 lines

        # Check for specific patterns
        real_db_score = sum(1 for indicator in self.real_db_indicators if indicator in content)
        mock_score = sum(1 for indicator in self.mock_indicators if indicator in content)

        # Special cases
        if 'real_db' in definition_line.lower():
            return '@pytest.mark.real_data'
        elif 'mock' in definition_line.lower():
            return '@pytest.mark.mock_data'
        elif real_db_score > mock_score:
            return '@pytest.mark.real_data'
        else:
            return '@pytest.mark.mock_data'

    def generate_report(self) -> Dict[str, any]:
        """Generate comprehensive report of test classification."""
        test_files = list(self.tests_directory.rglob("test_*.py"))

        total_files = len(test_files)
        files_needing_markers = 0
        mock_files = 0
        real_db_files = 0
        mixed_files = 0

        detailed_analysis = []

        for test_file in test_files:
            analysis = self.analyze_test_file(test_file)
            if 'error' not in analysis:
                detailed_analysis.append(analysis)

                if analysis['needs_markers']:
                    files_needing_markers += 1

                if analysis.get('primary_classification') == 'mock_data':
                    mock_files += 1
                elif analysis.get('primary_classification') == 'real_data':
                    real_db_files += 1

                if analysis['has_mock_indicators'] and analysis['has_real_db_indicators']:
                    mixed_files += 1

        return {
            'summary': {
                'total_files': total_files,
                'files_needing_markers': files_needing_markers,
                'mock_files': mock_files,
                'real_db_files': real_db_files,
                'mixed_files': mixed_files
            },
            'detailed_analysis': detailed_analysis
        }


def main():
    """Main function to analyze and add markers to test files."""
    print("🏷️  TEST MARKER ANALYSIS AND APPLICATION")
    print("=" * 60)

    analyzer = TestMarkerAnalyzer("tests")
    report = analyzer.generate_report()

    # Print summary
    summary = report['summary']
    print(f"📊 SUMMARY")
    print(f"  Total test files: {summary['total_files']}")
    print(f"  Files needing markers: {summary['files_needing_markers']}")
    print(f"  Mock-heavy files: {summary['mock_files']}")
    print(f"  Real database files: {summary['real_db_files']}")
    print(f"  Mixed files: {summary['mixed_files']}")
    print()

    # Show files that need markers
    print("📋 FILES NEEDING MARKERS")
    print("-" * 30)
    files_modified = 0

    for analysis in report['detailed_analysis']:
        if analysis['needs_markers']:
            file_path = Path("tests") / analysis['file']
            print(f"  📁 {analysis['file']}")
            print(f"    Primary: {analysis.get('primary_classification', 'unknown')}")
            print(f"    Mock indicators: {analysis['mock_count']}")
            print(f"    Real DB indicators: {analysis['real_db_count']}")

            # Apply markers
            if analyzer.add_markers_to_file(file_path, analysis):
                print(f"    ✅ Markers added successfully")
                files_modified += 1
            else:
                print(f"    ⚠️  Could not add markers")
            print()

    print("🎯 RESULTS")
    print("-" * 10)
    print(f"Files modified: {files_modified}")
    print(f"Files still needing manual review: {summary['files_needing_markers'] - files_modified}")

    if files_modified > 0:
        print("\n✅ Test markers have been added!")
        print("📋 Next steps:")
        print("  1. Review the added markers for accuracy")
        print("  2. Run tests to ensure they still pass")
        print("  3. Manually adjust any incorrect classifications")
        print("  4. Consider creating real database alternatives for mock-heavy tests")

    return 0


if __name__ == "__main__":
    exit(main())