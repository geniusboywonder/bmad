# Technology Stack

## Overview

BotArmy POC leverages a modern, scalable technology stack designed for multi-agent orchestration, real-time communication, and robust data persistence.

## Backend Stack

### Core Framework

- **FastAPI 0.104.1** - High-performance Python web framework for APIs
- **Uvicorn 0.24.0** - ASGI server with WebSocket support
- **Python 3.11+** - Runtime environment

### Data & Persistence

- **PostgreSQL** - Primary relational database for application data
- **SQLAlchemy 2.0.43** - Modern Python SQL toolkit and ORM
- **Alembic 1.13.1** - Database migration management
- **Redis 5.0.1** - Caching layer and message broker

### Agent Framework (Task 2 Enhanced)

- **AutoGen AgentChat 0.7.4** - Microsoft's multi-agent conversation framework with enhanced integration
  - **ConversableAgent Integration**: Each agent wraps AutoGen ConversableAgent instances
  - **GroupChat Support**: Multi-agent collaboration with round-robin speaker selection
  - **Dynamic Configuration**: Runtime agent config loading from `.bmad-core/agents/`
  - **Context Passing**: Structured handoff management via HandoffSchema
- **BaseAgent Architecture** - Abstract agent foundation with LLM reliability integration
  - **Factory Pattern**: Type-based agent instantiation via AgentService
  - **LLM Reliability**: Integration with Task 1 validation, retry, and monitoring
  - **Context Management**: Artifact consumption and creation with validation
- **Celery 5.3.4** - Distributed task queue for asynchronous processing

### Data Validation & Serialization

- **Pydantic 2.10.0** - Data validation using Python type hints with enhanced validation patterns
  - **Custom Validators**: Agent type validation, limit constraints, and enum value verification
  - **Field Validation**: Comprehensive field-level validation with descriptive error messages
  - **Model Consistency**: Standardized metadata field naming and UUID serialization handling
  - **Type Safety**: Strengthened type safety across all data models with proper enum handling
- **Pydantic Settings 2.5.0** - Configuration management
- **orjson 3.9.10** - Fast JSON serialization

### Communication & Networking

- **WebSockets 12.0** - Real-time bidirectional communication
- **Docker 7.1.0** - Containerization support

### Development & Testing

- **pytest 7.4.3** - Testing framework
- **pytest-asyncio 0.21.1** - Async testing support
- **httpx 0.25.2** - HTTP client for testing

### Utilities

- **structlog 23.2.0** - Structured logging
- **python-dotenv 1.0.0** - Environment variable management
- **click 8.1.7** - Command-line interface creation

## Frontend Stack

### Framework (Planned/In Development)

- **Next.js** - React-based framework for web applications
- **React** - Component-based UI library
- **TypeScript** - Type-safe JavaScript development
- **Tailwind CSS** - Utility-first CSS framework
- **Zustand** - Lightweight state management

## Infrastructure Components

### Message Broker & Queue

- **Redis** - Task queue broker and caching
- **Celery** - Asynchronous task processing

### Database

- **PostgreSQL** - ACID-compliant relational database
- **Connection Pooling** - Efficient database connections

### Real-time Communication

- **WebSocket Manager** - Custom WebSocket connection management
- **Event Broadcasting** - Real-time status updates

## BMAD Core Integration (Task 3 - Implemented)

### YAML Parser Utilities

- **Robust YAML Parsing** - Schema validation with comprehensive error handling
- **Variable Substitution Engine** - `{{variable}}` pattern support with conditional logic
- **Type Safety** - Full type validation and data integrity checks
- **Error Recovery** - Graceful handling of malformed configurations

### Template System

- **Dynamic Template Loading** - Runtime loading from `.bmad-core/templates/` directory
- **Multi-Format Rendering** - Support for Markdown, HTML, JSON, and YAML output formats
- **Conditional Sections** - `condition: variable_exists` logic for dynamic content
- **Template Validation** - Schema validation and caching for performance
- **Variable Substitution** - Advanced templating with nested variable support

### Workflow System

- **Dynamic Workflow Loading** - Runtime loading from `.bmad-core/workflows/` directory
- **Execution Orchestration** - Multi-agent workflow coordination with state management
- **Handoff Processing** - Structured agent transitions with prompt generation
- **Progress Tracking** - Real-time workflow execution monitoring and validation
- **Error Handling** - Comprehensive workflow failure recovery and retry logic

### Agent Team Integration

- **Team Configuration Loading** - Runtime loading from `.bmad-core/agent-teams/` directory
- **Compatibility Matching** - Intelligent team-to-workflow compatibility validation
- **Team Composition Validation** - Automated validation of agent combinations
- **Dynamic Assignment** - Runtime agent team assignment based on workflow requirements

### REST API Integration

- **Template Management** - Complete CRUD operations for template lifecycle
- **Workflow Execution** - REST endpoints for workflow orchestration and monitoring
- **Team Management** - API endpoints for team configuration and validation
- **Health Monitoring** - System health checks for BMAD Core components
- **Error Handling** - Comprehensive error responses with detailed diagnostics

### Testing & Validation

- **Unit Test Coverage** - 100% test coverage for all BMAD Core components
- **Integration Testing** - End-to-end workflow validation and performance testing
- **Mock Infrastructure** - Comprehensive mocking for external dependencies
- **Performance Validation** - Sub-200ms response time validation for all endpoints

## LLM Provider Support

### Multi-Provider Architecture

- **OpenAI GPT-4** - Primary reasoning and technical tasks
- **Anthropic Claude** - Requirements analysis and documentation
- **Google Gemini** - Alternative provider with fallback
- **Provider Abstraction** - Unified interface for all LLMs

### LLM Reliability & Monitoring (Task 1 Implementation)

- **Response Validation** - Comprehensive validation and sanitization of LLM responses
- **Exponential Backoff Retry** - 1s, 2s, 4s retry intervals with intelligent error classification
- **Usage Tracking** - Real-time token consumption and cost monitoring
- **Anomaly Detection** - Automated detection of cost spikes and error patterns
- **Health Monitoring** - LLM provider connectivity and performance tracking
- **Structured Logging** - Machine-readable monitoring data for observability

## Development Tools

### Code Quality

- **Black** - Python code formatting
- **isort** - Import sorting
- **Pre-commit hooks** - Automated code quality checks

### Database Management

- **Alembic migrations** - Version-controlled schema changes
- **Database seeding** - Initial data population

### Monitoring & Observability

- **Structured logging** - JSON-formatted logs
- **Health checks** - System status monitoring
- **Performance metrics** - Response time tracking

## Deployment Architecture

### Containerization

- **Docker** - Application containerization
- **Docker Compose** - Multi-service orchestration

### Environment Management

- **Environment variables** - Configuration management
- **Secrets management** - Secure credential handling

## Security Considerations

### Data Protection

- **Input validation** - Pydantic schema validation
- **SQL injection prevention** - SQLAlchemy ORM protection
- **CORS configuration** - Cross-origin request security

### Authentication & Authorization

- **JWT tokens** - Stateless authentication (planned)
- **Role-based access** - Permission management (planned)

## Performance Optimizations

### Caching Strategy

- **Redis caching** - Sub-200ms API responses
- **Connection pooling** - Database efficiency
- **WebSocket optimization** - Real-time communication

### Asynchronous Processing

- **Async/await patterns** - Non-blocking I/O
- **Task queues** - Background processing
- **Retry mechanisms** - Fault tolerance

## Monitoring & Debugging

### Logging

- **Structured logging** - Machine-readable log format
- **Log levels** - Configurable verbosity
- **Context propagation** - Request tracking

### Testing Strategy

- **Unit tests** - Component-level testing
- **Integration tests** - Service interaction testing
- **End-to-end tests** - Full workflow validation

## Technology Decisions

### Why FastAPI?

- High performance with async support
- Automatic API documentation generation
- Excellent type hint integration
- Native WebSocket support

### Why AutoGen? (Task 2 Enhanced)

- **Microsoft-backed Framework**: Enterprise-grade multi-agent conversation management
- **Structured Conversation**: Built-in support for agent-to-agent communication patterns
- **Extensible Architecture**: Easy integration with custom agent implementations via ConversableAgent
- **GroupChat Capabilities**: Native support for multi-agent collaboration scenarios
- **LLM Provider Agnostic**: Seamless integration with OpenAI, Claude, and other providers
- **Code Execution**: Built-in support for code generation and execution workflows
- **Context Management**: Sophisticated conversation context and state management
- **Speaker Selection**: Configurable agent selection methods (round-robin, manual, auto)

### Why PostgreSQL?

- ACID compliance for data integrity
- JSON support for flexible schemas
- Mature ecosystem and tooling
- Excellent performance characteristics

### Why Redis?

- In-memory performance for caching
- Native pub/sub for real-time features
- Celery broker compatibility
- Simple deployment and scaling
