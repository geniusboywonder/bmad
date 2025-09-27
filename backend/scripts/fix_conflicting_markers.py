#!/usr/bin/env python3
"""
Fix conflicting pytest markers in test files.

This script identifies and resolves conflicting @pytest.mark.mock_data and
@pytest.mark.real_data markers based on content analysis.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple


def find_conflicting_markers(file_path: str) -> List[Dict]:
    """Find test functions with conflicting markers."""
    with open(file_path, 'r') as f:
        content = f.read()

    conflicts = []

    # Pattern to match test functions with their decorators
    func_pattern = r'(\s*@pytest\.mark\.[^\n]*\n)*(\s*)def (test_[^(]+)\([^)]*\):'

    matches = re.finditer(func_pattern, content, re.MULTILINE)

    for match in matches:
        decorators = match.group(1) or ''
        func_name = match.group(3)
        line_num = content[:match.start()].count('\n') + 1

        # Check for conflicting markers
        has_mock_data = '@pytest.mark.mock_data' in decorators
        has_real_data = '@pytest.mark.real_data' in decorators

        if has_mock_data and has_real_data:
            conflicts.append({
                'function': func_name,
                'line': line_num,
                'decorators': decorators.strip()
            })

    return conflicts


def analyze_function_content(file_path: str, func_name: str) -> str:
    """Analyze function content to determine appropriate marker."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Find the function and extract its content
    func_pattern = rf'def {re.escape(func_name)}\([^)]*\):(.*?)(?=\n\s*def|\n\s*class|\Z)'
    match = re.search(func_pattern, content, re.DOTALL)

    if not match:
        return 'mock_data'  # Default fallback

    func_content = match.group(1)

    # Analyze content for indicators
    real_data_indicators = [
        'db_session', 'DatabaseTestManager', 'session.add', 'session.commit',
        'session.query', 'TestingSessionLocal', 'real_database', 'use_memory_db',
        'setup_test_database', 'create_test_project', 'create_test_task'
    ]

    mock_indicators = [
        'Mock(', 'AsyncMock(', '@patch', 'mock_', 'return_value', 'side_effect',
        'MagicMock', 'spec='
    ]

    real_score = sum(1 for indicator in real_data_indicators if indicator in func_content)
    mock_score = sum(1 for indicator in mock_indicators if indicator in func_content)

    # Decision logic
    if real_score > mock_score:
        return 'real_data'
    else:
        return 'mock_data'


def fix_conflicting_markers_in_file(file_path: str) -> int:
    """Fix conflicting markers in a single file."""
    conflicts = find_conflicting_markers(file_path)

    if not conflicts:
        return 0

    print(f"\nFixing conflicts in {file_path}:")

    with open(file_path, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    changes_made = 0

    for conflict in conflicts:
        func_name = conflict['function']
        recommended_marker = analyze_function_content(file_path, func_name)

        print(f"  - {func_name}: Using @pytest.mark.{recommended_marker}")

        # Find and fix the conflicting markers
        for i, line in enumerate(lines):
            if f'def {func_name}(' in line:
                # Look backwards for markers
                j = i - 1
                while j >= 0 and ('@pytest.mark.' in lines[j] or lines[j].strip() == ''):
                    if '@pytest.mark.mock_data' in lines[j] or '@pytest.mark.real_data' in lines[j]:
                        # Remove both conflicting markers
                        if '@pytest.mark.mock_data' in lines[j]:
                            lines[j] = lines[j].replace('@pytest.mark.mock_data', '').strip()
                        if '@pytest.mark.real_data' in lines[j]:
                            lines[j] = lines[j].replace('@pytest.mark.real_data', '').strip()

                        # If line becomes empty, remove it
                        if not lines[j].strip():
                            lines[j] = ''
                    j -= 1

                # Add the correct marker before the function
                indent = len(line) - len(line.lstrip())
                marker_line = ' ' * indent + f'@pytest.mark.{recommended_marker}'
                lines.insert(i, marker_line)
                changes_made += 1
                break

    if changes_made > 0:
        # Write the fixed content back
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))

    return changes_made


def main():
    """Main function to fix conflicting markers across all test files."""
    print("🔧 FIXING CONFLICTING PYTEST MARKERS")
    print("=" * 50)

    backend_dir = Path(__file__).parent.parent
    test_files = list(backend_dir.glob("tests/**/*.py"))

    total_fixed = 0
    files_fixed = 0

    for test_file in test_files:
        if test_file.name.startswith('test_'):
            fixed_count = fix_conflicting_markers_in_file(str(test_file))
            if fixed_count > 0:
                total_fixed += fixed_count
                files_fixed += 1

    print(f"\n✅ SUMMARY")
    print(f"Files processed: {len([f for f in test_files if f.name.startswith('test_')])}")
    print(f"Files with conflicts fixed: {files_fixed}")
    print(f"Total conflicts resolved: {total_fixed}")

    if total_fixed > 0:
        print("\n🧪 Next step: Run pytest to verify fixes")
        print("   python -m pytest tests/unit/ --tb=short -q")


if __name__ == '__main__':
    main()