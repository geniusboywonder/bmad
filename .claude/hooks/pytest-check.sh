#!/bin/bash

# Pytest Validation Hook (PostToolUse)
#
# Runs after Write/Edit operations on Python test files
# Executes pytest for the modified test file or related tests
#
# Behavior:
# - All tests pass: Silent (suppressOutput: true)
# - Tests fail: Reports failures to Claude via additionalContext

# Read JSON from stdin
input=$(cat)

# Extract file path from JSON
file_path=$(echo "$input" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('parameters', {}).get('file_path', ''))" 2>/dev/null)

# Check if file path exists
if [ -z "$file_path" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Only process .py files in backend directory
if [[ ! "$file_path" =~ \.py$ ]] || [[ ! "$file_path" =~ /backend/ ]]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip non-test files (only run for test files or app files)
# Test files: test_*.py or *_test.py
# App files: run related tests
if [[ ! "$file_path" =~ test_ ]] && [[ ! "$file_path" =~ _test\.py$ ]] && [[ ! "$file_path" =~ /app/ ]]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip __pycache__ and virtual environment directories
if [[ "$file_path" =~ __pycache__ ]] || [[ "$file_path" =~ /venv/ ]] || [[ "$file_path" =~ /.venv/ ]]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Find project root
project_root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
backend_dir="$project_root/backend"

# Change to backend directory
cd "$backend_dir" || exit 0

# Determine what tests to run
if [[ "$file_path" =~ test_ ]] || [[ "$file_path" =~ _test\.py$ ]]; then
  # If it's a test file, run only that test file
  test_target="$file_path"
else
  # If it's an app file, run all related tests (fast unit tests only)
  # Extract module name and find related test
  module_name=$(basename "$file_path" .py)
  test_target="tests/unit/test_${module_name}.py"

  # If related test doesn't exist, run all unit tests (fast)
  if [ ! -f "$test_target" ]; then
    test_target="tests/unit/"
  fi
fi

# Run pytest with timeout and capture output
# Use -x to stop on first failure for faster feedback
# Use -q for quiet output
# Use --tb=short for concise traceback
output=$(timeout 30s python3 -m pytest "$test_target" -v --tb=short 2>&1)
exit_code=$?

# Check if tests passed (exit code 0) or no tests were collected (exit code 5)
if [ $exit_code -eq 0 ] || [ $exit_code -eq 5 ]; then
  # Tests passed or no tests found - silent success
  echo '{"continue": true, "suppressOutput": true}'
elif [ $exit_code -eq 124 ]; then
  # Timeout occurred
  echo '{"continue": true, "additionalContext": "Pytest timed out after 30 seconds. Tests may be hanging or taking too long."}'
else
  # Tests failed - extract relevant information
  # Get failure summary
  failure_summary=$(echo "$output" | grep -A 20 "FAILED\|ERROR" | head -30)

  if [ -z "$failure_summary" ]; then
    failure_summary="$output"
  fi

  # Escape quotes and format for JSON
  error_msg=$(echo "$failure_summary" | sed 's/"/\\"/g' | sed 's/$/\\n/' | tr -d '\n')

  echo "{\"continue\": true, \"additionalContext\": \"Pytest failed:\\n\\n$error_msg\\n\\nPlease fix the failing tests or update the code.\"}"
fi
