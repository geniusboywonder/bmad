#!/bin/bash

# BotArmy Backend Startup Script with Port Management

# Default port
PORT=${1:-8000}

echo "🚀 Starting BotArmy Backend on port $PORT..."

# Kill any existing processes first
echo "🔪 Cleaning up existing processes..."
./scripts/kill_processes.sh

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

# Upgrade pip first
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install minimal dependencies first
echo "📥 Installing minimal dependencies..."
pip install -r requirements-minimal.txt

# Check if we can import the app
echo "🔍 Testing imports..."
python test_basic_imports.py

if [ $? -ne 0 ]; then
    echo "❌ Import test failed. Please check the error messages above."
    exit 1
fi

# Check if port is available
echo "🔍 Checking if port $PORT is available..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port $PORT is already in use. Trying to kill existing processes..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 2
    
    # Check again
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $PORT is still in use. Please choose a different port:"
        echo "   ./scripts/start_with_port.sh 8001"
        exit 1
    fi
fi

echo "✅ Port $PORT is available"

# Check database connection (optional)
echo "🗄️  Checking database connection (optional)..."
python -c "
try:
    from sqlalchemy import create_engine, text
    from app.config import settings
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful')
except Exception as e:
    print(f'⚠️  Database connection failed: {e}')
    print('   This is expected if PostgreSQL is not running')
"

# Check Redis connection (optional)
echo "🔴 Checking Redis connection (optional)..."
python -c "
try:
    import redis
    from app.config import settings
    r = redis.from_url(settings.redis_url)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'⚠️  Redis connection failed: {e}')
    print('   This is expected if Redis is not running')
"

# Start FastAPI server
echo "🌐 Starting FastAPI server on port $PORT..."
echo "📍 Server will be available at: http://localhost:$PORT"
echo "📚 API documentation at: http://localhost:$PORT/docs"
echo "🔌 WebSocket endpoint at: ws://localhost:$PORT/ws"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload
