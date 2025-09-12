# BotArmy Backend

The foundational backend services for the BotArmy POC project, implementing the core architecture and SOLID principles as specified in the project documentation.

## 🏗️ Architecture Overview

This backend implements a modern microservice-oriented architecture with:

- **FastAPI**: High-performance web framework for building APIs
- **PostgreSQL**: Relational database for persistent storage
- **Redis**: In-memory cache and message broker for Celery
- **Celery**: Asynchronous task queue for agent processing
- **WebSocket**: Real-time communication for live updates
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/                 # FastAPI endpoints
│   │   ├── dependencies.py  # Dependency injection
│   │   ├── health.py        # Health check endpoints
│   │   ├── hitl.py          # Human-in-the-Loop endpoints
│   │   ├── projects.py      # Project management endpoints
│   │   └── websocket.py     # WebSocket endpoints
│   ├── config.py            # Application configuration
│   ├── database/            # Database models and connection
│   │   ├── connection.py    # Database connection setup
│   │   └── models.py        # SQLAlchemy models
│   ├── models/              # Pydantic data models
│   │   ├── agent.py         # Agent status and types
│   │   ├── context.py       # Context artifacts
│   │   ├── handoff.py       # Agent handoff schema
│   │   ├── hitl.py          # HITL request models
│   │   └── task.py          # Task models
│   ├── services/            # Business logic services
│   │   ├── context_store.py # Context Store pattern implementation
│   │   └── orchestrator.py  # Agent orchestration service
│   ├── tasks/               # Celery task definitions
│   │   ├── agent_tasks.py   # Agent task processing
│   │   └── celery_app.py    # Celery configuration
│   ├── websocket/           # WebSocket services
│   │   ├── events.py        # WebSocket event models
│   │   └── manager.py       # Connection management
│   └── main.py              # FastAPI application
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
└── tests/                   # Test suite
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Git

### Installation

1. **Clone and navigate to the backend directory:**

   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**

   ```bash
   cp env.example .env
   # Edit .env with your actual configuration values
   ```

5. **Set up database:**

   ```bash
   # Create PostgreSQL database
   createdb botarmy_db
   
   # Run migrations
   alembic upgrade head
   ```

6. **Start Redis:**

   ```bash
   redis-server
   ```

7. **Start the development environment:**

   ```bash
   ./scripts/start_dev.sh
   ```

### Manual Startup

If you prefer to start services manually:

1. **Start Celery worker:**

   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

2. **Start FastAPI server:**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🔌 API Endpoints

### Health Checks

- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed component status
- `GET /health/ready` - Readiness check

### Projects

- `POST /api/v1/projects/` - Create a new project
- `GET /api/v1/projects/{project_id}/status` - Get project status
- `POST /api/v1/projects/{project_id}/tasks` - Create a new task

### Human-in-the-Loop (HITL)

- `POST /api/v1/hitl/{request_id}/respond` - Respond to HITL request
- `GET /api/v1/hitl/{request_id}` - Get HITL request details
- `GET /api/v1/hitl/project/{project_id}/requests` - Get project HITL requests

### WebSocket

- `WS /ws?project_id={project_id}` - Real-time communication

## 🧪 Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```

## 📊 Monitoring

### Health Check

The application provides comprehensive health checks:

```bash
curl http://localhost:8000/health/detailed
```

### Logging

Structured logging is configured using `structlog`. Logs are output in JSON format for easy parsing and analysis.

### WebSocket Events

Real-time events are emitted for:

- Agent status changes
- Task lifecycle events
- HITL requests and responses
- Artifact creation
- Workflow events

## 🔧 Configuration

All configuration is managed through environment variables. See `env.example` for available options.

Key configuration areas:

- **Database**: Connection strings and settings
- **Redis**: Cache and message broker configuration
- **API**: CORS, rate limiting, and security settings
- **WebSocket**: Connection limits and heartbeat settings
- **LLM**: API keys for future agent integration

## 🏛️ SOLID Principles Implementation

The codebase adheres to SOLID principles:

- **Single Responsibility**: Each class has a single, well-defined purpose
- **Open/Closed**: Extensible through interfaces and dependency injection
- **Liskov Substitution**: All agents implement common interfaces
- **Interface Segregation**: Small, focused interfaces for specific needs
- **Dependency Inversion**: High-level modules depend on abstractions

## 🚧 Development Status

This is Sprint 1 implementation focusing on:

- ✅ FastAPI project setup with PostgreSQL and Redis
- ✅ Pydantic data models implementation
- ✅ WebSocket service for real-time communication
- ✅ Celery task queue setup
- ✅ Health check endpoints
- ✅ Database schema and migrations
- ✅ Context Store Pattern service layer
- ✅ Basic API endpoints for projects and HITL
- ✅ Structured logging and error handling

## 🔧 Troubleshooting

If you encounter issues during setup, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common solutions.

### Quick Fixes

1. **Use the simple startup script:**

   ```bash
   ./scripts/start_simple.sh
   ```

2. **Use Docker for a clean environment:**

   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

3. **Install minimal dependencies:**

   ```bash
   pip install -r requirements-minimal.txt
   ```

## 🔮 Next Steps

Future sprints will implement:

- Agent framework integration (AutoGen)
- Complete HITL workflow implementation
- Real-time WebSocket event broadcasting
- Agent orchestration logic
- Frontend integration
- Testing and documentation

## 📝 License

This project is part of the BotArmy POC development.
