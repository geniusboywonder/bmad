#!/usr/bin/env python3
"""
MEDIUM Priority Mock Analysis

Analyzes MEDIUM priority mocking patterns to identify which files actually
need fixes vs which have appropriate mocking patterns.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def analyze_medium_priority_files():
    """Analyze MEDIUM priority mocking patterns."""
    test_dir = Path("tests")

    # MEDIUM priority patterns to analyze
    patterns = {
        'celery_tasks': {
            'patterns': [
                r'@patch.*celery', r'mock.*task', r'task.*mock',
                r'patch.*delay', r'mock.*apply_async', r'celery.*Mock'
            ],
            'severity': 'MEDIUM',
            'description': 'Celery task mocking - may hide task execution issues'
        },
        'generic_mocks': {
            'patterns': [
                r'Mock\(\)', r'MagicMock\(\)', r'AsyncMock\(\)',
                r'mock = Mock', r'mock = MagicMock'
            ],
            'severity': 'MEDIUM',
            'description': 'Generic mocks - need investigation'
        },
        'return_value_mocks': {
            'patterns': [
                r'\.return_value\s*=', r'\.side_effect\s*=',
                r'return_value\s*=.*Mock'
            ],
            'severity': 'MEDIUM',
            'description': 'Mock return values - check if internal vs external'
        }
    }

    results = defaultdict(lambda: defaultdict(int))
    file_details = defaultdict(lambda: defaultdict(list))

    for test_file in test_dir.rglob("test_*.py"):
        try:
            content = test_file.read_text()
            file_rel = str(test_file.relative_to(Path('.')))

            for category, config in patterns.items():
                for pattern in config['patterns']:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    if matches:
                        results[category][file_rel] += len(matches)

                        # Get context around matches
                        for match in matches[:3]:  # Top 3 examples
                            line_num = content[:match.start()].count('\n') + 1
                            line_start = content.rfind('\n', 0, match.start()) + 1
                            line_end = content.find('\n', match.end())
                            if line_end == -1:
                                line_end = len(content)
                            context_line = content[line_start:line_end].strip()

                            file_details[category][file_rel].append({
                                'line': line_num,
                                'context': context_line[:100],  # Limit context length
                                'pattern': match.group()
                            })

        except Exception as e:
            continue

    return results, file_details, patterns

def categorize_by_appropriateness(file_details):
    """Categorize files by whether their mocking is appropriate or problematic."""

    appropriate_patterns = [
        # External dependencies that should be mocked
        r'celery\.task', r'celery\.delay', r'apply_async',  # External Celery
        r'requests\.', r'httpx\.', r'aiohttp\.',  # External HTTP
        r'openai\.', r'anthropic\.', r'autogen\.',  # External APIs
        r'pathlib\.Path', r'builtins\.open',  # File system
        r'websocket_manager',  # External WebSocket
    ]

    problematic_patterns = [
        # Internal business logic that shouldn't be mocked
        r'app\.services\.', r'app\.models\.', r'app\.database\.',
        r'OrchestratorCore', r'ProjectLifecycleManager',
        r'AgentCoordinator', r'WorkflowIntegrator',
        r'Mock\(\).*service', r'MagicMock\(\).*service'
    ]

    categorized = {
        'appropriate': defaultdict(list),
        'problematic': defaultdict(list),
        'needs_investigation': defaultdict(list)
    }

    for category, files in file_details.items():
        for file_path, details in files.items():
            file_content = ""
            try:
                file_content = Path(file_path).read_text()
            except:
                continue

            is_appropriate = False
            is_problematic = False

            # Check if mocking appears to be external dependencies
            for pattern in appropriate_patterns:
                if re.search(pattern, file_content, re.IGNORECASE):
                    is_appropriate = True
                    break

            # Check if mocking appears to be internal services
            for pattern in problematic_patterns:
                if re.search(pattern, file_content, re.IGNORECASE):
                    is_problematic = True
                    break

            if is_problematic:
                categorized['problematic'][category].append({
                    'file': file_path,
                    'details': details,
                    'reason': 'Mocks internal business logic'
                })
            elif is_appropriate:
                categorized['appropriate'][category].append({
                    'file': file_path,
                    'details': details,
                    'reason': 'Mocks external dependencies'
                })
            else:
                categorized['needs_investigation'][category].append({
                    'file': file_path,
                    'details': details,
                    'reason': 'Unclear - needs manual review'
                })

    return categorized

def main():
    print("🔍 MEDIUM PRIORITY MOCK ANALYSIS")
    print("=" * 50)
    print("Analyzing Celery, Generic, and Return Value mocks...")
    print()

    results, file_details, patterns = analyze_medium_priority_files()
    categorized = categorize_by_appropriateness(file_details)

    # Summary by category
    print("📊 MEDIUM PRIORITY CATEGORIES")
    print("-" * 30)
    for category, files in results.items():
        total_files = len(files)
        total_instances = sum(files.values())
        print(f"{category.replace('_', ' ').title()}: {total_files} files, {total_instances} instances")
    print()

    # Detailed analysis by appropriateness
    print("🎯 APPROPRIATENESS ANALYSIS")
    print("-" * 30)

    for appropriateness, categories in categorized.items():
        if not categories:
            continue

        emoji = {
            'appropriate': '✅',
            'problematic': '🚨',
            'needs_investigation': '🔍'
        }[appropriateness]

        print(f"\n{emoji} {appropriateness.upper().replace('_', ' ')}")

        for category, files in categories.items():
            if files:
                print(f"  📂 {category.replace('_', ' ').title()}: {len(files)} files")
                for item in files[:5]:  # Top 5 files
                    print(f"    📁 {item['file']}")
                    print(f"       Reason: {item['reason']}")
                    if item['details']:
                        example = item['details'][0]
                        print(f"       Example: Line {example['line']}: {example['context'][:60]}...")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more files")
                print()

    # Priority recommendations
    problematic_count = sum(len(files) for files in categorized['problematic'].values())
    needs_investigation_count = sum(len(files) for files in categorized['needs_investigation'].values())

    print("🎯 PRIORITY ACTIONS")
    print("-" * 20)
    if problematic_count > 0:
        print(f"🚨 HIGH: Fix {problematic_count} files with problematic internal service mocking")
    if needs_investigation_count > 0:
        print(f"🔍 MEDIUM: Investigate {needs_investigation_count} files requiring manual review")

    appropriate_count = sum(len(files) for files in categorized['appropriate'].values())
    print(f"✅ GOOD: {appropriate_count} files have appropriate external dependency mocking")
    print()

    print("💡 RECOMMENDATIONS")
    print("-" * 20)
    print("1. Focus on 🚨 PROBLEMATIC files first - these hide business logic issues")
    print("2. Review 🔍 NEEDS INVESTIGATION files - may need case-by-case decisions")
    print("3. Leave ✅ APPROPRIATE files as-is - external dependency mocking is correct")
    print("4. For Celery mocks: Consider integration tests with real Celery workers")
    print("5. For generic mocks: Replace with specific real instances where possible")

    return problematic_count

if __name__ == "__main__":
    exit(main())