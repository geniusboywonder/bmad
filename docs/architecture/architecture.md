### **BotArmy Software Specification (Updated)**

This document outlines the technical specifications for the BotArmy Proof-of-Concept (POC), based on the architectural decisions and design principles discussed. The design adheres to the SOLID principles to ensure the system is maintainable, scalable, and extensible.

***

### **1. Overall System Architecture**

The system follows a modern microservice-oriented architecture with multi-LLM support, AutoGen agent framework integration, and BMAD Core template system. The architecture is designed for scalability, maintainability, and extensibility.

#### **1.1 Core Components**

* **Frontend (Next.js/React)**: A responsive single-page application with real-time chat interface, workflow visualization, and HITL approval components. Uses Zustand for state management and Tailwind CSS for styling.

* **Backend (FastAPI)**: The orchestration hub hosting the Orchestrator service, multi-agent coordination, and all data persistence. Provides REST APIs and WebSocket services for real-time communication.

* **Multi-LLM Provider Layer**: Configurable support for multiple LLM providers:
  * **OpenAI GPT-4**: Primary provider for technical architecture and complex reasoning
  * **Anthropic Claude**: Specialized for requirements analysis and documentation
  * **Google Gemini**: Alternative provider with configurable fallback
  * **Provider Abstraction**: Unified interface allowing agent-specific LLM assignments
  * **Provider Factory**: Dynamic selection of LLM providers based on configuration.

* **LLM Reliability & Monitoring Layer** (Task 1 - Implemented): Production-grade reliability features:
  * **Response Validation**: Comprehensive validation and sanitization of all LLM responses
  * **Exponential Backoff Retry**: 1s, 2s, 4s retry intervals with intelligent error classification
  * **Usage Tracking**: Real-time token consumption and cost monitoring per agent/project
  * **Anomaly Detection**: Automated detection of cost spikes and unusual usage patterns
  * **Health Monitoring**: LLM provider connectivity and performance tracking
  * **Structured Logging**: Machine-readable monitoring data for operational observability
  * **Task Queue (Celery)**: Asynchronous task processing with Redis broker, including priority queues and exponential backoff for retries.

* **Google ADK Integration** (Production-Ready): Advanced agent capabilities using Google's Agent Development Kit:
  * **Stable Dependencies**: Google ADK 1.14.1 fully integrated with resolved dependency conflicts
  * **Correct API Usage**: Uses `instruction` parameter, `Runner`-based execution, proper session management
  * **Enterprise Integration**: Full BMAD safety controls (HITL, audit, monitoring) with ADK agents
  * **Tool Integration**: `FunctionTool` support with graceful fallback and error handling
  * **Session Management**: Proper `InMemorySessionService` and `types.Content` message handling
  * **Wrapper Architecture**: `BMADADKWrapper` preserves enterprise features while leveraging ADK capabilities
  * **Startup Reliability**: Lazy initialization patterns and backward compatibility for stable operation

* **AutoGen Framework Integration**: Microsoft AutoGen framework managing agent conversations (Legacy Support):
  * **Agent Conversation Management**: Structured multi-agent dialogues
  * **Group Chat Capabilities**: Multi-agent collaboration scenarios
  * **Context Passing**: Proper handoff schemas between agents
  * **Configuration Loading**: Dynamic agent configs from `backend/app/teams/` directory, loaded via `AgentTeamService`.

* **BMAD Core Template System** (Task 3 - Implemented): Complete dynamic workflow and document generation:
  * **YAML Parser Utilities**: Robust parsing with schema validation and variable substitution
  * **Workflow Definitions**: Loaded from `backend/app/workflows/` with execution orchestration
  * **Document Templates**: YAML-based templates in `backend/app/templates/` with conditional rendering
  * **Agent Team Configs**: Team compositions in `backend/app/teams/` with compatibility matching
  * **Variable Substitution**: Dynamic template rendering with `{{variable}}` pattern support
  * **REST API Integration**: Complete CRUD operations for templates, workflows, and teams
  * **Testing & Validation**: Comprehensive test suites with 100% coverage

* **Workflow Orchestration Engine** (Task 5 - Implemented): Complete workflow execution and state management:
  * **Dynamic Workflow Loading**: Runtime loading from BMAD Core templates with state machine pattern
  * **Agent Handoff Coordination**: Structured HandoffSchema validation with context passing between agents
  * **Conditional Workflow Routing**: Decision points and complex workflow logic with expression evaluation
  * **Parallel Task Execution**: Concurrent workflow step execution with result aggregation
  * **Workflow State Persistence**: Complete database persistence with recovery mechanisms for interruptions
  * **Progress Tracking & Milestones**: Real-time workflow monitoring with WebSocket event broadcasting
  * **Template System Integration**: Seamless document generation coordination with workflow execution
  * **Error Recovery Mechanisms**: Multi-tier recovery strategy with automatic retry and escalation
  * **Modular Service Architecture**: Split into WorkflowStepProcessor, WorkflowPersistenceManager, WorkflowHitlIntegrator

* **Human-in-the-Loop (HITL) System** (Task 6 - Implemented): Comprehensive human oversight and approval system:
  * **Configurable Trigger Conditions**: Phase completion, quality thresholds, conflicts, errors, budget exceeded, safety violations
  * **Oversight Levels**: High/Medium/Low configurable supervision levels per project
  * **Trigger Manager**: Dedicated service for HITL trigger condition evaluation and management
  * **Response Processing**: Approve/Reject/Amend actions with complete audit trail and workflow resumption
  * **Context-Aware Interfaces**: Full context provision including artifacts, task details, and workflow state
  * **Expiration Management**: Configurable timeouts with automatic escalation for stale requests
  * **Bulk Operations**: Batch approval capabilities for similar requests
  * **Real-Time Notifications**: WebSocket broadcasting for HITL request creation and response events
  * **Workflow Integration**: Seamless pausing and resumption of workflow execution for human approval
  * **Audit Trail**: Complete history tracking with timestamps, user attribution, and decision rationale

* **Infrastructure Foundation** (Task 0 - Completed): Complete Phase 1 foundation infrastructure:
  * **PostgreSQL Database**: Full database schema with migrations (Alembic) including HITL safety tables
  * **Database Models**: All core tables implemented with proper relationships, indexes, and timezone-aware datetime handling
  * **Task Queue (Celery)**: Asynchronous task processing with Redis broker
    * **Real Agent Processing** (Task 4 - Completed): Live LLM-powered agent execution replacing simulation
      * **AutoGen Integration**: Multi-agent conversation framework for task execution with real LLM calls
      * **Database Lifecycle**: Complete task status tracking (PENDING → WORKING → COMPLETED/FAILED) with UTC timestamps
      * **WebSocket Broadcasting**: Real-time task progress updates to connected clients with structured events
      * **Context Artifact Integration**: Dynamic artifact creation and retrieval during execution with type validation
      * **Input Validation**: Comprehensive task data validation with UUID format checking
    * **Retry Logic**: Exponential backoff (1s, 2s, 4s) for failed tasks with proper error classification
    * **Progress Tracking**: Real-time task progress updates via WebSocket with heartbeat mechanism
    * **Timeout Management**: 5-minute task timeouts with automatic status updates and cleanup
  * **WebSocket Manager**: Real-time event broadcasting system with enhanced reliability
    * **Connection Management**: Project-scoped and global event distribution with async broadcasting
    * **Event Types**: Comprehensive event system for agent status, tasks, HITL, and workflow events
    * **Auto-cleanup**: Automatic disconnection handling and resource cleanup with proper session management
  * **Health Monitoring**: Multi-tier service health checking with detailed component status
    * **Basic Health**: `/health` endpoint for service status with standardized response format
    * **Detailed Health**: `/health/detailed` with component breakdown and 'detail' key consistency
    * **Kubernetes Health**: `/health/z` endpoint for container orchestration with performance metrics

* **HITL Safety Architecture** (Mandatory Agent Controls - Implemented): Comprehensive agent runaway prevention system:
  * **Mandatory Agent Approvals**: Pre-execution, response approval, and next-step authorization controls
  * **Budget Controls**: Token limits with daily/session thresholds and automatic emergency stops
  * **Emergency Stop System**: Immediate agent halting with multi-trigger conditions (user, budget, repetition, error)
  * **Response Approval Tracking**: Content safety scoring, code validation, and quality metrics
  * **Recovery Session Management**: Systematic recovery procedures with rollback and retry strategies
  * **WebSocket Notifications**: Real-time alerts for safety events with priority levels

* **Database Layer (PostgreSQL)**: Multi-tenant data storage with proper indexing:
  * **Core Application Data**: Projects, tasks, agents, and user information
  * **Context Store**: Mixed-granularity artifact storage (document/section/concept level)
  * **HITL System**: Request tracking with complete history and audit trails
  * **Safety Control Tables**: Agent approvals, budget controls, emergency stops, response approvals, recovery sessions
  * **Migration Management**: Alembic-based version control with timezone-aware datetime handling

* **Caching Layer (Redis)**: High-performance caching and session management:
  * **WebSocket Sessions**: Connection state and subscription management
  * **Task Queue Broker**: Celery job distribution and result caching
  * **API Response Caching**: Sub-200ms response times for status queries

* **Audit Trail System (Sprint 4)**: Complete immutable event logging for compliance:
  * **Event Log Database**: Dedicated `event_log` table with full payload capture
  * **Comprehensive Event Types**: Task lifecycle, HITL interactions, agent status, system events
  * **Structured Metadata**: Enriched event data with timestamps, service versions, and context
  * **Performance Optimized**: Indexed queries for sub-200ms audit retrieval
  * **GDPR Compliant**: Immutable audit trail with proper data retention policies

* **Real-Time Communication (WebSocket)**: Event-driven architecture with 100ms delivery:
  * **Agent Status Broadcasting**: Live agent state changes
  * **Task Progress Updates**: Real-time workflow monitoring
  * **HITL Request Alerts**: Immediate approval request notifications
  * **Error Notifications**: Structured error reporting with severity levels

### **2. Enhanced SOLID Principles Architecture**

The system architecture strictly adheres to SOLID principles with advanced patterns for maintainability and extensibility:

#### **2.1 Single Responsibility Principle (SRP) - Complete Refactoring Implementation**

**SOLID Refactoring Completed (2024-09-17)**: All major monolithic services have been successfully refactored into focused, single-responsibility services following SOLID principles:

**Phase 1 - Orchestrator Service Decomposition (2,541 LOC → 7 services):**
* **OrchestratorCore** (309 LOC): Main coordination and delegation logic with dependency injection
* **ProjectLifecycleManager** (373 LOC): Project state transitions and SDLC phase management
* **AgentCoordinator** (375 LOC): Agent assignment and task distribution logic
* **WorkflowIntegrator** (391 LOC): Workflow engine integration and coordination
* **HandoffManager** (338 LOC): Agent handoff logic and task transitions
* **StatusTracker** (441 LOC): Project status monitoring and performance metrics
* **ContextManager** (614 LOC): Context artifact management with granularity features

**Phase 1 - HITL Service Decomposition (1,325 LOC → 5 services):**
* **HitlCore** (285 LOC): Core HITL coordination logic with dependency injection
* **TriggerProcessor** (351 LOC): Trigger evaluation and condition management
* **ResponseProcessor** (425 LOC): Response handling and workflow resumption
* **PhaseGateManager** (628 LOC): Phase gate validation and approval workflows
* **ValidationEngine** (667 LOC): Quality validation and threshold management

**Phase 1 - Workflow Engine Decomposition (1,226 LOC → 4 services):**
* **ExecutionEngine** (550 LOC): Core workflow execution logic with dependency injection
* **StateManager** (428 LOC): State persistence and recovery mechanisms
* **EventDispatcher** (521 LOC): Event management and WebSocket broadcasting
* **SdlcOrchestrator** (581 LOC): SDLC-specific workflow logic and phase management

**Phase 2 - AutoGen Service Decomposition (681 LOC → 3 services):**
* **AutoGenCore** (126 LOC): Main coordination logic with dependency injection
* **AgentFactory** (208 LOC): Agent instantiation and configuration management
* **ConversationManager** (554 LOC): Conversation flow and message handling

**Phase 2 - Template Service Decomposition (526 LOC → 3 services):**
* **TemplateCore** (218 LOC): Main coordination logic with dependency injection
* **TemplateLoader** (171 LOC): Template loading and caching mechanisms
* **TemplateRenderer** (328 LOC): Template rendering and output formatting

**Phase 3 - Complete Interface Layer:**
* **Service Interfaces**: 11 comprehensive interface files providing dependency injection abstractions
* **Backward Compatibility**: All original service names preserved as aliases for seamless migration
* **Type Safety**: Full TypeScript-style interface definitions for all service dependencies

#### **2.2 Open/Closed Principle (OCP)**

The system is extensible without modification:

* **Plugin Architecture**: AutoGen framework allows new agents without core changes
* **LLM Provider Extension**: New providers added via configuration, not code changes
* **BMAD Template System**: New workflows and templates loaded dynamically
* **HITL Action Extension**: New approval actions (approve/reject/amend) added without modifying core logic
* **Context Artifact Types**: New artifact types registered without changing storage logic

#### **2.3 Liskov Substitution Principle (LSP)**

All components can be substituted with compatible implementations:

* **BaseAgent Interface**: All agents implement consistent contract for task execution
* **LLMProvider Interface**: OpenAI, Claude, and Gemini providers interchangeable
* **StorageBackend Interface**: PostgreSQL can be substituted with other SQL databases
* **MessageBroker Interface**: Redis can be replaced with other Celery-compatible brokers

#### **2.4 Interface Segregation Principle (ISP)**

Small, client-specific interfaces prevent unwanted dependencies:

* **ITaskDelegator**: Orchestrator task delegation interface
* **IContextReader**: Read-only context access for agents
* **IContextWriter**: Write-only context creation for agents
* **IHitlRequestor**: HITL request creation interface
* **IHitlResponder**: HITL response processing interface
* **IProgressReporter**: Task progress update interface

#### **2.5 Dependency Inversion Principle (DIP)**

High-level modules depend on abstractions, not concretions:

* **Service Layer Abstractions**: All services implement interfaces
* **Repository Pattern**: Data access abstracted behind repository interfaces
* **Factory Pattern**: LLM providers created via factory abstraction
* **Strategy Pattern**: Agent selection and task routing via strategy interfaces
* **Dependency Injection**: All dependencies injected via FastAPI's DI system

***

### **3. Comprehensive Data Models (Pydantic v2)**

All models use Pydantic v2 with ConfigDict for enhanced type safety, validation, and serialization across the FastAPI backend.

#### **3.1 Core Workflow Models**

```python
class Task(BaseModel):
    """Represents a single unit of work for an agent with full lifecycle tracking."""
    task_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    agent_type: str  # Validated against AgentType enum values
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    context_ids: List[UUID] = Field(default_factory=list)
    instructions: str
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @validator('agent_type')
    def validate_agent_type(cls, v):
        """Validate that agent_type is a valid AgentType enum value."""
        from app.models.agent import AgentType
        valid_agent_types = [agent_type.value for agent_type in AgentType]
        if v not in valid_agent_types:
            raise ValueError(f'Invalid agent_type: {v}. Must be one of {valid_agent_types}')
        return v
    
    model_config = ConfigDict(use_enum_values=True)

class TaskStatus(str, Enum):
    PENDING = "pending"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_HITL = "waiting_for_hitl"

class AgentStatus(BaseModel):
    """Real-time agent state tracking with enhanced monitoring."""
    agent_type: str
    status: Literal["idle", "working", "waiting_for_hitl", "error"]
    current_task_id: Optional[UUID] = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    performance_metrics: Optional[Dict[str, float]] = None
    
    model_config = ConfigDict(use_enum_values=True)
```

#### **3.2 Context Store Models**

```python
class ContextArtifact(BaseModel):
    """Mixed-granularity artifact storage for the Context Store Pattern."""
    context_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    source_agent: str
    artifact_type: ArtifactType
    content: Dict[str, Any]
    artifact_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(json_encoders={
        datetime: lambda v: v.isoformat(),
        UUID: lambda v: str(v)
    })

class ArtifactType(str, Enum):
    """Comprehensive artifact type enumeration."""
    USER_INPUT = "user_input"
    PROJECT_PLAN = "project_plan"
    SOFTWARE_SPECIFICATION = "software_specification"
    IMPLEMENTATION_PLAN = "implementation_plan"
    SYSTEM_ARCHITECTURE = "system_architecture"
    SOURCE_CODE = "source_code"
    TEST_RESULTS = "test_results"
    DEPLOYMENT_LOG = "deployment_log"
    DEPLOYMENT_PACKAGE = "deployment_package"
    AGENT_OUTPUT = "agent_output"
    HITL_RESPONSE = "hitl_response"

class ProjectArtifact(BaseModel):
    """Sprint 3: Downloadable project artifact model."""
    name: str
    content: str
    file_type: str = "txt"
    created_at: datetime = Field(default_factory=datetime.now)
```

#### **3.3 HITL System Models**

```python
class HitlRequest(BaseModel):
    """Enhanced Human-in-the-Loop requests with complete lifecycle management."""
    request_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    task_id: UUID
    question: str
    options: List[str] = Field(default_factory=list)
    status: HitlStatus = Field(default=HitlStatus.PENDING)
    user_response: Optional[str] = None
    response_comment: Optional[str] = None
    amended_content: Optional[Dict[str, Any]] = None
    history: List[HitlHistoryEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    
    model_config = ConfigDict(json_encoders={
        datetime: lambda v: v.isoformat(),
        UUID: lambda v: str(v)
    })

class HitlStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AMENDED = "amended"

class HitlAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    AMEND = "amend"

class HitlHistoryEntry(BaseModel):
    """Complete audit trail for HITL interactions."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    user_id: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None
```

#### **3.4 Agent Communication Models (Task 2 Enhanced)**

```python
class HandoffPriority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class HandoffStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"

class HandoffSchema(BaseModel):
    """Enhanced structured agent handoff schema with comprehensive validation and lifecycle management."""
    handoff_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    from_agent: str
    to_agent: str
    phase: str
    instructions: str = Field(..., min_length=10, max_length=5000)
    context_ids: List[UUID] = Field(default_factory=list)
    expected_outputs: List[str] = Field(default_factory=list)
    priority: HandoffPriority = Field(default=HandoffPriority.MEDIUM)
    status: HandoffStatus = Field(default=HandoffStatus.PENDING)
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @validator('instructions')
    def validate_instructions(cls, v):
        if not v.strip():
            raise ValueError('Instructions cannot be empty')
        return v.strip()
    
    @validator('from_agent', 'to_agent')
    def validate_agent_types(cls, v):
        valid_agents = {"orchestrator", "analyst", "architect", "coder", "tester", "deployer"}
        if v not in valid_agents:
            raise ValueError(f'Invalid agent type: {v}. Must be one of {valid_agents}')
        return v
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )
```

***

### **4. Complete API and Communication Specifications**

#### **4.1 REST API Endpoints (FastAPI)**

**Project Management API:**

```http
POST /api/v1/projects
Content-Type: application/json
{
  "name": "string",
  "description": "string"  // optional
}
Response: 201 Created
{
  "id": "uuid",
  "name": "string", 
  "description": "string",
  "status": "active",
  "created_at": "datetime"
}

GET /api/v1/projects/{project_id}/status
Response: 200 OK
{
  "project_id": "uuid",
  "status": "active|completed|failed",
  "current_phase": "discovery|plan|design|build|validate|launch",
  "tasks": [
    {
      "task_id": "uuid",
      "agent_type": "string",
      "status": "pending|working|completed|failed|cancelled",
      "progress_percentage": 75,
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ]
}

POST /api/v1/projects/{project_id}/tasks
Content-Type: application/json
{
  "agent_type": "analyst|architect|coder|tester|deployer",
  "instructions": "string",
  "context_ids": ["uuid"]  // optional
}
Response: 201 Created
{
  "task_id": "uuid",
  "celery_task_id": "string",
  "status": "submitted"
}
```

**HITL Management API:**

```http
GET /api/v1/hitl/requests/{request_id}
Response: 200 OK
{
  "request_id": "uuid",
  "project_id": "uuid",
  "task_id": "uuid", 
  "question": "string",
  "options": ["string"],
  "status": "pending|approved|rejected|amended",
  "user_response": "string",
  "response_comment": "string",
  "amended_content": {},
  "history": [
    {
      "timestamp": "datetime",
      "action": "string",
      "user_id": "string",
      "comment": "string"
    }
  ],
  "created_at": "datetime",
  "expires_at": "datetime",
  "responded_at": "datetime"
}

POST /api/v1/hitl/requests/{request_id}/respond
Content-Type: application/json
{
  "action": "approve|reject|amend",
  "response": "string",
  "amended_content": {},  // required for amend action
  "comment": "string"     // optional
}
Response: 200 OK
{
  "status": "success",
  "message": "Response recorded successfully",
  "workflow_resumed": true
}

GET /api/v1/hitl/project/{project_id}
Response: 200 OK
{
  "requests": [
    // Array of HITL request objects
  ],
  "pending_count": 3,
  "total_count": 15
}
```

**Context Store API:**

```http
GET /api/v1/context/project/{project_id}/artifacts
Response: 200 OK
{
  "artifacts": [
    {
      "context_id": "uuid",
      "artifact_type": "string",
      "source_agent": "string",
      "created_at": "datetime",
      "metadata": {}
    }
  ]
}

GET /api/v1/context/artifacts/{artifact_id}
Response: 200 OK
{
  "context_id": "uuid",
  "project_id": "uuid",
  "source_agent": "string",
  "artifact_type": "string",
  "content": {},
  "artifact_metadata": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### **4.2 WebSocket Event Streaming**

**Connection:** `ws://localhost:8000/ws/{project_id?}`

**Event Types:**

```json
// Agent Status Change
{
  "event_type": "agent_status_changed",
  "project_id": "uuid",
  "agent_type": "analyst|architect|coder|tester|deployer",
  "data": {
    "status": "idle|working|waiting_for_hitl|error",
    "current_task_id": "uuid",
    "timestamp": "datetime"
  }
}

// Task Progress Update  
{
  "event_type": "task_progress_updated",
  "project_id": "uuid",
  "task_id": "uuid",
  "data": {
    "status": "pending|working|completed|failed|cancelled",
    "progress_percentage": 75,
    "message": "string",
    "timestamp": "datetime"
  }
}

// HITL Request Created
{
  "event_type": "hitl_request_created",
  "project_id": "uuid",
  "data": {
    "request_id": "uuid",
    "question": "string",
    "urgency": "low|medium|high",
    "expires_at": "datetime"
  }
}

// Context Artifact Generated
{
  "event_type": "artifact_generated", 
  "project_id": "uuid",
  "data": {
    "artifact_id": "uuid",
    "artifact_type": "user_input|project_plan|software_specification|implementation_plan|source_code|test_results|deployment_log",
    "source_agent": "string",
    "title": "string",
    "timestamp": "datetime"
  }
}

// Error Notification
{
  "event_type": "error_notification",
  "project_id": "uuid", 
  "data": {
    "severity": "warning|error|critical",
    "message": "string",
    "task_id": "uuid",
    "agent_type": "string", 
    "error_code": "string",
    "timestamp": "datetime"
  }
}

// Agent Chat Message
{
  "event_type": "agent_chat_message",
  "project_id": "uuid",
  "data": {
    "agent_type": "string",
    "message": "string",
    "message_type": "info|question|response|thinking",
    "requires_response": false,
    "timestamp": "datetime"
  }
}
```

#### **4.3 Health Check & Monitoring**

```http
GET /healthz
Response: 200 OK / 503 Service Unavailable
{
  "status": "healthy|degraded|unhealthy",
  "components": {
    "database": "healthy",
    "redis": "healthy", 
    "celery": "healthy",
    "llm_providers": {
      "openai": "healthy",
      "claude": "healthy", 
      "gemini": "degraded"
    }
  },
  "timestamp": "datetime"
}
```

***

### **5. Agent Framework Architecture (ADK Integration Complete)**

#### **5.1 Agent Framework Foundation**

**Purpose**: Implement enterprise-grade agent framework using Google ADK for enhanced capabilities while preserving BMAD safety controls.

**ADK Integration Architecture:**

```
backend/app/agents/
├── base_agent.py              # Abstract BaseAgent (legacy support)
├── bmad_adk_wrapper.py        # BMAD-ADK integration wrapper
├── adk_agent_with_tools.py    # ADK agent with tools support
├── adk_dev_tools.py           # ADK development and testing tools
├── orchestrator.py            # Orchestrator agent (legacy)
├── analyst.py                 # Analyst agent (legacy)
├── architect.py               # Architect agent (legacy)
├── coder.py                   # Developer/Coder agent (legacy)
├── tester.py                  # Tester agent (legacy)
├── deployer.py                # Deployer agent (legacy)
└── agent_factory.py           # Enhanced factory with ADK support

backend/app/tools/
├── adk_tool_registry.py       # Tool registry and management
├── adk_openapi_tools.py       # OpenAPI integration tools
└── specialized_adk_tools.py   # Specialized function tools

backend/app/services/
├── agent_service.py           # Agent service layer
├── adk_orchestration_service.py # Multi-agent orchestration
└── adk_handoff_service.py     # Agent handoff management
```

#### **5.2 BMAD-ADK Integration Wrapper**

**Purpose**: Enterprise wrapper that combines Google ADK capabilities with BMAD safety controls and audit requirements.

**Core Features:**

* **ADK Agent Management**: Proper `LlmAgent`, `Runner`, and `InMemorySessionService` usage
* **Enterprise Integration**: Full HITL safety controls, audit trails, and usage tracking
* **Session Management**: Correct `types.Content` and `types.Part` message handling
* **Error Recovery**: Comprehensive fallback mechanisms and graceful degradation
* **Cost Monitoring**: Token usage estimation and cost tracking per execution

**Implementation Architecture:**

```python
class BMADADKWrapper:
    """Integration wrapper combining ADK agents with BMAD enterprise features."""

    def __init__(self, agent_name: str, agent_type: str = "general",
                 model: str = "gemini-2.0-flash", instruction: str = "...",
                 tools: Optional[List[FunctionTool]] = None):
        # ADK components
        self.adk_agent = None          # LlmAgent instance
        self.adk_runner = None         # Runner for execution
        self.session_service = None    # InMemorySessionService

        # BMAD enterprise services
        self.hitl_service = HITLSafetyService()
        self.usage_tracker = LLMUsageTracker()
        self.audit_service = AuditTrailService()

    async def process_with_enterprise_controls(self, message: str,
                                             project_id: str, task_id: str) -> Dict[str, Any]:
        """Process message with full BMAD enterprise controls."""
        # 1. HITL Safety Check
        # 2. Audit Trail - Start
        # 3. Execute ADK Agent
        # 4. Usage Tracking
        # 5. Audit Trail - Complete
```

#### **5.3 BaseAgent Abstract Class (Legacy)**

**Purpose**: Provides legacy agent support with AutoGen integration for backward compatibility.

**Implementation Architecture:**

```python
class BaseAgent(ABC):
    """Abstract base class for all BotArmy agents with LLM reliability integration."""
    
    def __init__(self, agent_type: str, llm_config: Dict[str, Any]):
        self.agent_type = agent_type
        self.llm_config = llm_config
        
        # LLM Reliability Components (from Task 1)
        self.response_validator = LLMResponseValidator()
        self.retry_handler = LLMRetryHandler()
        self.usage_tracker = LLMUsageTracker()
        
        # AutoGen agent instance
        self.autogen_agent: Optional[ConversableAgent] = None
        self._initialize_autogen_agent()
    
    @abstractmethod
    async def execute_task(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute agent-specific task with context artifacts."""
        pass
    
    @abstractmethod
    async def create_handoff(self, to_agent: str, task: Task, context: List[ContextArtifact]) -> HandoffSchema:
        """Create structured handoff to another agent."""
        pass
```

#### **5.3 Orchestrator Agent (AB-01 to AB-05)**

The Orchestrator serves as the central coordinator managing the 6-phase SDLC workflow:

**Core Responsibilities:**

* **Phase Management**: Coordinates Discovery → Plan → Design → Build → Validate → Launch workflow
* **Context Passing**: Manages structured HandoffSchema between agents with proper validation
* **Conflict Resolution**: Detects and mediates conflicts between agent outputs after 3 automated attempts
* **State Management**: Maintains project state and progress tracking throughout workflow execution
* **Time-Conscious Orchestration**: Front-loads detail gathering to minimize iterative refinements

**Enhanced AutoGen Integration:**

```python
class OrchestratorAgent(BaseAgent):
    """Orchestrator manages 6-phase SDLC workflow with AutoGen integration."""
    
    def __init__(self, llm_config: Dict[str, Any]):
        super().__init__("orchestrator", llm_config)
        self.workflow_phases = ["discovery", "plan", "design", "build", "validate", "launch"]
    
    def _initialize_autogen_agent(self) -> None:
        self.autogen_agent = ConversableAgent(
            name="orchestrator",
            llm_config=self.llm_config,
            system_message="""You are the Orchestrator managing multi-agent SDLC workflows.
            Your responsibilities:
            - Coordinate 6-phase workflow: Discovery → Plan → Design → Build → Validate → Launch
            - Manage structured handoffs between agents using HandoffSchema
            - Resolve conflicts between agent outputs after 3 automated attempts
            - Maintain project state and progress tracking
            - Create HITL requests for critical decisions and conflicts"""
        )
```

#### **5.4 Analyst Agent (AB-06 to AB-10)**

Specialized for requirements analysis and PRD generation:

**Core Responsibilities:**

* **Requirements Analysis**: Generate structured Product Requirements Document from user input
* **Completeness Validation**: Identify missing requirements and create targeted clarifying questions
* **Stakeholder Interaction**: Engage users through chat interface for comprehensive requirement gathering
* **User Persona Creation**: Develop detailed user personas and business requirement mapping
* **Success Criteria Definition**: Define measurable acceptance conditions and success metrics

**Enhanced Implementation:**

```python
class AnalystAgent(BaseAgent):
    """Analyst specializes in requirements analysis with Claude LLM optimization."""
    
    def __init__(self, llm_config: Dict[str, Any]):
        # Configure for Anthropic Claude (optimized for requirements analysis)
        claude_config = {**llm_config, "model": "claude-3-sonnet-20240229"}
        super().__init__("analyst", claude_config)
    
    def _initialize_autogen_agent(self) -> None:
        self.autogen_agent = ConversableAgent(
            name="analyst",
            llm_config=self.llm_config,
            system_message="""You are the Analyst specializing in requirements analysis and PRD generation.
            Your responsibilities:
            - Generate structured Product Requirements Documents from user input
            - Identify missing requirements and create targeted clarifying questions
            - Develop detailed user personas and business requirement mapping
            - Define measurable acceptance criteria and success metrics
            - Engage users through chat interface for comprehensive requirement gathering"""
        )
```

**LLM Assignment**: Anthropic Claude (optimized for requirements analysis and documentation)

#### **5.3 Architect Agent (AB-11 to AB-15)**

Technical architecture and system design specialist:

**Core Responsibilities:**

* **Technical Architecture**: Create comprehensive system architecture from Analyst's PRD
* **API Design**: Generate detailed API specifications and data model definitions
* **Risk Assessment**: Identify technical risks, constraints, and dependency mapping
* **Implementation Planning**: Create task breakdown with clear deliverables and timelines
* **Integration Design**: Define database schema and system integration points

**LLM Assignment**: OpenAI GPT-4 (optimized for technical reasoning and architecture)

#### **5.4 Developer Agent (AB-16 to AB-20)**

Code generation and implementation specialist:

**Core Responsibilities:**

* **Code Generation**: Produce functional, production-ready code from Architect specifications
* **Quality Assurance**: Follow established coding standards with proper error handling
* **Test Creation**: Generate comprehensive unit tests for all generated code
* **Edge Case Handling**: Implement proper validation logic and edge case management
* **Documentation**: Create clear code comments and API documentation

**AutoGen Code Execution**: Integrated with code execution environment for validation

#### **5.5 Tester Agent (AB-21 to AB-25)**

Quality assurance and validation specialist:

**Core Responsibilities:**

* **Test Planning**: Create comprehensive test plans covering functional and edge cases
* **Automated Testing**: Execute testing scenarios and validate against requirements
* **Defect Reporting**: Identify and report bugs with detailed reproduction steps
* **Quality Validation**: Verify code quality and performance characteristics
* **Accessibility Compliance**: Validate user experience and accessibility standards

**Integration**: Connects to testing frameworks and CI/CD pipelines

#### **5.6 Deployer Agent (AB-26 to AB-30)**

Deployment automation and environment management:

**Core Responsibilities:**

* **Deployment Automation**: Handle application deployment to target environments
* **Pipeline Configuration**: Configure deployment pipelines and environment variables
* **Health Validation**: Validate deployment success and perform comprehensive health checks
* **Documentation**: Create deployment documentation and rollback procedures
* **Monitoring**: Monitor post-deployment system performance and stability

**Target Environments**: GitHub Codespaces (initial), Vercel (production path)

#### **5.7 Agent Service Layer & Factory Pattern (Task 2)**

**Purpose**: Provides service layer for agent instantiation, lifecycle management, and handoff execution.

**Core Components:**

* **AgentService**: Factory pattern implementation for type-based agent instantiation
* **AutoGenConversationManager**: Manages multi-agent conversations using AutoGen GroupChat
* **HandoffExecutor**: Orchestrates structured handoffs between agents

**Implementation Architecture:**

```python
class AgentService:
    """Agent service factory with type-based instantiation and lifecycle management."""
    
    def __init__(self):
        self.agent_classes: Dict[str, Type[BaseAgent]] = {
            "orchestrator": OrchestratorAgent,
            "analyst": AnalystAgent,
            "architect": ArchitectAgent,
            "coder": CoderAgent,
            "tester": TesterAgent,
            "deployer": DeployerAgent
        }
        self.agent_instances: Dict[str, BaseAgent] = {}
    
    async def get_agent(self, agent_type: str, llm_config: Dict[str, Any]) -> BaseAgent:
        """Get or create agent instance with proper LLM configuration."""
        if agent_type not in self.agent_instances:
            if agent_type not in self.agent_classes:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            agent_class = self.agent_classes[agent_type]
            self.agent_instances[agent_type] = agent_class(llm_config)
        
        return self.agent_instances[agent_type]
    
    async def execute_handoff(self, handoff: HandoffSchema, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute structured handoff between agents with full lifecycle tracking."""
        # Handoff implementation with status tracking
        pass
```

**AutoGen GroupChat Integration:**

```python
class AutoGenConversationManager:
    """Manages AutoGen group conversations between agents."""
    
    async def create_multi_agent_conversation(
        self, 
        agents: List[str], 
        initial_message: str,
        project_id: UUID
    ) -> str:
        """Create AutoGen group conversation with multiple agents."""
        
        # Get AutoGen agent instances
        autogen_agents = []
        for agent_type in agents:
            agent = await self.agent_service.get_agent(agent_type, {})
            autogen_agents.append(agent.autogen_agent)
        
        # Create group chat with round-robin speaker selection
        group_chat = GroupChat(
            agents=autogen_agents,
            messages=[],
            max_round=10,
            speaker_selection_method="round_robin"
        )
        
        # Execute conversation with manager
        manager = GroupChatManager(groupchat=group_chat, llm_config={})
        response = await manager.a_initiate_chat(recipient=autogen_agents[0], message=initial_message)
        
        return response
```

**Agent Configuration Loading:**

* **Dynamic Configuration**: Load agent configs from `.bmad-core/agents/` directory
* **LLM Assignment**: Automatic LLM provider assignment based on agent specialization
* **Context Integration**: Seamless integration with Context Store Pattern
* **Reliability Features**: All agents inherit Task 1 LLM reliability features

### **6. Enhanced HITL System Architecture**

#### **6.1 HITL Trigger Conditions (HL-01 to HL-06)**

**Automatic Triggers:**

* **Phase Completion**: Pause after each major SDLC phase (Discovery, Plan, Design, Build, Validate, Launch)
* **Confidence Threshold**: Request human input when agent confidence < 80%
* **Conflict Escalation**: Escalate agent conflicts after 3 automated resolution attempts
* **Critical Decisions**: Pause for architectural or design decision approval
* **Error Recovery**: Create HITL requests when agents encounter unresolvable errors

**User Configuration:**

* **Oversight Levels**: High (approval for all major decisions), Medium (critical decisions only), Low (conflicts and errors only)
* **Project-Specific Settings**: Configurable per-project supervision requirements

#### **6.2 HITL Response Processing (HL-07 to HL-12)**

**Response Actions:**

```python
class HitlResponseProcessor:
    def process_response(self, request_id: UUID, action: HitlAction, data: Dict[str, Any]):
        """Process HITL responses with complete audit trail."""
        if action == HitlAction.APPROVE:
            return self._resume_workflow(request_id, approved=True)
        elif action == HitlAction.REJECT:
            return self._handle_rejection(request_id, data.get('comment'))
        elif action == HitlAction.AMEND:
            return self._apply_amendments(request_id, data.get('amended_content'))
```

**Features:**

* **Complete History**: Maintain full audit trail with timestamps and user attribution
* **Bulk Operations**: Support batch approval of similar items for efficiency
* **Context-Aware Interface**: Provide relevant artifact previews for informed decisions
* **Expiration Management**: Configurable timeouts with automatic escalation
* **Real-Time Notifications**: Immediate alerts via WebSocket for new requests

#### **6.3 Conflict Resolution Process (HL-13 to HL-16)**

**Resolution Workflow:**

1. **Automated Mediation**: Orchestrator attempts resolution using project context
2. **Evidence Gathering**: Collect agent reasoning and supporting evidence
3. **Human Escalation**: Present structured conflict with resolution options
4. **Decision Tracking**: Capture rationale and apply resolution across system

### **7. Error Handling and Recovery Architecture**

#### **7.1 Agent Failure Recovery (EH-01 to EH-05)**

**Multi-Tier Recovery:**

```python
class TaskRecoveryService:
    async def handle_task_failure(self, task_id: UUID, error: Exception):
        """Implement graduated recovery strategy."""
        # Tier 1: Automatic Retry (3 attempts with exponential backoff)
        if self.retry_count < 3:
            return await self._retry_task(task_id, backoff_seconds=2**self.retry_count)
        
        # Tier 2: Orchestrator Reassignment
        if await self.orchestrator.can_reassign_task(task_id):
            return await self.orchestrator.reassign_task(task_id)
        
        # Tier 3: HITL Intervention
        return await self.hitl_service.create_failure_request(task_id, error)
```

#### **7.2 Timeout and Progress Management (EH-06 to EH-10)**

**Timeout Handling:**

* **Task Timeouts**: 5-minute automatic timeout with status updates
* **Progress Updates**: 30-second heartbeat via WebSocket for long-running tasks
* **Network Resilience**: Auto-reconnect with exponential backoff for WebSocket connections
* **Session Preservation**: Maintain user session state during temporary disconnections

#### **7.3 Data Integrity and Validation (EH-11 to EH-14)**

**Data Protection:**

* **Transaction Management**: All database operations use proper transaction rollback
* **Schema Validation**: Context artifacts validated before storage
* **Backup Procedures**: Automated backup with point-in-time recovery
* **Corruption Detection**: Automatic detection and repair attempts for data corruption

***

### **8. Sprint 3 Service Architecture Implementation**

Sprint 3 introduced three core services that enhance the system with real-time capabilities and project lifecycle management:

#### **8.1 AgentStatusService**

**Purpose**: Manages real-time agent status with WebSocket broadcasting and database persistence.

**Key Features:**

* **In-Memory Caching**: Fast agent status retrieval with thread-safe updates
* **WebSocket Broadcasting**: Real-time status change notifications to subscribed clients
* **Database Persistence**: Optional database synchronization for status history
* **Status Lifecycle**: Support for IDLE → WORKING → WAITING_FOR_HITL → ERROR state transitions

**Core Methods:**

```python
class AgentStatusService:
    async def update_agent_status(agent_type, status, project_id=None, task_id=None, db=None)
    async def set_agent_working(agent_type, task_id, project_id=None, db=None)
    async def set_agent_idle(agent_type, project_id=None, db=None)
    async def set_agent_waiting_for_hitl(agent_type, task_id, project_id=None, db=None)
    async def set_agent_error(agent_type, error_message, task_id=None, project_id=None, db=None)
    def get_agent_status(agent_type) -> AgentStatusModel
    def get_all_agent_statuses() -> Dict[AgentType, AgentStatusModel]
```

**WebSocket Integration:**

* Broadcasts `AGENT_STATUS_CHANGE` events with full agent state
* Project-scoped and global event distribution
* Automatic error handling and retry logic

#### **8.2 ArtifactService**

**Purpose**: Generates structured project artifacts and manages downloadable ZIP files.

**Key Features:**

* **Multi-Format Artifact Generation**: Code files, documentation, requirements.txt, README.md
* **ZIP File Creation**: Structured project downloads with proper organization
* **Content Extraction**: Intelligent parsing of context artifact data
* **Cleanup Management**: Automatic artifact lifecycle and storage management

**Core Methods:**

```python
class ArtifactService:
    async def generate_project_artifacts(project_id, db) -> List[ProjectArtifact]
    async def create_project_zip(project_id, artifacts) -> str
    async def notify_artifacts_ready(project_id)
    def cleanup_old_artifacts(max_age_hours=24)
    def _extract_requirements(artifacts) -> List[str]
    def _generate_readme(project, artifacts) -> str
```

**Generated Artifacts:**

* **Project Summary**: Comprehensive project overview with metadata
* **Source Code Files**: Extracted from SOURCE_CODE artifacts with proper naming
* **Documentation**: Generated from SOFTWARE_SPECIFICATION and PROJECT_PLAN artifacts
* **Requirements.txt**: Auto-extracted Python dependencies from import statements
* **README.md**: Structured project documentation with file descriptions

#### **8.3 ProjectCompletionService**

**Purpose**: Automatically detects project completion and triggers artifact generation.

**Key Features:**

* **Multi-Criteria Detection**: Task status analysis + completion keyword detection
* **Automatic Triggers**: Generates artifacts when projects complete
* **WebSocket Notifications**: Real-time completion event broadcasting
* **Detailed Metrics**: Comprehensive completion status and progress tracking

**Core Methods:**

```python
class ProjectCompletionService:
    async def check_project_completion(project_id, db) -> bool
    async def force_project_completion(project_id, db) -> bool
    async def get_project_completion_status(project_id, db) -> dict
    def _has_completion_indicators(tasks) -> bool
    async def _handle_project_completion(project_id, db)
```

**Completion Criteria:**

* **Task Status**: All tasks marked as COMPLETED or FAILED
* **Keyword Detection**: Tasks containing "deployment", "final check", "project completed", etc.
* **Manual Override**: Admin force-completion capability

#### **8.4 Enhanced WebSocket Event System**

**New Event Types:**

```python
# Agent Status Broadcasting
{
  "event_type": "AGENT_STATUS_CHANGE",
  "agent_type": "analyst",
  "project_id": "uuid",
  "data": {
    "status": "working",
    "current_task_id": "uuid",
    "last_activity": "datetime",
    "error_message": null
  }
}

# Artifact Generation Notifications
{
  "event_type": "ARTIFACT_CREATED", 
  "project_id": "uuid",
  "data": {
    "message": "Project artifacts are ready for download",
    "download_available": true,
    "generated_at": "datetime"
  }
}

# Project Completion Events
{
  "event_type": "WORKFLOW_EVENT",
  "project_id": "uuid", 
  "data": {
    "event": "project_completed",
    "message": "Project has completed successfully",
    "completed_at": "datetime",
    "artifacts_generating": true
  }
}
```

#### **8.5 API Endpoint Implementation**

**Agent Status Management (4 endpoints):**

* `GET /api/v1/agents/status` - Real-time status of all agents
* `GET /api/v1/agents/status/{agent_type}` - Specific agent status
* `GET /api/v1/agents/status-history/{agent_type}` - Database status history
* `POST /api/v1/agents/status/{agent_type}/reset` - Admin reset functionality

**Artifact Management (5 endpoints):**

* `POST /api/v1/artifacts/{project_id}/generate` - Generate project artifacts
* `GET /api/v1/artifacts/{project_id}/summary` - Artifact metadata
* `GET /api/v1/artifacts/{project_id}/download` - ZIP file download
* `DELETE /api/v1/artifacts/{project_id}/artifacts` - Project cleanup
* `DELETE /api/v1/artifacts/cleanup-old` - System-wide cleanup

**Project Completion (3 endpoints):**

* `GET /api/v1/projects/{project_id}/completion` - Detailed completion metrics
* `POST /api/v1/projects/{project_id}/check-completion` - Manual completion check
* `POST /api/v1/projects/{project_id}/force-complete` - Admin force completion

### **9. Enhanced Implementation Plan**

#### **Phase 1: Foundation & Infrastructure (4-6 weeks)**

**Backend Core Setup:**

* FastAPI project with PostgreSQL (Alembic migrations) and Redis
* Pydantic v2 models with ConfigDict for all data structures
* WebSocket service for real-time communication with auto-reconnect
* Celery task queue with retry logic and progress tracking
* Health check endpoint with multi-component monitoring

**Enhanced LLM Reliability System:** ✅ **COMPLETED (Task 1)**

* OpenAI GPT-4 integration with robust error handling and monitoring
* LLM response validation and sanitization to ensure Context Store integrity
* Exponential backoff retry logic (1s, 2s, 4s intervals) for API failures
* Comprehensive usage tracking and cost monitoring with structured logging
* Provider-specific error handling and graceful degradation

**BMAD Core Template System:**

* Dynamic workflow loading from `.bmad-core/workflows/`
* YAML template parsing from `.bmad-core/templates/`
* Agent team configuration loading from `.bmad-core/agent-teams/`
* Variable substitution and conditional logic processing

#### **Phase 2: Agent Framework & Core Logic (Task 2 Implementation - 6-8 weeks)**

**Agent Framework Foundation:** ✅ **PLANNED (Task 2)**

* BaseAgent abstract class with LLM reliability integration from Task 1
* Factory pattern for type-based agent instantiation with lifecycle management
* HandoffSchema enhanced with validation, priority levels, and status tracking
* Agent service layer with structured handoff execution and status management

**AutoGen Framework Integration:** ✅ **PLANNED (Task 2)**

* Microsoft AutoGen framework configuration and setup with ConversableAgent wrappers
* Agent conversation management with proper context passing and GroupChat support
* Group chat capabilities for multi-agent collaboration with round-robin speaker selection
* Dynamic agent configuration loading from `.bmad-core/agents/` directory

**Specialized Agent Implementation:** ✅ **PLANNED (Task 2)**

* **Orchestrator Agent**: 6-phase SDLC workflow coordination with conflict resolution
* **Analyst Agent**: Requirements analysis and PRD generation (Claude LLM optimization)
* **Architect Agent**: Technical architecture and API design (GPT-4 LLM optimization)
* **Developer Agent**: Code generation with AutoGen code execution capabilities
* **Tester Agent**: Quality assurance and validation with comprehensive test planning
* **Deployer Agent**: Deployment automation and monitoring with health validation

**Context Store Pattern Integration:**

* Mixed-granularity artifact storage (document/section/concept level)
* Repository pattern with proper abstraction layers
* Context artifact validation and metadata management via BaseAgent
* Intelligent retrieval and injection for agent workflows through HandoffSchema

#### **Phase 3: HITL System & Advanced Features (4-5 weeks)**

**Enhanced HITL Implementation:**

* Comprehensive approval/rejection/amendment workflow
* Configurable oversight levels (High/Medium/Low)
* Automatic trigger conditions with confidence scoring
* Complete audit trail and history tracking
* Real-time notifications via WebSocket

**Error Handling & Recovery:**

* Multi-tier recovery strategy (retry → reassign → HITL)
* Timeout management with progress heartbeats
* Network resilience and session preservation
* Data integrity and transaction management

#### **Phase 4: Frontend Application (5-7 weeks)**

**Next.js Application Setup:**

* Responsive UI with Tailwind CSS and modern design patterns
* Zustand state management for complex application state
* WebSocket client with automatic reconnection and event handling
* Component library following shadcn/ui patterns

**Core Interface Components:**

* Real-time chat interface with agent conversation history
* Workflow visualization with phase/task progress tracking
* HITL approval interface with context-aware decision support
* Agent status dashboard with performance monitoring
* Context artifact browser with search and filtering

#### **Phase 5: Integration & Testing (3-4 weeks)**

**End-to-End Integration:**

* Complete SDLC workflow testing from idea to deployment
* Multi-agent conversation and handoff validation
* HITL approval flow testing with all action types
* Error recovery and resilience testing

**Performance & Security:**

* API response time optimization (< 200ms status queries)
* WebSocket event delivery optimization (< 100ms)
* Concurrent project support testing (10 projects, 50 tasks each)
* Security audit and penetration testing
* Load testing and performance profiling

**Quality Assurance:**

* Comprehensive test suite (unit, integration, E2E)
* Code quality gates with automated linting and formatting
* Documentation completeness verification
* Accessibility compliance testing (WCAG 2.1 AA)

#### **Phase 6: Deployment & Monitoring (2-3 weeks)**

**Production Deployment:**

* GitHub Codespaces initial deployment configuration
* Vercel production deployment with environment management
* Database migration and backup procedures
* CI/CD pipeline setup with automated testing

**Monitoring & Observability:**

* Application performance monitoring (APM) integration
* Structured logging with correlation IDs
* Alert system for critical failures and performance degradation
* Usage analytics and performance metrics dashboard

### **9. System Health & Monitoring Architecture**

#### **9.1 Multi-Component Health Checks**

**Enhanced Health Endpoint** (`/healthz`):

* **Application Layer**: FastAPI service status and response times
* **Database Layer**: PostgreSQL connectivity, query performance, migration status
* **Cache Layer**: Redis connectivity, memory usage, key-value performance
* **Task Queue**: Celery worker availability, queue depth, processing times
* **LLM Providers**: OpenAI/Claude/Gemini API connectivity and rate limits
* **WebSocket Service**: Connection pool status and message delivery rates

**Health Status Levels:**

* **Healthy**: All components operational within performance thresholds
* **Degraded**: Some components experiencing performance issues but functional
* **Unhealthy**: Critical components down or performance severely impacted

#### **9.2 Observability & Metrics**

**Key Performance Indicators:**

* API response times (P50, P95, P99 percentiles)
* WebSocket event delivery latency
* Agent task completion rates and performance
* HITL request resolution times
* Context artifact retrieval performance
* Error rates and failure patterns

**Structured Logging:**

* Correlation IDs for request tracing across services
* Agent conversation logging with privacy controls
* HITL interaction audit trails
* Performance metrics and resource utilization
* Security events and access patterns

### **10. Implementation Status & Architectural Validation**

#### **10.1 Completed Tasks Overview**

**Task 0: Infrastructure Foundation** ✅ **COMPLETED**
- PostgreSQL database with complete schema migrations
- All core tables implemented with proper relationships and indexes
- WebSocket manager with real-time event broadcasting
- Health check endpoints with multi-component monitoring
- Context Store database integration with mixed-granularity storage

**Task 4: Real Agent Processing** ✅ **COMPLETED**
- Replaced simulation with live LLM-powered agent execution via AutoGen
- Complete database task lifecycle tracking with UTC timezone handling
- Real-time WebSocket progress broadcasting with structured events
- Context artifact integration with dynamic creation and retrieval
- Comprehensive input validation and error handling with retry mechanisms

**Task 5: Workflow Orchestration Engine** ✅ **COMPLETED**
- Dynamic workflow execution engine with state machine pattern
- BMAD Core template system integration with YAML workflow definitions
- Agent handoff coordination with structured HandoffSchema validation
- Workflow state persistence and recovery mechanisms for interruptions
- Conditional workflow routing and parallel task execution capabilities

**Task 6: Human-in-the-Loop System** ✅ **COMPLETED**
- Comprehensive HITL system with configurable trigger conditions
- Complete approval/rejection/amendment workflow with audit trails
- Context-aware approval interfaces with artifact previews
- Bulk approval operations for workflow efficiency
- Real-time WebSocket notifications for HITL request events

**HITL Safety Architecture** ✅ **COMPLETED**
- Mandatory agent approval controls (pre-execution, response, next-step)
- Budget control mechanisms with token limits and automatic stops
- Emergency stop system with multi-trigger conditions
- Response approval tracking with content safety and quality scoring
- Recovery session management with systematic procedures

#### **10.2 Architectural Corrections Applied**

**Database Model Consistency** ✅ **FIXED**
- Corrected incorrect SQLEnum(AgentStatus) usage for Boolean fields
- Fixed `auto_approved`, `emergency_stop_enabled`, `active`, `delivered`, `expired` field types
- Resolved architectural type inconsistencies across all models

**Timezone-Aware Datetime Handling** ✅ **FIXED**
- Replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`
- Created timezone-aware `utcnow()` function for SQLAlchemy defaults
- Applied consistent UTC handling across all database models and services

**Service Integration Patterns** ✅ **VALIDATED**
- Verified consistent dependency injection patterns across all services
- Fixed missing `HitlService` import in workflow engine
- Validated proper database session passing to all stateful services

**API Response Format Standardization** ✅ **FIXED**
- Standardized health check endpoints to include 'detail' key consistently
- Enhanced error type classification for timeout and connection errors
- Fixed hardcoded timestamps in health monitoring responses

#### **10.3 System Architecture Validation**

**SOLID Principles Compliance** ✅ **VERIFIED**
- Single Responsibility: Each service has clearly defined, focused responsibilities
- Open/Closed: Plugin architecture allows extension without modification
- Liskov Substitution: All interfaces properly substitutable with implementations
- Interface Segregation: Client-specific interfaces prevent unwanted dependencies
- Dependency Inversion: High-level modules depend on abstractions, not concretions

**Cross-System Integration** ✅ **VALIDATED**
- Task processing → Workflow engine → HITL system integration verified
- Context Store → Agent communication → Artifact generation flow working
- WebSocket → Database → API response consistency maintained
- AutoGen → Agent services → Task execution pipeline operational

### **11. LLM Reliability & Monitoring Architecture**

#### **10.1 Response Validation & Sanitization System**

**Purpose**: Ensure Context Store integrity by validating and sanitizing all LLM responses before persistence.

**Core Components:**

* **Response Validator**: Validates LLM response structure, content format, and data types
* **Content Sanitizer**: Removes malicious content, validates JSON structures, and ensures data integrity
* **Error Recovery**: Handles malformed responses with graceful fallbacks and retry mechanisms

**Implementation Requirements:**

```python
class LLMResponseValidator:
    """Validates and sanitizes LLM responses before Context Store persistence."""
    
    async def validate_response(self, response: str, expected_format: str) -> ValidationResult:
        """Validate LLM response against expected format and content rules."""
        
    async def sanitize_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize response content for Context Store integrity."""
        
    async def handle_validation_failure(self, response: str, error: ValidationError) -> str:
        """Handle validation failures with recovery strategies."""
```

**Validation Rules:**

* **JSON Structure**: Validate expected JSON schemas for structured responses
* **Content Safety**: Remove potentially malicious content or script injections
* **Data Type Validation**: Ensure proper data types for Context Store persistence
* **Size Limits**: Enforce response size constraints to prevent resource exhaustion

#### **10.2 Exponential Backoff Retry System**

**Purpose**: Handle LLM API failures gracefully with intelligent retry mechanisms.

**Retry Configuration:**

* **Retry Intervals**: 1 second, 2 seconds, 4 seconds (exponential backoff)
* **Maximum Retries**: 3 attempts before escalation
* **Retry Conditions**: API timeouts, rate limits, temporary service failures
* **Circuit Breaker**: Automatic failsafe after consecutive failures

**Implementation Architecture:**

```python
class LLMRetryHandler:
    """Implements exponential backoff retry logic for LLM API calls."""
    
    async def execute_with_retry(self, llm_call: Callable, max_retries: int = 3) -> Any:
        """Execute LLM call with exponential backoff retry logic."""
        
    def calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay: 2^(attempt-1) seconds."""
        
    async def should_retry(self, exception: Exception) -> bool:
        """Determine if exception is retryable."""
```

**Error Classification:**

* **Retryable Errors**: Network timeouts, rate limits, temporary API failures
* **Non-Retryable Errors**: Authentication failures, invalid API keys, permanent service errors
* **Escalation Triggers**: Maximum retry attempts exceeded, service degradation detected

#### **10.3 Usage Tracking & Cost Monitoring**

**Purpose**: Provide comprehensive monitoring of LLM usage patterns, costs, and performance metrics.

**Monitoring Components:**

* **Usage Metrics**: Token consumption, request counts, response times per agent type
* **Cost Analysis**: Real-time cost tracking based on provider pricing models
* **Performance Monitoring**: Success rates, error patterns, response quality metrics
* **Agent Attribution**: Usage breakdown by agent type and project

**Implementation Requirements:**

```python
class LLMUsageTracker:
    """Comprehensive LLM usage tracking and cost monitoring."""
    
    async def track_request(self, agent_type: str, tokens_used: int, response_time: float):
        """Track individual LLM request metrics."""
        
    async def calculate_costs(self, usage_data: UsageData) -> CostBreakdown:
        """Calculate costs based on provider pricing models."""
        
    async def generate_usage_report(self, project_id: UUID, date_range: DateRange) -> UsageReport:
        """Generate comprehensive usage and cost reports."""
        
    async def detect_usage_anomalies(self) -> List[UsageAnomaly]:
        """Detect unusual usage patterns or cost spikes."""
```

**Structured Logging Integration:**

```python
# Example usage tracking log entries
logger.info("LLM request completed", 
           agent_type="analyst", 
           project_id=str(project_id),
           tokens_used=450, 
           response_time_ms=1250,
           estimated_cost=0.0025,
           provider="openai",
           model="gpt-4",
           success=True)

logger.warning("LLM retry triggered", 
              agent_type="architect",
              project_id=str(project_id), 
              attempt=2,
              backoff_delay=2.0,
              error_type="rate_limit",
              provider="openai")
```

**Monitoring Dashboard Metrics:**

* **Real-Time Usage**: Current API calls, token consumption, active agents
* **Cost Analysis**: Daily/weekly/monthly spend tracking with budget alerts
* **Performance Metrics**: Success rates, average response times, error distributions
* **Agent Efficiency**: Usage patterns and performance by agent type

#### **10.4 Enhanced AutoGen Service Integration**

**Purpose**: Integrate LLM reliability features into existing AutoGen service without breaking changes.

**Integration Points:**

```python
# Updated AutoGenService with reliability features
class AutoGenService:
    def __init__(self):
        self.agents: Dict[str, AssistantAgent] = {}
        self.response_validator = LLMResponseValidator()
        self.retry_handler = LLMRetryHandler()
        self.usage_tracker = LLMUsageTracker()
        
    def _create_model_client(self, model: str, temperature: float = 0.7) -> OpenAIChatCompletionClient:
        """Enhanced model client with reliability features."""
        # Add retry logic, usage tracking, and validation
        
    async def run_single_agent_conversation(self, agent: AssistantAgent, message: str, task: Task) -> str:
        """Enhanced conversation with validation and monitoring."""
        # Integrate retry logic, response validation, and usage tracking
```

**Enhancement Features:**

* **Transparent Integration**: Existing AutoGen calls enhanced without API changes
* **Comprehensive Monitoring**: All LLM interactions tracked and monitored
* **Graceful Degradation**: Fallback responses when LLM services unavailable
* **Performance Optimization**: Intelligent retry logic to minimize service impact

#### **10.5 LLM Reliability Configuration**

**Purpose**: Environment-based configuration for LLM reliability features with production-ready defaults.

**Configuration Variables:**

```bash
# Core LLM Configuration
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here  # Optional
GOOGLE_API_KEY=your_google_key_here        # Optional

# LLM Reliability Settings
LLM_RETRY_MAX_ATTEMPTS=3                    # Maximum retry attempts (default: 3)
LLM_RETRY_BASE_DELAY=1.0                    # Base delay in seconds (default: 1.0)
LLM_RESPONSE_TIMEOUT=30                     # Response timeout in seconds (default: 30)
LLM_MAX_RESPONSE_SIZE=50000                 # Maximum response size in characters (default: 50000)
LLM_ENABLE_USAGE_TRACKING=true              # Enable usage tracking (default: true)
```

**Configuration Management:**

* **Environment-based**: All settings configurable via environment variables
* **Production Defaults**: Sensible defaults for production deployment
* **Development Override**: Lower timeouts and limits for development
* **Validation**: Configuration validation at startup with clear error messages
* **Hot Reload**: Configuration changes reflected without restart (where safe)

**Health Check Integration:**

```python
# LLM provider health status in /healthz endpoint
{
  "llm_providers": {
    "openai": {"status": "healthy", "response_time_ms": 245},
    "anthropic": {"status": "not_configured"},
    "google": {"status": "not_configured"}
  }
}
```

### **11. Testing & Quality Assurance Architecture**

#### **10.1 Comprehensive Test Coverage Strategy**

The BotArmy system implements a **multi-layered testing strategy** with **70+ test cases** ensuring production readiness across all Sprint 4 features.

**Testing Pyramid Structure:**

```
                    E2E Tests (10+)
                 ╱─────────────────╲
              API Tests (15+)
           ╱─────────────────────╲
        Integration Tests (6)
     ╱─────────────────────────╲
  Unit Tests (48+)
╱─────────────────────────────╲
```

#### **10.2 Test Categories & Coverage**

**Unit Tests** (`tests/unit/`):

* **Audit Service Tests**: 13 comprehensive test cases covering all audit trail functionality
* **Model Validation Tests**: 20+ Pydantic model tests for data integrity
* **API Endpoint Tests**: 15+ endpoint-specific validation tests
* **Service Layer Tests**: Business logic validation and error handling

**Integration Tests** (`tests/integration/`):

* **Database Integration**: SQLAlchemy operations, query performance, data persistence
* **Audit Trail Workflows**: Complete event logging and retrieval workflows
* **High-Volume Testing**: 100+ event handling and performance validation
* **Date Range Filtering**: Time-based queries and pagination

**API Tests** (`tests/unit/test_audit_api.py`):

* **Endpoint Functionality**: All 4 new audit endpoints comprehensive testing
* **Parameter Validation**: Query parameters, filtering, pagination
* **Error Handling**: Invalid inputs, database failures, recovery scenarios
* **Performance Testing**: NFR-01 compliance validation (sub-200ms)

**End-to-End Tests** (`tests/e2e/`):

* **Complete Workflows**: Project lifecycle with audit trail integration
* **System Integration**: WebSocket, database, and API coordination
* **Performance Validation**: Full system NFR-01 compliance testing
* **Error Recovery**: Database failures, service degradation scenarios

#### **10.3 Quality Assurance Metrics**

**Performance Requirements (NFR-01):**

* **API Response Times**: < 200ms for all endpoints
* **Database Operations**: Query performance optimization
* **WebSocket Latency**: Real-time event delivery < 100ms
* **Health Check Response**: Comprehensive service status < 50ms

**Test Coverage Goals:**

* **Unit Test Coverage**: 95%+ for core business logic
* **API Endpoint Coverage**: 100% of Sprint 4 endpoints
* **Integration Coverage**: All database workflows validated
* **E2E Coverage**: Complete user journeys tested

#### **10.4 Test Infrastructure Architecture**

**Test Database Strategy:**

```python
# In-memory SQLite for unit/integration tests
engine = create_engine("sqlite:///:memory:")

# Isolated test sessions with rollback
@pytest.fixture
def test_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
```

**Mock Strategy:**

* **Service Layer Mocking**: Database operations and external dependencies
* **Pydantic Model Mocking**: Data validation and serialization testing
* **WebSocket Mocking**: Real-time communication simulation
* **LLM Provider Mocking**: AI service interaction testing

#### **10.5 Continuous Quality Validation**

**Pre-deployment Test Checklist:**

* ✅ Core audit service: 13/13 unit tests passing
* ✅ API endpoint coverage: 100% of new Sprint 4 endpoints tested
* ✅ Performance validation: All endpoints meet NFR-01 requirements
* ✅ Integration reliability: Full workflow testing with database operations
* ✅ Error resilience: Database failure and recovery testing

**Test Automation Pipeline:**

1. **Unit Tests**: Fast feedback on code changes
2. **Integration Tests**: Database and service integration validation
3. **API Tests**: Endpoint functionality and performance validation
4. **E2E Tests**: Complete system workflow verification
5. **Performance Tests**: NFR-01 compliance continuous monitoring

#### **10.6 Production Readiness Validation**

**Sprint 4 Testing Achievement:**

* **70+ comprehensive test cases** implemented and validated
* **Core audit trail functionality** fully tested and production-ready
* **Enhanced health monitoring** with Kubernetes-compatible endpoints
* **Performance compliance** verified across all new features
* **Error handling** comprehensive validation and recovery testing

**Quality Metrics Achieved:**

* **Audit Service Reliability**: 13/13 unit tests passing
* **API Stability**: All endpoints tested with error scenarios
* **Database Integration**: Complete workflow validation
* **Performance Compliance**: Sub-200ms response time validation
* **Production Readiness**: Comprehensive error handling and monitoring
