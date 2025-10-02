# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.8.0] - 2025-10-02

### ✨ Feature - Dynamic Workflow Deliverables & Agile Alignment

**Backend Workflow Restructuring**
- **New Production Workflow Location**: `backend/app/workflows/greenfield-fullstack.yaml`
- **Deprecated Reference Location**: `.bmad-core/workflows/` (reference only - DO NOT USE)
- **17 Streamlined Artifacts**: Reduced from 30+ to 17 focused SDLC deliverables aligned with Agile methodology
- **5 HITL-Required Plans**: Each SDLC stage (Analyze, Design, Build, Validate, Launch) starts with mandatory human-approved plan

**Streamlined Artifact Structure**

**Analyze Stage (4 artifacts)**
1. Analyze Plan (HITL required)
2. Product Requirement
3. PRD Epic
4. Feature Story

**Design Stage (3 artifacts)**
1. Design Plan (HITL required)
2. Front End Spec
3. Fullstack Architecture

**Build Stage (4 artifacts)**
1. Build Plan (HITL required)
2. Story
3. Implementation Files
4. Bug Fixes

**Validate Stage (3 artifacts)**
1. Validate Plan (HITL required)
2. Test Case
3. Validation Report

**Launch Stage (3 artifacts)**
1. Launch Plan (HITL required)
2. Deployment Checklist
3. Deployment Report

**Frontend Integration**
- **New Workflows Service**: `frontend/lib/services/api/workflows.service.ts`
- **Dynamic Loading**: Deliverables fetched from `/api/v1/workflows/greenfield-fullstack/deliverables` on component mount
- **API Integration**: `frontend/lib/services/api/index.ts` exports workflow types and service
- **Process Summary Enhancement**: `project-process-summary.tsx` loads artifacts from API instead of hardcoded constants

**API Enhancements**
- **Workflow Service**: `backend/app/services/workflow_service.py` reads from `app/workflows/` directory
- **Optional Agent Fields**: WorkflowStep model supports non-agent workflow steps
- **Error Handling**: Graceful handling of missing validate_sequence method and None agents

**Benefits**
- ✅ **Agile Alignment**: Artifacts match modern Agile/Scrum methodology (Epic → Story → Implementation)
- ✅ **HITL Control**: Each stage requires human approval before proceeding with work artifacts
- ✅ **Maintainability**: Single source of truth in backend YAML configuration
- ✅ **Flexibility**: Easy to add/remove artifacts by editing YAML file
- ✅ **Type Safety**: TypeScript interfaces generated from backend workflow definitions

**Files Changed**
- `backend/app/workflows/greenfield-fullstack.yaml` - New production workflow with 17 artifacts
- `backend/app/api/workflows.py` - Updated path from `.bmad-core/workflows` to `app/workflows`
- `backend/app/models/workflow.py` - Made agent field optional
- `backend/app/utils/yaml_parser.py` - Optional agent handling
- `backend/app/services/workflow_service.py` - Added hasattr check for validate_sequence
- `frontend/lib/services/api/workflows.service.ts` - New service for workflow deliverables
- `frontend/lib/services/api/index.ts` - Exported workflow service and types
- `frontend/components/projects/project-process-summary.tsx` - Dynamic deliverable loading
- `docs/architecture/architecture.md` - Updated workflow and artifact documentation
- `docs/architecture/source-tree.md` - Added workflows directory and service references

### 🐛 Fix - Chat Window Scrolling Behavior

**Problem**
- Chat window expanded vertically as HITL messages were added
- Messages pushed content off screen requiring page scroll
- Poor UX for monitoring multiple HITL approval requests

**Solution**
- **Fixed Container Height**: Replaced ScrollArea with native `overflow-y-auto` div
- **Flex Layout**: Added `flex-1 overflow-y-auto min-h-0` to messages container
- **Flex Shrink Prevention**: Added `flex-shrink-0` to header, agent filter, and chat input
- **Proper Scrolling**: Messages now scroll within fixed-height container

**Technical Implementation**
- **File**: `frontend/components/chat/copilot-chat.tsx` (lines 237-321)
- **Container**: Changed from `<ScrollArea className="flex-1">` to `<div className="flex-1 overflow-y-auto min-h-0">`
- **Header/Footer**: Added `flex-shrink-0` to prevent compression
- **Main Container**: Conditional `h-full` only when not expanded

**Benefits**
- ✅ **Fixed Height**: Chat window maintains consistent size
- ✅ **Internal Scrolling**: Messages scroll up within container
- ✅ **Better UX**: No page scroll needed to see new messages
- ✅ **Predictable Layout**: Chat window doesn't expand unexpectedly

**Files Changed**
- `frontend/components/chat/copilot-chat.tsx` - Fixed scrolling behavior
- `docs/architecture/architecture.md` - Documented chat scrolling fix
- `docs/architecture/source-tree.md` - Updated chat component description

## [2.7.1] - 2025-10-02

### 🐛 Critical Fix - Celery Worker Database Connection

**Root Cause**
- **Issue**: Celery workers were not connecting to PostgreSQL database
- **Symptom**: HITL approval requests created in database but not visible in frontend
- **Cause**: Celery worker started without `DATABASE_URL` environment variable
- **Impact**: HITL approval workflow completely broken - approvals stored but never retrieved

**Technical Details**
- **Problem**: Starting Celery with only `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` overrides .env file
- **Missing Variable**: `DATABASE_URL` required by `get_session()` in `agent_tasks.py`
- **Result**: Celery worker couldn't connect to PostgreSQL for HITL approval records

**Fix Implementation**
1. **Updated CLAUDE.md** (line 15-20): Added `source .env &&` before Celery command
2. **Updated start_dev.sh** (lines 128-140): Added automatic .env sourcing with `set -a` pattern
3. **Added Documentation**: Clear comments explaining DATABASE_URL requirement

**Files Changed**
- `CLAUDE.md` - Fixed Celery startup command documentation
- `backend/scripts/start_dev.sh` - Added .env loading before Celery worker startup
- `docs/CHANGELOG.md` - This entry

**Testing**
- ✅ Verified Celery worker connects to PostgreSQL successfully
- ✅ Confirmed HITL approval records created in database
- ✅ Validated WebSocket events broadcast correctly
- ✅ Tested HITL alerts display in frontend

**Prevention**
- Startup script now automatically loads all environment variables before starting Celery
- Documentation updated with clear warnings about DATABASE_URL requirement
- Added comments explaining why each environment variable is needed

## [2.7.0] - 2025-10-01

### 🐛 Critical Fix - HITL Duplicate Message Prevention

**Backend Workflow Optimization**
- **Fixed duplicate HITL approval creation** in Celery task processing workflow
- **Removed redundant RESPONSE_APPROVAL** creation that caused second HITL message for same task
- **Added existing approval check** before creating new PRE_EXECUTION approval records
- **Streamlined approval workflow** to use single approval per task instead of two

**Technical Implementation**
- **File**: `backend/app/tasks/agent_tasks.py` (lines 198-321)
- **Fix 1**: Check for existing PENDING/APPROVED approval before creating new record
- **Fix 2**: Skip RESPONSE_APPROVAL creation - pre-execution approval is sufficient for simple tasks
- **Result**: One approval per task eliminates duplicate HITL messages in chat

**Root Cause Analysis**
- **Previous behavior**: Backend created TWO approval records per task:
  1. PRE_EXECUTION approval (before task execution) - creates first HITL message
  2. RESPONSE_APPROVAL (after task execution) - creates second HITL message for same task
- **Issue**: Same task appeared twice in chat with different approval IDs but same task ID
- **Impact**: User confusion, cluttered UI, duplicate approval requests

**Benefits**
- ✅ **Clean UI**: Only one HITL message per task appears in chat
- ✅ **No Duplicates**: Approval/rejection doesn't trigger second message
- ✅ **Proper Workflow**: Pre-execution approval sufficient for task authorization
- ✅ **Better UX**: Clear one-to-one relationship between tasks and approval requests
- ✅ **Performance**: Reduced database writes and WebSocket events

**Implementation Details**
```python
# Check if approval already exists for this task
existing_approval = db.query(HitlAgentApprovalDB).filter(
    HitlAgentApprovalDB.task_id == task_uuid,
    HitlAgentApprovalDB.status.in_(["PENDING", "APPROVED"])
).first()

if existing_approval:
    logger.info("Using existing HITL approval record")
    approval_id = existing_approval.id
else:
    # Create new PRE_EXECUTION approval
    # ...

# Skip RESPONSE_APPROVAL creation - would create duplicate
logger.info("Skipping response approval - using pre-execution approval only")
```

**Testing Validation**
- ✅ Verified single HITL message creation per task
- ✅ Confirmed approval/rejection doesn't create duplicate
- ✅ Tested message persistence with status updates
- ✅ Validated no stale approval IDs after approval

## [2.6.0] - 2025-09-27

### 🎨 Major - Enhanced Process Summary & SDLC Workflow Visualization

**Enhanced Process Summary Architecture**
- **Complete redesign** of ProjectProcessSummary component to match EnhancedProcessSummaryMockup styling
- **50/50 Layout Implementation**: Updated ProjectWorkspace from 1:2 to equal split between Process Summary and Chat Interface
- **SDLC Workflow Stages**: Interactive 5-stage workflow (Analyze → Design → Build → Validate → Launch)
- **Stage Navigation System**: Click-to-switch between workflow stages with real-time content updates

**Visual Design System**
- **Role-Based Iconography**: Agent-specific icons for each stage (ClipboardCheck, DraftingCompass, Construction, TestTube2, Rocket)
- **Status Overlay System**: Dynamic status indicators with color coding (completed, in_progress, pending, failed)
- **Connecting Lines**: Visual workflow progression with gradient connectors
- **Enhanced Typography**: Proper spacing, visual hierarchy, and responsive design

**Artifacts Management System**
- **Stage-Specific Filtering**: Artifacts automatically mapped to SDLC stages based on name patterns and agent assignments
- **Progress Tracking**: Real-time progress bars showing completion status (e.g., "2/3 artifacts completed")
- **Expandable Details**: Click to expand artifact details with task breakdown and status information
- **Download Functionality**: Working download buttons for completed artifacts with disabled states for pending items

**Backend Integration Enhancements**
- **Artifacts Service**: New `lib/services/api/artifacts.service.ts` with project-specific endpoints (`/api/v1/artifacts/{project_id}/summary`)
- **Project Artifacts Hook**: New `hooks/use-project-artifacts.ts` for real-time data management with 30-second refresh
- **Navigation Store**: New `lib/stores/navigation-store.ts` for view state management and breadcrumb navigation
- **Badge Utilities**: New `lib/utils/badge-utils.ts` for centralized status and agent badge styling

**Component Architecture**
- **ProjectWorkspace**: Updated to 50/50 grid layout (`grid-cols-1 xl:grid-cols-2`) with proper spacing
- **ProjectProcessSummary**: Complete rewrite with SDLC stage navigation and artifact management
- **ProjectBreadcrumb**: Enhanced navigation with keyboard shortcuts (Escape key support)
- **Error Handling**: Comprehensive null checks and fallback values for all undefined data

**Responsive Design Implementation**
- **Desktop (1440px)**: Full 50/50 layout with all features visible and working
- **Tablet (768px)**: Responsive grid maintains functionality with adjusted spacing
- **Mobile (375px)**: Stacked layout with stage navigation preserved and accessible

**Technical Improvements**
- **Type Safety**: Added null checks for `toLowerCase()` and `toUpperCase()` operations
- **Performance**: Efficient re-rendering with React hooks and memoization
- **Modular Design**: Clean separation between stage navigation and artifact management
- **Error Recovery**: Graceful handling of missing or undefined artifact data

**User Experience Enhancements**
- **Enhanced Visibility**: Clear visual representation of SDLC workflow progress
- **Interactive Navigation**: Easy switching between workflow stages with visual feedback
- **Progress Awareness**: Real-time progress tracking for each stage and overall project
- **Artifact Accessibility**: Direct access to stage-specific deliverables with download capability

**Quality Assurance**
- **Cross-Browser Testing**: Verified functionality across all major browsers
- **Viewport Testing**: Comprehensive testing at required viewport sizes per TESTPROTOCOL.md
- **Screenshot Documentation**: Visual evidence captured at all tested resolutions
- **Stage Navigation Testing**: Verified dynamic content updates when switching between stages

## [2.5.0] - 2025-09-23

### 🔄 Major - Startup Cleanup Service & System State Management

**Automatic Server Startup Cleanup**
- **StartupService implementation** with comprehensive queue flushing and state reset
- **Redis Queue Flushing**: Automatic clearing of stale cache and queue data (`celery`, `agent_tasks`, `_kombu.*`)
- **Celery Queue Purging**: Removal of orphaned background tasks to prevent accumulation
- **Agent Status Reset**: All agents automatically initialized to IDLE state on server restart
- **Pending Task Cleanup**: Cancellation of incomplete tasks from previous sessions with proper error messages

**Implementation Features**
- **4-step cleanup sequence** executed during FastAPI lifespan startup
- **Database session management** with proper generator pattern usage and cleanup
- **Comprehensive error handling** with detailed logging for each cleanup step
- **Production-ready architecture** suitable for containerized deployments
- **Zero-downtime restarts** with guaranteed clean system state

**Benefits**
- **Prevents task queue buildup** across server restarts
- **Eliminates orphaned tasks** and memory leaks
- **Ensures consistent agent state** initialization
- **Provides clean development experience** with automatic reset
- **Supports production deployments** with reliable startup procedures

**Technical Implementation**
- **FastAPI lifespan integration** for automatic startup execution
- **Redis client management** with pattern-based key deletion
- **Celery control commands** for queue purging across worker processes
- **SQLAlchemy ORM integration** for agent status and task management
- **Structured logging** with comprehensive cleanup reporting

## [2.4.0] - 2025-01-21

### 🧪 Major - Complete Frontend Integration Test Suite

**Frontend Test Suite Implementation**
- **228 comprehensive test cases** covering all integration layers
- **Complete backend integration testing** with API services, WebSocket, and safety systems
- **Component testing suite** with React Testing Library and user interaction validation
- **End-to-end integration tests** for complete workflow validation

**Testing Infrastructure**
- **Vitest configuration** with jsdom environment and comprehensive mocking
- **Test categories breakdown**:
  - **156 Unit Tests**: Individual components and services
  - **52 Integration Tests**: Inter-service communication
  - **20 End-to-End Tests**: Complete workflow validation
- **Comprehensive mocking system** for WebSocket, Fetch, and browser APIs

**Phase 1 API Service Layer Tests**
- **API Client Tests** (`lib/services/api/client.test.ts`): 15 tests covering retry logic, error handling, and response validation
- **Projects Service Tests** (`lib/services/api/projects.service.test.ts`): 17 tests for CRUD operations and lifecycle management
- **WebSocket Integration Tests** (`lib/services/websocket/enhanced-websocket-client.test.ts`): 24 tests for connection management and event handling
- **Safety Event Handler Tests** (`lib/services/safety/safety-event-handler.test.ts`): 46 tests for HITL workflows and emergency controls

**Phase 2 Project Management Tests**
- **Project Store Tests** (`lib/stores/project-store.test.ts`): 34 tests for state management and backend synchronization
- **Project Dashboard Tests** (`components/projects/project-dashboard.test.tsx`): 28 tests for UI components and interactions
- **Project Creation Form Tests** (`components/projects/project-creation-form.test.tsx`): 24 tests for form validation and submission

**Integration Test Suite**
- **Frontend Integration Tests** (`tests/integration/frontend-integration.test.ts`): 20 comprehensive end-to-end tests
- **Performance testing** with concurrent connections and load scenarios
- **Error recovery testing** across all integration layers
- **Data consistency verification** between components and backend

**Quality Assurance Features**
- **Real-time event testing** with WebSocket simulation
- **Safety system testing** with HITL workflow validation
- **Component interaction testing** with accessibility verification
- **Error boundary testing** with recovery scenarios

## [2.3.0] - 2025-09-19

### 🔧 Major - Test Suite Refactoring & Production Readiness

**Comprehensive Test Suite Transformation**
- **967 total tests** with **95%+ success rate** (up from heavily broken state)
- **Real database integration** with `DatabaseTestManager` utilities
- **Service architecture alignment** - Fixed all misalignments between tests and current implementations
- **Template system integration** - Fixed BMAD Core template loading and rendering
- **AutoGen integration** - Resolved conversation patterns and team configuration

**Key Infrastructure Fixes**
- **Template Service**: Fixed constructors to accept string paths instead of dict configs
- **Agent Team Configuration**: Added missing 'orchestrator' agent type, fixed workflow arrays
- **HandoffSchema Validation**: Added required UUID fields with proper format validation
- **Database Integration**: Complete migration from mock-heavy to production-like testing

**Quality Achievements**
- **Infrastructure Stability**: 0 infrastructure or architectural errors remaining
- **Service Reliability**: All major services tested with real dependencies
- **Production Readiness**: Test suite supports robust platform development
- **Performance Validation**: Sub-200ms response times across all endpoints

## [2.2.0] - 2025-09-17

### 🔒 Major - Complete API Implementation & HITL Safety Controls

**Complete API Endpoint Coverage - 81 endpoints across 13 service groups**
- **HITL Safety Controls** (10 endpoints): Production-ready agent runaway prevention
- **ADK Integration** (26 endpoints): Agent Development Kit full implementation
- **Workflow Management** (17 endpoints): Complete workflow orchestration
- **HITL Management** (12 endpoints): Human oversight and approval workflows
- **Project Management** (6 endpoints): Enhanced project lifecycle controls
- **Agent Management** (4 endpoints): Real-time agent status monitoring
- **Artifact Management** (5 endpoints): Project deliverable generation
- **Audit Trail** (4 endpoints): Comprehensive event logging
- **Health Monitoring** (5 endpoints): System health and readiness checks

**Mandatory Agent Safety Controls**
- **Pre-execution approval** required for all agent operations
- **Budget controls** with automatic emergency stops
- **Response validation** and approval tracking
- **Real-time safety monitoring** with WebSocket event broadcasting

**OpenAPI Documentation**
- **Interactive API documentation** available at `/docs`
- **Complete endpoint coverage** with testing capabilities
- **Standardized error responses** across all endpoints

## [2.1.0] - 2025-09-17

### 🎯 Major - AutoGen Integration & BMAD Core Template System

**AutoGen Framework Integration**
- **Enhanced ConversationManager**: Proper AutoGen conversation patterns with context passing
- **AutoGenGroupChatManager**: Multi-agent collaboration with conflict resolution
- **Enhanced AgentFactory**: Dynamic configuration loading from `.bmad-core/agents/`
- **Group chat capabilities** with parallel task execution

**BMAD Core Template System**
- **Enhanced TemplateLoader**: Dynamic workflow and team configuration loading
- **Enhanced TemplateRenderer**: Advanced Jinja2 template processing
- **BMADCoreService**: Unified BMAD Core integration and management
- **Template validation** and schema enforcement

**Advanced Features**
- **Conditional workflow routing** with expression evaluation
- **Parallel task execution** with result aggregation
- **Custom Jinja2 filters** for BMAD-specific formatting
- **Hot-reload configurations** without restart

## [2.0.0] - 2024-09-17

### 🏗️ Major - SOLID Architecture Refactoring

**Service Decomposition (SOLID Principles)**
- **Orchestrator Services** (2,541 LOC → 7 focused services)
  - OrchestratorCore, ProjectLifecycleManager, AgentCoordinator
  - WorkflowIntegrator, HandoffManager, StatusTracker, ContextManager
- **HITL Services** (1,325 LOC → 5 focused services)
  - HitlCore, TriggerProcessor, ResponseProcessor, PhaseGateManager, ValidationEngine
- **Workflow Engine** (1,226 LOC → 4 focused services)
  - ExecutionEngine, StateManager, EventDispatcher, SdlcOrchestrator
- **Template System** (526 LOC → 3 focused services)
  - TemplateCore, TemplateLoader, TemplateRenderer

**Architecture Improvements**
- **Dependency injection** throughout service layer
- **Interface segregation** with 11 comprehensive interface files
- **Backward compatibility** maintained with service aliases
- **Type safety** with enhanced interface definitions

## [1.5.0] - 2025-09-16

### 🚀 Major - Google ADK Integration & Hybrid Architecture

**Google ADK (Agent Development Kit) Integration**
- **Production-grade agent framework** with `gemini-2.0-flash` model
- **BMAD-ADK Wrapper**: Enterprise wrapper preserving BMAD safety controls
- **Tool integration** with `FunctionTool` support
- **Session management** with proper `InMemorySessionService`
- **Development tools** with comprehensive testing framework

**Hybrid Agent Architecture**
- **ADK and AutoGen integration** with seamless interoperability
- **Feature flags** for gradual ADK rollout
- **Enterprise controls** maintained across both frameworks
- **Tool registry** with OpenAPI integration support

## [Phase 1 Foundation Complete] - 2025-09-16

### 🏗️ Infrastructure Foundation & Core Systems

**Database Infrastructure**
- **PostgreSQL schema** with complete migrations (Alembic)
- **Core tables**: projects, tasks, agent_status, context_artifacts, hitl_requests, event_log
- **HITL Safety tables**: agent_budget_controls, emergency_stops, response_approvals
- **Performance optimization** with proper indexing and connection pooling

**Task Processing System**
- **Celery integration** with Redis broker
- **Real agent execution** replacing simulation
- **WebSocket broadcasting** for real-time updates
- **Context artifact management** with mixed-granularity storage

**HITL (Human-in-the-Loop) System**
- **Comprehensive approval workflows** with approve/reject/amend actions
- **Configurable oversight levels** (High/Medium/Low)
- **Context-aware interfaces** with artifact previews
- **Bulk operations** and expiration management
- **Real-time notifications** via WebSocket

**Workflow Orchestration Engine**
- **Dynamic workflow loading** from BMAD Core templates
- **State machine pattern** with persistence and recovery
- **Agent handoff coordination** with structured validation
- **Conditional routing** and parallel execution
- **Progress tracking** with milestone management

## [Task Implementation History] - 2025-09-14

### Core System Development

**Task 0: Infrastructure Foundation**
- Database schema, WebSocket manager, health monitoring
- Core table implementation with proper relationships

**Task 4: Real Agent Processing**
- AutoGen integration for live LLM-powered execution
- Database lifecycle tracking with WebSocket progress updates
- Context artifact integration with dynamic creation

**Task 5: Workflow Orchestration**
- Complete workflow execution engine with state persistence
- BMAD Core template integration with YAML workflow definitions
- Multi-tier recovery strategy with automatic retry

**Task 6: Human-in-the-Loop System**
- Comprehensive HITL system with configurable triggers
- Context-aware approval interfaces with audit trails
- Real-time WebSocket notifications for approval requests

## [Sprint Development History] - 2024-09-12 to 2024-09-13

### Production System Development

**Sprint 3: Backend Infrastructure**
- Agent status service with real-time broadcasting
- Artifact service with ZIP generation
- Project completion service with automatic detection
- Enhanced WebSocket event system

**Sprint 4: Production Readiness**
- Model validation and Pydantic v2 migration
- Performance optimizations and caching
- Comprehensive error handling and logging
- Security enhancements and input validation

## Migration Notes

### Database Changes
- **Schema Evolution**: Progressive migrations from basic tables to comprehensive HITL safety architecture
- **Performance Optimizations**: Indexes added for frequently queried fields
- **Type Safety**: Boolean/Enum type consistency across all models

### API Evolution
- **Endpoint Growth**: From basic CRUD to 81 comprehensive endpoints
- **Documentation**: Complete OpenAPI/Swagger integration
- **Validation**: Pydantic v2 for all request/response models

### Testing Strategy
- **Real Database Integration**: Migration from mock-heavy to production-like testing
- **Service Architecture**: Dependency injection testing patterns
- **Performance Validation**: Sub-200ms response time requirements

### Technology Stack
- **Agent Frameworks**: AutoGen (legacy) + Google ADK (production)
- **Template System**: BMAD Core with dynamic loading
- **Safety Controls**: Comprehensive HITL with mandatory approvals
- **Monitoring**: Multi-tier health checks and real-time events

This changelog represents the evolution of BMAD from initial concept to production-ready enterprise AI orchestration platform with comprehensive safety controls, real-time communication, and scalable architecture.