#!/bin/bash

# BotArmy Full-Stack Process Killer Script

echo "🔪 Killing existing BotArmy processes..."

# Kill frontend processes on common ports
echo "  - Killing frontend processes..."
echo "    - Port 3000 (Next.js dev server)..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "      No processes found on port 3000"
echo "    - Port 3001 (alternate frontend)..."
lsof -ti:3001 | xargs kill -9 2>/dev/null || echo "      No processes found on port 3001"
echo "    - Port 5173 (Vite dev server)..."
lsof -ti:5173 | xargs kill -9 2>/dev/null || echo "      No processes found on port 5173"
echo "    - Port 4173 (Vite preview)..."
lsof -ti:4173 | xargs kill -9 2>/dev/null || echo "      No processes found on port 4173"

# Kill backend processes
echo "  - Killing backend processes..."
echo "    - Port 8000 (FastAPI)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "      No processes found on port 8000"
echo "    - Port 5555 (Celery Flower)..."
lsof -ti:5555 | xargs kill -9 2>/dev/null || echo "      No processes found on port 5555"

# Kill frontend Node.js processes
echo "  - Killing frontend Node.js processes..."
pkill -f "next.*dev" 2>/dev/null || echo "    No Next.js dev processes found"
pkill -f "npm.*dev" 2>/dev/null || echo "    No npm dev processes found"
pkill -f "yarn.*dev" 2>/dev/null || echo "    No yarn dev processes found"
pkill -f "pnpm.*dev" 2>/dev/null || echo "    No pnpm dev processes found"
pkill -f "vite" 2>/dev/null || echo "    No Vite processes found"
pkill -f "webpack.*serve" 2>/dev/null || echo "    No webpack dev server processes found"

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
echo "   - Frontend servers stopped (Next.js, Vite, etc.)"
echo "   - FastAPI server stopped"
echo "   - Celery workers stopped"
echo "   - Redis server stopped"
echo ""
echo "   You can now run ./scripts/start_dev.sh or ./scripts/start_simple.sh"
