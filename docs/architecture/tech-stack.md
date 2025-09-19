# Technology Stack

## Overview

BMAD Enterprise AI Orchestration Platform leverages a modern, production-ready technology stack designed for multi-agent coordination, real-time communication, and enterprise-grade safety controls.

## Backend Stack

### Core Framework

- **FastAPI >=0.115.0** - High-performance Python web framework with async support
- **Uvicorn >=0.32.0** - ASGI server with WebSocket capabilities
- **Python 3.11+** - Modern runtime environment with enhanced type hints

### Data & Persistence

**Database**
- **PostgreSQL 13+** - ACID-compliant relational database with JSON support
- **SQLAlchemy 2.0.43** - Modern async ORM with connection pooling
- **Alembic 1.13.1** - Database migration management with version control

**Caching & Queue**
- **Redis 6+** - High-performance in-memory caching and session management
- **Celery 5.3.4** - Distributed task queue for asynchronous agent processing

**Database Schema**
- **Core Tables**: projects, tasks, agent_status, context_artifacts, hitl_requests, event_log
- **HITL Safety Tables**: hitl_agent_approvals, agent_budget_controls, emergency_stops, response_approvals
- **Performance Features**: Optimized indexes, connection pooling, timezone-aware datetime handling

### Agent Framework

**Google ADK Integration**
- **Google ADK (Agent Development Kit)** - Production-grade agent framework
- **LlmAgent Integration** - Advanced capabilities with `gemini-2.0-flash` model
- **Session Management** - Proper `InMemorySessionService` and `types.Content` handling
- **Tool Integration** - `FunctionTool` support with enterprise safety controls
- **BMAD-ADK Wrapper** - Enterprise wrapper preserving BMAD safety and audit requirements

**Microsoft AutoGen Integration**
- **ConversationManager** - Multi-agent conversation patterns with context passing
- **GroupChatManager** - Multi-agent collaboration with conflict resolution
- **Agent Factory** - Dynamic agent configuration and lifecycle management

**Service Architecture (SOLID Principles)**
- **Orchestrator Services** - Modular architecture with dependency injection
- **HITL Services** - Comprehensive human oversight and approval workflows
- **Workflow Engine** - State machine pattern with persistence and recovery
- **Template System** - BMAD Core integration with dynamic loading

### HITL Safety Architecture

**Mandatory Safety Controls**
- **Pre-execution Approval** - Human authorization required for all agent operations
- **Budget Controls** - Token limits with automatic emergency stops
- **Response Validation** - Content safety scoring and quality metrics
- **Emergency Stop System** - Immediate agent halting with multiple trigger conditions
- **Real-time Monitoring** - WebSocket-based safety event broadcasting

**API Endpoints**
- 10 dedicated HITL safety endpoints (`/api/v1/hitl-safety/*`)
- Budget management, emergency controls, approval tracking
- Health monitoring with real-time safety system status

### API Architecture

**RESTful Design**
- **81 Total Endpoints** across 13 organized service groups
- **OpenAPI Documentation** - Interactive Swagger UI at `/docs`
- **Endpoint Categories**: Projects, HITL, Agents, ADK, Workflows, Artifacts, Audit, Health
- **Standards Compliance** - Proper HTTP methods, status codes, error handling

**Data Validation**
- **Pydantic 2.10.0** - Type-safe request/response validation
- **Custom Validators** - Agent type validation, UUID handling, enum verification
- **Error Handling** - Standardized error responses with detailed messages

### Communication & Real-time Features

**WebSocket System**
- **WebSockets >=15.0.1** - Real-time bidirectional communication
- **Project-scoped Broadcasting** - Event distribution by project ID
- **Event Types** - Agent status, task progress, HITL notifications, safety alerts
- **Auto-reconnection** - Graceful handling of connection failures

**Health Monitoring**
- **Multi-tier Health Checks** - Database, Redis, Celery, LLM providers
- **Health Endpoints** - `/health`, `/health/detailed`, `/health/z`
- **Component Status** - Real-time monitoring of all system dependencies

### Testing & Quality Assurance

**Production-Grade Test Suite**
- **967 Total Tests** with 95%+ success rate
- **Real Database Integration** - Production-like testing with `DatabaseTestManager`
- **Service Integration** - All services tested with proper dependency injection
- **API Coverage** - Complete endpoint testing with error scenarios

**Test Infrastructure**
- **pytest 7.4.3** - Comprehensive testing framework
- **pytest-asyncio 0.21.1** - Async testing support
- **httpx 0.25.2** - HTTP client for API testing
- **DatabaseTestManager** - Real database utilities with automatic cleanup

## Frontend Stack

### Framework
- **Next.js 14+** - React-based framework with App Router
- **React 18+** - Component-based UI library with modern hooks
- **TypeScript 5+** - Type-safe development with enhanced inference
- **Tailwind CSS 3+** - Utility-first CSS framework
- **Zustand 4+** - Lightweight state management

### Development Tools
- **Vite** - Fast build tool and development server
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting
- **PostCSS** - CSS processing and optimization

## BMAD Core Integration

### Template System
- **Dynamic Template Loading** - Runtime loading from `.bmad-core/templates/`
- **Jinja2 Integration** - Advanced template processing with variable substitution
- **Multi-format Support** - Markdown, HTML, JSON, YAML output formats
- **Schema Validation** - Template structure validation with error reporting

### Workflow Engine
- **Dynamic Workflow Loading** - Runtime loading from `.bmad-core/workflows/`
- **State Machine Pattern** - Complete workflow lifecycle management
- **Agent Coordination** - Structured handoffs with context passing
- **Progress Tracking** - Real-time monitoring with WebSocket broadcasting

### Agent Team Management
- **Team Configuration** - Dynamic loading from `.bmad-core/agent-teams/`
- **Coordination Patterns** - Sequential, parallel, hybrid execution patterns
- **Team Validation** - Automated validation of agent combinations and roles
- **Runtime Assignment** - Dynamic team assignment based on workflow requirements

## LLM Provider Support

### Multi-Provider Architecture
- **Google Gemini** - Primary provider with `gemini-2.0-flash` model
- **OpenAI GPT-4** - Technical architecture and complex reasoning
- **Anthropic Claude** - Requirements analysis and documentation
- **Provider Abstraction** - Unified interface with factory pattern

### Reliability Features
- **Response Validation** - Comprehensive validation and sanitization
- **Exponential Backoff** - 1s, 2s, 4s retry intervals with error classification
- **Usage Tracking** - Real-time token consumption and cost monitoring
- **Anomaly Detection** - Automated detection of cost spikes and patterns
- **Health Monitoring** - Provider connectivity and performance tracking

## Infrastructure Components

### Database Layer
- **PostgreSQL 13+** - Multi-tenant data storage with proper indexing
- **Connection Pooling** - Efficient database connections with StaticPool
- **Migration System** - Alembic-based version control
- **Backup & Recovery** - Automated backup with point-in-time recovery

### Message Broker & Queue
- **Redis 6+** - Task queue broker and caching layer
- **Celery 5.3.4** - Asynchronous task processing with retry logic
- **Queue Management** - Priority queues and job distribution
- **Monitoring** - Queue depth and worker availability tracking

### Security & Compliance

**Current Implementation**
- **Environment-based Configuration** - API key management via environment variables
- **CORS Middleware** - Cross-origin request security
- **Input Validation** - Pydantic schema validation
- **SQL Injection Prevention** - SQLAlchemy ORM protection

**Production Requirements**
- **Secret Management** - HashiCorp Vault or AWS Secrets Manager
- **Runtime Secret Injection** - Encrypted configuration for production
- **Audit Trails** - Immutable event logging for compliance
- **Data Retention** - GDPR-compliant data management policies

## Performance & Monitoring

### Performance Targets
- **API Response Times** - <200ms for status queries
- **WebSocket Latency** - <100ms for real-time events
- **Database Operations** - Optimized with proper indexing
- **Health Checks** - <50ms response times

### Observability
- **Structured Logging** - JSON-formatted logs with correlation IDs
- **Performance Metrics** - Response time tracking and resource utilization
- **Error Tracking** - Comprehensive error classification and reporting
- **Health Monitoring** - Multi-component status with detailed diagnostics

## Development Tools

### Code Quality
- **Black** - Python code formatting
- **isort** - Import sorting and organization
- **Pre-commit Hooks** - Automated code quality checks
- **SOLID Principles** - Architecture validation and testing

### Database Management
- **Alembic Migrations** - Version-controlled schema changes
- **Database Seeding** - Initial data population for development
- **Test Data Management** - Isolated test environments with cleanup

## Deployment Architecture

### Containerization
- **Docker** - Application containerization with multi-stage builds
- **Docker Compose** - Multi-service orchestration for development
- **Production Deployment** - Kubernetes-ready container images

### Environment Management
- **Environment Variables** - Configuration management via .env files
- **Secret Management** - Secure credential handling for production
- **Configuration Validation** - Startup validation with clear error messages

## Technology Decisions

### Why FastAPI?
- **High Performance** - Async support with excellent throughput
- **Auto Documentation** - OpenAPI/Swagger generation
- **Type Safety** - Native type hint integration
- **WebSocket Support** - Real-time communication capabilities
- **Modern Python** - Full async/await pattern support

### Why Google ADK?
- **Production-Grade** - Enterprise-ready agent development framework
- **Advanced Models** - Native Gemini integration with latest capabilities
- **Session Management** - Built-in state handling and conversation management
- **Tool Integration** - Native function tool support with safety controls
- **Performance** - Optimized message passing and resource management

### Why PostgreSQL?
- **ACID Compliance** - Data integrity and consistency guarantees
- **JSON Support** - Flexible schema capabilities for complex data
- **Performance** - Excellent query optimization and indexing
- **Ecosystem** - Mature tooling and operational knowledge
- **Scalability** - Proven horizontal and vertical scaling patterns

### Why Redis?
- **In-Memory Performance** - Sub-millisecond response times for caching
- **Pub/Sub Support** - Native real-time messaging capabilities
- **Celery Integration** - Seamless task queue broker functionality
- **Simple Operations** - Straightforward deployment and scaling
- **Data Structures** - Rich data types for complex caching scenarios

This technology stack provides a robust foundation for enterprise-grade multi-agent orchestration with comprehensive safety controls, real-time communication, and production-ready scalability.