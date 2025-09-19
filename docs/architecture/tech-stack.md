# Technology Stack

## Overview

BotArmy POC leverages a modern, scalable technology stack designed for multi-agent orchestration, real-time communication, and robust data persistence.

## Backend Stack

### Core Framework

- **FastAPI >=0.115.0** - High-performance Python web framework for APIs (updated for Google ADK compatibility)
- **Uvicorn >=0.32.0** - ASGI server with WebSocket support (updated for Google ADK compatibility)
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
  - **Lazy Initialization**: Improved startup reliability with lazy connection patterns
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
- **SOLID Refactored Orchestrator Services** - Modular orchestration architecture following SOLID principles
  - **OrchestratorCore**: Main coordination logic with dependency injection (309 LOC)
  - **ProjectLifecycleManager**: Project state and phase management (373 LOC)
  - **AgentCoordinator**: Agent assignment and task distribution (375 LOC)
  - **WorkflowIntegrator**: Workflow engine integration and coordination (391 LOC)
  - **HandoffManager**: Agent handoff and task transition management (338 LOC)
  - **StatusTracker**: Project status monitoring and performance metrics (441 LOC)
  - **ContextManager**: Context artifact management with granularity features (614 LOC)
  - **Service Interfaces**: Complete interface layer for dependency injection and testing
  - **Backward Compatibility**: Legacy OrchestratorService alias maintained for existing code
- **Enhanced AutoGen Framework Integration** - Microsoft's multi-agent conversation framework (TR-06 to TR-09)
  - **ConversationManager**: Enhanced conversation patterns with context passing and validation
    - `create_agent_conversation()`: Dedicated AutoGen conversation creation
    - `validate_conversation_patterns()`: AutoGen best practice enforcement
    - `ensure_context_continuity()`: Context preservation across handoffs
  - **GroupChatManager**: Multi-agent collaboration with conflict resolution (TR-08)
    - `create_group_chat()`: Dynamic group chat scenarios with agent context
    - `manage_group_conversation()`: Conversation flow management and result collection
    - `resolve_group_conflicts()`: Majority vote, expert arbitration, and human escalation
    - `execute_parallel_agent_tasks()`: Parallel task execution with group chat coordination
  - **Enhanced AgentFactory**: AutoGen configuration loading from .bmad-core/agents/ (TR-09)
    - `_load_autogen_configs()`: Loads agent configurations from .bmad-core/agents/ directory
    - `_parse_agent_config()`: Comprehensive markdown configuration parsing
    - Configuration extraction for system messages, LLM settings, tools, capabilities
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
  - **Enhanced Startup**: Improved worker startup reliability with PID tracking and logging

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

### HITL Safety Architecture (Agent Runaway Prevention - Fully Implemented)

- **Production-Ready API Endpoints**: 9 dedicated HITL safety endpoints (`/api/v1/hitl-safety/*`)
  - **Health Monitoring**: `/api/v1/hitl-safety/health` - Real-time safety system status
  - **Agent Execution Controls**: `/api/v1/hitl-safety/request-agent-execution` and `/api/v1/hitl-safety/approve-agent-execution/{approval_id}`
  - **Budget Management**: `/api/v1/hitl-safety/budget/{project_id}/{agent_type}` (GET/PUT)
  - **Emergency Controls**: `/api/v1/hitl-safety/emergency-stop` and `/api/v1/hitl-safety/emergency-stops`
  - **Approval Tracking**: `/api/v1/hitl-safety/approvals/project/{project_id}` and `/api/v1/hitl-safety/approvals/{approval_id}`
- **Mandatory Agent Approval Controls** - Hard HITL controls preventing unauthorized agent execution
  - **Pre-Execution Approval**: Human approval required before any agent invocation via safety API
  - **Response Approval**: Agent responses must be approved through dedicated approval workflow
  - **Next-Step Authorization**: Explicit human authorization for each subsequent action
  - **Budget Verification**: Human approval of token expenditure for each operation with budget API
- **Agent Budget Control System** - Token-based agent spending limitations
  - **Daily Token Limits**: Configurable per-agent daily consumption limits via budget endpoints
  - **Session Token Limits**: Per-session spending controls with automatic cutoffs
  - **Budget Tracking**: Real-time token usage monitoring and cost calculation via API
  - **Emergency Stop Triggers**: Automatic agent halting when budget thresholds exceeded
- **Emergency Stop System** - Immediate agent halting capabilities
  - **Multi-Trigger Conditions**: User-initiated, budget-based, repetition detection, error-based stops
  - **Global Stop Controls**: System-wide agent termination via emergency stop API
  - **Project-Specific Stops**: Targeted agent termination by project or agent type
  - **Recovery Session Management**: Systematic recovery procedures with rollback options
- **Response Approval Tracking** - Agent output validation and safety scoring
  - **Content Safety Analysis**: Automated safety scoring of agent responses (0.00-1.00)
  - **Code Validation Scoring**: Quality metrics for code generation outputs
  - **Quality Metrics Tracking**: Performance and reliability scoring systems
  - **Approval Status Management**: Complete audit trail via approval tracking endpoints
- **Real-Time Safety Notifications** - WebSocket-based safety event broadcasting
  - **Safety Event Alerts**: Immediate notifications for budget violations, emergency stops
  - **Priority Level Management**: Critical, high, normal, low priority safety events
  - **Delivery Tracking**: Notification delivery confirmation and retry mechanisms
- **System Health Integration**: HITL safety status integrated into system health monitoring
  - **Health Endpoint**: Shows `controls_active: true`, emergency stop status, and feature availability
  - **Production Readiness**: All safety controls operational and validated

### API Architecture & Documentation

- **OpenAPI/Swagger Integration** - Complete API documentation and testing interface
  - **80 Total Endpoints** - Comprehensive API coverage across 9 service groups
  - **Interactive Documentation**: Available at `/docs` with full endpoint testing capabilities
  - **OpenAPI Specification**: Complete JSON specification at `/openapi.json`
  - **Endpoint Groups**: Projects (6), HITL (11), HITL Safety (9), Agents (4), Artifacts (5), ADK (20), Workflows (17), Audit (4), Health (4)
- **RESTful API Design** - Standards-compliant REST API architecture
  - **HTTP Methods**: Proper GET, POST, PUT, DELETE verb usage
  - **Status Codes**: Appropriate HTTP status code responses
  - **Error Handling**: Standardized error response format across all endpoints
  - **Content Negotiation**: JSON request/response handling with proper serialization
- **API Security & Validation** - Production-ready security controls
  - **Request Validation**: Pydantic schema validation for all endpoints
  - **Response Serialization**: Type-safe response models with proper JSON encoding
  - **Error Responses**: Consistent error handling with detailed error messages
  - **CORS Configuration**: Cross-origin request handling for frontend integration

### Data Validation & Serialization

- **Pydantic 2.10.0** - Data validation using Python type hints with enhanced validation patterns
  - **Custom Validators**: Agent type validation, limit constraints, and enum value verification
  - **Field Validation**: Comprehensive field-level validation with descriptive error messages
  - **Model Consistency**: Standardized metadata field naming and UUID serialization handling
  - **Type Safety**: Strengthened type safety across all data models with proper enum handling
- **Pydantic Settings 2.5.0** - Configuration management
- **orjson 3.9.10** - Fast JSON serialization

### Communication & Networking (Task 0 Infrastructure - Validated)

- **WebSockets >=15.0.1,<16.0.0** - Real-time bidirectional communication (updated for Google ADK compatibility)
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

### Development & Testing (Production-Grade Test Suite)

- **pytest 7.4.3** - Testing framework with 967 comprehensive tests
- **pytest-asyncio 0.21.1** - Async testing support for real-time operations
- **httpx 0.25.2** - HTTP client for API endpoint testing
- **DatabaseTestManager** - Real database testing utilities with proper session management
  - **Production-Grade Testing**: Real database integration instead of mock-heavy testing
  - **Service Integration**: All services tested with proper dependency injection patterns
  - **Test Data Management**: Automatic cleanup and isolation between test runs
  - **95%+ Success Rate**: Comprehensive test suite refactoring achieved high reliability

**Test Architecture Improvements (September 2025):**

- **Real Database Integration**: Complete migration from mock-heavy to production-like testing
- **Service Constructor Validation**: All services tested with proper dependency injection
- **Template System Testing**: BMAD Core template loading and rendering with real file operations
- **Agent Framework Testing**: AutoGen conversation patterns and team configuration validation
- **HITL Safety Testing**: Complete safety controls testing with real database persistence
- **Infrastructure Testing**: 100% infrastructure and architectural issues resolved

**Test Coverage Excellence:**

- **967 Total Tests**: Comprehensive coverage across all system components
- **Service Layer**: 95%+ coverage for all refactored services with dependency injection
- **Database Integration**: 100% coverage with real database operations
- **API Endpoints**: Complete endpoint testing with error scenarios and performance validation
- **Agent Framework**: Full AutoGen and ADK integration testing
- **Template Processing**: Complete BMAD Core functionality validation

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

## BMAD Core Integration (Enhanced - Missing10.md Implementation)

### YAML Parser Utilities

- **Robust YAML Parsing** - Schema validation with comprehensive error handling
- **Variable Substitution Engine** - `{{variable}}` pattern support with conditional logic
- **Type Safety** - Full type validation and data integrity checks
- **Error Recovery** - Graceful handling of malformed configurations

### Enhanced Template System (TR-11, TR-13)

- **Advanced Template Processing** - Enhanced TemplateRenderer with Jinja2 integration
  - `process_document_template()`: Processes document templates with variable substitution
  - `_process_conditional_logic()`: Handles conditional content based on context variables
  - `_apply_custom_filters()`: Custom Jinja2 filters for BMAD-specific formatting
  - `substitute_variables()`: Enhanced variable substitution with type validation
- **Dynamic Template Loading** - Runtime loading from `.bmad-core/templates/` directory (TR-11)
- **Multi-Format Rendering** - Support for Markdown, HTML, JSON, and YAML output formats
- **Conditional Logic** - Advanced conditional content processing with Jinja2 expressions
- **Custom Filters** - BMAD-specific template filters for specialized formatting
- **Template Validation** - Schema validation and caching for performance

### Enhanced Workflow System (TR-10)

- **Dynamic Workflow Loading** - Enhanced TemplateLoader with .bmad-core/workflows/ support
  - `load_workflow_definitions()`: Loads workflow definitions from .bmad-core/workflows/
  - `_validate_workflow_schema()`: Validates workflow definitions against BMAD schema
  - `get_workflow_definition()`: Retrieves specific workflow with caching support
  - `list_available_workflows()`: Lists all available workflow definitions
- **Execution Orchestration** - Multi-agent workflow coordination with state management
- **Schema Validation** - Comprehensive workflow structure validation with error reporting
- **Caching System** - Intelligent workflow caching for performance optimization
- **Progress Tracking** - Real-time workflow execution monitoring and validation
- **Error Handling** - Comprehensive workflow failure recovery and retry logic

### Enhanced Agent Team Integration (TR-12)

- **Dynamic Team Configuration Loading** - Enhanced support for .bmad-core/agent-teams/
  - `load_agent_team_configurations()`: Loads team configurations from .bmad-core/agent-teams/
  - `_validate_team_config()`: Validates team configurations with coordination patterns
  - `get_team_configuration()`: Retrieves specific team configuration with caching
  - `list_available_teams()`: Lists all available team configurations
- **Coordination Pattern Support** - Sequential, parallel, hybrid, round-robin, priority-based patterns
- **Team Composition Validation** - Automated validation of agent combinations and roles
- **Dynamic Assignment** - Runtime agent team assignment based on workflow requirements
- **Metadata Management** - Complete team configuration metadata and validation tracking

### Unified BMAD Core Service

- **BMADCoreService** - Comprehensive BMAD Core integration service
  - `initialize_bmad_core()`: Initializes all BMAD Core components with validation
  - `validate_bmad_core_structure()`: Validates .bmad-core directory structure and files
  - `get_comprehensive_status()`: Provides unified status across all BMAD Core components
  - `reload_all_configurations()`: Hot-reloads all BMAD Core configurations
- **Component Integration** - Unified management of templates, workflows, and teams
- **Error Recovery** - Comprehensive error handling with retry logic and timeout management
- **Status Monitoring** - Real-time status tracking across all BMAD Core components

### REST API Integration

- **Template Management** - Complete CRUD operations for template lifecycle
- **Workflow Execution** - REST endpoints for workflow orchestration and monitoring
- **Team Management** - API endpoints for team configuration and validation
- **Health Monitoring** - System health checks for BMAD Core components
- **Error Handling** - Comprehensive error responses with detailed diagnostics

### Testing & Validation (Production-Ready Test Suite)

- **Comprehensive Test Coverage** - 967 tests with 95%+ success rate across all BMAD Core components
- **Real Database Integration** - Production-grade testing with DatabaseTestManager utilities
- **Service Integration Testing** - All services tested with proper dependency injection patterns
- **Template System Validation** - Complete BMAD Core template loading and rendering testing
- **Agent Framework Testing** - AutoGen conversation patterns and team configuration validation
- **Performance Validation** - Sub-200ms response time validation for all endpoints
- **Infrastructure Reliability** - 100% infrastructure and architectural issues resolved

**Test Suite Achievements (September 2025):**

- **Service Constructor Fixes** - All template services use proper string path initialization
- **Agent Team Configuration** - Complete team configurations with all required agent types
- **Database Integration** - Migration from mock-heavy to real database testing
- **AutoGen Integration** - Fixed conversation patterns and handoff schema validation
- **Import Path Resolution** - Corrected all module import paths for proper resolution
- **Schema Validation** - Enhanced Pydantic models with proper UUID and field validation

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
- **Provider Abstraction** - Unified interface supporting multiple LLM providers (OpenAI, Anthropic, Google Gemini) via a dynamic factory.

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
- **SOLID Principles Enforcement** - Comprehensive testing for Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion principles

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

### Testing Strategy (967 Tests, 95%+ Success Rate)

**Comprehensive Test Suite (September 2025):**

- **Unit Tests** - Service-level testing with dependency injection validation (95%+ coverage)
- **Integration Tests** - Cross-service workflow testing with real database operations
- **End-to-End Tests** - Complete system workflow validation and performance testing
- **Real Database Tests** - Production-grade database integration with DatabaseTestManager
- **Service Constructor Tests** - Proper dependency injection pattern validation
- **Template System Tests** - BMAD Core template loading and rendering validation
- **Agent Framework Tests** - AutoGen conversation patterns and team configuration testing

**Test Infrastructure Excellence:**

- **DatabaseTestManager** - Real database testing utilities with session management
- **Service Integration** - All services tested with actual database sessions
- **Template Processing** - Real file operations and YAML parsing validation
- **Agent Team Validation** - Complete team configurations with all required agent types
- **Performance Testing** - Sub-200ms response time validation across all endpoints

**Quality Achievements:**

- **Infrastructure Stability** - 0 infrastructure or architectural errors remaining
- **Service Reliability** - All major services tested with real dependencies
- **Integration Confidence** - Complete workflow testing from API to database
- **Error Recovery** - Comprehensive error handling and recovery validation

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
