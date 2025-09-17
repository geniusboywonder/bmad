#!/bin/bash

# BotArmy Backend Simple Startup Script

echo "🚀 Starting BotArmy Backend (Simple Mode)..."

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

# Start Redis if needed (optional for simple mode)
echo "🔴 Checking/Starting Redis..."
if command -v brew &> /dev/null; then
    if brew services list | grep redis | grep started > /dev/null; then
        echo "   ✅ Redis already running"
    else
        echo "   🚀 Starting Redis..."
        brew services start redis && echo "   ✅ Redis started" || echo "   ⚠️  Redis start failed (continuing anyway)"
    fi
elif command -v systemctl &> /dev/null; then
    if systemctl is-active --quiet redis-server; then
        echo "   ✅ Redis already running"
    else
        echo "   🚀 Starting Redis..."
        sudo systemctl start redis-server && echo "   ✅ Redis started" || echo "   ⚠️  Redis start failed (continuing anyway)"
    fi
fi

# Verify Redis connection
python -c "
try:
    import redis
    from app.config import settings
    r = redis.from_url(settings.redis_url)
    r.ping()
    print('   ✅ Redis connection successful')
except Exception as e:
    print(f'   ⚠️  Redis connection failed: {e}')
    print('   Continuing without Redis - some features may not work')
"

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo "🔌 WebSocket endpoint at: ws://localhost:8000/ws"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
