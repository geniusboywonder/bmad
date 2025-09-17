# Source Tree Structure

## Project Root

```
bmad/
├── .bmad-core/                 # BMAD Core framework configuration
├── .claude/                   # Claude Code settings and commands
├── .cursor/                   # Cursor IDE configuration
├── .gemini/                   # Gemini AI configuration
├── backend/                   # Python FastAPI backend
├── docs/                      # Project documentation
├── frontend/                  # Next.js frontend application
├── venv/                     # Python virtual environment
├── CLAUDE.md                 # Claude development instructions
└── .gitignore               # Git ignore patterns
```

## BMAD Core Framework (.bmad-core/)

```
.bmad-core/
├── agents/                   # Agent persona definitions
│   ├── analyst.md           # Requirements analyst agent
│   ├── architect.md         # System architect agent
│   ├── bmad-master.md       # Master orchestrator agent
│   ├── bmad-orchestrator.md # Project orchestrator agent
│   ├── dev.md              # Full-stack developer agent
│   ├── pm.md               # Project manager agent
│   ├── po.md               # Product owner agent
│   ├── qa.md               # Quality assurance agent
│   ├── sm.md               # Scrum master agent
│   └── ux-expert.md        # UX design expert agent
├── agent-teams/             # Predefined team compositions
│   ├── team-all.yaml       # Complete team configuration
│   ├── team-fullstack.yaml # Full-stack development team
│   ├── team-ide-minimal.yaml # Minimal IDE integration team
│   └── team-no-ui.yaml     # Backend-only team
├── checklists/             # Quality assurance checklists
│   ├── architect-checklist.md
│   ├── change-checklist.md
│   ├── pm-checklist.md
│   ├── po-master-checklist.md
│   ├── story-dod-checklist.md
│   └── story-draft-checklist.md
├── data/                   # Reference data and knowledge base
│   ├── bmad-kb.md          # BMAD knowledge base
│   ├── brainstorming-techniques.md
│   ├── elicitation-methods.md
│   ├── technical-preferences.md
│   ├── test-levels-framework.md
│   └── test-priorities-matrix.md
├── tasks/                  # Executable task workflows
│   ├── advanced-elicitation.md
│   ├── apply-qa-fixes.md
│   ├── brownfield-create-epic.md
│   ├── brownfield-create-story.md
│   ├── correct-course.md
│   ├── create-brownfield-story.md
│   ├── create-deep-research-prompt.md
│   ├── create-doc.md
│   ├── create-next-story.md
│   ├── document-project.md
│   ├── execute-checklist.md
│   ├── facilitate-brainstorming-session.md
│   ├── generate-ai-frontend-prompt.md
│   ├── index-docs.md
│   ├── kb-mode-interaction.md
│   ├── nfr-assess.md
│   ├── qa-gate.md
│   ├── review-story.md
│   ├── risk-profile.md
│   ├── shard-doc.md
│   ├── test-design.md
│   ├── trace-requirements.md
│   └── validate-next-story.md
├── templates/              # Document and code templates
│   ├── architecture-tmpl.yaml
│   ├── brainstorming-output-tmpl.yaml
│   ├── brownfield-architecture-tmpl.yaml
│   ├── brownfield-prd-tmpl.yaml
│   ├── competitor-analysis-tmpl.yaml
│   ├── front-end-architecture-tmpl.yaml
│   ├── front-end-spec-tmpl.yaml
│   ├── fullstack-architecture-tmpl.yaml
│   ├── market-research-tmpl.yaml
│   ├── prd-tmpl.yaml
│   ├── project-brief-tmpl.yaml
│   ├── qa-gate-tmpl.yaml
│   └── story-tmpl.yaml
├── utils/                  # Utility documents and tools
│   ├── bmad-doc-template.md
│   └── workflow-management.md
├── workflows/              # Workflow definitions
│   ├── brownfield-fullstack.yaml
│   ├── brownfield-service.yaml
│   ├── brownfield-ui.yaml
│   ├── greenfield-fullstack.yaml
│   ├── greenfield-service.yaml
│   └── greenfield-ui.yaml
├── core-config.yaml        # Core BMAD configuration
├── enhanced-ide-development-workflow.md
├── install-manifest.yaml   # Installation configuration
├── user-guide.md          # User documentation
└── working-in-the-brownfield.md
```

## Backend Structure (backend/)

```
backend/
├── alembic/                # Database migration management
│   ├── versions/           # Database migration scripts
│   │   ├── 001_initial_tables.py        # Initial database schema (Task 0)
│   │   └── 004_add_event_log_table.py   # Event log table for audit trail
│   ├── env.py             # Alembic environment configuration
│   └── alembic.ini        # Alembic configuration file
├── app/                   # Main application package
│   ├── agents/            # Agent implementations
│   │   ├── __init__.py
│   │   ├── adk_agent_with_tools.py    # ADK agent with tools support
│   │   ├── adk_dev_tools.py           # ADK development and testing framework
│   │   ├── analyst.py                 # Legacy analyst agent (AutoGen)
│   │   ├── architect.py               # Legacy architect agent (AutoGen)
│   │   ├── base_agent.py              # Legacy base agent class (AutoGen)
│   │   ├── bmad_adk_wrapper.py        # BMAD-ADK integration wrapper
│   │   ├── coder.py                   # Legacy coder agent (AutoGen)
│   │   ├── deployer.py                # Legacy deployer agent (AutoGen)
│   │   ├── factory.py                 # Agent factory with ADK support
│   │   ├── orchestrator.py            # Legacy orchestrator agent (AutoGen)
│   │   └── tester.py                  # Legacy tester agent (AutoGen)
│   ├── api/               # REST API endpoints
│   │   ├── __init__.py
│   │   ├── agents.py      # Agent management endpoints
│   │   ├── artifacts.py   # Artifact management endpoints
│   │   ├── dependencies.py # FastAPI dependency injection
│   │   ├── health.py      # Health check endpoints
│   │   ├── hitl.py        # Human-in-the-loop endpoints (Task 6)
│   │   ├── hitl_request_endpoints.py # HITL request management (Task 6)
│   │   ├── projects.py    # Project management endpoints
│   │   └── websocket.py   # WebSocket endpoint handlers
│   ├── database/          # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py  # Database connection management with session handling
│   │   └── models.py      # SQLAlchemy ORM models with HITL safety architecture
│   ├── models/            # Pydantic data models
│   │   ├── __init__.py
│   │   ├── agent.py       # Agent data models with status enumeration
│   │   ├── context.py     # Context data models with artifact types
│   │   ├── handoff.py     # Enhanced handoff data models with priority and status
│   │   ├── hitl.py        # HITL data models with safety controls and history (Task 6)
│   │   ├── task.py        # Task data models with enhanced validation (Task 4)
│   │   ├── template.py    # Template data models (Task 3)
│   │   ├── workflow.py    # Workflow data models with execution state (Task 5)
│   │   └── workflow_state.py # Workflow state management models (Task 5)
│   ├── interfaces/         # Service interfaces for dependency injection
│   │   ├── __init__.py
│   │   ├── orchestrator_interface.py    # Main orchestrator interface
│   │   ├── project_lifecycle_interface.py # Project lifecycle management interface
│   │   ├── agent_coordinator_interface.py # Agent coordination interface
│   │   ├── workflow_integrator_interface.py # Workflow integration interface
│   │   ├── handoff_manager_interface.py  # Handoff management interface
│   │   ├── status_tracker_interface.py   # Status tracking interface
│   │   └── context_manager_interface.py  # Context management interface
│   ├── schemas/           # API request/response schemas
│   │   ├── __init__.py
│   │   ├── handoff.py     # Handoff schemas
│   │   └── hitl.py        # HITL schemas
│   ├── services/          # Business logic services (SOLID Refactored 2024-09-17)
│   │   ├── __init__.py
│   │   ├── adk_handoff_service.py  # ADK agent handoff management
│   │   ├── adk_orchestration_service.py # ADK multi-agent orchestration
│   │   ├── agent_service.py        # Agent service with factory pattern and dependency injection
│   │   ├── agent_status_service.py # Agent status management
│   │   ├── artifact_service.py     # Artifact management
│   │   ├── audit_service.py        # Audit trail and event logging (Task 0)
│   │   ├── autogen/                # SOLID refactored AutoGen services (681 LOC → 3 services)
│   │   │   ├── __init__.py         # Package initialization with backward compatibility
│   │   │   ├── autogen_core.py     # Main coordination logic with dependency injection (126 LOC)
│   │   │   ├── agent_factory.py    # Agent instantiation and configuration management (208 LOC)
│   │   │   └── conversation_manager.py # Conversation flow and message handling (554 LOC)
│   │   ├── autogen_service.py      # Backward compatibility alias module
│   │   ├── context_store.py        # Context storage service with database integration
│   │   ├── hitl/                   # SOLID refactored HITL services (1,325 LOC → 5 services)
│   │   │   ├── __init__.py         # Package initialization with backward compatibility
│   │   │   ├── hitl_core.py        # Core HITL coordination logic with dependency injection (285 LOC)
│   │   │   ├── trigger_processor.py # Trigger evaluation and condition management (351 LOC)
│   │   │   ├── response_processor.py # Response handling and workflow resumption (425 LOC)
│   │   │   ├── phase_gate_manager.py # Phase gate validation and approval workflows (628 LOC)
│   │   │   └── validation_engine.py # Quality validation and threshold management (667 LOC)
│   │   ├── hitl_safety_service.py  # HITL safety service for ADK integration
│   │   ├── hitl_service.py         # Backward compatibility alias module
│   │   ├── hitl_trigger_manager.py # HITL trigger condition management (with HITLTriggerManager alias)
│   │   ├── llm_monitoring.py       # LLM usage tracking and cost monitoring (Task 1)
│   │   ├── llm_retry.py           # Exponential backoff retry logic (Task 1)
│   │   ├── llm_validation.py      # Response validation and sanitization (Task 1)
│   │   ├── orchestrator/           # SOLID refactored orchestrator services (2,541 LOC → 7 services)
│   │   │   ├── __init__.py         # Package initialization with backward compatibility
│   │   │   ├── orchestrator_core.py   # Main coordination logic with dependency injection (309 LOC)
│   │   │   ├── project_lifecycle_manager.py # Project state transitions and SDLC phase management (373 LOC)
│   │   │   ├── agent_coordinator.py    # Agent assignment and task distribution logic (375 LOC)
│   │   │   ├── workflow_integrator.py  # Workflow engine integration and coordination (391 LOC)
│   │   │   ├── handoff_manager.py      # Agent handoff logic and task transitions (338 LOC)
│   │   │   ├── status_tracker.py       # Project status monitoring and performance metrics (441 LOC)
│   │   │   └── context_manager.py      # Context artifact management with granularity features (614 LOC)
│   │   ├── orchestrator.py         # Backward compatibility alias module
│   │   ├── project_completion_service.py # Project lifecycle management
│   │   ├── template/               # SOLID refactored template services (526 LOC → 3 services)
│   │   │   ├── __init__.py         # Package initialization with backward compatibility
│   │   │   ├── template_core.py    # Main coordination logic with dependency injection (218 LOC)
│   │   │   ├── template_loader.py  # Template loading and caching mechanisms (171 LOC)
│   │   │   └── template_renderer.py # Template rendering and output formatting (328 LOC)
│   │   ├── template_service.py     # Backward compatibility alias module
│   │   ├── workflow/               # SOLID refactored workflow services (1,226 LOC → 4 services)
│   │   │   ├── __init__.py         # Package initialization with backward compatibility
│   │   │   ├── execution_engine.py # Core workflow execution logic with dependency injection (550 LOC)
│   │   │   ├── state_manager.py    # State persistence and recovery mechanisms (428 LOC)
│   │   │   ├── event_dispatcher.py # Event management and WebSocket broadcasting (521 LOC)
│   │   │   └── sdlc_orchestrator.py # SDLC-specific workflow logic and phase management (581 LOC)
│   │   ├── workflow_engine.py      # Backward compatibility alias module
│   │   ├── workflow_execution_manager.py # Workflow execution coordination (Task 5)
│   │   ├── workflow_service.py     # Workflow definition loading and management (Task 5)
│   │   ├── workflow_step_processor.py # Workflow step execution (Task 5)
│   │   ├── workflow_persistence_manager.py # Workflow state persistence (Task 5)
│   │   └── workflow_hitl_integrator.py # Workflow HITL integration (Task 5)
│   ├── tools/             # ADK tools integration
│   │   ├── __init__.py
│   │   ├── adk_openapi_tools.py    # OpenAPI integration tools
│   │   ├── adk_tool_registry.py    # Tool registry and management
│   │   └── specialized_adk_tools.py # Specialized function tools
│   ├── tasks/             # Celery task definitions (Task 4 Enhanced)
│   │   ├── __init__.py
│   │   ├── agent_tasks.py # Real agent execution with LLM integration
│   │   └── celery_app.py  # Celery application setup
│   ├── websocket/         # WebSocket management
│   │   ├── __init__.py
│   │   ├── events.py      # WebSocket event handlers
│   │   └── manager.py     # WebSocket connection manager
│   ├── __init__.py
│   ├── config.py          # Application configuration
│   └── main.py            # FastAPI application entry point
│   ├── teams/             # Agent team configurations
│   ├── templates/         # Document templates
│   └── workflows/         # Workflow definitions
│   ├── llm_providers/     # LLM provider implementations
│   │   ├── __init__.py
│   │   ├── base_provider.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   ├── provider_factory.py
│   │   └── autogen_model_client_adapter.py
│   ├── group_chat_manager.py # Group chat manager service
├── tests/                 # Test suite
│   ├── e2e/               # End-to-end tests
│   │   ├── test_context_persistence_sprint2_e2e.py
│   │   ├── test_hitl_response_handling_e2e.py
│   │   ├── test_sequential_task_handoff_e2e.py
│   │   ├── test_sprint1_critical_paths.py
│   │   └── test_sprint3_e2e_workflows.py
│   ├── integration/       # Integration tests
│   │   ├── test_autogen_reliability.py     # AutoGen LLM reliability integration (Task 1)
│   │   ├── test_context_persistence_integration.py
│   │   ├── test_context_persistence_sprint2_integration.py
│   │   ├── test_hitl_response_handling_integration.py
│   │   ├── test_project_initiation_integration.py
│   │   ├── test_sequential_task_handoff_integration.py
│   │   └── test_sprint3_api_integration.py
│   ├── unit/              # Unit tests
│   │   ├── test_agent_status_service.py
│   │   ├── test_agent_tasks.py      # Real agent task processing tests (Task 4)
│   │   ├── test_artifact_service.py
│   │   ├── test_context_persistence.py
│   │   ├── test_context_persistence_sprint2.py
│   │   ├── test_hitl_response_handling.py
│   │   ├── test_llm_reliability.py         # LLM reliability components unit tests (Task 1)
│   │   ├── test_project_completion_service.py
│   │   ├── test_project_initiation.py
│   │   └── test_sequential_task_handoff.py
│   ├── __init__.py
│   ├── conftest.py        # Test configuration and fixtures
│   ├── test_health.py     # Health endpoint tests
│   ├── test_orchestrator_refactoring.py # SOLID orchestrator refactoring tests
│   └── README.md          # Test documentation
├── scripts/               # Development and deployment scripts
│   ├── kill_processes.sh # Process cleanup script
│   └── start_dev.sh      # Enhanced development startup script with PID tracking
├── venv/                  # Python virtual environment
├── .env.test              # Test environment configuration (Task 0)
├── adk_feature_flags.json # ADK feature flag configuration
├── celery.log            # Celery worker log file (generated)
├── celery.pid            # Celery worker PID file (generated)
├── docker-compose.dev.yml # Development Docker composition
├── docker-compose.yml     # Production Docker composition
├── install_deps.py        # Dependency installation script
├── pyproject.toml         # Python project configuration
├── README.md              # Backend documentation
├── start_server.py        # Server startup script
├── test_adk_enterprise_integration.py # ADK integration tests
├── test_basic_imports.py  # Basic import validation
└── test_imports.py        # Import dependency validation
```

## Documentation Structure (docs/)

```
docs/
├── architecture/          # System architecture documentation
│   ├── ADK-Hybrid-Architecture.md        # ADK hybrid architecture design
│   ├── ADK-Implementation-Plan.md        # ADK implementation guide
│   ├── ADKPROGRESS.md                   # ADK implementation progress
│   ├── HITL-AGENT-SAFETY-ARCHITECTURE.md # HITL safety architecture and mandatory controls
│   ├── HITL_ARCHITECTURE.md              # HITL system architecture documentation
│   ├── ALL_FIXES_SUMMARY.md
│   ├── FINAL_STATUS.md
│   ├── FIXES_APPLIED.md
│   ├── TROUBLESHOOTING.md
│   ├── architecture.md    # Main architecture document (updated with ADK integration)
│   ├── autogen_dependency_issue.md
│   ├── bmad-APIContract.md # API contract specification
│   ├── bmad-FrontendComponentsStates.md
│   ├── github-autogen.txt
│   ├── source-tree.md     # This document
│   └── tech-stack.md      # Technology stack overview
├── prd/                   # Product requirements documentation
├── qa/                    # Quality assurance documentation
├── sprints/              # Sprint planning and tracking
│   ├── README_SPRINT2.md
│   ├── SPRINT1_SUMMARY.md
│   ├── SPRINT2_COMPLETION_SUMMARY.md
│   ├── SPRINT2_OUTSTANDING_WORK.md
│   ├── SPRINT3_COMPLETION_SUMMARY.md
│   ├── Task0-InfrastructureSetup.md     # Infrastructure foundation (Task 0 - Completed)
│   ├── task4-Replace-Agent-Task-Simulation.md # Real agent processing (Task 4 - Completed)
│   ├── task5-Implement-Workflow.md      # Workflow orchestration engine (Task 5 - Completed)
│   ├── task5-Complete.md                # Task 5 completion documentation
│   ├── task6-Implement-Human-in-the-Loop.md # HITL system (Task 6 - Completed)
│   ├── bmad-Epic1-ProjectLifecycleOrch.md
│   ├── bmad-Epic2-Human-in-the-Loop.md
│   ├── bmad-Epic3-DataStateManagement.md
│   ├── bmad-sprint1.md
│   ├── bmad-sprint2.md
│   ├── bmad-sprint3.md
│   ├── bmad-sprint4.md    # Current sprint documentation
│   ├── epics.md           # Epic definitions
│   ├── stories.md         # User story collection
│   └── task[1-11]-*.md    # Individual task specifications
├── TASK4-TestFailures.md  # Test failure analysis document for architectural fixes
├── TASK3-TESTS-FIXED.md   # Task 3 test corrections documentation
├── genericprompts.md       # Generic prompt templates for agent interactions
├── CHANGELOG.md           # Project change history (updated with Tasks 4-6)
├── CODEPROTOCOL.md        # Development workflow protocol
├── SOLID.md               # SOLID principles guide
└── STYLEGUIDE.md          # Code style guidelines
```

## AI Integration Structure

```
.claude/
├── commands/BMad/         # Claude-specific BMAD commands
│   ├── agents/           # Agent command definitions
│   └── tasks/            # Task command definitions
└── settings.local.json   # Claude configuration

.cursor/
└── rules/bmad/           # Cursor IDE rules for BMAD

.gemini/
├── commands/BMad/        # Gemini-specific BMAD commands
│   ├── agents/          # Agent command definitions
│   └── tasks/           # Task command definitions
```

## Key Architectural Patterns

### Layered Architecture

- **API Layer** - FastAPI endpoints and WebSocket handlers
- **Service Layer** - Business logic and orchestration
- **Data Layer** - Database models and persistence
- **Integration Layer** - External service connections

### Domain Separation

- **Agent Management** - Agent lifecycle and status
- **Project Orchestration** - Workflow and task management
- **Human-in-the-Loop** - User interaction and approval
- **Context Management** - Data persistence and retrieval

### Configuration Management

- **Environment-based** - Development, staging, production
- **BMAD Core integration** - Dynamic template loading
- **Agent configuration** - Runtime agent personality loading

### Testing Strategy

- **Unit tests** - Individual component testing
- **Integration tests** - Service interaction testing
- **End-to-end tests** - Complete workflow validation

## Development Workflow

### Code Organization

- **Single responsibility** - Each module has one clear purpose
- **Dependency injection** - Loose coupling between components
- **Type safety** - Comprehensive type hints and validation
- **Error handling** - Structured exception management

### Quality Assurance

- **Automated testing** - Comprehensive test coverage
- **Code formatting** - Black and isort integration
- **Static analysis** - Type checking and linting
- **Documentation** - Inline and architectural documentation
