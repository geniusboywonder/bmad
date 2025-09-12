#!/bin/bash

# BotArmy Backend Status Check Script

echo "🔍 BotArmy Backend Status Check"
echo "================================"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
else
    echo "❌ Virtual environment not found"
fi

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ Environment file exists"
else
    echo "❌ Environment file not found"
fi

# Check port 8000
echo ""
echo "🌐 Port Status:"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "  Port 8000: 🔴 IN USE"
    echo "    Process: $(lsof -Pi :8000 -sTCP:LISTEN -t | xargs ps -p 2>/dev/null | tail -n +2 || echo 'Unknown')"
else
    echo "  Port 8000: 🟢 AVAILABLE"
fi

# Check port 5555 (Celery Flower)
if lsof -Pi :5555 -sTCP:LISTEN -t >/dev/null ; then
    echo "  Port 5555: 🔴 IN USE (Celery Flower)"
else
    echo "  Port 5555: 🟢 AVAILABLE"
fi

# Check PostgreSQL
echo ""
echo "🗄️  Database Status:"
if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "  PostgreSQL: 🟢 RUNNING"
else
    echo "  PostgreSQL: 🔴 NOT RUNNING"
fi

# Check Redis
echo ""
echo "🔴 Redis Status:"
if redis-cli ping >/dev/null 2>&1; then
    echo "  Redis: 🟢 RUNNING"
else
    echo "  Redis: 🔴 NOT RUNNING"
fi

# Check Python processes
echo ""
echo "🐍 Python Processes:"
uvicorn_count=$(pgrep -f uvicorn | wc -l)
celery_count=$(pgrep -f celery | wc -l)
echo "  Uvicorn processes: $uvicorn_count"
echo "  Celery processes: $celery_count"

echo ""
echo "📝 Quick Commands:"
echo "  Start server: ./scripts/start_simple.sh"
echo "  Kill processes: ./scripts/kill_processes.sh"
echo "  Check status: ./scripts/status.sh"
echo "  Start on different port: ./scripts/start_with_port.sh 8001"
