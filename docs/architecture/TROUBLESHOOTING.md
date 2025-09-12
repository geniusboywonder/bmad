# Troubleshooting Guide

## Common Issues and Solutions

### 1. psycopg2 Installation Issues

**Problem**: `Error: pg_config executable not found`

**Solution**: Install PostgreSQL development headers:

```bash
# macOS with Homebrew
brew install postgresql

# Ubuntu/Debian
sudo apt-get install libpq-dev

# CentOS/RHEL
sudo yum install postgresql-devel
```

**Alternative**: Use the Docker setup instead:

```bash
docker-compose -f docker-compose.dev.yml up
```

### 2. Python Version Compatibility

**Problem**: Dependencies not installing with Python 3.13

**Solution**: Use Python 3.11 or 3.12:

```bash
# Install Python 3.11
brew install python@3.11

# Create virtual environment with specific version
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Missing Dependencies

**Problem**: `ModuleNotFoundError: No module named 'structlog'`

**Solution**: Install minimal requirements first:

```bash
pip install -r requirements-minimal.txt
```

### 4. Database Connection Issues

**Problem**: Database connection failed

**Solution**: Ensure PostgreSQL is running:

```bash
# Start PostgreSQL service
brew services start postgresql

# Create database
createdb botarmy_db
```

### 5. Redis Connection Issues

**Problem**: Redis connection failed

**Solution**: Start Redis service:

```bash
# Start Redis
redis-server

# Or with Homebrew
brew services start redis
```

## Quick Fixes

### Option 1: Use Simple Startup Script

```bash
./scripts/start_simple.sh
```

### Option 2: Use Docker (Recommended)

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up

# Or start just database and Redis
docker-compose -f docker-compose.dev.yml up postgres redis
```

### Option 3: Manual Setup

```bash
# 1. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements-minimal.txt

# 3. Start services
# In one terminal: redis-server
# In another terminal: uvicorn app.main:app --reload
```

## Environment Setup

### Required Services

- **PostgreSQL**: Database server
- **Redis**: Cache and message broker
- **Python 3.11+**: Runtime environment

### Optional Services

- **Celery Worker**: For background tasks
- **Flower**: For Celery monitoring

## Testing the Setup

### 1. Test API Health

```bash
curl http://localhost:8000/health/
```

### 2. Test Database Connection

```bash
curl http://localhost:8000/health/detailed
```

### 3. Test WebSocket

```bash
# Use a WebSocket client or browser console
ws = new WebSocket('ws://localhost:8000/ws');
```

## Common Error Messages

### `ModuleNotFoundError`

- **Cause**: Missing Python package
- **Fix**: Install requirements or use Docker

### `Connection refused`

- **Cause**: Service not running
- **Fix**: Start PostgreSQL/Redis services

### `Permission denied`

- **Cause**: File permissions issue
- **Fix**: Check file ownership and permissions

### `Port already in use`

- **Cause**: Another service using the port
- **Fix**: Kill the process or use a different port

## Getting Help

1. Check the logs for detailed error messages
2. Ensure all required services are running
3. Verify environment variables in `.env` file
4. Try the Docker setup for a clean environment
5. Check Python version compatibility

## Development Tips

- Use `docker-compose` for consistent environment
- Check `requirements-minimal.txt` for core dependencies
- Use the simple startup script for quick testing
- Monitor logs for debugging information
