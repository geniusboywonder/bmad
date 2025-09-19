# SQLite Fallback Setup Guide

## Overview

The BMAD backend now supports SQLite as a fallback database when PostgreSQL is not available. This enables deployment in environments without PostgreSQL infrastructure.

## Quick Setup

### 1. Install Base Requirements

```bash
# Install core dependencies (SQLite support included in Python)
pip install -r requirements.txt

# Optional: Install PostgreSQL support if needed
pip install -r requirements-postgres.txt
```

### 2. Configure Environment

Copy the SQLite configuration example:

```bash
cp env.sqlite.example .env
```

Edit `.env` and update any required settings (API keys, etc.).

### 3. Initialize Database

```bash
# Initialize SQLite database
python -m app.database.init init

# Or run migrations
alembic upgrade head
```

### 4. Start the Application

```bash
# Development server
python app/main.py

# Or with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration Examples

### SQLite Configuration (Minimal)
```bash
DATABASE_URL=sqlite:///./bmad.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_secret_key_here
# ... other required settings
```

### PostgreSQL Configuration (Full)
```bash
DATABASE_URL=postgresql+psycopg://user:pass@localhost/bmad
# ... requires psycopg installation
```

## Database Features

### Supported in SQLite Mode:
✅ All core BMAD functionality
✅ Agent orchestration
✅ Task management
✅ HITL workflows
✅ Context storage
✅ Event logging
✅ WebSocket support

### Database-Specific Considerations:

| Feature | PostgreSQL | SQLite |
|---------|------------|--------|
| **UUID Type** | Native UUID | CHAR(36) |
| **JSON Columns** | Native JSONB | TEXT (JSON) |
| **Concurrent Writes** | Excellent | Limited |
| **Connection Pooling** | Full support | Single connection |
| **Performance** | High | Moderate |
| **Deployment** | Requires PostgreSQL | No external dependencies |

## Migration Path

### From SQLite to PostgreSQL:
1. Export data using Alembic
2. Set up PostgreSQL instance
3. Update `DATABASE_URL` to PostgreSQL
4. Install `psycopg[binary]>=3.2.0`
5. Run migrations: `alembic upgrade head`

### From PostgreSQL to SQLite:
1. Export critical data
2. Update `DATABASE_URL` to SQLite
3. Initialize fresh SQLite database
4. Re-import data (may require data transformation)

## Limitations in SQLite Mode

1. **Concurrency**: SQLite has limited concurrent write support
2. **Scale**: Best for development, testing, or small deployments
3. **Advanced Features**: Some PostgreSQL-specific optimizations unavailable
4. **Performance**: Lower performance than PostgreSQL for large datasets

## Troubleshooting

### Database Connection Issues
```bash
# Test database connectivity
python -c "from app.database.init import test_database_connection; print(test_database_connection())"
```

### Missing PostgreSQL Driver
```bash
# If you see psycopg errors, install PostgreSQL support:
pip install 'psycopg[binary]>=3.2.0'
```

### Migration Issues
```bash
# Reset database (CAUTION: destroys data)
rm bmad.db  # for SQLite
alembic upgrade head
```

## Performance Optimization

### SQLite Optimizations:
- Use WAL mode for better concurrency
- Regular VACUUM operations
- Appropriate indexing strategy
- Connection pooling disabled (single connection)

### PostgreSQL Optimizations:
- Connection pooling enabled
- Advanced indexing
- Query optimization
- Concurrent connection support

## Production Recommendations

### Development/Testing: ✅ SQLite
- Local development
- CI/CD testing
- Demo environments

### Staging/Production: ✅ PostgreSQL
- High availability requirements
- Concurrent user support
- Performance critical applications
- Data backup/recovery needs