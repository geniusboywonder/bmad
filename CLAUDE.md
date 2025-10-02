# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend Development

**Start Backend Server:**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Start Celery Worker:**
```bash
cd backend
# IMPORTANT: Source .env first to load DATABASE_URL and other environment variables
# The Celery worker needs DATABASE_URL to connect to PostgreSQL for HITL approvals
source .env && CELERY_BROKER_URL="redis://localhost:6379/1" CELERY_RESULT_BACKEND="redis://localhost:6379/1" celery -A app.tasks.celery_app worker --loglevel=info --queues=agent_tasks,celery
```

**Backend Testing:**
```bash
cd backend
pytest                                    # Run all tests
pytest -v                                 # Verbose output
pytest tests/unit/                        # Unit tests only
pytest tests/integration/                 # Integration tests only
pytest --cov=app                          # With coverage report
pytest -k test_name                       # Run specific test
```

**Database Migrations:**
```bash
cd backend
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                              # Apply migrations
alembic downgrade -1                              # Rollback one migration
```

**System Cleanup:**
```bash
cd backend
python scripts/cleanup_system.py --confirm  # Clean database and Redis
```

### Frontend Development

**Start Frontend Server:**
```bash
cd frontend
npm run dev                    # Development server (localhost:3000)
```

**Frontend Testing:**
```bash
cd frontend
npm test                       # Run all tests
npm run test:ui                # Run tests with UI
```

**Build Frontend:**
```bash
cd frontend
npm run build                  # Production build
npm run lint                   # Run linter
```

## Code Standards

**IMPORTANT**: Always read and follow `docs/CODEPROTOCOL.md` before making any code changes. This file contains the complete development workflow, quality standards, and enforcement rules that must be followed for every task.
Read and follow the front-end style guide in `docs/STYLEGUIDE.md` before making any front-end changes.
Read and follow the SOLID principles in `docs/SOLID.md`
**ALWAYS USE A TODO LIST TO PLAN YOUR STEPS AND TRACK PROGRESS**

## Development Patterns

### Component Architecture

- Use functional components with hooks
- Implement proper TypeScript typing
- Follow existing shadcn/ui patterns for new components
- Maintain consistent import structure with `@/` paths

### Backend Development

- Follow FastAPI async patterns
- Use Pydantic models for data validation
- Implement proper error handling with ErrorHandler
- Maintain WebSocket connection stability

### Agent Development

- **ADK Integration (Primary)**: Use Google ADK framework for new agents via `bmad_adk_wrapper.py`
- **Legacy AutoGen**: Legacy agents in `backend/app/agents/` for reference only
- **Status Broadcasting**: All agent state changes must broadcast via WebSocket manager
- **HITL Integration**: All agent operations require pre-execution HITL approval (see `backend/app/tasks/agent_tasks.py`)

## Code Standards

**IMPORTANT**: Always read and follow `/Users/neill/Documents/AI Code/Projects/v0-botarmy-poc/docs/CODEPROTOCOL.md` before making any code changes. This file contains the complete development workflow, quality standards, and enforcement rules that must be followed for every task.

## Architecture Overview

### Multi-Agent System

**BMAD (BotArmy Multi-Agent Development)** is an enterprise AI orchestration platform with:

- **Backend**: FastAPI + PostgreSQL + Redis + Celery for async task processing
- **Frontend**: Next.js 15 + React 19 + Zustand for state management
- **Agent Framework**: Google ADK (primary) + AutoGen (legacy)
- **Safety Controls**: Mandatory HITL (Human-in-the-Loop) approval system

### Critical System Components

**HITL Approval Workflow (October 2025 - Duplicate Fix)**
- **Single Approval per Task**: One `PRE_EXECUTION` approval record prevents duplicate HITL messages
- **Backend**: `backend/app/tasks/agent_tasks.py` checks for existing approval before creating new one
- **Frontend**: `frontend/components/hitl/inline-hitl-approval.tsx` displays approval UI
- **State Management**: `frontend/lib/stores/hitl-store.ts` with automatic cleanup of expired requests
- **WebSocket Events**: Real-time HITL request broadcasting via `websocketService`

**Database Architecture**
- **PostgreSQL 13+**: ACID-compliant with JSON support for complex data
- **Key Tables**: `projects`, `tasks`, `hitl_agent_approvals`, `agent_status`, `context_artifacts`, `event_log`
- **Migrations**: Alembic-managed migrations in `backend/alembic/versions/`
- **Session Management**: Proper cleanup via generator pattern in services

**WebSocket Communication**
- **Project-scoped Broadcasting**: All events tagged with `project_id` for filtering
- **Event Types**: Agent status, task progress, HITL requests, safety alerts
- **Frontend Client**: `frontend/lib/services/websocket/enhanced-websocket-client.ts`
- **Backend Manager**: `backend/app/websocket/manager.py` with connection pooling

**Service Architecture (SOLID Principles)**
- **Orchestrator Services**: 7 focused services (OrchestratorCore, ProjectLifecycleManager, AgentCoordinator, etc.)
- **HITL Services**: 5 focused services (HitlCore, TriggerProcessor, ResponseProcessor, etc.)
- **Workflow Engine**: 4 focused services (ExecutionEngine, StateManager, EventDispatcher, SdlcOrchestrator)
- **Maximum Service Size**: 600 LOC per file
- **Dependency Injection**: All services use DI for testability

### Key File Locations

**Backend Critical Files:**
- `backend/app/tasks/agent_tasks.py` - Celery task processing with HITL approval logic
- `backend/app/services/hitl_safety_service.py` - HITL safety controls and budget management
- `backend/app/services/startup_service.py` - Server startup cleanup (queues, agents, tasks)
- `backend/app/api/hitl_safety.py` - HITL approval API endpoints
- `backend/app/websocket/manager.py` - WebSocket connection management

**Frontend Critical Files:**
- `frontend/components/chat/copilot-chat.tsx` - Main chat interface with HITL message display
- `frontend/components/hitl/inline-hitl-approval.tsx` - HITL approval buttons and status
- `frontend/lib/stores/hitl-store.ts` - HITL request lifecycle with auto-cleanup
- `frontend/lib/services/websocket/websocket-service.ts` - WebSocket client with reconnection
- `frontend/lib/services/api/client.ts` - API client with retry logic and error handling

**BMAD Core Framework:**
- `.bmad-core/agents/` - Agent persona definitions (analyst, architect, dev, qa, deployer)
- `.bmad-core/workflows/` - SDLC workflow definitions (YAML format)
- `.bmad-core/templates/` - Document and code templates (Jinja2)

## Testing Strategy

### Backend Testing (pytest)

**Test Categories:**
- **Unit Tests**: Service logic, model validation (`tests/unit/`)
- **Integration Tests**: Database operations, workflow validation (`tests/integration/`)
- **Real Database Tests**: Production-like testing with `DatabaseTestManager`
- **Performance Tests**: Sub-200ms API response validation

**Test Markers:**
- `@pytest.mark.real_data` - Tests use real database (no mocking internal components)
- `@pytest.mark.external_service` - Tests mock external APIs only
- `@pytest.mark.mock_data` - Legacy tests with mocks

### Frontend Testing (Vitest + React Testing Library)

**Test Coverage (228 Tests):**
- **156 Unit Tests**: Individual components and services
- **52 Integration Tests**: Inter-service communication
- **20 End-to-End Tests**: Complete workflow validation

**Test Files:**
- `frontend/tests/integration/frontend-integration.test.ts` - E2E integration tests
- `frontend/lib/services/api/*.test.ts` - API service tests
- `frontend/lib/stores/*.test.ts` - State management tests
- `frontend/components/projects/*.test.tsx` - Component tests

## Common Development Workflows

### Adding New HITL Functionality

1. **Backend**: Update `backend/app/services/hitl_safety_service.py` for new approval types
2. **Database**: Create Alembic migration if schema changes needed
3. **API**: Add endpoints to `backend/app/api/hitl_safety.py`
4. **Frontend Store**: Update `frontend/lib/stores/hitl-store.ts` for new state
5. **UI Component**: Modify `frontend/components/hitl/inline-hitl-approval.tsx` for UI changes
6. **WebSocket**: Ensure proper event broadcasting in `backend/app/websocket/manager.py`

### Adding New Agent Type

1. **BMAD Core**: Create agent definition in `.bmad-core/agents/{agent_name}.md`
2. **Backend Factory**: Update `backend/app/agents/factory.py` to support new type
3. **ADK Wrapper**: Extend `backend/app/agents/bmad_adk_wrapper.py` if needed
4. **Database**: Add agent type to enum in `backend/app/database/models.py`
5. **Migration**: Create Alembic migration for schema update
6. **Frontend**: Add agent icon/badge to `frontend/lib/agents/agent-definitions.ts`

### Debugging HITL Issues

1. **Check Backend Logs**: Look for `[AppStore]` and `[CopilotChat]` log entries
2. **Verify Database**: Query `hitl_agent_approvals` table for approval records
3. **Check Redis**: Verify WebSocket events in Redis (use `redis-cli monitor`)
4. **Frontend State**: Check `hitl-store.ts` state in browser dev tools
5. **Network Tab**: Verify WebSocket connection and message flow
6. **Common Issue**: Duplicate messages = check `agent_tasks.py` for multiple approval creation

## Code Standards

- **Max 500 lines per file** (300 for components, 600 for services)
- **Single responsibility** for components and functions
- **Domain boundaries** must be respected
- **Type safety** is mandatory - no `any` types
- **Error handling** must include recovery mechanisms
- **State updates** must be atomic and predictable
- **Service constructors** must accept string paths, not dict configurations
- **SOLID architecture** with dependency injection for all services
- **Real database integration** in tests (no mock-heavy testing)

### Backend-Specific Standards

- **Pydantic v2.10.0** for all data validation
- **SQLAlchemy 2.0.43** with async patterns
- **Celery 5.3.4** for async task processing
- **WebSocket broadcasting** for all state changes
- **HITL approval** required for all agent operations
- **Structured logging** with `structlog` in JSON format
- **Database migrations** via Alembic for all schema changes

### Frontend-Specific Standards

- **Next.js 15 App Router** with React 19
- **Zustand** for state management (no Redux)
- **shadcn/ui** for all UI components
- **TypeScript strict mode** enabled
- **Vitest + React Testing Library** for testing
- **WebSocket client** with auto-reconnection
- **API client** with exponential backoff retry logic

## Visual Development & Testing

### Quick Visual Check

**IMMEDIATELY after implementing any front-end change:**

1. **Identify what changed** - Review the modified components/pages
2. **Navigate to affected pages** - Use `mcp__puppeteer__puppeteer_navigate` to visit each changed view
4. **Validate feature implementation** - Ensure the change fulfills the user's specific request
5. **Check acceptance criteria** - Review any provided context files or requirements
6. **Capture evidence** - Take full page screenshot at desktop viewport (1440px) of each changed view
7. **Check for errors** - Use `mcp__puppeteer__puppeteer_evaluate` to check console messages ⚠️

This verification ensures changes meet design standards and user requirements.

### Puppeteer MCP Integration

#### Essential Commands for UI Testing

```javascript
// Navigation & Screenshots
mcp__puppeteer__puppeteer_navigate({url}); // Navigate to page
mcp__puppeteer__puppeteer_screenshot({name, width, height}); // Capture visual evidence

// Interaction Testing
mcp__puppeteer__puppeteer_click({selector}); // Test clicks
mcp__puppeteer__puppeteer_fill({selector, value}); // Test input
mcp__puppeteer__puppeteer_hover({selector}); // Test hover states
mcp__puppeteer__puppeteer_select({selector, value}); // Test select elements

// Validation
mcp__puppeteer__puppeteer_evaluate({script}); // Execute JavaScript and check for errors
```

### Design Compliance Checklist

When implementing UI features, verify:

- [ ] **Visual Hierarchy**: Clear focus flow, appropriate spacing
- [ ] **Consistency**: Uses design tokens, follows patterns
- [ ] **Responsiveness**: Works on mobile (375px), tablet (768px), desktop (1440px)
- [ ] **Accessibility**: Keyboard navigable, proper contrast, semantic HTML
- [ ] **Performance**: Fast load times, smooth animations (150-300ms)
- [ ] **Error Handling**: Clear error states, helpful messages
- [ ] **Polish**: Micro-interactions, loading states, empty states

## When to Use Automated Visual Testing

### Use Quick Visual Check for

- Every front-end change, no matter how small
- After implementing new components or features
- When modifying existing UI elements
- After fixing visual bugs
- Before committing UI changes

### Skip Visual Testing for

- Backend-only changes (API, database)
- Configuration file updates
- Documentation changes
- Test file modifications
- Non-visual utility functions
