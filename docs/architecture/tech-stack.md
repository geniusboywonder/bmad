# Technology Stack

## Overview

BotArmy POC leverages a modern, scalable technology stack designed for multi-agent orchestration, real-time communication, and robust data persistence.

## Backend Stack

### Core Framework

- **FastAPI 0.104.1** - High-performance Python web framework for APIs
- **Uvicorn 0.24.0** - ASGI server with WebSocket support
- **Python 3.11+** - Runtime environment

### Data & Persistence (Task 0 Foundation - Implemented)

- **PostgreSQL** - Primary relational database for application data
  - **Database Schema**: Complete schema with core tables plus HITL safety architecture tables
  - **Core Application Tables**: projects, tasks, agent_status, context_artifacts, hitl_requests, event_log
  - **HITL Safety Tables**: hitl_agent_approvals, agent_budget_controls, emergency_stops, response_approvals, recovery_sessions, websocket_notifications
  - **Migration System**: Alembic migrations validated and operational with timezone-aware datetime handling
  - **Performance Indexes**: Optimized indexes for frequently queried fields
  - **Data Integrity**: Fixed Boolean/Enum type consistency across all models
- **SQLAlchemy 2.0.43** - Modern Python SQL toolkit and ORM
  - **Database Models**: Full SQLAlchemy models with proper relationships
  - **Session Management**: Generator-based session handling with proper cleanup
  - **Connection Pooling**: Efficient database connections with StaticPool
- **Alembic 1.13.1** - Database migration management
  - **Initial Migration**: 001_initial_tables.py (comprehensive base schema)
  - **Audit Migration**: 004_add_event_log_table.py (event logging)
  - **Configuration**: Fixed interpolation issues and validated migrations
- **Redis 5.0.1** - Caching layer and message broker
  - **Celery Broker**: Separate Redis instance for task queue
  - **Caching Layer**: High-performance caching for API responses

### Agent Framework (ADK Integration Complete)

- **Google ADK (Agent Development Kit)** - Production-grade agent framework with enterprise controls
  - **Correct API Usage**: Uses `instruction` parameter, `Runner`-based execution, proper session management
  - **LlmAgent Integration**: Advanced agent capabilities with `gemini-2.0-flash` model support
  - **Session Management**: Proper `InMemorySessionService` and `types.Content` message handling
  - **Tool Integration**: `FunctionTool` support with graceful fallback and error handling
  - **BMAD-ADK Wrapper**: Enterprise wrapper preserving BMAD safety controls and audit requirements
  - **Development Tools**: Comprehensive testing framework with benchmarking and HITL simulation
- **Legacy AutoGen Support** - Microsoft's multi-agent conversation framework (backward compatibility)
  - **ConversableAgent Integration**: Legacy agent wrapper for AutoGen instances
  - **GroupChat Support**: Multi-agent collaboration with round-robin speaker selection
  - **Context Passing**: Structured handoff management via HandoffSchema
- **Hybrid Agent Architecture** - Seamless integration between ADK and legacy systems
  - **Agent Factory**: Enhanced factory with ADK support and gradual rollout capabilities
  - **Feature Flags**: Configurable ADK adoption with `use_adk` flag support
  - **Enterprise Integration**: Full HITL safety controls, audit trails, and usage tracking
  - **Tool Registry**: Comprehensive tool management with OpenAPI integration support
- **Celery 5.3.4** - Distributed task queue for asynchronous processing
  - **Real Agent Processing**: Production-ready task execution with lifecycle management
  - **Database Integration**: Full task status tracking with atomic updates
  - **WebSocket Events**: Real-time broadcasting of agent progress and results
  - **Artifact Management**: Dynamic context creation and retrieval during execution

### Workflow Orchestration Engine (Task 5 - Implemented)

- **WorkflowExecutionEngine** - Core workflow orchestration with state machine pattern
  - **Dynamic Workflow Loading**: Runtime loading from BMAD Core templates with YAML parsing
  - **State Machine Pattern**: Complete workflow lifecycle management (PENDING → RUNNING → COMPLETED/FAILED)
  - **Agent Handoff Coordination**: Structured HandoffSchema validation with context passing
  - **Conditional Workflow Routing**: Expression-based decision points and branching logic
  - **Parallel Task Execution**: Concurrent workflow step processing with result aggregation
  - **Workflow State Persistence**: Database-backed state management with recovery mechanisms
  - **Progress Tracking & Milestones**: Real-time workflow monitoring with WebSocket broadcasting
  - **Template System Integration**: Seamless coordination with BMAD Core document generation
  - **Error Recovery Mechanisms**: Multi-tier recovery strategy with automatic retry and escalation
- **WorkflowStepProcessor** - Individual workflow step execution and agent coordination
  - **Step Execution Logic**: Conditional evaluation, task creation, and result processing
  - **Agent Task Management**: AutoGen integration for LLM-powered agent execution
  - **Context Data Updates**: Dynamic context variable management and artifact creation
  - **Parallel Processing Support**: Concurrent step execution with synchronization
- **WorkflowPersistenceManager** - Workflow state persistence and recovery
  - **Database State Management**: SQLAlchemy-based workflow state storage and retrieval
  - **Recovery Mechanisms**: Automatic workflow restoration from persisted state
  - **Cleanup Operations**: Automated removal of old workflow executions
  - **Statistics Generation**: Workflow execution metrics and performance analytics
- **WorkflowHitlIntegrator** - Workflow and HITL system integration
  - **HITL Trigger Checking**: Post-step HITL condition evaluation and request creation
  - **Workflow Pausing/Resuming**: Seamless workflow state management for human approval
  - **HITL Response Handling**: Workflow resumption after human decision processing
  - **Context Preservation**: Maintained workflow state during HITL interactions

### Human-in-the-Loop (HITL) System (Task 6 - Implemented)

- **HitlService** - Comprehensive HITL request lifecycle management
  - **Trigger Condition Evaluation**: Configurable oversight levels and approval workflows
  - **Request Processing**: Approve/Reject/Amend actions with complete audit trails
  - **Context-Aware Interfaces**: Full artifact and task detail provision for informed decisions
  - **Expiration Management**: Configurable timeouts with automatic escalation
  - **Bulk Operations**: Batch approval capabilities for similar requests
  - **Workflow Integration**: Seamless pausing and resumption of workflow execution
- **HitlTriggerManager** - HITL trigger condition management and evaluation
  - **Configurable Trigger Conditions**: Phase completion, quality thresholds, conflicts, errors, budget exceeded, safety violations
  - **Oversight Level Processing**: High/Medium/Low supervision level filtering
  - **Trigger Evaluation Logic**: Context-based condition assessment and request creation
  - **Configuration Management**: Runtime trigger condition updates and validation
- **HITL API Endpoints** - RESTful API for HITL request management
  - **Request Creation**: Automatic HITL request generation based on trigger conditions
  - **Response Processing**: Human decision processing with workflow resumption
  - **Context Retrieval**: Full request context including artifacts and task details
  - **Statistics & Monitoring**: HITL request analytics and performance metrics
- **WebSocket Integration** - Real-time HITL event broadcasting
  - **Request Notifications**: Immediate alerts for new HITL approval requests
  - **Response Broadcasting**: Real-time updates for HITL decision processing
  - **Status Updates**: Live HITL request status changes and workflow state

### HITL Safety Architecture (Agent Runaway Prevention - Implemented)

- **Mandatory Agent Approval Controls** - Hard HITL controls preventing unauthorized agent execution
  - **Pre-Execution Approval**: Human approval required before any agent invocation
  - **Response Approval**: Agent responses must be approved before workflow continuation
  - **Next-Step Authorization**: Explicit human authorization for each subsequent action
  - **Budget Verification**: Human approval of token expenditure for each operation
- **Agent Budget Control System** - Token-based agent spending limitations
  - **Daily Token Limits**: Configurable per-agent daily consumption limits
  - **Session Token Limits**: Per-session spending controls with automatic cutoffs
  - **Budget Tracking**: Real-time token usage monitoring and cost calculation
  - **Emergency Stop Triggers**: Automatic agent halting when budget thresholds exceeded
- **Emergency Stop System** - Immediate agent halting capabilities
  - **Multi-Trigger Conditions**: User-initiated, budget-based, repetition detection, error-based stops
  - **Global Stop Controls**: System-wide agent termination capabilities
  - **Project-Specific Stops**: Targeted agent termination by project or agent type
  - **Recovery Session Management**: Systematic recovery procedures with rollback options
- **Response Approval Tracking** - Agent output validation and safety scoring
  - **Content Safety Analysis**: Automated safety scoring of agent responses (0.00-1.00)
  - **Code Validation Scoring**: Quality metrics for code generation outputs
  - **Quality Metrics Tracking**: Performance and reliability scoring systems
  - **Approval Status Management**: Complete audit trail of response approvals and rejections
- **Real-Time Safety Notifications** - WebSocket-based safety event broadcasting
  - **Safety Event Alerts**: Immediate notifications for budget violations, emergency stops
  - **Priority Level Management**: Critical, high, normal, low priority safety events
  - **Delivery Tracking**: Notification delivery confirmation and retry mechanisms

### Data Validation & Serialization

- **Pydantic 2.10.0** - Data validation using Python type hints with enhanced validation patterns
  - **Custom Validators**: Agent type validation, limit constraints, and enum value verification
  - **Field Validation**: Comprehensive field-level validation with descriptive error messages
  - **Model Consistency**: Standardized metadata field naming and UUID serialization handling
  - **Type Safety**: Strengthened type safety across all data models with proper enum handling
- **Pydantic Settings 2.5.0** - Configuration management
- **orjson 3.9.10** - Fast JSON serialization

### Communication & Networking (Task 0 Infrastructure - Validated)

- **WebSockets 12.0** - Real-time bidirectional communication
  - **WebSocket Manager**: Global connection management with auto-cleanup
  - **Project-Scoped Broadcasting**: Event distribution by project ID
  - **Event System**: Type-safe WebSocket events with proper serialization
  - **Auto-Reconnection**: Graceful handling of connection failures
- **Health Monitoring** - Multi-tier service health checking
  - **Basic Health**: `/health` endpoint for service status
  - **Detailed Health**: `/health/detailed` with component breakdown
  - **Kubernetes Health**: `/health/z` endpoint for container orchestration
  - **Service Dependencies**: Database, Redis, Celery, and LLM provider monitoring
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

## ADK Tools Integration

### Tool Architecture

- **ADK Tool Registry** - Centralized tool management and assignment system
  - **Function Tools**: Custom Python function integration with ADK framework
  - **OpenAPI Tools**: External API integration with enterprise safety controls
  - **Specialized Tools**: Code analysis, API health checks, and project metrics
  - **Agent-Specific Assignment**: Tool mapping based on agent type and capabilities

### Enterprise Tool Safety

- **HITL Tool Approval** - Human oversight for high-risk tool operations
  - **Risk Assessment**: Automatic risk level evaluation (high/medium/low)
  - **Approval Workflows**: HITL integration for external API calls and write operations
  - **Audit Trails**: Complete tool execution logging with cost tracking
- **BMADOpenAPITool** - Enterprise wrapper for external API integration
  - **Safety Controls**: Risk assessment and HITL approval for external calls
  - **Error Recovery**: Graceful failure handling with comprehensive logging
  - **Cost Monitoring**: Token usage and API call cost estimation

### Tool Development Framework

- **ADK Development Tools** - Comprehensive testing and validation framework
  - **Test Scenarios**: Predefined test cases for agent validation
  - **Benchmarking Tools**: Performance metrics and quality scoring
  - **HITL Simulation**: Development-time human interaction simulation
  - **Integration Testing**: End-to-end tool execution validation

## LLM Provider Support

### Multi-Provider Architecture

- **Google Gemini (Primary)** - ADK-integrated agent execution with `gemini-2.0-flash`
- **OpenAI GPT-4** - Legacy agent support for technical tasks
- **Anthropic Claude** - Legacy agent support for requirements analysis
- **Provider Abstraction** - Unified interface supporting both ADK and legacy agents

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

### Why Google ADK? (Primary Agent Framework)

- **Production-Grade Framework**: Google's enterprise-ready agent development toolkit
- **Advanced Model Access**: Native integration with latest Gemini models (`gemini-2.0-flash`)
- **Proper Session Management**: Built-in session handling with `InMemorySessionService`
- **Tool Integration**: Native support for function tools and external API integration
- **Enterprise Architecture**: Designed for production deployments with proper error handling
- **Performance Optimization**: Efficient message passing with `types.Content` patterns
- **Development Support**: Comprehensive testing and debugging tools

### Why AutoGen? (Legacy Support)

- **Backward Compatibility**: Maintains existing agent implementations during ADK transition
- **Microsoft-backed Framework**: Enterprise-grade multi-agent conversation management
- **GroupChat Capabilities**: Native support for multi-agent collaboration scenarios
- **Structured Conversation**: Built-in support for agent-to-agent communication patterns
- **Gradual Migration**: Allows phased transition to ADK without disrupting existing workflows

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
