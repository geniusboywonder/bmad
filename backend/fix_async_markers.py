#!/usr/bin/env python3
"""
Script to fix async decorator syntax errors.
"""

import os
import re
import glob

def fix_async_markers():
    """Fix async decorator syntax errors in test files."""
    test_files = glob.glob("tests/**/*.py", recursive=True)

    for test_file in test_files:
        if "__pycache__" in test_file:
            continue

        try:
            with open(test_file, 'r') as f:
                content = f.read()

            original_content = content

            # Fix pattern: async @pytest.mark.marker\n def function
            content = re.sub(r'(\s*)async (@pytest\.mark\.\w+)\s*\n(\s*)(def\s+)', r'\1\2\n\1async \4', content)

            # Fix pattern: async @pytest.mark.marker\n def function (single line)
            content = re.sub(r'(\s*)async (@pytest\.mark\.\w+)\s+(def\s+)', r'\1\2\n\1async \3', content)

            if content != original_content:
                with open(test_file, 'w') as f:
                    f.write(content)
                print(f"Fixed {test_file}")

        except Exception as e:
            print(f"Error processing {test_file}: {e}")

if __name__ == "__main__":
    fix_async_markers()