### **BotArmy Software Specification (Updated)**

This document outlines the technical specifications for the BotArmy Proof-of-Concept (POC), based on the architectural decisions and design principles discussed. The design adheres to the SOLID principles to ensure the system is maintainable, scalable, and extensible.

***

### **1. Overall System Architecture**

The system follows a modern microservice-oriented architecture with multi-LLM support, AutoGen agent framework integration, and BMAD Core template system. The architecture is designed for scalability, maintainability, and extensibility.

#### **1.1 Core Components**

* **Frontend (Next.js/React)**: A responsive single-page application with real-time chat interface, workflow visualization, and HITL approval components. Uses Zustand for state management and Tailwind CSS for styling.

* **Backend (FastAPI)**: The orchestration hub hosting the Orchestrator service, multi-agent coordination, and all data persistence. Provides REST APIs and WebSocket services for real-time communication.

* **Multi-LLM Provider Layer**: Configurable support for multiple LLM providers:
  - **OpenAI GPT-4**: Primary provider for technical architecture and complex reasoning
  - **Anthropic Claude**: Specialized for requirements analysis and documentation
  - **Google Gemini**: Alternative provider with configurable fallback
  - **Provider Abstraction**: Unified interface allowing agent-specific LLM assignments

* **AutoGen Framework Integration**: Microsoft AutoGen framework managing agent conversations:
  - **Agent Conversation Management**: Structured multi-agent dialogues
  - **Group Chat Capabilities**: Multi-agent collaboration scenarios  
  - **Context Passing**: Proper handoff schemas between agents
  - **Configuration Loading**: Dynamic agent configs from `.bmad-core/agents/`

* **BMAD Core Template System**: Dynamic workflow and document generation:
  - **Workflow Definitions**: Loaded from `.bmad-core/workflows/`
  - **Document Templates**: YAML-based templates in `.bmad-core/templates/`
  - **Agent Team Configs**: Team compositions in `.bmad-core/agent-teams/`
  - **Variable Substitution**: Dynamic template rendering with conditional logic

* **Task Queue (Celery)**: Asynchronous task processing with Redis broker:
  - **Retry Logic**: Exponential backoff (1s, 2s, 4s) for failed tasks
  - **Progress Tracking**: Real-time task progress updates via WebSocket
  - **Timeout Management**: 5-minute task timeouts with automatic status updates

* **Database Layer (PostgreSQL)**: Multi-tenant data storage with proper indexing:
  - **Core Application Data**: Projects, tasks, agents, and user information
  - **Context Store**: Mixed-granularity artifact storage (document/section/concept level)
  - **HITL System**: Request tracking with complete history and audit trails
  - **Migration Management**: Alembic-based version control

* **Caching Layer (Redis)**: High-performance caching and session management:
  - **WebSocket Sessions**: Connection state and subscription management
  - **Task Queue Broker**: Celery job distribution and result caching
  - **API Response Caching**: Sub-200ms response times for status queries

* **Real-Time Communication (WebSocket)**: Event-driven architecture with 100ms delivery:
  - **Agent Status Broadcasting**: Live agent state changes
  - **Task Progress Updates**: Real-time workflow monitoring
  - **HITL Request Alerts**: Immediate approval request notifications
  - **Error Notifications**: Structured error reporting with severity levels

### **2. Enhanced SOLID Principles Architecture**

The system architecture strictly adheres to SOLID principles with advanced patterns for maintainability and extensibility:

#### **2.1 Single Responsibility Principle (SRP)**
Each component has a single, well-defined responsibility:
* **OrchestratorService**: Coordinates workflow execution and agent task delegation
* **ContextStoreService**: Manages artifact persistence and retrieval
* **HitlService**: Handles human-in-the-loop request lifecycle
* **TaskExecutionService**: Manages Celery task processing and monitoring
* **LLMProviderService**: Abstracts multi-provider LLM communication
* **WebSocketManager**: Handles real-time event broadcasting
* **Agent Classes**: Each agent (Analyst, Architect, Coder, Tester, Deployer) focuses solely on their domain expertise

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
    agent_type: Literal["orchestrator", "analyst", "architect", "coder", "tester", "deployer"]
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    context_ids: List[UUID] = Field(default_factory=list)
    instructions: str
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
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

#### **3.4 Agent Communication Models**

```python
class HandoffSchema(BaseModel):
    """Generic JSON schema for structured agent handoffs with validation."""
    handoff_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    from_agent: str
    to_agent: str
    phase: str
    instructions: str
    context_ids: List[UUID] = Field(default_factory=list)
    expected_outputs: List[str] = Field(default_factory=list)
    priority: int = Field(default=1, ge=1, le=5)
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(json_encoders={
        datetime: lambda v: v.isoformat(),
        UUID: lambda v: str(v)
    })
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

### **5. Implementation Plan**

1. **Phase 1: Foundation (Backend)**
    * Set up a FastAPI project with a PostgreSQL database and Redis.
    * Implement the Pydantic data models, including the new `amended` status for `HitlRequest`.
    * Build the core WebSocket service for real-time communication.
    * Create a simple task queue with Celery and Redis.
2. **Phase 2: Core Logic (Backend)**
    * Integrate and configure the **AutoGen** framework.
    * Implement the Orchestrator service, adhering to the specified workflow and SOLID principles.
    * Develop the individual agent classes (Analyst, Architect, etc.) as AutoGen agents.
    * Implement the Context Store Pattern with a service layer that manages data access, abstracting the database details from the agents.
3. **Phase 3: Frontend Integration (React)**
    * Set up a Next.js project with Zustand for state management and Tailwind CSS for styling.
    * Build a WebSocket client to connect to the backend and handle real-time events.
    * Develop the main chat interface and UI components for displaying agent status and the workflow.
    * Create the HITL interface component that renders based on incoming WebSocket events and posts responses back to the REST API, now with explicit support for an `amend` action.
4. **Phase 4: Refinement & Testing**
    * Implement JSONL logging and ensure a full audit trail, including tracking `amended` requests.
    * Conduct end-to-end testing to ensure the entire workflow, including the new HITL amendment process, functions as designed.
    * Perform performance and security testing.

***

### **6. System Health Checks (First Pass)**

For the initial pass, we will implement a dedicated health endpoint to confirm that the key system components are online and communicating correctly. This will provide a clear, machine-readable status of the system's health.

* **Endpoint**: A simple `GET` endpoint at `/healthz` will return a JSON response with a status for each core component.

* **Health Checks**: The endpoint will perform the following checks:
  * **Backend Status**: A simple check to ensure the FastAPI service is running.
  * **LLM Connection Status**: A check to ensure the LLM provider's API is reachable and authorized.
  * **Task Queue Status**: A check to ensure the Redis broker and at least one Celery worker are online and available.
  * **Database Status**: A check to confirm connectivity to the PostgreSQL database.

* **Response**: The endpoint will return a 200 OK status code if all components are healthy, and a 503 Service Unavailable status code if any component is down. The JSON body will provide details on which components are healthy or unhealthy.

This simple API endpoint serves as both a human-readable status page and a robust health check for automated monitoring systems. We can expand upon it with more detailed metrics and alerting in future development phases.
