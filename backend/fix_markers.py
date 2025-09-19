#!/usr/bin/env python3
"""
Script to automatically add missing test classification markers.
"""

import os
import re
import glob

def find_unmarked_tests():
    """Find test functions that don't have classification markers."""
    test_files = glob.glob("tests/**/*.py", recursive=True)

    unmarked = []

    for test_file in test_files:
        if "__pycache__" in test_file or not test_file.endswith(".py"):
            continue

        try:
            with open(test_file, 'r') as f:
                content = f.read()

            # Find test functions
            test_functions = re.findall(r'def (test_\w+)', content)

            for func in test_functions:
                # Check if the function has a marker before it
                pattern = rf'@pytest\.mark\.(mock_data|real_data|external_service)\s*\n\s*def {func}'
                if not re.search(pattern, content):
                    unmarked.append((test_file, func))

        except Exception as e:
            print(f"Error processing {test_file}: {e}")

    return unmarked

def add_markers_to_file(file_path, default_marker="mock_data"):
    """Add markers to unmarked test functions in a file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Find test functions without markers
        # Pattern to match test functions that don't have markers above them
        pattern = r'(\s*)(def (test_\w+)\([^)]*\):)'

        def replace_func(match):
            indent = match.group(1)
            func_def = match.group(2)
            func_name = match.group(3)

            # Check if there's already a marker above this function
            lines_before = content[:match.start()].split('\n')
            if lines_before and '@pytest.mark.' in lines_before[-1]:
                return match.group(0)  # Already has a marker

            # Determine appropriate marker based on function name and context
            if 'import' in func_name or 'library' in func_name or 'external' in func_name:
                marker = "external_service"
            elif 'db' in func_name or 'database' in func_name or 'real' in func_name:
                marker = "real_data"
            else:
                marker = default_marker

            return f"{indent}@pytest.mark.{marker}\n{indent}{func_def}"

        # Apply the replacement
        new_content = re.sub(pattern, replace_func, content)

        # Only write if content changed
        if new_content != content:
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"Updated {file_path}")
            return True

    except Exception as e:
        print(f"Error updating {file_path}: {e}")

    return False

def main():
    print("Finding unmarked test functions...")
    unmarked = find_unmarked_tests()

    print(f"Found {len(unmarked)} unmarked test functions")

    if not unmarked:
        print("All tests have classification markers!")
        return

    # Group by file
    files_to_update = {}
    for file_path, func_name in unmarked:
        if file_path not in files_to_update:
            files_to_update[file_path] = []
        files_to_update[file_path].append(func_name)

    print(f"\nUpdating {len(files_to_update)} files...")

    updated_count = 0
    for file_path in files_to_update:
        if add_markers_to_file(file_path):
            updated_count += 1

    print(f"\nUpdated {updated_count} files with missing markers")

if __name__ == "__main__":
    main()