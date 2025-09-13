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
- **Audit Trail System**: Complete event logging for compliance (Sprint 4)
- **Health Monitoring**: Comprehensive service monitoring with `/healthz` endpoint (Sprint 4)

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/                 # FastAPI endpoints
│   │   ├── agents.py        # Agent status management (Sprint 3)
│   │   ├── artifacts.py     # Project artifact management (Sprint 3)
│   │   ├── audit.py         # Audit trail API endpoints (Sprint 4)
│   │   ├── dependencies.py  # Dependency injection
│   │   ├── health.py        # Health check endpoints + /healthz (Sprint 4)
│   │   ├── hitl.py          # Human-in-the-Loop endpoints + audit integration
│   │   ├── projects.py      # Project management endpoints
│   │   └── websocket.py     # WebSocket endpoints
│   ├── config.py            # Application configuration
│   ├── database/            # Database models and connection
│   │   ├── connection.py    # Database connection setup
│   │   └── models.py        # SQLAlchemy models
│   ├── models/              # Pydantic data models
│   │   ├── agent.py         # Agent status and types
│   │   ├── context.py       # Context artifacts
│   │   ├── event_log.py     # Audit trail event models (Sprint 4)
│   │   ├── handoff.py       # Agent handoff schema
│   │   ├── hitl.py          # HITL request models
│   │   └── task.py          # Task models
│   ├── services/            # Business logic services
│   │   ├── agent_status_service.py    # Real-time agent status management (Sprint 3)
│   │   ├── artifact_service.py        # Project artifact generation (Sprint 3)
│   │   ├── audit_service.py           # Comprehensive audit trail logging (Sprint 4)
│   │   ├── context_store.py           # Context Store pattern implementation
│   │   ├── orchestrator.py            # Agent orchestration service
│   │   └── project_completion_service.py # Project completion detection (Sprint 3)
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
- `GET /health/z` - **Kubernetes-style comprehensive health monitoring (Sprint 4)**

### Projects

- `POST /api/v1/projects/` - Create a new project
- `GET /api/v1/projects/{project_id}/status` - Get project status
- `POST /api/v1/projects/{project_id}/tasks` - Create a new task
- `GET /api/v1/projects/{project_id}/completion` - Get completion status (Sprint 3)
- `POST /api/v1/projects/{project_id}/check-completion` - Check completion (Sprint 3)
- `POST /api/v1/projects/{project_id}/force-complete` - Force completion (Sprint 3)

### Agent Status Management (Sprint 3)

- `GET /api/v1/agents/status` - Get all agent statuses
- `GET /api/v1/agents/status/{agent_type}` - Get specific agent status  
- `GET /api/v1/agents/status-history/{agent_type}` - Get agent status history
- `POST /api/v1/agents/status/{agent_type}/reset` - Reset agent status

### Artifact Management (Sprint 3)

- `POST /api/v1/artifacts/{project_id}/generate` - Generate project artifacts
- `GET /api/v1/artifacts/{project_id}/summary` - Get artifact summary
- `GET /api/v1/artifacts/{project_id}/download` - Download artifact ZIP
- `DELETE /api/v1/artifacts/{project_id}/artifacts` - Clean up artifacts
- `DELETE /api/v1/artifacts/cleanup-old` - Admin cleanup endpoint

### Human-in-the-Loop (HITL)

- `POST /api/v1/hitl/{request_id}/respond` - Respond to HITL request (with audit logging)
- `GET /api/v1/hitl/{request_id}` - Get HITL request details
- `GET /api/v1/hitl/project/{project_id}/requests` - Get project HITL requests

### Audit Trail Management (Sprint 4)

- `GET /api/v1/audit/events` - Get filtered audit events
- `GET /api/v1/audit/events/{event_id}` - Get specific audit event
- `GET /api/v1/audit/projects/{project_id}/events` - Get project audit events
- `GET /api/v1/audit/tasks/{task_id}/events` - Get task audit events

### WebSocket

- `WS /ws?project_id={project_id}` - Real-time communication

## 🧪 Testing

### Comprehensive Test Coverage

The project includes extensive testing across all Sprint 4 features with **70+ test cases**:

**Unit Tests:**
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific Sprint 4 components
pytest tests/unit/test_audit_service.py -v        # Audit trail service (13 tests)
pytest tests/unit/test_audit_api.py -v           # Audit API endpoints (15+ tests)
pytest tests/unit/test_event_log_models.py -v    # Pydantic models (20+ tests)
```

**Integration Tests:**
```bash
# Run audit trail integration tests
pytest tests/integration/test_audit_trail_integration.py -v
```

**End-to-End Tests:**
```bash
# Run Sprint 4 E2E workflow validation
pytest tests/e2e/test_sprint4_full_workflow_e2e.py -v

# Run performance validation tests (NFR-01 compliance)
pytest tests/e2e/test_sprint4_full_workflow_e2e.py::TestSprintFourPerformanceValidation -v
```

**Health Check Tests:**
```bash
# Run enhanced /healthz endpoint tests
pytest tests/test_health.py::TestHealthzEndpoint -v
```

**Run Complete Test Suite:**
```bash
# All tests
pytest

# With coverage report
pytest --cov=app

# Sprint 4 specific test coverage
pytest tests/unit/test_audit* tests/test_health.py::TestHealthzEndpoint tests/integration/test_audit* tests/e2e/test_sprint4* -v
```

### Test Categories

- **Unit Tests**: Service logic, model validation, error handling
- **Integration Tests**: Database operations, filtering, pagination
- **API Tests**: Endpoint functionality, parameter validation, error responses  
- **E2E Tests**: Complete workflows, performance validation, system integration
- **Health Tests**: Service monitoring, degraded mode handling, Kubernetes compatibility

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

- **Agent status changes** (Sprint 3) - Real-time agent state broadcasting  
- **Artifact creation** (Sprint 3) - Notifications when project artifacts are ready
- **Workflow events** (Sprint 3) - Project completion and major milestone notifications
- **Enhanced HITL responses** (Sprint 3) - Improved real-time HITL interaction broadcasting
- Task lifecycle events
- HITL requests and responses

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

**Current Status: Sprint 4 Complete - PRODUCTION READY** 

### Sprint 1 & 2 (Completed)
- ✅ FastAPI project setup with PostgreSQL and Redis
- ✅ Pydantic data models implementation
- ✅ WebSocket service for real-time communication
- ✅ Celery task queue setup
- ✅ Health check endpoints
- ✅ Database schema and migrations
- ✅ Context Store Pattern service layer
- ✅ Basic API endpoints for projects and HITL
- ✅ Structured logging and error handling

### Sprint 3 (Completed) - Backend Real-Time Integration
- ✅ **Agent Status Service** - Real-time agent status tracking and WebSocket broadcasting
- ✅ **Artifact Service** - Project artifact generation, ZIP creation, and download management
- ✅ **Project Completion Service** - Automatic completion detection and artifact triggers
- ✅ **Enhanced WebSocket Events** - Real-time notifications for status changes, artifacts, and HITL
- ✅ **12 New API Endpoints** - Agent status, artifact management, and project completion APIs
- ✅ **Comprehensive Test Coverage** - 67/67 unit tests passing, extensive integration testing

### Sprint 4 (Completed) - Validation & Production Readiness
- ✅ **Audit Trail System** - Complete immutable event logging with full payloads
- ✅ **Enhanced Health Monitoring** - `/healthz` endpoint with comprehensive service checks
- ✅ **End-to-End Testing** - Full workflow validation with performance testing
- ✅ **Deployment Automation** - Production-ready deployment scripts with rollback
- ✅ **Performance Validation** - Sub-200ms API responses (NFR-01 compliance)
- ✅ **Comprehensive Test Coverage** - 70+ new test cases across unit, integration, and E2E levels
- ✅ **Documentation Consolidation** - Complete architecture and operational documentation

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

## 🚀 Deployment

### Quick Deployment

```bash
# Deploy to development
./deploy.sh dev

# Deploy to production  
./deploy.sh prod

# Health check only
./deploy.sh health-check

# Database migrations only
./deploy.sh migrate
```

### Docker Deployment

```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose up
```

## 🔮 Next Steps

**Future Sprints:**

- **Frontend Integration** - React/Next.js frontend for HITL request history display
- **AutoGen Framework Integration** - Multi-agent conversation implementation 
- **LLM Provider Integration** - OpenAI, Anthropic, and Google connectivity
- **Production Monitoring** - Comprehensive logging and alerting setup
- **Load Testing** - Performance validation and capacity planning

## 📝 License

This project is part of the BotArmy POC development.
