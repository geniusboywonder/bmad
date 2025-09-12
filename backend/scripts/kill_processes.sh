#!/bin/bash

# BotArmy Backend Process Killer Script

echo "🔪 Killing existing BotArmy processes..."

# Kill processes on port 8000 (FastAPI)
echo "  - Killing processes on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "    No processes found on port 8000"

# Kill processes on port 5555 (Celery Flower)
echo "  - Killing processes on port 5555..."
lsof -ti:5555 | xargs kill -9 2>/dev/null || echo "    No processes found on port 5555"

# Kill any remaining uvicorn processes
echo "  - Killing uvicorn processes..."
pkill -f uvicorn 2>/dev/null || echo "    No uvicorn processes found"

# Kill any remaining celery processes
echo "  - Killing celery processes..."
pkill -f celery 2>/dev/null || echo "    No celery processes found"

# Kill any remaining python processes running our app
echo "  - Killing BotArmy python processes..."
pkill -f "app.main:app" 2>/dev/null || echo "    No BotArmy python processes found"

echo "✅ Process cleanup complete!"
echo "   You can now run ./scripts/start_simple.sh"
