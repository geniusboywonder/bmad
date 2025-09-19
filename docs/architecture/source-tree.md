# Source Tree Structure

## Project Root

```
bmad/
├── .bmad-core/                 # BMAD Core framework configuration
├── backend/                    # Python FastAPI backend
├── frontend/                   # Next.js frontend application
├── docs/                       # Project documentation
├── .claude/                    # Claude Code settings and commands
├── .cursor/                    # Cursor IDE configuration
├── .gemini/                    # Gemini AI configuration
├── CLAUDE.md                   # Development instructions
└── .gitignore                  # Git ignore patterns
```

## BMAD Core Framework (.bmad-core/)

```
.bmad-core/
├── agents/                     # Agent persona definitions
│   ├── analyst.md             # Requirements analyst agent
│   ├── architect.md           # System architect agent
│   ├── dev.md                 # Full-stack developer agent
│   ├── qa.md                  # Quality assurance agent
│   └── deployer.md            # Deployment specialist agent
├── agent-teams/               # Predefined team compositions
│   ├── team-all.yaml         # Complete team configuration
│   ├── team-fullstack.yaml   # Full-stack development team
│   └── team-minimal.yaml     # Minimal team configuration
├── tasks/                     # Executable task workflows
│   ├── create-implementation-plan.md
│   ├── nfr-assess.md         # Non-functional requirements assessment
│   ├── qa-gate.md            # Quality gate evaluation
│   ├── review-story.md       # Story review workflow
│   ├── risk-profile.md       # Risk assessment workflow
│   ├── test-design.md        # Test design workflow
│   └── trace-requirements.md # Requirements traceability
├── templates/                 # Document and code templates
│   ├── analyst-implementation-plan-tmpl.yaml
│   ├── architect-implementation-plan-tmpl.yaml
│   ├── coder-implementation-plan-tmpl.yaml
│   ├── deployer-implementation-plan-tmpl.yaml
│   ├── tester-implementation-plan-tmpl.yaml
│   ├── qa-gate-tmpl.yaml     # Quality gate template
│   └── story-tmpl.yaml       # Story template
├── workflows/                 # Workflow definitions
│   ├── greenfield-fullstack.yaml
│   ├── greenfield-service.yaml
│   └── greenfield-ui.yaml
├── core-config.yaml          # Core BMAD configuration
└── user-guide.md            # User documentation
```

## Backend Structure (backend/)

```
backend/
├── alembic/                   # Database migration management
│   ├── versions/             # Database migration scripts
│   ├── env.py               # Alembic environment configuration
│   └── alembic.ini          # Alembic configuration file
├── app/                      # Main application package
│   ├── agents/              # Agent implementations
│   │   ├── adk_agent_with_tools.py    # ADK agent with tools support
│   │   ├── adk_dev_tools.py           # ADK development framework
│   │   ├── bmad_adk_wrapper.py        # BMAD-ADK integration wrapper
│   │   ├── base_agent.py              # Base agent class (legacy)
│   │   ├── factory.py                 # Agent factory with ADK support
│   │   └── [analyst|architect|coder|tester|deployer].py # Legacy agents
│   ├── api/                 # REST API endpoints (81 endpoints, 13 groups)
│   │   ├── adk.py          # ADK endpoints (26 endpoints)
│   │   ├── agents.py       # Agent management (4 endpoints)
│   │   ├── artifacts.py    # Artifact management (5 endpoints)
│   │   ├── audit.py        # Audit trail (4 endpoints)
│   │   ├── health.py       # Health monitoring (5 endpoints)
│   │   ├── hitl.py         # Human-in-the-loop (12 endpoints)
│   │   ├── hitl_safety.py  # HITL safety controls (10 endpoints)
│   │   ├── projects.py     # Project management (6 endpoints)
│   │   ├── websocket.py    # WebSocket handlers
│   │   └── workflows.py    # Workflow management (17 endpoints)
│   ├── database/           # Database layer
│   │   ├── connection.py   # Database connection and session management
│   │   └── models.py       # SQLAlchemy ORM models
│   ├── models/             # Pydantic data models
│   │   ├── agent.py        # Agent data models
│   │   ├── context.py      # Context and artifact models
│   │   ├── handoff.py      # Agent handoff models
│   │   ├── hitl.py         # HITL and safety models
│   │   ├── hitl_request.py # HITL request models
│   │   ├── quality_gate.py # Quality gate models
│   │   ├── task.py         # Task execution models
│   │   └── workflow.py     # Workflow execution models
│   ├── services/           # Business logic services (SOLID architecture)
│   │   ├── orchestrator/   # Orchestrator service components
│   │   │   ├── orchestrator_core.py      # Main coordination logic
│   │   │   ├── project_lifecycle_manager.py # SDLC phase management
│   │   │   ├── agent_coordinator.py       # Agent assignment and distribution
│   │   │   ├── workflow_integrator.py     # Workflow engine integration
│   │   │   ├── handoff_manager.py         # Agent handoff coordination
│   │   │   ├── status_tracker.py          # Project status monitoring
│   │   │   └── context_manager.py         # Context artifact management
│   │   ├── hitl/           # HITL service components
│   │   │   ├── hitl_core.py              # Core HITL coordination
│   │   │   ├── trigger_processor.py      # Trigger evaluation
│   │   │   ├── response_processor.py     # Response handling
│   │   │   ├── phase_gate_manager.py     # Phase gate validation
│   │   │   └── validation_engine.py      # Quality validation
│   │   ├── workflow/       # Workflow service components
│   │   │   ├── execution_engine.py       # Workflow execution logic
│   │   │   ├── state_manager.py          # State persistence
│   │   │   ├── event_dispatcher.py       # Event broadcasting
│   │   │   └── sdlc_orchestrator.py      # SDLC workflow logic
│   │   ├── template/       # Template service components
│   │   │   ├── template_core.py          # Template coordination
│   │   │   ├── template_loader.py        # Template loading and caching
│   │   │   └── template_renderer.py      # Template rendering
│   │   ├── autogen/        # AutoGen service components
│   │   │   ├── autogen_core.py           # AutoGen coordination
│   │   │   ├── agent_factory.py          # Agent instantiation
│   │   │   ├── conversation_manager.py   # Conversation management
│   │   │   └── group_chat_manager.py     # Multi-agent collaboration
│   │   ├── adk_orchestration_service.py  # ADK multi-agent orchestration
│   │   ├── adk_handoff_service.py        # ADK agent handoff management
│   │   ├── agent_status_service.py       # Agent status management
│   │   ├── artifact_service.py           # Artifact generation and management
│   │   ├── audit_service.py              # Audit trail and compliance
│   │   ├── bmad_core_service.py          # BMAD Core integration
│   │   ├── context_store.py              # Context storage service
│   │   ├── hitl_safety_service.py        # HITL safety controls
│   │   ├── project_completion_service.py # Project lifecycle management
│   │   ├── quality_gate_service.py       # Quality gate evaluation
│   │   └── response_safety_analyzer.py   # Response safety analysis
│   ├── tools/              # ADK tools integration
│   │   ├── adk_openapi_tools.py          # OpenAPI integration tools
│   │   ├── adk_tool_registry.py          # Tool registry and management
│   │   └── specialized_adk_tools.py      # Specialized function tools
│   ├── tasks/              # Celery task definitions
│   │   ├── agent_tasks.py  # Agent execution tasks
│   │   └── celery_app.py   # Celery application setup
│   ├── websocket/          # WebSocket management
│   │   ├── events.py       # WebSocket event handlers
│   │   └── manager.py      # WebSocket connection management
│   ├── settings.py         # Application configuration
│   └── main.py            # FastAPI application entry point
├── tests/                  # Comprehensive test suite (967 tests, 95%+ success)
│   ├── conftest.py        # Test configuration with DatabaseTestManager
│   ├── utils/             # Test utilities
│   │   └── database_test_utils.py # Real database testing utilities
│   ├── integration/       # Integration tests with real database
│   │   ├── test_adk_integration.py
│   │   ├── test_agent_conversation_flow.py
│   │   ├── test_context_persistence_integration.py
│   │   ├── test_database_schema_validation.py
│   │   ├── test_full_stack_api_database_flow.py
│   │   └── test_hitl_response_handling_integration.py
│   ├── unit/              # Unit tests with dependency injection
│   │   ├── test_adk_handoff_service.py
│   │   ├── test_adk_orchestration_service.py
│   │   ├── test_agent_status_service.py
│   │   ├── test_artifact_service.py
│   │   ├── test_project_completion_service.py
│   │   └── test_template_service.py
│   ├── test_adk_integration.py        # ADK core integration tests
│   ├── test_adk_tools.py              # ADK tools framework tests
│   ├── test_autogen_conversation.py   # AutoGen conversation tests
│   ├── test_bmad_template_loading.py  # BMAD template loading tests
│   ├── test_health.py                 # Health endpoint tests
│   ├── test_hitl_safety.py            # HITL safety system tests
│   ├── test_marker_check.py           # Test marker validation
│   ├── test_orchestrator_services_real.py # Real orchestrator tests
│   └── test_workflow_engine_real_db.py # Workflow engine tests
├── scripts/               # Development and deployment scripts
│   └── start_dev.sh      # Development startup script
├── adk_feature_flags.json # ADK feature flag configuration
├── celery.log            # Celery worker log file
├── celery.pid            # Celery worker PID file
├── pyproject.toml        # Python project configuration
└── README.md             # Backend documentation
```

## Frontend Structure (frontend/)

```
frontend/
├── app/                      # Next.js App Router structure
│   ├── analytics/           # Analytics and metrics pages
│   ├── api/                # API route handlers
│   ├── artifacts/          # Project artifacts management
│   ├── bot-army-ux-review/ # UX review components
│   ├── deploy/             # Deployment management
│   ├── design/             # Design system pages
│   ├── dev/                # Development tools
│   ├── hitl-test/          # HITL testing interface
│   ├── logs/               # System logs interface
│   ├── processes/          # Process management
│   ├── requirements/       # Requirements management
│   ├── settings/           # Application settings
│   ├── tasks/              # Task management interface
│   ├── test/               # Testing interface
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout component
│   └── page.tsx            # Home page component
├── components/             # Reusable UI components
├── hooks/                  # Custom React hooks
├── lib/                    # Utility libraries and configurations
├── public/                 # Static assets
├── styles/                 # Additional stylesheets
├── components.json         # shadcn/ui configuration
├── next.config.mjs         # Next.js configuration
├── package.json            # Node.js dependencies
├── tailwind.config.js      # Tailwind CSS configuration
└── tsconfig.json          # TypeScript configuration
```

## Documentation Structure (docs/)

```
docs/
├── architecture/           # System architecture documentation
│   ├── architecture.md    # Main architecture document
│   ├── source-tree.md     # This document
│   └── tech-stack.md      # Technology stack overview
├── qa/                    # Quality assurance documentation
│   ├── gates/             # Quality gate decisions
│   └── reports/           # QA analysis reports
├── CHANGELOG.md           # Project change history
├── CODEPROTOCOL.md        # Development workflow protocol
├── SOLID.md               # SOLID principles guide
├── STYLEGUIDE.md          # Code style guidelines
└── TESTPROTOCOL.md        # Testing standards and protocols
```

## AI Integration Structure

```
.claude/
├── commands/              # Claude-specific commands
└── settings.local.json    # Claude configuration

.cursor/
└── rules/                 # Cursor IDE rules

.gemini/
├── commands/              # Gemini-specific commands
└── configuration files
```

## Key Architectural Patterns

### Layered Architecture

**API Layer**
- FastAPI REST endpoints with OpenAPI documentation
- WebSocket handlers for real-time communication
- Request/response validation with Pydantic models

**Service Layer**
- SOLID-principle based service decomposition
- Dependency injection for loose coupling
- Business logic separation from presentation

**Data Layer**
- SQLAlchemy ORM models with proper relationships
- Database migrations with Alembic
- Context store for artifact management

**Integration Layer**
- Multi-LLM provider support (OpenAI, Anthropic, Google)
- BMAD Core framework integration
- External service connections with retry logic

### Domain Separation

**Agent Management**
- Agent lifecycle and status tracking
- ADK and AutoGen framework integration
- Tool registry and execution management

**Project Orchestration**
- Workflow and task management
- SDLC phase coordination
- Multi-agent collaboration patterns

**Human-in-the-Loop (HITL)**
- Approval workflows and safety controls
- Budget management and emergency stops
- Response validation and quality gates

**Context Management**
- Artifact storage and retrieval
- Mixed-granularity data persistence
- Cross-agent context sharing

### Configuration Management

**Environment-based Configuration**
- Development, staging, production environments
- Secret management and secure credential handling
- Environment variable validation at startup

**BMAD Core Integration**
- Dynamic template and workflow loading
- Agent configuration from `.bmad-core/agents/`
- Team composition and coordination patterns

**Feature Flags**
- ADK gradual rollout configuration
- A/B testing and experimental features
- Runtime feature toggling

### Testing Strategy

**Production-Grade Test Suite**
- **967 total tests** with **95%+ success rate**
- Real database integration with `DatabaseTestManager`
- Service integration with proper dependency injection
- Complete API endpoint coverage

**Test Categories**
- **Unit Tests**: Service-level testing with mocking
- **Integration Tests**: Cross-service workflow validation
- **End-to-End Tests**: Complete system workflow testing
- **Real Database Tests**: Production-like database operations
- **Performance Tests**: Response time and load validation

**Quality Metrics**
- Infrastructure stability (100% passing)
- Service reliability with real dependencies
- API performance (<200ms response times)
- WebSocket latency (<100ms delivery)

## Development Workflow

### Code Organization Principles

**Single Responsibility**
- Each module serves one clear purpose
- Service decomposition following SOLID principles
- Clear separation of concerns

**Type Safety**
- Comprehensive type hints throughout codebase
- Pydantic model validation for all data
- TypeScript for frontend development

**Error Handling**
- Structured exception management
- Graceful degradation patterns
- Comprehensive retry logic with exponential backoff

**Documentation**
- Inline code documentation
- API documentation with OpenAPI
- Architectural decision records

### Quality Assurance

**Automated Testing**
- Continuous integration with test validation
- Real database testing for production confidence
- Performance benchmarking and monitoring

**Code Quality**
- Automated formatting with Black and Prettier
- Static analysis and linting
- Pre-commit hooks for quality gates

**Security**
- Input validation and sanitization
- Secret management for production deployment
- Audit trails and compliance tracking

This source tree represents a mature, production-ready multi-agent orchestration platform with comprehensive safety controls, real-time communication capabilities, and enterprise-grade quality assurance.