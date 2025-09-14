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
├── web-bundles/              # Frontend assets (planned)
├── venv/                     # Python virtual environment
├── CLAUDE.md                 # Claude development instructions
├── GEMINI.md                 # Gemini development instructions
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
│   ├── schemas/           # API request/response schemas
│   │   ├── __init__.py
│   │   ├── handoff.py     # Handoff schemas
│   │   └── hitl.py        # HITL schemas
│   ├── services/          # Business logic services
│   │   ├── __init__.py
│   │   ├── agent_service.py        # Agent service with factory pattern and dependency injection
│   │   ├── agent_status_service.py # Agent status management
│   │   ├── artifact_service.py     # Artifact management
│   │   ├── audit_service.py        # Audit trail and event logging (Task 0)
│   │   ├── autogen_service.py      # AutoGen integration (enhanced with reliability features)
│   │   ├── context_store.py        # Context storage service with database integration
│   │   ├── hitl_service.py         # Comprehensive HITL service (Task 6 - Completed)
│   │   ├── hitl_trigger_manager.py # HITL trigger condition management (Task 6)
│   │   ├── llm_monitoring.py       # LLM usage tracking and cost monitoring (Task 1)
│   │   ├── llm_retry.py           # Exponential backoff retry logic (Task 1)
│   │   ├── llm_validation.py      # Response validation and sanitization (Task 1)
│   │   ├── orchestrator.py         # Enhanced orchestration service with dynamic workflows
│   │   ├── project_completion_service.py # Project lifecycle management
│   │   ├── workflow_engine.py      # Complete workflow execution engine (Task 5 - Completed)
│   │   ├── workflow_execution_manager.py # Workflow execution coordination (Task 5)
│   │   ├── workflow_service.py     # Workflow definition loading and management (Task 5)
│   │   ├── workflow_step_processor.py # Workflow step execution (Task 5)
│   │   ├── workflow_persistence_manager.py # Workflow state persistence (Task 5)
│   │   └── workflow_hitl_integrator.py # Workflow HITL integration (Task 5)
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
│   └── README.md          # Test documentation
├── venv/                  # Python virtual environment
├── .env.test              # Test environment configuration (Task 0)
├── docker-compose.dev.yml # Development Docker composition
├── docker-compose.yml     # Production Docker composition
├── install_deps.py        # Dependency installation script
├── pyproject.toml         # Python project configuration
├── README.md              # Backend documentation
├── start_server.py        # Server startup script
├── test_basic_imports.py  # Basic import validation
└── test_imports.py        # Import dependency validation
```

## Documentation Structure (docs/)

```
docs/
├── architecture/          # System architecture documentation
│   ├── HITL-AGENT-SAFETY-ARCHITECTURE.md # HITL safety architecture and mandatory controls
│   ├── HITL_ARCHITECTURE.md              # HITL system architecture documentation
│   ├── ALL_FIXES_SUMMARY.md
│   ├── FINAL_STATUS.md
│   ├── FIXES_APPLIED.md
│   ├── TROUBLESHOOTING.md
│   ├── architecture.md    # Main architecture document (updated with Tasks 4-6)
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
