# BMAD Enterprise AI Orchestration Platform - Architecture

This document outlines the current architecture of the BMAD Enterprise AI Orchestration Platform, a production-ready multi-agent system with comprehensive safety controls and enterprise features.

## 1. System Architecture Overview

BMAD follows a modern microservice-oriented architecture designed for scalability, maintainability, and enterprise production deployment.

### 1.1 Core Components

**Frontend (Next.js/React) ✅ Enhanced - September 2025**
- Responsive web application with real-time chat interface
- Complete project management dashboard with lifecycle controls
- Enhanced Zustand state management with backend integration
- Comprehensive WebSocket integration with project-scoped connections
- HITL approval components with safety event handling
- Complete test suite with 228 test cases covering all integration layers
- **✅ NEW**: Enhanced Process Summary with SDLC workflow visualization (50/50 layout)
- **✅ NEW**: Interactive stage navigation with role-based icons and status overlays
- **✅ NEW**: Expandable artifacts system with progress tracking and download functionality

**Backend (FastAPI)**
- Central orchestration hub with REST APIs and WebSocket services
- Multi-agent coordination and workflow execution
- Comprehensive database persistence with PostgreSQL
- Production-grade HITL safety controls

**Database Layer (PostgreSQL)**
- Multi-tenant data storage with proper indexing
- Complete schema with Alembic migrations
- HITL safety tables and audit trails
- Mixed-granularity context artifact storage

**Caching & Queue Layer (Redis)**
- WebSocket session management
- Celery task queue broker with retry logic
- API response caching for performance optimization
- **CRITICAL**: Dual Redis database architecture (0 for WebSocket, 1 for Celery tasks)

## 2. Multi-LLM Provider Architecture

**Provider Support:**
- **OpenAI GPT-4**: Primary provider for technical architecture and reasoning
- **Anthropic Claude**: Specialized for requirements analysis and documentation
- **Google Gemini**: Alternative provider with configurable fallback

**Provider Features:**
- Unified provider abstraction with factory pattern
- Agent-specific LLM assignments via configuration
- Response validation and cost monitoring
- Exponential backoff retry (1s, 2s, 4s intervals)
- Real-time usage tracking and anomaly detection

## 3. Agent Framework (ADK Integration)

### 3.1 Agent Architecture

**Agent Types:**
- **Orchestrator**: Workflow coordination and phase management
- **Analyst**: Requirements analysis and PRD generation
- **Architect**: System design and technical architecture
- **Coder**: Code generation and implementation
- **Tester**: Quality assurance and validation
- **Deployer**: Deployment automation and monitoring

**Integration Frameworks:**
- **Google ADK**: Enterprise-grade agent capabilities with tool integration
- **Microsoft AutoGen**: Multi-agent conversation management
- **BMAD Core**: Template system and workflow orchestration

### 3.2 Service Architecture (SOLID Principles)

**Orchestrator Service Decomposition:**
- OrchestratorCore: Main coordination logic
- ProjectLifecycleManager: SDLC phase management
- AgentCoordinator: Agent assignment and task distribution
- WorkflowIntegrator: Workflow engine coordination
- HandoffManager: Agent handoff logic
- StatusTracker: Performance monitoring
- ContextManager: Artifact management

**Additional Service Decomposition:**
- HITL services (5 components): Core, TriggerProcessor, ResponseProcessor, PhaseGateManager, ValidationEngine
- Workflow Engine (4 components): ExecutionEngine, StateManager, EventDispatcher, SdlcOrchestrator
- Template System (3 components): TemplateCore, TemplateLoader, TemplateRenderer

## 4. HITL Safety Architecture

### 4.1 Mandatory Safety Controls

**Core Safety Features:**
- Pre-execution agent approval controls
- Response validation and content safety scoring
- Budget controls with token limits and emergency stops
- Real-time safety monitoring and alerts

**Safety Configuration:**
- Environment variables for global defaults
- Per-project database controls for fine-grained management
- Emergency stop mechanisms with multiple trigger conditions
- Comprehensive audit trails and compliance tracking

### 4.2 HITL Request Lifecycle Management ✅ Enhanced September 2025 + October 2025 Critical Fixes

**Frontend Store Management:**
- **Request Creation**: HITL requests stored in persistent Zustand store with localStorage
- **Status Tracking**: Real-time updates via WebSocket events
- **Alert Display**: Pending requests shown in alerts bar with navigation links
- **✅ Automatic Cleanup**: Resolved requests completely removed from store (not just status updated)
- **✅ Manual Cleanup**: `clearAllRequests()`, `removeResolvedRequests()`, `removeExpiredRequests()` methods
- **✅ NEW: Expiration Handling**: 30-minute request expiration with automatic cleanup
- **✅ NEW: Error Recovery**: Graceful handling of 404/400 errors for stale requests

**Resolution Workflow:**
1. User approves/rejects/modifies HITL request via inline component
2. Frontend calls backend HITL safety API endpoint
3. Backend processes approval and notifies relevant systems
4. **✅ CRITICAL**: Frontend removes request from store completely
5. Alert automatically disappears from UI
6. Safety event handler acknowledges related alerts
7. **✅ NEW**: Stale/expired requests gracefully handled and removed

**Store Methods (`frontend/lib/stores/hitl-store.ts`):**
```typescript
// Enhanced resolution with error handling
resolveRequest: async (id, status, response) => {
  // API call to backend with 404/400 error handling
  if (!apiResponse.ok) {
    if (apiResponse.status === 404) {
      console.warn('Approval not found (likely expired), removing from store');
      // Still remove from store even if backend doesn't have it
    } else if (apiResponse.status === 400 && errorText.includes('expired')) {
      console.warn('Approval expired, removing from store');
    }
  }
  
  // Remove from store (not just update status)
  set((state) => ({
    requests: state.requests.filter((req) => req.id !== id),
    activeRequest: state.activeRequest?.id === id ? null : state.activeRequest,
  }));
}

// Enhanced pending count with expiration filtering
getPendingCount: () => {
  const now = new Date();
  return get().requests.filter((req) => {
    if (req.status !== 'pending') return false;
    const requestAge = now.getTime() - new Date(req.timestamp).getTime();
    return requestAge <= THIRTY_MINUTES; // 30 minute expiration
  }).length;
}

// Cleanup methods
clearAllRequests: () => void;           // Remove all requests
removeResolvedRequests: () => void;     // Remove non-pending requests
removeExpiredRequests: () => void;      // Remove requests older than 30 minutes

// Automatic periodic cleanup (runs every 5 minutes)
setInterval(() => {
  useHITLStore.getState().removeExpiredRequests();
}, 5 * 60 * 1000);
```

**Alert Bar Navigation (`frontend/components/hitl/hitl-alerts-bar.tsx`):**
```typescript
// Enhanced navigation with project routing
const handleHITLClick = (requestId: string) => {
  // 1. Check expiration (30-minute timeout)
  if (requestAge > THIRTY_MINUTES) {
    resolveRequest(requestId, 'rejected', 'Request expired');
    return;
  }
  
  // 2. Navigate to project workspace
  const projectId = request.context?.projectId;
  if (currentView !== 'project-workspace' || currentProject?.id !== projectId) {
    navigateToProject(projectId);
  }
  
  // 3. Scroll to and highlight specific HITL message
  const selectors = [
    `[data-approval-id="${approvalId}"]`,
    `[data-request-id="${requestId}"]`,
    `[data-task-id="${taskId}"]`
  ];
  targetElement.scrollIntoView({ behavior: 'smooth' });
  targetElement.classList.add('bg-yellow-100', 'ring-2', 'ring-yellow-300');
};
```

**Benefits:**
- ✅ **Clean UI**: Resolved and expired alerts automatically disappear
- ✅ **Memory Management**: No accumulation of resolved/expired requests
- ✅ **Error Recovery**: Graceful handling of backend sync issues
- ✅ **Developer Experience**: Manual cleanup tools for testing
- ✅ **Smart Navigation**: Direct routing to specific project and HITL message
- ✅ **Visual Feedback**: Temporary highlighting for navigated messages
- ✅ **Consistency**: Store state matches backend reality after system cleanup

### 4.3 HITL Approval Workflow ✅ Fixed October 2025

**Single Approval Per Task Architecture:**
- **PRE_EXECUTION Approval Only**: Tasks require single approval before execution
- **No Duplicate Approvals**: Removed redundant RESPONSE_APPROVAL that created duplicate messages
- **Existing Approval Check**: Backend verifies no PENDING/APPROVED approval exists before creating new one
- **Simplified Workflow**: One task → one approval → one chat message

**Implementation** (`backend/app/tasks/agent_tasks.py:198-321`):
```python
# Check if approval already exists for this task to prevent duplicates
existing_approval = db.query(HitlAgentApprovalDB).filter(
    HitlAgentApprovalDB.task_id == task_uuid,
    HitlAgentApprovalDB.status.in_(["PENDING", "APPROVED"])
).first()

if existing_approval:
    logger.info("Using existing HITL approval record",
               task_id=str(task_uuid),
               approval_id=str(existing_approval.id))
    approval_id = existing_approval.id
else:
    # Create new PRE_EXECUTION approval
    approval_record = HitlAgentApprovalDB(
        project_id=project_uuid,
        task_id=task_uuid,
        agent_type=agent_type,
        request_type="PRE_EXECUTION",
        # ... other fields
    )
    db.add(approval_record)
    db.commit()

# Execute task after approval
result = asyncio.run(autogen_service.execute_task(task, handoff, context_artifacts))

# Skip response approval - pre-execution approval is sufficient
logger.info("Skipping response approval - using pre-execution approval only",
           task_id=str(task_uuid),
           pre_execution_approval_id=str(approval_id))
```

**Benefits:**
- ✅ **No Duplicates**: Single HITL message per task in chat interface
- ✅ **Clean UX**: Clear one-to-one mapping between tasks and approvals
- ✅ **Performance**: Reduced database writes and WebSocket events
- ✅ **Simplified Logic**: Easier to track approval status and workflow state

### 4.4 Budget Control System

**Control Mechanisms:**
- Daily and session token limits per agent/project
- Automatic emergency stops at 90% budget threshold
- Real-time cost monitoring and usage tracking
- Admin override capabilities for budget adjustments

**Storage Locations:**
- Global defaults: Environment variables (`HITL_BUDGET_DAILY_LIMIT`, `HITL_BUDGET_SESSION_LIMIT`)
- Runtime controls: Database `agent_budget_controls` table
- Emergency stops: Database `emergency_stops` table

## 5. API Architecture

### 5.1 RESTful API Design

**Current Status: 81 endpoints across 13 service groups**

**Primary API Groups:**
- **Projects** (6 endpoints): Project lifecycle management
- **HITL** (12 endpoints): Human oversight and approval workflows
- **HITL Safety** (10 endpoints): Mandatory agent safety controls
- **Agents** (4 endpoints): Agent status and management
- **ADK** (26 endpoints): Agent Development Kit functionality
- **Workflows** (17 endpoints): Template and execution management
- **Artifacts** (5 endpoints): Project deliverable generation
- **Audit** (4 endpoints): Comprehensive event logging
- **Health** (5 endpoints): System monitoring and status

### 5.2 OpenAPI Documentation

**Organization Structure:**
- 13 organized tag categories with emoji visual indicators
- Comprehensive endpoint descriptions and examples
- Production-ready API documentation with clear grouping
- No orphaned endpoints or missing categorization

## 6. Data Models (Pydantic v2)

### 6.1 Core Workflow Models

```python
class Task(BaseModel):
    task_id: UUID
    project_id: UUID
    agent_type: str
    status: TaskStatus  # PENDING, WORKING, COMPLETED, FAILED, CANCELLED
    instructions: str
    context_ids: List[UUID]
    created_at: datetime
    updated_at: datetime
```

### 6.2 HITL Safety Models

```python
class HitlAgentApprovalDB(BaseModel):
    project_id: UUID
    task_id: UUID
    agent_type: str
    request_type: str  # PRE_EXECUTION, RESPONSE_APPROVAL
    status: str  # PENDING, APPROVED, REJECTED
    estimated_tokens: int
    estimated_cost: Decimal
    expires_at: datetime
```

### 6.3 Agent Handoff Models

```python
class HandoffSchema(BaseModel):
    handoff_id: UUID
    project_id: UUID
    from_agent: str
    to_agent: str
    phase: str
    instructions: str
    context_ids: List[UUID]
    priority: HandoffPriority
    status: HandoffStatus
```

## 7. Real-Time Communication

### 7.1 WebSocket Event System ✅ Fixed September 2025

**Connection Pattern:** `ws://localhost:8000/ws/{project_id?}`

**Event Types:**
- Agent status changes and task progress updates
- HITL request creation and response notifications
- Context artifact generation and availability
- Error notifications with severity levels
- Emergency stop and safety alerts
- Agent chat message responses (agent_chat_message)

**Recent Fixes:**
- ✅ Fixed WebSocket message type mismatch (`chat_message` vs `chat` compatibility)
- ✅ Fixed nested message data extraction for `{"data": {"message": "..."}}`
- ✅ Fixed database session generator usage in WebSocket handlers
- ✅ Added comprehensive event type validation with EventType enum
- ✅ Resolved syntax errors in exception handling blocks

### 7.2 Event Broadcasting

**Distribution Patterns:**
- Project-scoped events for specific project subscribers
- Global events for system-wide notifications
- Real-time delivery with <100ms latency targets
- Automatic reconnection and session preservation

**Message Flow Architecture:**
```
Frontend Chat Input → HTTP API Call → Backend Task Creation → HITL Safety Check
→ Celery Agent Execution → WebSocket Event Broadcast → Frontend UI Update
```

### 7.3 Chat Message Processing Pipeline ✅ ENHANCED (September 2025)

**CRITICAL: Frontend chat messages must trigger HTTP API calls, not WebSocket messages, to activate HITL workflows.**

**Enhanced Message Flow Steps:**
1. **Frontend Chat**: User sends message via `CopilotChat` component
2. **HTTP API Call**: Frontend calls `POST /api/v1/projects/{project_id}/tasks` with task data
3. **Task Creation**: Backend creates database task with status PENDING
4. **Celery Queue**: Backend calls `process_agent_task.delay()` to queue task execution
5. **HITL Safety Check**: Celery task calls `HITLSafetyService.create_approval_request()`
6. **WebSocket Broadcast**: HITL approval request broadcast via `HITL_REQUEST_CREATED` event
7. **Frontend UI Update**: WebSocket event triggers HITL alerts bar display
8. **✅ NEW: Separate HITL Messages**: Each HITL request creates a unique chat message with persistent state
9. **✅ NEW: Alert Navigation**: Alert bar clicks navigate directly to specific HITL messages with visual highlighting

**Implementation Details:**
```typescript
// Frontend: CopilotChat component calls task creation API
const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/tasks`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_type: 'analyst',
    instructions: content,
    context_ids: [],
    estimated_tokens: 100
  })
});
```

**✅ September 2025 HITL Enhancements:**
- ✅ **Separate HITL Messages**: Each HITL request now creates a dedicated `hitl_request` message type
- ✅ **Message Persistence**: HITL messages retain their approval state permanently (approved/rejected/pending)
- ✅ **Navigation Integration**: Alert bar provides direct navigation to specific HITL chat messages
- ✅ **Visual Highlighting**: Clicked HITL messages receive temporary highlighting for user feedback
- ✅ **Status Indicators**: Visual badges show HITL approval status within chat messages
- ✅ **Alert Lifecycle Management**: HITL alerts now properly disappear when requests are resolved
- ✅ **Store Cleanup Integration**: Frontend HITL store removes resolved requests instead of updating status

**Current Status: ✅ FULLY FUNCTIONAL WITH ENHANCEMENTS**
- ✅ HTTP API task creation working
- ✅ HITL approval requests created and broadcast
- ✅ WebSocket events properly received by frontend
- ✅ Backend HITL workflow proven functional end-to-end
- ✅ Celery worker configuration issue resolved (September 2025)
- ✅ **NEW**: Individual HITL message persistence and navigation system operational

### 7.4 Critical Configuration Issue Resolution (September 2025)

**⚠️ CRITICAL REDIS DATABASE CONFIGURATION ISSUE**

**The Problem**: Multiple Redis database configuration points caused persistent Celery worker misconfiguration:

**Root Cause Analysis**:
1. **`.env` configuration**: `REDIS_CELERY_URL=redis://localhost:6379/1` (Database 1)
2. **Celery workers**: Defaulting to `redis://localhost:6379/0` (Database 0)
3. **Result**: Tasks queued in DB1, workers polling DB0 → Tasks remain PENDING indefinitely
4. **Symptom**: HITL approval requests expire after 30 minutes, causing 400 Bad Request errors

**Why Two Redis Databases?**
- **Database 0**: WebSocket session management and general caching
- **Database 1**: Celery task queue isolation to prevent data conflicts

**Configuration Points Requiring Alignment**:
```bash
# Environment file (.env)
REDIS_CELERY_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Celery worker startup
CELERY_BROKER_URL="redis://localhost:6379/1" CELERY_RESULT_BACKEND="redis://localhost:6379/1" \
celery -A app.tasks.celery_app worker --loglevel=info --queues=agent_tasks,celery
```

**Why This Issue Keeps Recurring**:
1. **Multiple configuration sources**: Environment variables, runtime flags, defaults
2. **Development shortcuts**: Using `celery worker` without explicit DB specification
3. **No validation**: System doesn't validate broker connectivity on startup
4. **Silent failures**: Tasks remain PENDING without clear error messages

**Permanent Solution Strategy**:
1. **Centralized configuration**: Single source of truth for Redis database selection
2. **Startup validation**: Check Celery worker connectivity during app initialization
3. **Clear documentation**: Explicit worker startup commands in development guides
4. **Health checks**: Monitor task queue processing and alert on PENDING buildup

**Impact Assessment**:
- **Before Fix**: HITL workflow broken, 400 Bad Request errors, task execution failure
- **After Fix**: Complete end-to-end HITL workflow operational, fresh approval processing working
- **Future Prevention**: Configuration validation and startup checks prevent recurrence

## 8. Security and Compliance

### 8.1 Authentication and Authorization

**Current Implementation:**
- Environment-based API key management
- Secret key configuration for JWT tokens
- CORS middleware with configurable origins

**Production Requirements:**
- Secret management system (HashiCorp Vault, AWS Secrets Manager)
- Runtime secret injection for sensitive configuration
- Encrypted secret storage for production deployment

### 8.2 Audit and Compliance

**Audit Trail System:**
- Immutable event logging in dedicated `event_log` table
- Complete task lifecycle and HITL interaction tracking
- Structured metadata with timestamps and service versions
- GDPR-compliant data retention policies

## 9. Startup & Cleanup Services

### 9.1 Automatic Startup Cleanup

**StartupService Implementation:**
- **Redis Queue Flushing**: Clears all Redis queues and patterns (`celery`, `agent_tasks`, `_kombu.*`)
- **Celery Queue Purging**: Purges all Celery task queues to prevent orphaned tasks
- **Agent Status Reset**: Resets all agent statuses to `IDLE` and creates missing standard agent records
- **Pending Task Cleanup**: Cancels all `PENDING` and `WORKING` tasks from previous sessions
- **✅ NEW: HITL Approval Cleanup**: Rejects all pending HITL approval requests on startup

**Execution Sequence:**
1. Server startup triggers `lifespan` context manager
2. StartupService performs 5-step cleanup sequence
3. Redis and Celery queues are flushed
4. Database agent statuses reset to clean state
5. Orphaned tasks are cancelled with proper error messages
6. **✅ NEW**: Stale HITL approvals marked as REJECTED
7. System starts with guaranteed clean slate

**Benefits:**
- Prevents task queue buildup across server restarts
- Ensures consistent agent state initialization
- Eliminates orphaned tasks and memory leaks
- **✅ NEW**: Prevents 404 errors from stale HITL approval IDs
- **✅ NEW**: Maintains frontend/backend HITL state consistency
- Provides clean development and production startup experience

### 9.2 ✅ NEW: Comprehensive System Cleanup Script (September 2025)

**Manual Cleanup Utility: `scripts/cleanup_system.py`**

**Complete System Reset Capabilities:**
- **Database Cleanup**: Removes all records from 14+ database tables in proper dependency order
- **Redis Cleanup**: Clears both Redis databases (0: WebSocket sessions, 1: Celery queues)
- **Celery Queue Management**: Purges all task queues and results
- **PostgreSQL Sequence Reset**: Resets all auto-increment sequences to start from 1
- **Verification System**: Confirms successful cleanup across all components

**Usage Options:**
```bash
# Complete system cleanup (database + Redis + Celery)
python scripts/cleanup_system.py --confirm

# Database tables only
python scripts/cleanup_system.py --db-only --confirm

# Redis and queues only
python scripts/cleanup_system.py --redis-only --confirm

# Interactive mode with confirmation prompts
python scripts/cleanup_system.py
```

**Tables Cleaned (Dependency Order):**
1. Child tables: `event_log`, `response_approvals`, `recovery_sessions`, `websocket_notifications`
2. HITL tables: `hitl_agent_approvals`, `hitl_requests`
3. Task-related: `context_artifacts`, `tasks`, `workflow_states`
4. Agent control: `agent_budget_controls`, `emergency_stops`, `agent_status`
5. Parent tables: `projects` (deleted last due to foreign key constraints)

**Safety Features:**
- **Confirmation Prompts**: Interactive mode requires explicit user confirmation
- **Error Handling**: Continues cleanup if individual table operations fail
- **Transaction Safety**: Database operations wrapped in transactions with rollback capability
- **Verification**: Post-cleanup verification ensures complete system reset
- **Logging**: Comprehensive logging of all cleanup operations and results

**Development Benefits:**
- **Repeatable Clean State**: Can be run repeatedly for testing and development
- **Targeted Cleanup**: Options for selective cleanup (database-only or Redis-only)
- **Fresh Testing Environment**: Ensures each test cycle starts with clean data
- **Debug Support**: Clear logging helps identify cleanup issues

**Production Considerations:**
- **Destructive Operation**: Permanently deletes ALL system data
- **Backup Requirement**: Should only be used after confirming data backup
- **Development/Testing Only**: Not intended for production environment usage
- **Team Coordination**: Requires team awareness when used in shared development environments

## 10. Performance and Monitoring

### 10.1 Performance Targets

**Response Time Requirements:**
- API status queries: <200ms
- WebSocket event delivery: <100ms
- Database operations: Optimized with proper indexing
- Health check responses: <50ms

### 9.2 Health Monitoring

**Multi-Component Health Checks:**
- Database connectivity and query performance
- Redis connectivity and memory usage
- Celery worker availability and queue depth
- LLM provider connectivity and rate limits
- HITL safety controls status

**Health Status Levels:**
- **Healthy**: All components operational within thresholds
- **Degraded**: Some performance issues but functional
- **Unhealthy**: Critical components down or severely impacted

## 10. Configuration Simplification (October 2025)

### 10.1 Redis Configuration Consolidation

**Problem**: Dual Redis database architecture caused persistent configuration mismatches
- Database 0 for WebSocket sessions
- Database 1 for Celery task queue
- #1 recurring issue: Tasks queued in DB1, workers polling DB0

**Solution**: Single Redis database (DB0) for all services
- **Simplified Configuration**: Single `REDIS_URL` environment variable
- **Logical Separation**: Key prefixes instead of separate databases (`celery:*`, `websocket:*`, `cache:*`)
- **Eliminated Variables**: Removed `REDIS_CELERY_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- **Developer Experience**: Simplified Celery worker startup (no environment variable juggling)

**Implementation** (October 2025):
```python
# backend/app/settings.py (simplified)
redis_url: str = Field(default="redis://localhost:6379/0")  # Single Redis DB

# backend/app/tasks/celery_app.py
celery_app.conf.broker_url = settings.redis_url
celery_app.conf.result_backend = settings.redis_url

# .env (simplified)
REDIS_URL=redis://localhost:6379/0
# Celery uses REDIS_URL automatically (no separate config)

# Celery worker startup (simplified)
celery -A app.tasks.celery_app worker --loglevel=info --queues=agent_tasks,celery
```

**Benefits**:
- ✅ **Eliminated Configuration Drift**: Single source of truth for Redis connection
- ✅ **No More DB Mismatches**: Workers and tasks always use same database
- ✅ **Simpler Developer Onboarding**: One variable instead of four
- ✅ **Reduced Troubleshooting**: No more "tasks stuck in PENDING" debugging

### 10.2 Workflow Model Consolidation (October 2025)

**Problem**: Duplicate WorkflowStep classes across codebase
- 5 separate WorkflowStep definitions with inconsistent fields
- Maintenance burden keeping models in sync
- Potential for bugs due to model inconsistencies

**Solution**: Canonical WorkflowStep in `models/workflow.py`
```python
# backend/app/models/workflow.py (canonical)
class WorkflowStep(BaseModel):
    agent: Optional[str] = Field(None, description="Agent responsible for this step")
    creates: Optional[str] = Field(None, description="Output artifact created")
    requires: Union[str, List[str]] = Field(default_factory=list, description="Required inputs")
    condition: Optional[str] = Field(None, description="Conditional execution criteria")
    notes: Optional[str] = Field(None, description="Additional notes and guidance")
    optional_steps: List[str] = Field(default_factory=list, description="Optional sub-steps")
    action: Optional[str] = Field(None, description="Specific action to perform")
    repeatable: bool = Field(False, description="Whether this step can be repeated")
```

**Files Consolidated**:
- ✅ `utils/yaml_parser.py`: Removed duplicate, imports canonical model
- ✅ `services/workflow_step_processor.py`: Already using canonical model
- ⚠️ `workflows/adk_workflow_templates.py`: Flagged for Phase 3 cleanup (unused dead code)

**Benefits**:
- ✅ **Single Source of Truth**: One canonical model definition
- ✅ **Eliminated 31 Lines**: Removed duplicate code from yaml_parser.py
- ✅ **Consistent Behavior**: All workflow processing uses same model
- ✅ **Easier Maintenance**: Changes in one place propagate everywhere

## 11. Deployment Architecture

### 11.1 Environment Configuration

**Development:**
- Local PostgreSQL and Redis instances
- Mock external services for testing
- Debug mode with hot reload enabled
- Automatic startup cleanup on server restart

**Production:**
- Containerized deployment with orchestration
- External managed database and cache services
- Secret management and encrypted configuration
- Comprehensive monitoring and alerting
- Startup cleanup service for queue management and state reset

### 10.2 Infrastructure Requirements

**Core Services:**
- PostgreSQL 13+ with proper indexing and backups
- Redis 6+ for caching and session management
- Python 3.11+ with FastAPI and async support
- Node.js 18+ for Next.js frontend application

**External Dependencies:**
- LLM provider APIs (OpenAI, Anthropic, Google)
- Secret management service for production
- Monitoring and observability platform
- Load balancer and CDN for production traffic

## 11. ✅ NEW: Enhanced Process Summary Architecture (September 2025)

### 11.1 SDLC Workflow Visualization

**Component: `frontend/components/projects/project-process-summary.tsx`**

**Core Features:**
- **50/50 Layout**: Equal split between Process Summary and Chat Interface (`grid-cols-1 xl:grid-cols-2`)
- **5-Stage SDLC Workflow**: Analyze → Design → Build → Validate → Launch
- **Interactive Stage Navigation**: Click to switch between workflow stages with real-time content updates
- **Role-Based Visual Design**: Agent-specific icons and color coding for each stage

**Stage Mapping System:**
```typescript
const defaultStages = [
  { id: "analyze", agent: "Analyst", icon: ClipboardCheck },
  { id: "design", agent: "Architect", icon: DraftingCompass },
  { id: "build", agent: "Developer", icon: Construction },
  { id: "validate", agent: "Tester", icon: TestTube2 },
  { id: "launch", agent: "Deployer", icon: Rocket }
];
```

### 11.2 Artifacts Management System ✅ Enhanced October 2025

**Dynamic Workflow Deliverables:**
- **API-Driven Artifacts**: Deliverables loaded from `backend/app/workflows/greenfield-fullstack.yaml` via `/api/v1/workflows/{workflow_id}/deliverables` endpoint
- **17 Total Artifacts**: Streamlined SDLC deliverables aligned with Agile methodology
- **Stage Distribution**: Analyze (4), Design (3), Build (4), Validate (3), Launch (3)
- **HITL-Required Plans**: Each stage starts with mandatory human-approved plan artifact

**Streamlined Artifact List:**

**Analyze Stage:**
1. Analyze Plan (HITL required)
2. Product Requirement
3. PRD Epic
4. Feature Story

**Design Stage:**
1. Design Plan (HITL required)
2. Front End Spec
3. Fullstack Architecture

**Build Stage:**
1. Build Plan (HITL required)
2. Story
3. Implementation Files
4. Bug Fixes

**Validate Stage:**
1. Validate Plan (HITL required)
2. Test Case
3. Validation Report

**Launch Stage:**
1. Launch Plan (HITL required)
2. Deployment Checklist
3. Deployment Report

**Artifact Mapping Logic:**
```typescript
// Dynamic loading from workflow YAML via API
const response = await workflowsService.getWorkflowDeliverables('greenfield-fullstack');
// Stage-specific filtering based on agent assignments from YAML
```

### 11.3 Visual Design System

**Status Overlay System:**
- **Status Icons**: CheckCircle (completed), Play (in_progress), Clock (pending), AlertTriangle (failed)
- **Color Coding**: Dynamic background colors based on status (tester green, analyst blue, amber warnings)
- **Visual Hierarchy**: Connecting lines between stages, proper spacing, and responsive design

**Role-Based Iconography:**
- **Analyst**: ClipboardCheck icon with slate-500 color scheme
- **Architect**: DraftingCompass icon with pink-500 color scheme
- **Developer**: Construction icon with lime-600 color scheme
- **Tester**: TestTube2 icon with sky-500 color scheme
- **Deployer**: Rocket icon with rose-600 color scheme

### 11.4 Backend Integration ✅ Enhanced October 2025

**Workflow API Integration:**
- **Workflows Service**: `lib/services/api/workflows.service.ts` for dynamic deliverable loading
- **Artifacts Service**: `lib/services/api/artifacts.service.ts` with project-specific endpoints
- **Workflow Endpoint**: `GET /api/v1/workflows/{workflow_id}/deliverables` returns structured deliverables by stage
- **Project Artifacts Hook**: `hooks/use-project-artifacts.ts` for real-time data management
- **Error Handling**: Comprehensive null checks and fallback values for missing data

**Workflow Definition Source:**
- **Production Workflow**: `backend/app/workflows/greenfield-fullstack.yaml` (active workflow used by system)
- **Reference Workflows**: `.bmad-core/workflows/*.yaml` (reference only - DO NOT USE)
- **Dynamic Loading**: WorkflowService loads YAML from `app/workflows/` directory at startup with caching

**Real-Time Updates:**
- **30-Second Refresh**: Automatic artifact data refresh every 30 seconds
- **Progress Calculation**: Dynamic progress percentage based on completed vs. total artifacts
- **Status Synchronization**: Backend artifact status reflected in UI immediately
- **On-Mount Loading**: Workflow deliverables fetched from API when component mounts

### 11.5 Responsive Design Implementation

**Multi-Device Support:**
- **Desktop (1440px)**: Full 50/50 layout with all features visible
- **Tablet (768px)**: Responsive grid maintains functionality with adjusted spacing
- **Mobile (375px)**: Stacked layout with stage navigation preserved

**Layout Adaptation:**
```typescript
// Responsive grid system
<div className="flex-1 grid grid-cols-1 xl:grid-cols-2 gap-8 p-6 min-h-0">
  <div className="min-h-[500px]" data-testid="process-summary-section">
    <ProjectProcessSummary projectId={project.id} />
  </div>
  <div className="min-h-[500px]" data-testid="chat-section">
    <CopilotChat projectId={project.id} />
  </div>
</div>
```

### 11.6 Implementation Benefits

**User Experience Improvements:**
- **Enhanced Visibility**: Clear visual representation of SDLC workflow progress
- **Interactive Navigation**: Easy switching between workflow stages
- **Progress Awareness**: Real-time progress tracking for each stage and overall project
- **Artifact Accessibility**: Direct access to stage-specific deliverables with download capability
- **Fixed Chat Scrolling**: Chat window maintains fixed height with internal message scrolling (October 2025)

**Technical Improvements:**
- **Modular Design**: Clean separation between stage navigation and artifact management
- **Type Safety**: Comprehensive TypeScript interfaces with null safety
- **Performance**: Efficient re-rendering with React hooks and memoization
- **Maintainability**: Well-structured component architecture following existing patterns
- **Dynamic Workflows**: Backend-driven artifact definitions via YAML configuration
- **Agile Alignment**: 17 streamlined deliverables matching modern Agile methodology

## 12. Quality Assurance

### 11.1 Test Suite Architecture

**Current Status (September 2025):**
- **Total Tests**: 967 tests with 95%+ success rate
- **Infrastructure Tests**: 100% passing with real database integration
- **Service Integration**: Complete dependency injection testing
- **API Coverage**: All 81 endpoints validated

**Test Infrastructure:**
- Real database testing with `DatabaseTestManager`
- Service integration with proper dependency injection
- AutoGen conversation pattern validation
- BMAD Core template processing verification

### 11.2 Quality Gates

**Production Readiness Criteria:**
- ✅ All services follow SOLID principles
- ✅ Real database integration with proper cleanup
- ✅ API reliability with error scenario validation
- ✅ Agent framework integration with AutoGen/ADK
- ✅ Template system functionality verification

## 12. Current Implementation Status

### 12.1 Completed Components

**Core Infrastructure:**
- ✅ Complete database schema with migrations
- ✅ WebSocket manager with real-time broadcasting
- ✅ Multi-component health monitoring
- ✅ Celery task queue with retry logic
- ✅ Startup cleanup service with queue flushing and agent reset
- ✅ **NEW**: Comprehensive manual cleanup script for development/testing

**Agent Framework:**
- ✅ Google ADK integration with enterprise controls
- ✅ AutoGen conversation management
- ✅ BMAD Core template system
- ✅ Agent service layer with factory patterns

**HITL Safety System:**
- ✅ Mandatory approval controls
- ✅ Budget management with emergency stops
- ✅ Response validation and safety scoring
- ✅ Comprehensive audit trails
- ✅ **NEW**: Enhanced HITL chat message persistence and navigation

**API and Documentation:**
- ✅ 81 endpoints across 13 organized categories
- ✅ OpenAPI documentation with proper grouping
- ✅ Real-time WebSocket event system
- ✅ Multi-tier health check endpoints

**✅ September 2025 Enhancements:**
- ✅ **HITL Message Persistence**: Individual HITL requests create dedicated persistent chat messages
- ✅ **Alert Navigation**: Direct navigation from alert bar to specific HITL messages with highlighting
- ✅ **System Cleanup Utility**: Comprehensive script for database and queue cleanup
- ✅ **Development Workflow**: Enhanced tools for clean testing environments and debugging
- ✅ **HITL Alert Lifecycle**: Resolved HITL requests completely removed from frontend store
- ✅ **Store Cleanup Methods**: Manual cleanup utilities for development and testing workflows
- ✅ **Enhanced Process Summary**: Complete redesign with SDLC workflow stages and artifact management
- ✅ **Interactive UI Components**: Stage navigation, expandable artifacts, and progress visualization

**✅ October 2025 HITL Fixes:**
- ✅ **Expiration Handling**: 30-minute request timeout with automatic cleanup every 5 minutes
- ✅ **Error Recovery**: Graceful 404/400 error handling for expired/missing approvals
- ✅ **Smart Navigation**: Direct routing from alert bar to specific project workspace and HITL message
- ✅ **Visual Highlighting**: 3-second yellow highlight on navigated messages with dark mode support
- ✅ **Backend Startup Cleanup**: Automatic rejection of stale HITL approvals on server restart
- ✅ **Project Context**: WebSocket events include projectId for proper navigation routing
- ✅ **Badge Utilities**: Centralized badge styling system for consistent UI across components
- ✅ **Debug Logging**: Comprehensive logging for tracking HITL request lifecycle and troubleshooting
- ✅ **Duplicate Prevention**: Fixed backend workflow to create only one approval per task (removed redundant RESPONSE_APPROVAL)

### 12.2 Architecture Validation

**SOLID Principles Compliance:**
- Single Responsibility: Focused service decomposition
- Open/Closed: Plugin architecture for extensibility
- Liskov Substitution: Interface-based implementations
- Interface Segregation: Client-specific interfaces
- Dependency Inversion: Abstraction-based dependencies

**Production Readiness:**
- Comprehensive error handling and recovery
- Performance optimization with <200ms response times
- Security implementation with audit trails
- Scalability patterns with proper separation of concerns

This architecture represents a mature, production-ready multi-agent orchestration platform with enterprise-grade safety controls, comprehensive monitoring, and scalable service design patterns.