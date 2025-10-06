#!/bin/bash

# BotArmy Backend Development Startup Script

# Get the script's directory and navigate to backend folder
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BACKEND_DIR"

echo "🚀 Starting BotArmy Backend Development Environment..."
echo "📂 Working directory: $(pwd)"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "📝 Please update .env with your actual configuration values"
    else
        echo "❌ env.example not found. Using existing .env file."
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found in $(pwd)"
    exit 1
fi

# Check if database exists (PostgreSQL)
echo "🗄️  Checking database connection..."
export PYTHONPATH="${BACKEND_DIR}:$PYTHONPATH"
python -c "
try:
    from sqlalchemy import create_engine, text
    from app.settings import settings
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('Please ensure PostgreSQL is running and the database exists')
"

# Start Redis if not running
echo "🔴 Starting Redis server..."
if command -v brew &> /dev/null; then
    # macOS with Homebrew
    if brew services list | grep redis | grep started > /dev/null; then
        echo "   ✅ Redis already running (Homebrew)"
    else
        brew services start redis && echo "   ✅ Redis started (Homebrew)" || echo "   ❌ Failed to start Redis with Homebrew"
    fi
elif command -v systemctl &> /dev/null; then
    # Linux with systemd
    if systemctl is-active --quiet redis-server; then
        echo "   ✅ Redis already running (systemctl)"
    else
        sudo systemctl start redis-server && echo "   ✅ Redis started (systemctl)" || echo "   ❌ Failed to start Redis with systemctl"
    fi
else
    echo "   ⚠️  Cannot auto-start Redis. Please start it manually:"
    echo "      macOS: brew services start redis"
    echo "      Linux: sudo systemctl start redis-server"
fi

# Verify Redis connection
echo "🔍 Verifying Redis connection..."
python -c "
import time
try:
    import redis
    from app.settings import settings
    r = redis.from_url(settings.redis_url)
    r.ping()
    print('   ✅ Redis connection successful')
except Exception as e:
    print(f'   ❌ Redis connection failed: {e}')
    print('   Please ensure Redis is running on localhost:6379')
    exit(1)
"

# Exit if Redis check failed
if [ $? -ne 0 ]; then
    echo "❌ Cannot proceed without Redis. Please start Redis and try again."
    exit 1
fi

# Run database migrations
echo "🔄 Running database migrations..."
if [ -f alembic.ini ]; then
    alembic upgrade head
else
    echo "⚠️  alembic.ini not found, skipping migrations"
fi

# Start Celery worker in background
echo "👷 Starting Celery worker..."
export PYTHONPATH="${BACKEND_DIR}:$PYTHONPATH"

# Kill any existing Celery workers first
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "app.tasks.celery_app" 2>/dev/null || true

# Wait a moment for processes to die
sleep 1

# Start Celery worker with proper error handling
echo "   Starting Celery worker process..."
# Create log file for Celery
CELERY_LOG_FILE="${BACKEND_DIR}/celery.log"
CELERY_PID_FILE="${BACKEND_DIR}/celery.pid"

# CRITICAL: Source .env to load DATABASE_URL before starting Celery
# The Celery worker MUST have DATABASE_URL to connect to PostgreSQL for HITL approvals
echo "   Loading environment variables from .env..."
set -a  # Automatically export all variables
source "${BACKEND_DIR}/.env"
set +a  # Stop auto-exporting

# Override CELERY-specific settings (these take precedence over .env)
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6379/1}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://localhost:6379/1}"

# Start Celery worker in background and capture output
nohup celery -A app.tasks.celery_app worker --loglevel=info --pidfile="$CELERY_PID_FILE" --queues=agent_tasks,celery > "$CELERY_LOG_FILE" 2>&1 &
CELERY_PID=$!

# Give Celery time to start
sleep 3

# Check if Celery process is still running
if kill -0 "$CELERY_PID" 2>/dev/null; then
    echo "   ✅ Celery worker started successfully (PID: $CELERY_PID)"
    echo "   📋 Celery logs: $CELERY_LOG_FILE"
else
    echo "   ❌ Celery worker failed to start. Check the logs:"
    echo "   📋 Log file: $CELERY_LOG_FILE"
    if [ -f "$CELERY_LOG_FILE" ]; then
        echo "   Last few lines of error log:"
        tail -n 5 "$CELERY_LOG_FILE" | sed 's/^/      /'
    fi
    echo "   Try running manually: celery -A app.tasks.celery_app worker --loglevel=info"
fi

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo "🔌 WebSocket endpoint at: ws://localhost:8000/ws"
echo "🤖 AG-UI CopilotKit endpoints:"
echo "   - /api/copilotkit/analyst"
echo "   - /api/copilotkit/architect"
echo "   - /api/copilotkit/coder"
echo "   - /api/copilotkit/orchestrator"
echo "   - /api/copilotkit/tester"
echo "   - /api/copilotkit/deployer"
echo ""
echo "Press Ctrl+C to stop the server"

export PYTHONPATH="${BACKEND_DIR}:$PYTHONPATH"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
