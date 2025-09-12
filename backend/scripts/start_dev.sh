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
    from app.config import settings
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('Please ensure PostgreSQL is running and the database exists')
"

# Check if Redis is running
echo "🔴 Checking Redis connection..."
python -c "
try:
    import redis
    from app.config import settings
    r = redis.from_url(settings.redis_url)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    print('Please ensure Redis is running')
"

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
celery -A app.tasks.celery_app worker --loglevel=info --detach 2>/dev/null || echo "⚠️  Celery worker failed to start, continuing without it"

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo "🔌 WebSocket endpoint at: ws://localhost:8000/ws"
echo ""
echo "Press Ctrl+C to stop the server"

export PYTHONPATH="${BACKEND_DIR}:$PYTHONPATH"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
