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

# Kill any remaining celery processes (more thorough)
echo "  - Killing celery processes..."
pkill -f "celery.*worker" 2>/dev/null || echo "    No celery worker processes found"
pkill -f "app.tasks.celery_app" 2>/dev/null || echo "    No BotArmy celery processes found"
pkill -f celery 2>/dev/null || echo "    No general celery processes found"

# Kill any remaining python processes running our app
echo "  - Killing BotArmy python processes..."
pkill -f "app.main:app" 2>/dev/null || echo "    No BotArmy python processes found"

# Stop Redis (Homebrew on macOS)
echo "  - Stopping Redis server..."
if command -v brew &> /dev/null; then
    brew services stop redis 2>/dev/null && echo "    ✅ Redis stopped (Homebrew)" || echo "    ⚠️  Redis not running or not managed by Homebrew"
elif command -v systemctl &> /dev/null; then
    sudo systemctl stop redis-server 2>/dev/null && echo "    ✅ Redis stopped (systemctl)" || echo "    ⚠️  Redis not running or permission denied"
else
    # Try manual killall as fallback
    killall redis-server 2>/dev/null && echo "    ✅ Redis stopped (manual)" || echo "    ⚠️  Redis not running or not found"
fi

echo "✅ Complete process cleanup finished!"
echo "   - FastAPI server stopped"
echo "   - Celery workers stopped"
echo "   - Redis server stopped"
echo ""
echo "   You can now run ./scripts/start_dev.sh or ./scripts/start_simple.sh"
