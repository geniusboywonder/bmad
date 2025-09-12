#!/bin/bash

# Simple development server startup script
# Run this from the backend directory

# Get current directory
CURRENT_DIR="$(pwd)"

# Check if we're in the backend directory
if [[ ! -f "app/main.py" ]]; then
    echo "❌ Please run this script from the backend directory"
    echo "Current directory: $CURRENT_DIR"
    exit 1
fi

echo "🚀 Starting BotArmy Backend Development Server..."
echo "📂 Working directory: $CURRENT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

# Export PYTHONPATH to current directory
export PYTHONPATH="$CURRENT_DIR:$PYTHONPATH"

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "📍 Server available at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload