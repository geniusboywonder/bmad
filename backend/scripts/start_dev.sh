#!/bin/bash

# BotArmy Backend Development Startup Script

echo "🚀 Starting BotArmy Backend Development Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from env.example..."
    cp env.example .env
    echo "📝 Please update .env with your actual configuration values"
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
pip install -r requirements.txt

# Check if database exists (PostgreSQL)
echo "🗄️  Checking database connection..."
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
import redis
from app.config import settings
try:
    r = redis.from_url(settings.redis_url)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    print('Please ensure Redis is running')
"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Start Celery worker in background
echo "👷 Starting Celery worker..."
celery -A app.tasks.celery_app worker --loglevel=info --detach

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo "🔌 WebSocket endpoint at: ws://localhost:8000/ws"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
