#!/usr/bin/env python3
"""
Mock Usage Analysis Tool

Analyzes the test suite to identify excessive mock usage and provides
recommendations for replacing mocks with real database tests.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class MockUsageAnalyzer:
    """Analyzes mock usage patterns in test files."""

    def __init__(self, test_directory: str):
        self.test_directory = Path(test_directory)
        self.mock_patterns = {
            'patch_decorators': r'@patch\([\'"]([^\'"]+)[\'"]\)',
            'patch_context': r'with patch\([\'"]([^\'"]+)[\'"]\)',
            'mock_imports': r'from unittest\.mock import.*',
            'mock_objects': r'Mock\(\)|MagicMock\(\)',
            'database_mocks': r'mock.*session|session.*mock|patch.*get_session',
        }
        self.results = defaultdict(list)

    def analyze_all_tests(self) -> Dict[str, any]:
        """Analyze all test files for mock usage."""
        test_files = list(self.test_directory.rglob("test_*.py"))

        total_files = len(test_files)
        mock_files = 0
        high_risk_files = []
        database_mock_files = []

        for test_file in test_files:
            analysis = self.analyze_file(test_file)
            if analysis['has_mocks']:
                mock_files += 1

            if analysis['risk_level'] == 'HIGH':
                high_risk_files.append({
                    'file': str(test_file.relative_to(self.test_directory)),
                    'issues': analysis['issues'],
                    'database_mocks': analysis['database_mocks']
                })

            if analysis['database_mocks']:
                database_mock_files.append(str(test_file.relative_to(self.test_directory)))

        return {
            'summary': {
                'total_test_files': total_files,
                'files_with_mocks': mock_files,
                'mock_percentage': round((mock_files / total_files) * 100, 1),
                'high_risk_files': len(high_risk_files),
                'files_with_database_mocks': len(database_mock_files)
            },
            'high_risk_files': high_risk_files,
            'database_mock_files': database_mock_files,
            'recommendations': self.generate_recommendations(high_risk_files)
        }

    def analyze_file(self, file_path: Path) -> Dict[str, any]:
        """Analyze a single test file for mock usage."""
        try:
            content = file_path.read_text()
        except Exception as e:
            return {'error': str(e), 'has_mocks': False, 'risk_level': 'LOW'}

        issues = []
        database_mocks = []
        mock_count = 0

        # Check for patch decorators
        patch_matches = re.findall(self.mock_patterns['patch_decorators'], content, re.IGNORECASE)
        for match in patch_matches:
            mock_count += 1
            if any(keyword in match.lower() for keyword in ['session', 'database', 'db']):
                database_mocks.append(f"@patch('{match}')")
                issues.append(f"Database session mocking: @patch('{match}')")

        # Check for patch context managers
        patch_context_matches = re.findall(self.mock_patterns['patch_context'], content, re.IGNORECASE)
        mock_count += len(patch_context_matches)

        # Check for Mock object usage
        mock_objects = len(re.findall(self.mock_patterns['mock_objects'], content))
        mock_count += mock_objects

        # Check for database-specific mocking patterns
        db_mock_matches = re.findall(self.mock_patterns['database_mocks'], content, re.IGNORECASE)
        database_mocks.extend(db_mock_matches)

        # Additional pattern checks
        if 'mock_db' in content.lower():
            issues.append("Generic database mocking (mock_db)")
            database_mocks.append("mock_db usage")

        if 'get_session' in content and 'patch' in content:
            issues.append("Database session patching")

        # Determine risk level
        risk_level = self.assess_risk_level(mock_count, len(database_mocks), issues)

        return {
            'has_mocks': mock_count > 0,
            'mock_count': mock_count,
            'database_mocks': database_mocks,
            'issues': issues,
            'risk_level': risk_level
        }

    def assess_risk_level(self, mock_count: int, db_mock_count: int, issues: List[str]) -> str:
        """Assess the risk level of mock usage in a file."""
        if db_mock_count > 0 or any('database' in issue.lower() for issue in issues):
            return 'HIGH'  # Database mocking is high risk
        elif mock_count > 10:
            return 'MEDIUM'  # Heavy mock usage
        elif mock_count > 0:
            return 'LOW'  # Some mock usage
        else:
            return 'NONE'  # No mocks

    def generate_recommendations(self, high_risk_files: List[Dict]) -> List[str]:
        """Generate recommendations for reducing mock usage."""
        recommendations = []

        if high_risk_files:
            recommendations.extend([
                "🚨 CRITICAL: Replace database session mocking with real PostgreSQL tests",
                "📊 Use DatabaseTestManager for real database operations",
                "🔧 Replace @patch('get_session') with db_manager.get_session()",
                "✅ Add database state verification after API calls",
                "🧪 Use APITestClient.post_and_verify_db() for end-to-end testing"
            ])

        total_db_files = len([f for f in high_risk_files if f['database_mocks']])
        if total_db_files > 5:
            recommendations.append(
                f"📈 Priority: {total_db_files} files have database mocking - start with most critical business logic"
            )

        recommendations.extend([
            "🎯 Keep mocks only for external dependencies (APIs, file system, email)",
            "🔄 Migration strategy: Create real DB tests alongside mocks, then remove mocks",
            "📝 Use tests/integration/test_replace_critical_mocks.py as reference",
            "⚡ Run schema validation after replacing mocks to catch hidden issues"
        ])

        return recommendations

    def find_specific_patterns(self) -> Dict[str, List[str]]:
        """Find specific problematic mock patterns."""
        patterns = {
            'session_mocking': [],
            'database_service_mocking': [],
            'generic_db_mocks': [],
            'celery_mocking': []
        }

        for test_file in self.test_directory.rglob("test_*.py"):
            try:
                content = test_file.read_text()
                file_rel = str(test_file.relative_to(self.test_directory))

                # Session mocking
                if re.search(r'patch.*get_session|mock.*session', content, re.IGNORECASE):
                    patterns['session_mocking'].append(file_rel)

                # Database service mocking
                if re.search(r'patch.*service.*db|mock.*database.*service', content, re.IGNORECASE):
                    patterns['database_service_mocking'].append(file_rel)

                # Generic database mocks
                if re.search(r'mock_db|Mock\(\).*db|db.*Mock\(\)', content, re.IGNORECASE):
                    patterns['generic_db_mocks'].append(file_rel)

                # Celery mocking
                if re.search(r'patch.*celery|mock.*task|task.*mock', content, re.IGNORECASE):
                    patterns['celery_mocking'].append(file_rel)

            except Exception:
                continue

        return patterns


def main():
    """Main analysis function."""
    analyzer = MockUsageAnalyzer("tests")
    results = analyzer.analyze_all_tests()
    patterns = analyzer.find_specific_patterns()

    print("🔍 MOCK USAGE ANALYSIS REPORT")
    print("=" * 50)

    # Summary
    summary = results['summary']
    print(f"📊 SUMMARY")
    print(f"  Total test files: {summary['total_test_files']}")
    print(f"  Files with mocks: {summary['files_with_mocks']} ({summary['mock_percentage']}%)")
    print(f"  High-risk files: {summary['high_risk_files']}")
    print(f"  Database mock files: {summary['files_with_database_mocks']}")
    print()

    # High-risk files
    if results['high_risk_files']:
        print("🚨 HIGH-RISK FILES (Database Mocking)")
        print("-" * 40)
        for file_info in results['high_risk_files'][:10]:  # Show top 10
            print(f"  📁 {file_info['file']}")
            for issue in file_info['issues'][:3]:  # Show top 3 issues
                print(f"    ⚠️  {issue}")
            print()

    # Specific patterns
    print("🎯 PROBLEMATIC PATTERNS")
    print("-" * 30)
    for pattern_name, files in patterns.items():
        if files:
            print(f"  {pattern_name.replace('_', ' ').title()}: {len(files)} files")
            for file in files[:3]:  # Show first 3 examples
                print(f"    - {file}")
            if len(files) > 3:
                print(f"    ... and {len(files) - 3} more")
            print()

    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 20)
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"  {i}. {rec}")
    print()

    # Next steps
    print("🚀 NEXT STEPS")
    print("-" * 15)
    print("  1. Run: python -m pytest tests/integration/test_full_stack_api_database_flow.py")
    print("  2. Replace high-risk database mocking files first")
    print("  3. Use DatabaseTestManager for new tests")
    print("  4. Run schema validation after each replacement")
    print("  5. Monitor test performance and adjust as needed")

    # Exit with warning if high-risk files found
    if results['high_risk_files']:
        print()
        print("⚠️  WARNING: Database mocking detected - schema issues may be hidden!")
        return 1
    else:
        print()
        print("✅ No high-risk database mocking found!")
        return 0


if __name__ == '__main__':
    exit(main())