#!/usr/bin/env python3
"""
Script to clean up duplicate test markers.
"""

import os
import re
import glob

def clean_duplicate_markers():
    """Clean up duplicate test markers in test files."""
    test_files = glob.glob("tests/**/*.py", recursive=True)

    for test_file in test_files:
        if "__pycache__" in test_file:
            continue

        try:
            with open(test_file, 'r') as f:
                content = f.read()

            original_content = content

            # Remove duplicate consecutive markers
            content = re.sub(r'(@pytest\.mark\.\w+)\s*\n\s*\1', r'\1', content)

            # Clean up empty lines that might have been left
            content = re.sub(r'\n\s*\n\s*\n', r'\n\n', content)

            if content != original_content:
                with open(test_file, 'w') as f:
                    f.write(content)
                print(f"Cleaned {test_file}")

        except Exception as e:
            print(f"Error processing {test_file}: {e}")

if __name__ == "__main__":
    clean_duplicate_markers()