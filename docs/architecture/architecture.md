# BMAD Enterprise AI Orchestration Platform - Architecture

This document outlines the current architecture of the BMAD Enterprise AI Orchestration Platform, a production-ready multi-agent system with comprehensive safety controls and enterprise features.

## 1. System Architecture Overview

BMAD follows a modern microservice-oriented architecture designed for scalability, maintainability, and enterprise production deployment.

### 1.1 Core Components

**Frontend (Next.js/React)**
- Responsive web application with real-time chat interface
- Workflow visualization and HITL approval components
- Zustand state management and Tailwind CSS styling
- WebSocket integration for real-time updates

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

### 7.1 WebSocket Event System

**Connection Pattern:** `ws://localhost:8000/ws/{project_id?}`

**Event Types:**
- Agent status changes and task progress updates
- HITL request creation and response notifications
- Context artifact generation and availability
- Error notifications with severity levels
- Emergency stop and safety alerts

### 7.2 Event Broadcasting

**Distribution Patterns:**
- Project-scoped events for specific project subscribers
- Global events for system-wide notifications
- Real-time delivery with <100ms latency targets
- Automatic reconnection and session preservation

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

## 9. Performance and Monitoring

### 9.1 Performance Targets

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

**Production:**
- Containerized deployment with orchestration
- External managed database and cache services
- Secret management and encrypted configuration
- Comprehensive monitoring and alerting

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