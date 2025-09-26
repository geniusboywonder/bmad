# BMAD Enterprise AI Orchestration Platform - Architecture

This document outlines the current architecture of the BMAD Enterprise AI Orchestration Platform, a production-ready multi-agent system with comprehensive safety controls and enterprise features.

## 1. System Architecture Overview

BMAD follows a modern microservice-oriented architecture designed for scalability, maintainability, and enterprise production deployment.

### 1.1 Core Components

**Frontend (Next.js/React) ✅ Enhanced**
- Responsive web application with real-time chat interface
- Complete project management dashboard with lifecycle controls
- Enhanced Zustand state management with backend integration
- Comprehensive WebSocket integration with project-scoped connections
- HITL approval components with safety event handling
- Complete test suite with 228 test cases covering all integration layers

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

### 4.2 Budget Control System

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

### 7.3 Chat Message Processing Pipeline ✅ CORRECTED FLOW (September 2025)

**CRITICAL: Frontend chat messages must trigger HTTP API calls, not WebSocket messages, to activate HITL workflows.**

**Corrected Message Flow Steps:**
1. **Frontend Chat**: User sends message via `CopilotChat` component
2. **HTTP API Call**: Frontend calls `POST /api/v1/projects/{project_id}/tasks` with task data
3. **Task Creation**: Backend creates database task with status PENDING
4. **Celery Queue**: Backend calls `process_agent_task.delay()` to queue task execution
5. **HITL Safety Check**: Celery task calls `HITLSafetyService.create_approval_request()`
6. **WebSocket Broadcast**: HITL approval request broadcast via `HITL_REQUEST_CREATED` event
7. **Frontend UI Update**: WebSocket event triggers HITL alerts bar display

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

**Current Status: ✅ FULLY FUNCTIONAL**
- ✅ HTTP API task creation working
- ✅ HITL approval requests created and broadcast
- ✅ WebSocket events properly received by frontend
- ✅ Backend HITL workflow proven functional end-to-end
- ✅ Celery worker configuration issue resolved (September 2025)

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

**Execution Sequence:**
1. Server startup triggers `lifespan` context manager
2. StartupService performs 4-step cleanup sequence
3. Redis and Celery queues are flushed
4. Database agent statuses reset to clean state
5. Orphaned tasks are cancelled with proper error messages
6. System starts with guaranteed clean slate

**Benefits:**
- Prevents task queue buildup across server restarts
- Ensures consistent agent state initialization
- Eliminates orphaned tasks and memory leaks
- Provides clean development and production startup experience

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

## 10. Deployment Architecture

### 10.1 Environment Configuration

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

## 11. Quality Assurance

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

**API and Documentation:**
- ✅ 81 endpoints across 13 organized categories
- ✅ OpenAPI documentation with proper grouping
- ✅ Real-time WebSocket event system
- ✅ Multi-tier health check endpoints

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