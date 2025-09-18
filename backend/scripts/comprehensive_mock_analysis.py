#!/usr/bin/env python3
"""
Comprehensive Mock Analysis Tool

Analyzes ALL types of mocking in the test suite to identify tests that may need to be fixed,
not just database-related mocks.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class ComprehensiveMockAnalyzer:
    """Analyzes all types of mocking patterns in test files."""

    def __init__(self, test_directory: str):
        self.test_directory = Path(test_directory)

        # Define different categories of mocking patterns
        self.mock_categories = {
            'database_mocks': {
                'patterns': [
                    r'patch.*get_session', r'mock.*session', r'Session.*mock',
                    r'mock_db', r'db.*Mock', r'@patch.*database',
                    r'mock.*query', r'session\.add.*mock', r'session\.commit.*mock'
                ],
                'severity': 'CRITICAL',
                'description': 'Database session/query mocking - hides schema issues'
            },

            'service_layer_mocks': {
                'patterns': [
                    r'@patch.*service', r'mock.*service', r'Service.*Mock',
                    r'patch.*orchestrator', r'mock.*orchestrator',
                    r'patch.*workflow', r'mock.*workflow'
                ],
                'severity': 'HIGH',
                'description': 'Service layer mocking - may hide business logic issues'
            },

            'api_endpoint_mocks': {
                'patterns': [
                    r'@patch.*api', r'mock.*endpoint', r'patch.*router',
                    r'mock.*request', r'patch.*FastAPI', r'TestClient.*mock'
                ],
                'severity': 'HIGH',
                'description': 'API endpoint mocking - bypasses actual request handling'
            },

            'celery_task_mocks': {
                'patterns': [
                    r'@patch.*celery', r'mock.*task', r'task.*mock',
                    r'patch.*delay', r'mock.*apply_async', r'celery.*Mock'
                ],
                'severity': 'MEDIUM',
                'description': 'Celery task mocking - may hide task execution issues'
            },

            'external_http_mocks': {
                'patterns': [
                    r'@patch.*requests', r'mock.*http', r'patch.*httpx',
                    r'mock.*get', r'mock.*post', r'requests.*Mock',
                    r'aiohttp.*mock', r'httpx.*Mock'
                ],
                'severity': 'LOW',
                'description': 'External HTTP mocking - appropriate for external services'
            },

            'file_system_mocks': {
                'patterns': [
                    r'@patch.*open', r'mock.*file', r'patch.*Path',
                    r'mock.*read', r'mock.*write', r'patch.*os\.',
                    r'patch.*pathlib', r'mock.*exists'
                ],
                'severity': 'LOW',
                'description': 'File system mocking - appropriate for file operations'
            },

            'time_mocks': {
                'patterns': [
                    r'@patch.*time', r'mock.*datetime', r'freezegun',
                    r'patch.*now', r'mock.*sleep', r'time.*Mock'
                ],
                'severity': 'LOW',
                'description': 'Time mocking - appropriate for time-dependent tests'
            },

            'llm_model_mocks': {
                'patterns': [
                    r'mock.*llm', r'patch.*openai', r'mock.*gpt',
                    r'patch.*anthropic', r'mock.*claude', r'ai.*Mock',
                    r'mock.*chat', r'patch.*completion'
                ],
                'severity': 'LOW',
                'description': 'LLM/AI model mocking - appropriate for AI service calls'
            },

            'generic_mocks': {
                'patterns': [
                    r'Mock\(\)', r'MagicMock\(\)', r'AsyncMock\(\)',
                    r'mock = Mock', r'mock = MagicMock'
                ],
                'severity': 'MEDIUM',
                'description': 'Generic mocks - need investigation to determine appropriateness'
            },

            'return_value_mocks': {
                'patterns': [
                    r'\.return_value\s*=', r'\.side_effect\s*=',
                    r'return_value\s*=.*Mock'
                ],
                'severity': 'MEDIUM',
                'description': 'Mock return values - check if mocking internal vs external'
            }
        }

        self.results = defaultdict(list)

    def analyze_all_tests(self) -> Dict[str, any]:
        """Analyze all test files for different types of mocking."""
        test_files = list(self.test_directory.rglob("test_*.py"))

        analysis_results = {
            'summary': {
                'total_files': len(test_files),
                'files_with_mocks': 0,
                'category_breakdown': defaultdict(int),
                'severity_breakdown': defaultdict(int)
            },
            'by_category': defaultdict(list),
            'by_severity': defaultdict(list),
            'problematic_files': [],
            'recommendations': []
        }

        for test_file in test_files:
            file_analysis = self.analyze_file(test_file)

            if file_analysis['has_mocks']:
                analysis_results['summary']['files_with_mocks'] += 1

                # Categorize by mock types
                for category, details in file_analysis['mock_categories'].items():
                    if details['count'] > 0:
                        analysis_results['summary']['category_breakdown'][category] += 1
                        analysis_results['by_category'][category].append({
                            'file': file_analysis['file'],
                            'count': details['count'],
                            'examples': details['examples'][:3]  # Top 3 examples
                        })

                        # Track by severity
                        severity = self.mock_categories[category]['severity']
                        analysis_results['summary']['severity_breakdown'][severity] += 1

                        analysis_results['by_severity'][severity].append({
                            'file': file_analysis['file'],
                            'category': category,
                            'count': details['count'],
                            'description': self.mock_categories[category]['description']
                        })

        # Generate recommendations
        analysis_results['recommendations'] = self.generate_comprehensive_recommendations(analysis_results)

        return analysis_results

    def analyze_file(self, file_path: Path) -> Dict[str, any]:
        """Analyze a single test file for all types of mocking."""
        try:
            content = file_path.read_text()
        except Exception as e:
            return {'error': str(e), 'has_mocks': False}

        file_analysis = {
            'file': str(file_path.relative_to(self.test_directory)),
            'has_mocks': False,
            'total_mock_patterns': 0,
            'mock_categories': {}
        }

        # Analyze each category of mocks
        for category, config in self.mock_categories.items():
            category_analysis = {
                'count': 0,
                'examples': [],
                'line_numbers': []
            }

            for pattern in config['patterns']:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                category_analysis['count'] += len(matches)

                for match in matches:
                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1
                    category_analysis['line_numbers'].append(line_num)
                    category_analysis['examples'].append(f"Line {line_num}: {match.group()}")

            file_analysis['mock_categories'][category] = category_analysis
            file_analysis['total_mock_patterns'] += category_analysis['count']

            if category_analysis['count'] > 0:
                file_analysis['has_mocks'] = True

        return file_analysis

    def generate_comprehensive_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on comprehensive analysis."""
        recommendations = []

        # Critical issues first
        if results['summary']['severity_breakdown']['CRITICAL'] > 0:
            recommendations.extend([
                "🚨 CRITICAL: Database mocking detected - replace with real database tests immediately",
                "📊 Use DatabaseTestManager for real PostgreSQL operations",
                "🔧 Replace @patch('get_session') with db_manager.get_session()",
                "✅ Validate database state after operations instead of mock assertions"
            ])

        # High priority issues
        if results['summary']['severity_breakdown']['HIGH'] > 0:
            recommendations.extend([
                "⚠️  HIGH PRIORITY: Service layer and API endpoint mocking found",
                "🔄 Replace service mocks with real service instances where possible",
                "🌐 Use TestClient for actual API endpoint testing",
                "📝 Keep mocks only for external dependencies"
            ])

        # Category-specific recommendations
        if 'celery_task_mocks' in results['by_category'] and results['by_category']['celery_task_mocks']:
            recommendations.append(
                "📋 CELERY: Consider testing actual task execution in integration tests"
            )

        if 'generic_mocks' in results['by_category'] and results['by_category']['generic_mocks']:
            recommendations.append(
                "🔍 GENERIC MOCKS: Review generic Mock() usage - specify what's being mocked"
            )

        # General recommendations
        recommendations.extend([
            "📊 PRINCIPLE: Mock external dependencies, test internal logic with real implementations",
            "🎯 PRIORITY ORDER: Fix CRITICAL → HIGH → MEDIUM severity mocks",
            "📈 MIGRATION: Create real tests alongside mocks, then remove mocks gradually",
            "✅ VALIDATION: Use schema validation tools after replacing database mocks"
        ])

        return recommendations

    def find_specific_antipatterns(self) -> Dict[str, List[str]]:
        """Find specific anti-patterns that should definitely be fixed."""
        antipatterns = {
            'business_logic_mocks': [],
            'internal_api_mocks': [],
            'database_constraint_bypassing': [],
            'cascading_mocks': []
        }

        for test_file in self.test_directory.rglob("test_*.py"):
            try:
                content = test_file.read_text()
                file_rel = str(test_file.relative_to(self.test_directory))

                # Business logic mocking
                if re.search(r'patch.*business|mock.*logic|patch.*service.*core', content, re.IGNORECASE):
                    antipatterns['business_logic_mocks'].append(file_rel)

                # Internal API mocking
                if re.search(r'patch.*app\.api|mock.*internal.*api|patch.*router', content, re.IGNORECASE):
                    antipatterns['internal_api_mocks'].append(file_rel)

                # Database constraint bypassing
                if re.search(r'mock.*constraint|patch.*foreign.*key|mock.*relationship', content, re.IGNORECASE):
                    antipatterns['database_constraint_bypassing'].append(file_rel)

                # Cascading mocks (too many mocks in one test)
                mock_count = len(re.findall(r'@patch|Mock\(|mock\.|\.mock', content, re.IGNORECASE))
                if mock_count > 10:  # Arbitrary threshold
                    antipatterns['cascading_mocks'].append(f"{file_rel} ({mock_count} mocks)")

            except Exception:
                continue

        return antipatterns


def main():
    """Main function to run comprehensive mock analysis."""
    print("🔍 COMPREHENSIVE MOCK ANALYSIS")
    print("=" * 60)
    print("Analyzing ALL types of mocking in the test suite...")
    print()

    analyzer = ComprehensiveMockAnalyzer("tests")
    results = analyzer.analyze_all_tests()

    # Summary
    summary = results['summary']
    print("📊 OVERALL SUMMARY")
    print("-" * 20)
    print(f"Total test files: {summary['total_files']}")
    if summary['total_files'] > 0:
        print(f"Files with mocks: {summary['files_with_mocks']} ({(summary['files_with_mocks']/summary['total_files']*100):.1f}%)")
    else:
        print(f"Files with mocks: {summary['files_with_mocks']} (0 total files found)")
    print()

    # Severity breakdown
    print("🚨 BY SEVERITY LEVEL")
    print("-" * 20)
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        count = summary['severity_breakdown'][severity]
        if count > 0:
            emoji = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '🔶', 'LOW': '🟡'}[severity]
            print(f"{emoji} {severity}: {count} files")
    print()

    # Category breakdown
    print("📋 BY MOCK CATEGORY")
    print("-" * 20)
    for category, count in summary['category_breakdown'].items():
        if count > 0:
            description = analyzer.mock_categories[category]['description']
            severity = analyzer.mock_categories[category]['severity']
            print(f"  {category.replace('_', ' ').title()}: {count} files ({severity})")
            print(f"    └─ {description}")
    print()

    # Issues by severity
    print("🚨 ISSUES BY SEVERITY")
    print("-" * 35)
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if severity in results['by_severity']:
            print(f"\n{severity} SEVERITY:")
            for issue in results['by_severity'][severity]:
                print(f"  📁 {issue['file']}")
                print(f"    Category: {issue['category'].replace('_', ' ').title()}")
                print(f"    Count: {issue['count']} instances")
                print(f"    Issue: {issue['description']}")
                print()

    # Anti-patterns
    antipatterns = analyzer.find_specific_antipatterns()
    if any(antipatterns.values()):
        print("🚩 SPECIFIC ANTI-PATTERNS FOUND")
        print("-" * 30)
        for pattern_type, files in antipatterns.items():
            if files:
                print(f"  {pattern_type.replace('_', ' ').title()}:")
                for file in files[:5]:  # Top 5
                    print(f"    - {file}")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more")
                print()

    # Recommendations
    print("💡 COMPREHENSIVE RECOMMENDATIONS")
    print("-" * 35)
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"  {i}. {rec}")
    print()

    # Priority action items
    print("🎯 IMMEDIATE ACTION ITEMS")
    print("-" * 25)
    critical_count = summary['severity_breakdown']['CRITICAL']
    high_count = summary['severity_breakdown']['HIGH']

    if critical_count > 0:
        print(f"  1. 🚨 URGENT: Fix {critical_count} CRITICAL database mocking files")
        print("     → Replace with real database tests using DatabaseTestManager")

    if high_count > 0:
        print(f"  2. ⚠️  HIGH: Review {high_count} service/API mocking files")
        print("     → Replace with real service instances where appropriate")

    medium_count = summary['severity_breakdown']['MEDIUM']
    if medium_count > 0:
        print(f"  3. 🔶 MEDIUM: Investigate {medium_count} generic/return value mocking files")
        print("     → Determine if mocking internal vs external dependencies")

    print()
    print("📈 Next step: Review the detailed file listings above and prioritize fixes")
    print("🔧 Use the existing real database testing infrastructure for replacements")

    return 1 if critical_count > 0 or high_count > 0 else 0


if __name__ == "__main__":
    exit(main())