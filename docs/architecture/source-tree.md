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
│   │   ├── 004_add_event_log_table.py   # Event log table for audit trail
│   │   ├── 005_add_performance_indexes.py # Performance optimization indexes
│   │   └── 57e8207a27ec_fix_emergency_stops_active_column_type_.py # Fix emergency_stops boolean field
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
│   ├── api/               # REST API endpoints (80 total endpoints across 9 service groups)
│   │   ├── __init__.py
│   │   ├── adk.py         # ADK (Agent Development Kit) endpoints (20 endpoints)
│   │   ├── agents.py      # Agent management endpoints (4 endpoints)
│   │   ├── artifacts.py   # Artifact management endpoints (5 endpoints)
│   │   ├── audit.py       # Audit trail endpoints (4 endpoints)
│   │   ├── dependencies.py # FastAPI dependency injection
│   │   ├── health.py      # Health check endpoints (4 endpoints)
│   │   ├── hitl.py        # Human-in-the-loop endpoints (11 endpoints)
│   │   ├── hitl_request_endpoints.py # HITL request management endpoints (5 endpoints)
│   │   ├── hitl_safety.py # HITL safety control endpoints (9 endpoints)
│   │   ├── projects.py    # Project management endpoints (6 endpoints)
│   │   ├── websocket.py   # WebSocket endpoint handlers
│   │   └── workflows.py   # Workflow management endpoints (17 endpoints)
│   ├── database/          # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py  # Database connection management with session handling
│   │   └── models.py      # SQLAlchemy ORM models with HITL safety architecture
│   ├── models/            # Pydantic data models
│   │   ├── __init__.py
│   │   ├── agent.py       # Agent data models with status enumeration
│   │   ├── context.py     # Context data models with artifact types
│   │   ├── handoff.py     # Enhanced handoff data models with priority and status
│   │   ├── hitl.py        # HITL data models with safety controls, history, and HitlRequestResponse (Task 6)
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
│   │   ├── autogen/                # SOLID refactored AutoGen services (681 LOC → 4 services)
│   │   │   ├── __init__.py         # Package initialization with backward compatibility
│   │   │   ├── autogen_core.py     # Main coordination logic with dependency injection (126 LOC)
│   │   │   ├── agent_factory.py    # Agent instantiation and configuration management (Enhanced TR-09)
│   │   │   ├── conversation_manager.py # Conversation flow and message handling (Enhanced TR-07)
│   │   │   └── group_chat_manager.py # Multi-agent collaboration and conflict resolution (TR-08)
│   │   ├── autogen_service.py      # Backward compatibility alias module
│   │   ├── bmad_core_service.py    # Unified BMAD Core integration service (Missing10.md)
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
│   │   │   ├── template_loader.py  # Template loading and caching mechanisms (Enhanced TR-10, TR-12)
│   │   │   └── template_renderer.py # Template rendering and output formatting (Enhanced TR-11, TR-13)
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
├── tests/                 # Comprehensive test suite (967 tests, 95%+ success rate)
│   ├── conftest.py        # Enhanced test configuration with DatabaseTestManager
│   ├── utils/             # Test utilities and helpers
│   │   └── database_test_utils.py  # Real database testing utilities
│   ├── e2e/               # End-to-end tests
│   │   ├── test_context_persistence_sprint2_e2e.py
│   │   ├── test_hitl_response_handling_e2e.py
│   │   ├── test_sequential_task_handoff_e2e.py
│   │   ├── test_sprint1_critical_paths.py
│   │   └── test_sprint3_e2e_workflows.py
│   ├── integration/       # Integration tests with real database
│   │   ├── test_adk_context_integration.py           # ADK context integration
│   │   ├── test_adk_integration.py                   # Core ADK integration tests
│   │   ├── test_adk_websocket_integration.py         # ADK WebSocket integration
│   │   ├── test_agent_conversation_flow.py           # Agent conversation patterns
│   │   ├── test_agent_task_api_real_db.py           # Agent task API with real database
│   │   ├── test_autogen_reliability.py               # AutoGen LLM reliability integration
│   │   ├── test_context_persistence_integration.py   # Context store integration
│   │   ├── test_context_persistence_sprint2_integration.py
│   │   ├── test_database_schema_validation.py        # Database schema validation
│   │   ├── test_external_services.py                 # External service integration
│   │   ├── test_full_stack_api_database_flow.py     # Complete API to database flow
│   │   ├── test_hitl_response_handling_integration.py
│   │   ├── test_project_initiation_integration.py
│   │   ├── test_replace_critical_mocks.py            # Mock replacement validation
│   │   ├── test_sequential_task_handoff_integration.py
│   │   └── test_sprint3_api_integration.py
│   ├── unit/              # Unit tests with dependency injection
│   │   ├── test_adk_handoff_service.py               # ADK handoff service tests
│   │   ├── test_adk_openapi_tools.py                 # ADK OpenAPI tools tests
│   │   ├── test_adk_orchestration_service.py         # ADK orchestration tests
│   │   ├── test_adk_tool_registry.py                 # ADK tool registry tests
│   │   ├── test_adk_workflow_templates.py            # ADK workflow template tests
│   │   ├── test_agent_factory_adk.py                 # Agent factory ADK tests
│   │   ├── test_agent_framework.py                   # Agent framework tests
│   │   ├── test_agent_status_service.py              # Agent status service tests
│   │   ├── test_agent_tasks.py                       # Real agent task processing tests
│   │   ├── test_agent_tasks_real_db.py              # Agent tasks with real database
│   │   ├── test_artifact_service.py                  # Artifact service tests
│   │   ├── test_audit_service.py                     # Audit service tests
│   │   ├── test_context_persistence.py               # Context persistence tests
│   │   ├── test_context_persistence_sprint2.py       # Sprint 2 context tests
│   │   ├── test_event_log_models.py                  # Event log model tests
│   │   ├── test_hitl_response_handling.py            # HITL response handling tests
│   │   ├── test_llm_reliability.py                   # LLM reliability component tests
│   │   ├── test_project_completion_service.py        # Project completion tests
│   │   ├── test_project_completion_service_real.py   # Project completion with real DB
│   │   ├── test_project_initiation.py                # Project initiation tests
│   │   ├── test_sequential_task_handoff.py           # Task handoff tests
│   │   ├── test_specialized_adk_tools.py             # Specialized ADK tools tests
│   │   ├── test_template_service.py                  # Template service tests
│   │   └── test_workflow_service.py                  # Workflow service tests
│   ├── test_adk_dev_tools.py              # ADK development tools tests
│   ├── test_adk_enterprise_integration.py # ADK enterprise integration tests
│   ├── test_adk_integration.py            # ADK core integration tests
│   ├── test_adk_simple.py                 # Simple ADK functionality tests
│   ├── test_adk_system_integration.py     # ADK system integration tests
│   ├── test_adk_tools.py                  # ADK tools framework tests
│   ├── test_autogen_conversation.py       # AutoGen conversation tests (FIXED)
│   ├── test_autogen_simple.py             # Simple AutoGen tests
│   ├── test_basic_imports.py              # Basic import validation
│   ├── test_bmad_integration.py           # BMAD Core integration tests
│   ├── test_bmad_template_loading.py      # BMAD template loading tests (FIXED)
│   ├── test_conflict_resolution.py        # Conflict resolution algorithm tests
│   ├── test_context_store_mixed_granularity.py # Context store granularity tests
│   ├── test_database_setup.py             # Database setup validation
│   ├── test_extracted_orchestrator_services.py # Orchestrator service tests
│   ├── test_health.py                     # Health endpoint tests
│   ├── test_hitl_safety.py                # HITL safety system tests
│   ├── test_hitl_safety_real_db.py        # HITL safety with real database
│   ├── test_hitl_service_basic.py         # Basic HITL service tests
│   ├── test_hitl_triggers.py              # HITL trigger management tests
│   ├── test_imports.py                    # Import dependency validation
│   ├── test_llm_providers.py              # LLM provider tests
│   ├── test_llm_providers_simple.py       # Simple LLM provider tests
│   ├── test_marker_check.py               # Test marker validation
│   ├── test_orchestrator_core_real_db.py  # Orchestrator core with real database
│   ├── test_orchestrator_refactoring.py   # SOLID orchestrator refactoring tests
│   ├── test_orchestrator_services_real.py # Real orchestrator services tests
│   ├── test_sdlc_orchestration.py         # SDLC orchestration tests
│   ├── test_smoke.py                      # Smoke tests for basic functionality
│   ├── test_solid_refactored_services.py  # SOLID refactored services tests
│   ├── test_template_loading_simple.py    # Simple template loading tests
│   ├── test_workflow_engine.py            # Workflow engine tests
│   ├── test_workflow_engine_real_db.py    # Workflow engine with real database
│   ├── marker-analysis-report.md          # Test marker analysis documentation
│   ├── marker-maintenance-report.md       # Test marker maintenance guide
│   ├── test_failure_analysis.md           # Test failure analysis report
│   └── README.md                          # Test documentation
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
- **BMAD Core integration** - Dynamic template and workflow loading (TR-10 to TR-13)
- **Agent configuration** - Runtime agent personality loading from .bmad-core/agents/ (TR-09)
- **AutoGen integration** - Group chat and conversation management (TR-06 to TR-08)

### Testing Strategy (967 Tests, 95%+ Success Rate)

**Test Suite Transformation (September 2025):**
- **Comprehensive Coverage** - 967 total tests across all system components
- **High Success Rate** - 95%+ tests passing after major refactoring
- **Real Database Integration** - DatabaseTestManager utilities for production-like testing
- **Service Integration** - All services tested with proper dependency injection
- **Infrastructure Validation** - 100% infrastructure and architectural issues resolved

**Test Categories:**
- **Unit tests** - Service-level testing with dependency injection validation
- **Integration tests** - Cross-service workflow testing with real database
- **End-to-end tests** - Complete system workflow validation
- **Real Database Tests** - Production-grade database integration testing
- **Service Constructor Tests** - Proper dependency injection pattern validation
- **Template System Tests** - BMAD Core template loading and rendering validation
- **Agent Framework Tests** - AutoGen conversation patterns and team configuration testing

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
