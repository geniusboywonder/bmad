#!/bin/bash

# Black Auto-Formatting Hook (PostToolUse)
#
# Runs after Write/Edit operations to auto-format Python files
# Executes `black` with project configuration from pyproject.toml
#
# Behavior:
# - Success: Silent (suppressOutput: true)
# - Errors: Reports formatting issues via additionalContext

# Read JSON from stdin
input=$(cat)

# Extract file path from JSON
file_path=$(echo "$input" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('parameters', {}).get('file_path', ''))" 2>/dev/null)

# Check if file path exists
if [ -z "$file_path" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Only process .py files
if [[ ! "$file_path" =~ \.py$ ]]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Only process files in backend directory
if [[ ! "$file_path" =~ /backend/ ]]; then
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

# Check if pyproject.toml exists
if [ ! -f "$backend_dir/pyproject.toml" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Run Black formatter
cd "$backend_dir" || exit 0

# Run black and capture output
output=$(python3 -m black --config pyproject.toml "$file_path" 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ]; then
  # Successfully formatted - silent success
  echo '{"continue": true, "suppressOutput": true}'
else
  # Formatting failed - report error
  error_msg=$(echo "$output" | sed 's/"/\\"/g' | tr '\n' ' ')
  echo "{\"continue\": true, \"additionalContext\": \"Black formatting failed:\\n$error_msg\\n\\nPlease check the Python syntax.\"}"
fi
