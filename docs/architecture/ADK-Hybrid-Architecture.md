# BMad ADK Hybrid Fullstack Architecture

## Executive Summary

This document defines the complete hybrid architecture for BMad, strategically combining **Google ADK's agent framework** with **BMad's enterprise capabilities**. This approach leverages ADK's production-ready LlmAgent implementations while preserving BMad's critical enterprise features that have no ADK equivalent: HITL systems, immutable audit trails, and real-time WebSocket integration.

**Key Innovation**: The world's first enterprise-grade AI development platform combining Google's agent excellence with comprehensive human oversight and real-time frontend capabilities.

## Introduction

### Architecture Decision: Selective ADK Adoption

Based on the comprehensive ADK Framework Analysis, we implement a **hybrid approach**:

**✅ ADOPT ADK FOR:**
- Core agent implementation (LlmAgent replaces BaseAgent)
- Multi-model orchestration and tool ecosystem
- Agent-to-agent communication via Session State
- Development and testing tooling

**✅ PRESERVE BMAD FOR:**
- Human-in-the-Loop (HITL) system ⭐ (no ADK equivalent)
- Immutable audit trails ⭐ (ADK only has basic logging)
- Real-time WebSocket service ⭐ (ADK has no client-facing capabilities)
- Context store persistence ⭐ (ADK Session State is ephemeral)
- Project lifecycle management ⭐ (SDLC workflow orchestration)

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-09-15 | 1.0 | Initial ADK+BMad hybrid architecture | Winston (Architect) |

## High Level Architecture

### Technical Summary

BMad implements a **revolutionary hybrid agent architecture** that strategically combines:

1. **ADK Agent Core**: Production-ready LlmAgent implementations for all specialized agents (Analyst, Architect, Coder, Tester, Deployer)
2. **ADK Context Management**: Session State for ephemeral agent coordination, Memory Service for RAG retrieval, Artifacts for file handling
3. **BMad Enterprise Layer**: HITL oversight, immutable audit trails, real-time WebSocket communication, persistent context management
4. **Dual Orchestration**: ADK handles agent conversations while BMad orchestrates HITL integration and project lifecycle

This creates an enterprise-grade platform where Google's agent reliability meets comprehensive human governance.

### Platform and Infrastructure Choice

**Platform**: Google Cloud Platform (optimized for ADK integration) with Vercel Frontend
**Key Services**:
- **Compute**: Cloud Run (ADK agents + BMad services), Vercel Functions (frontend API)
- **ADK Services**: Vertex AI (multi-LLM), ADK Memory Service (RAG), ADK Artifact Service (file storage)
- **BMad Services**: Cloud SQL (audit/HITL), Redis (WebSocket + Session State), Cloud Storage (persistent artifacts)
- **Integration Layer**: Custom ADK-BMad bridge services for seamless interop

**Deployment Regions**: us-central1 (primary), global CDN via Vercel

### Repository Structure

**Structure**: Hybrid Monorepo optimized for ADK integration
**Monorepo Tool**: npm workspaces with ADK CLI integration
**Package Organization**:
```
bmad-hybrid/
├── apps/
│   ├── backend/           # BMad enterprise services
│   ├── frontend/          # Task 7 real-time UI
│   └── adk-bridge/        # ADK-BMad integration layer
├── packages/
│   ├── adk-agents/        # ADK LlmAgent implementations
│   ├── bmad-core/         # Enterprise HITL, audit, WebSocket
│   ├── shared/            # TypeScript interfaces
│   └── adk-config/        # ADK configuration and setup
└── infrastructure/        # GCP deployment configs
```

### High Level Architecture Diagram

```mermaid
graph TB
    User[User] --> Frontend[Task 7 Frontend<br/>Next.js + Vercel]
    Frontend --> WebSocket[BMad WebSocket Service<br/>Real-time Updates]
    Frontend --> API[BMad Enterprise API<br/>FastAPI + HITL]

    API --> HITL[HITL Service<br/>Human Oversight ⭐]
    API --> Audit[Audit Trail Service<br/>Immutable Logging ⭐]
    API --> Bridge[ADK-BMad Bridge<br/>Integration Layer]

    Bridge --> ADKCore[ADK Agent Framework]
    ADKCore --> Analyst[Analyst Agent<br/>ADK LlmAgent]
    ADKCore --> Architect[Architect Agent<br/>ADK LlmAgent]
    ADKCore --> Coder[Coder Agent<br/>ADK LlmAgent]
    ADKCore --> Tester[Tester Agent<br/>ADK LlmAgent]
    ADKCore --> Deployer[Deployer Agent<br/>ADK LlmAgent]

    ADKCore --> SessionState[ADK Session State<br/>Agent Coordination]
    ADKCore --> Memory[ADK Memory Service<br/>RAG + History]
    ADKCore --> Artifacts[ADK Artifact Service<br/>File Management]

    Bridge --> Context[BMad Context Store<br/>Persistent JSONB ⭐]
    API --> Database[(Cloud SQL PostgreSQL<br/>Audit + HITL)]
    WebSocket --> Redis[(Redis<br/>Real-time State)]

    Analyst --> VertexAI[Vertex AI<br/>Multi-LLM Provider]
    Architect --> VertexAI
    Coder --> VertexAI
    Tester --> VertexAI
    Deployer --> VertexAI
```

### Architectural Patterns

- **Hybrid Agent Framework**: ADK LlmAgent + BMad enterprise wrapper
  - _Rationale_: Production-ready agents with enterprise governance
- **Dual Context Strategy**: ADK Session State + BMad persistent store
  - _Rationale_: Ephemeral coordination + long-term project data
- **Enterprise-First HITL**: BMad HITL integration with ADK agent workflows
  - _Rationale_: No ADK equivalent for human oversight capabilities
- **Bridge Pattern**: Custom integration layer between ADK and BMad
  - _Rationale_: Seamless interoperability without architectural compromises
- **Real-time Hybrid**: ADK internal events + BMad client-facing WebSocket
  - _Rationale_: ADK lacks client-facing real-time capabilities for Task 7

## Tech Stack

### Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Agent Framework** | **Google ADK** | **Latest** | **Core AI agent implementation** | **Production-ready LlmAgent, tool ecosystem, multi-model native** |
| **Enterprise Layer** | **BMad Services** | **Custom** | **HITL, audit, real-time** | **No ADK equivalent for enterprise features** |
| Frontend Language | TypeScript | 5.3+ | Type-safe development | ADK + BMad shared type definitions |
| Frontend Framework | Next.js | 14.2+ | React SSR/SSG | Vercel optimization, ADK integration ready |
| UI Components | shadcn/ui | Latest | Design system | Consistent with existing BMad patterns |
| State Management | Zustand | 4.5+ | Client state | Real-time WebSocket + ADK agent state |
| Backend Language | Python | 3.11+ | Agent + API development | ADK native support, existing BMad codebase |
| Backend Framework | FastAPI | 0.104+ | Enterprise API | BMad services, HITL integration |
| **ADK Integration** | **ADK Python SDK** | **Latest** | **Agent framework integration** | **Native ADK LlmAgent implementation** |
| API Style | REST + WebSocket | - | Standard + real-time | REST for ADK, WebSocket for real-time |
| **Agent Context** | **ADK Session State** | **-** | **Agent-to-agent coordination** | **Ephemeral state for ADK agent communication** |
| **Agent Memory** | **ADK Memory Service** | **-** | **RAG and agent history** | **Built-in searchable memory and retrieval** |
| **Agent Artifacts** | **ADK Artifact Service** | **-** | **File and blob management** | **Native ADK file handling capabilities** |
| Database | PostgreSQL | 15+ | Enterprise data | HITL, audit trails, project lifecycle |
| Cache | Redis | 7+ | Multi-purpose | Session State storage, WebSocket, real-time |
| **Persistent Context** | **BMad Context Store** | **-** | **Long-term project data** | **JSONB artifacts, project lifecycle (ADK is ephemeral)** |
| **Human Oversight** | **BMad HITL Service** | **-** | **Enterprise governance** | **No ADK equivalent for human approval workflows** |
| **Compliance** | **BMad Audit Service** | **-** | **Immutable audit trails** | **ADK only has basic logging, no compliance features** |
| **Real-time UI** | **BMad WebSocket Service** | **-** | **Task 7 frontend integration** | **ADK has no client-facing real-time capabilities** |
| Authentication | Google Cloud Identity | - | User auth + ADK integration | Seamless ADK ecosystem alignment |
| **LLM Providers** | **Vertex AI (via ADK)** | **-** | **Multi-model orchestration** | **ADK native multi-LLM support** |
| File Storage | Google Cloud Storage | - | Persistent storage | ADK Artifact Service integration |
| Frontend Testing | Vitest + Testing Library | Latest | Component testing | Modern testing with ADK agent mocking |
| **Agent Testing** | **ADK Evaluation System** | **-** | **Agent performance testing** | **Built-in agent evaluation framework** |
| Backend Testing | pytest + pytest-asyncio | Latest | API and integration | ADK agent integration testing |
| E2E Testing | Playwright | Latest | Full-stack testing | ADK + BMad + WebSocket integration |
| **Tool Ecosystem** | **ADK Tools + Google Cloud** | **-** | **Agent capabilities** | **Rich tool library vs custom development** |
| **Development UI** | **ADK Dev Interface** | **-** | **Agent development and testing** | **Built-in development tooling** |
| Monitoring | Google Cloud Monitoring | - | Infrastructure | Native GCP + ADK observability |
| **Agent Observability** | **ADK + Arize Integration** | **-** | **Agent performance monitoring** | **Professional ML observability** |
| IaC | Google Cloud Deploy | - | Infrastructure as Code | ADK-optimized deployment |
| CI/CD | GitHub Actions + Cloud Build | - | Build and deployment | ADK CLI integration |

## ADK Context Management Integration

### Session State Architecture

**Purpose**: Ephemeral agent-to-agent coordination using ADK's built-in Session State

**Implementation**:
```python
# ADK Session State for agent coordination
class ADKSessionManager:
    def __init__(self, session_service: SessionService):
        self.session_service = session_service

    async def set_agent_context(self, session_id: str, agent_type: str, context_data: Dict):
        """Store ephemeral context for agent handoffs"""
        session = await self.session_service.get_session(session_id)
        session.state[f"agent_{agent_type}_context"] = context_data

    async def get_handoff_context(self, session_id: str, from_agent: str, to_agent: str):
        """Retrieve context for agent handoffs"""
        session = await self.session_service.get_session(session_id)
        return session.state.get(f"handoff_{from_agent}_to_{to_agent}")
```

**Key Features**:
- **Agent Coordination**: Pass task results between ADK agents
- **Ephemeral Storage**: Session-scoped data that doesn't need persistence
- **Performance Optimized**: In-memory storage for fast agent communication
- **ADK Native**: Leverages built-in Session State capabilities

### Memory Service Integration

**Purpose**: Long-term agent memory and RAG capabilities using ADK Memory Service

**Implementation**:
```python
class ADKMemoryIntegration:
    def __init__(self, memory_service: BaseMemoryService):
        self.memory_service = memory_service

    async def store_agent_learning(self, agent_type: str, experience: str, metadata: Dict):
        """Store agent experiences for future retrieval"""
        await self.memory_service.add_memory(
            content=experience,
            metadata={
                "agent_type": agent_type,
                "timestamp": datetime.utcnow(),
                **metadata
            }
        )

    async def search_relevant_experience(self, agent_type: str, query: str) -> List[str]:
        """RAG-style retrieval of relevant agent experiences"""
        memories = await self.memory_service.search_memory(
            query=query,
            filters={"agent_type": agent_type}
        )
        return [memory.content for memory in memories]
```

**Key Features**:
- **RAG Integration**: Searchable agent experience and knowledge
- **Cross-Session Memory**: Persistent learning across project sessions
- **Agent-Specific**: Memory partitioned by agent type and project
- **Built-in Search**: ADK's native memory search capabilities

### Artifact Service Integration

**Purpose**: File and blob management using ADK Artifact Service

**Implementation**:
```python
class ADKArtifactManager:
    def __init__(self, artifact_service: ArtifactService):
        self.artifact_service = artifact_service

    async def store_agent_output(self, agent_type: str, content: bytes, metadata: Dict):
        """Store agent-generated files and artifacts"""
        artifact_id = await self.artifact_service.create_artifact(
            data=content,
            metadata={
                "source_agent": agent_type,
                "created_at": datetime.utcnow(),
                **metadata
            }
        )
        return artifact_id

    async def retrieve_project_artifacts(self, project_id: str) -> List[Artifact]:
        """Get all artifacts for a project"""
        return await self.artifact_service.list_artifacts(
            filters={"project_id": project_id}
        )
```

**Key Features**:
- **File Management**: Handle code, docs, images, and other agent outputs
- **Version Control**: Built-in artifact versioning and history
- **Cloud Storage**: Integrated with Google Cloud Storage
- **Metadata Rich**: Searchable artifact metadata and tagging

## BMad Enterprise Services (Preserved)

### HITL System Architecture

**Why Preserved**: ADK has no equivalent for human oversight and approval workflows

**Enhanced Integration**:
```python
class HitlADKIntegration:
    def __init__(self, hitl_service: HitlService, adk_bridge: ADKBridge):
        self.hitl_service = hitl_service
        self.adk_bridge = adk_bridge

    async def pause_adk_agent_for_approval(self, agent_type: str, task_data: Dict):
        """Pause ADK agent execution for human approval"""
        # Create HITL request with agent context
        request = await self.hitl_service.create_approval_request(
            agent_type=agent_type,
            task_data=task_data,
            context_artifacts=await self._get_relevant_context(task_data)
        )

        # Pause ADK agent execution
        await self.adk_bridge.pause_agent_execution(agent_type, request.request_id)

        return request

    async def resume_adk_agent(self, request_id: str, approval_result: Dict):
        """Resume ADK agent with human feedback"""
        # Process approval result
        agent_type = await self._get_agent_from_request(request_id)

        # Resume ADK agent with human input
        await self.adk_bridge.resume_agent_execution(
            agent_type,
            request_id,
            approval_result
        )
```

### Audit Trail System

**Why Preserved**: ADK only provides basic logging, not enterprise-grade audit trails

**ADK Event Integration**:
```python
class AuditADKIntegration:
    async def log_adk_agent_event(self, agent_type: str, event_type: str, payload: Dict):
        """Log ADK agent events to immutable audit trail"""
        await self.audit_service.log_event(
            event_type=f"adk_agent_{event_type}",
            agent_type=agent_type,
            payload={
                "adk_session_id": payload.get("session_id"),
                "adk_memory_id": payload.get("memory_id"),
                "adk_artifact_ids": payload.get("artifact_ids"),
                **payload
            },
            metadata={
                "adk_integration_version": "1.0",
                "compliance_required": True,
                "immutable": True
            }
        )
```

### Real-time WebSocket Service

**Why Preserved**: ADK has no client-facing real-time capabilities for Task 7

**ADK Event Bridge**:
```python
class WebSocketADKBridge:
    async def broadcast_adk_agent_status(self, agent_type: str, status_data: Dict):
        """Broadcast ADK agent status to frontend clients"""
        await self.websocket_manager.broadcast_event({
            "event_type": "adk_agent_status_changed",
            "agent_type": agent_type,
            "data": {
                "adk_session_id": status_data.get("session_id"),
                "status": status_data.get("status"),
                "current_memory": status_data.get("memory_context"),
                "artifacts_created": status_data.get("new_artifacts", []),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
```

## ADK-BMad Bridge Architecture

### Integration Layer Design

**Purpose**: Seamless interoperability between ADK agent framework and BMad enterprise services

```python
class ADKBmadBridge:
    """Central integration layer between ADK and BMad systems"""

    def __init__(self):
        self.adk_session_manager = ADKSessionManager()
        self.bmad_context_store = BmadContextStore()
        self.hitl_integration = HitlADKIntegration()
        self.audit_integration = AuditADKIntegration()
        self.websocket_bridge = WebSocketADKBridge()

    async def execute_adk_agent_with_bmad_oversight(
        self,
        agent_type: str,
        task_data: Dict,
        hitl_required: bool = True
    ):
        """Execute ADK agent with full BMad enterprise integration"""

        # 1. Initialize ADK session with BMad context
        session_id = await self._create_hybrid_session(task_data)

        # 2. Load relevant context from BMad persistent store
        context = await self.bmad_context_store.get_project_context(
            task_data["project_id"]
        )
        await self.adk_session_manager.set_agent_context(
            session_id, agent_type, context
        )

        # 3. Create HITL checkpoint if required
        if hitl_required:
            await self.hitl_integration.pause_adk_agent_for_approval(
                agent_type, task_data
            )

        # 4. Execute ADK agent
        result = await self._execute_adk_agent(agent_type, session_id, task_data)

        # 5. Persist results to BMad context store
        await self.bmad_context_store.store_agent_result(
            agent_type, result, task_data["project_id"]
        )

        # 6. Log to immutable audit trail
        await self.audit_integration.log_adk_agent_event(
            agent_type, "task_completed", result
        )

        # 7. Broadcast real-time updates
        await self.websocket_bridge.broadcast_adk_agent_status(
            agent_type, {"status": "completed", "result": result}
        )

        return result
```

## Data Models and Interfaces

### Hybrid Context Model

```typescript
interface HybridContext {
  // ADK Session State (ephemeral)
  adkSessionId: string;
  sessionState: {
    agentCoordination: Record<string, any>;
    currentHandoffs: HandoffData[];
    temporaryData: Record<string, any>;
  };

  // ADK Memory Service (searchable)
  memoryContext: {
    relevantExperiences: Memory[];
    agentLearnings: AgentLearning[];
    ragResults: RAGResult[];
  };

  // ADK Artifacts (file management)
  adkArtifacts: {
    generatedFiles: ADKArtifact[];
    processedDocuments: ADKArtifact[];
    codeOutputs: ADKArtifact[];
  };

  // BMad Context Store (persistent)
  bmadContext: {
    projectLifecycle: ProjectContext;
    auditTrail: AuditEvent[];
    hitlHistory: HITLRequest[];
    persistentArtifacts: ContextArtifact[];
  };
}
```

### ADK Agent Configuration

```python
# ADK LlmAgent Implementation for BMad
class BmadAnalystAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="bmad_analyst",
            model="gemini-2.0-flash-exp",  # ADK multi-model support
            instruction="""You are the Analyst agent in the BMad system.
            You analyze requirements and create detailed PRDs.

            BMad Integration Notes:
            - Use ctx.session.state for agent coordination
            - Store experiences in memory service for learning
            - Create artifacts for generated documents
            - Expect HITL approval at major milestones
            """,
            tools=[
                requirements_analysis_tool,
                user_story_generation_tool,
                prd_creation_tool
            ],
            sub_agents=[],  # No sub-agents for specialist roles
        )

    async def execute_bmad_task(self, task_data: Dict, ctx: InvocationContext):
        """Execute task with BMad integration"""
        # Get context from BMad persistent store via bridge
        bmad_context = await self._get_bmad_context(task_data["project_id"])

        # Use ADK session state for coordination
        ctx.session.state["current_task"] = task_data
        ctx.session.state["bmad_project_context"] = bmad_context

        # Execute analysis using ADK capabilities
        result = await self.run_async(
            message=task_data["instructions"],
            ctx=ctx
        )

        # Store result in ADK Memory Service for future retrieval
        await ctx.deps.memory_service.add_memory(
            content=result,
            metadata={
                "agent_type": "analyst",
                "project_id": task_data["project_id"],
                "task_type": "requirements_analysis"
            }
        )

        # Create artifacts for generated documents
        if result.get("prd_document"):
            await ctx.deps.artifact_service.create_artifact(
                data=result["prd_document"].encode(),
                metadata={
                    "type": "prd",
                    "agent": "analyst",
                    "project_id": task_data["project_id"]
                }
            )

        return result
```

## API Specifications

### Hybrid API Endpoints

```python
# ADK + BMad integrated endpoints
@app.post("/api/v1/adk/agents/{agent_type}/execute")
async def execute_adk_agent_with_bmad(
    agent_type: str,
    task_data: ADKTaskRequest,
    hitl_required: bool = True,
    db: Session = Depends(get_db)
):
    """Execute ADK agent with full BMad enterprise integration"""
    bridge = ADKBmadBridge()
    result = await bridge.execute_adk_agent_with_bmad_oversight(
        agent_type, task_data.dict(), hitl_required
    )
    return {"success": True, "result": result}

@app.get("/api/v1/adk/context/{project_id}")
async def get_hybrid_context(
    project_id: str,
    include_session_state: bool = True,
    include_memory: bool = True,
    include_artifacts: bool = True,
    db: Session = Depends(get_db)
):
    """Get complete hybrid context (ADK + BMad)"""
    context = await build_hybrid_context(
        project_id, include_session_state, include_memory, include_artifacts
    )
    return context

@app.post("/api/v1/adk/memory/search")
async def search_adk_memory(
    query: str,
    agent_type: Optional[str] = None,
    project_id: Optional[str] = None
):
    """Search ADK Memory Service with BMad context"""
    memory_service = get_adk_memory_service()
    results = await memory_service.search_memory(
        query=query,
        filters={
            "agent_type": agent_type,
            "project_id": project_id
        } if agent_type or project_id else {}
    )
    return {"results": results}
```

## Components Architecture

### ADK Agent Components

**Analyst Agent (ADK LlmAgent)**
- **Responsibility**: Requirements analysis and PRD generation with ADK reliability
- **Key Interfaces**: ADK Memory Service for learning, BMad Context Store for persistence
- **Dependencies**: Vertex AI (multi-LLM), ADK tools ecosystem, BMad HITL integration
- **Technology**: ADK LlmAgent with Gemini optimization, Python integration layer

**Architect Agent (ADK LlmAgent)**
- **Responsibility**: Technical architecture design using ADK tool ecosystem
- **Key Interfaces**: ADK Session State for agent coordination, ADK Artifact Service for diagrams
- **Dependencies**: ADK tools (Google Cloud, OpenAPI), BMad audit trail, HITL approvals
- **Technology**: ADK LlmAgent with GPT-4 optimization, Google Cloud tools integration

**Coder Agent (ADK LlmAgent)**
- **Responsibility**: Code generation with ADK's advanced capabilities
- **Key Interfaces**: ADK Artifact Service for code storage, Memory Service for pattern learning
- **Dependencies**: ADK code execution environment, BMad quality gates, HITL reviews
- **Technology**: ADK LlmAgent with code execution, integrated testing capabilities

**Tester Agent (ADK LlmAgent)**
- **Responsibility**: Quality assurance using ADK evaluation framework
- **Key Interfaces**: ADK evaluation tools, BMad audit trail for test results
- **Dependencies**: ADK testing framework, BMad HITL for failure escalation
- **Technology**: ADK LlmAgent with evaluation integration, automated test execution

**Deployer Agent (ADK LlmAgent)**
- **Responsibility**: Deployment automation with Google Cloud integration
- **Key Interfaces**: ADK Google Cloud tools, BMad monitoring integration
- **Dependencies**: Cloud deployment tools, BMad HITL for production approvals
- **Technology**: ADK LlmAgent with Google Cloud native tools

### BMad Enterprise Components (Preserved)

**HITL Service** ⭐
- **Responsibility**: Human oversight and approval workflows (no ADK equivalent)
- **Key Interfaces**: ADK agent pause/resume, WebSocket notifications, audit logging
- **Technology**: FastAPI service with PostgreSQL, WebSocket integration

**Audit Trail Service** ⭐
- **Responsibility**: Immutable compliance logging (ADK only has basic logs)
- **Key Interfaces**: ADK event capture, regulatory reporting, forensic analysis
- **Technology**: PostgreSQL with JSONB, immutable event logging

**WebSocket Service** ⭐
- **Responsibility**: Real-time frontend updates (ADK has no client-facing capabilities)
- **Key Interfaces**: ADK event bridging, Task 7 frontend, mobile notifications
- **Technology**: FastAPI WebSocket with Redis, real-time event streaming

**Context Store Service** ⭐
- **Responsibility**: Persistent project lifecycle data (ADK Session State is ephemeral)
- **Key Interfaces**: ADK Memory Service integration, long-term artifact storage
- **Technology**: PostgreSQL JSONB, structured artifact management

## External APIs and Integrations

### ADK Native Integrations

**Vertex AI Integration**
- **Purpose**: Multi-LLM provider access through ADK
- **Documentation**: Google Cloud Vertex AI REST API
- **Authentication**: Service account with Vertex AI permissions
- **Key Endpoints**: Model serving, fine-tuning, evaluation
- **Integration Notes**: ADK handles provider abstraction and model switching

**Google Cloud Tools via ADK**
- **Purpose**: Native Google Cloud service integration
- **Documentation**: ADK tool ecosystem documentation
- **Authentication**: Google Cloud SDK integration
- **Rate Limits**: Standard Google Cloud API limits
- **Integration Notes**: ADK provides pre-built tools vs custom development

**ADK Memory Service**
- **Purpose**: RAG and agent learning capabilities
- **Documentation**: ADK Memory Service API
- **Authentication**: ADK framework integration
- **Key Endpoints**: Memory storage, search, retrieval
- **Integration Notes**: Built-in vector search and semantic retrieval

### BMad External APIs (Preserved)

**Task 7 Frontend Integration**
- **Purpose**: Real-time UI updates and user interaction
- **Base URL**: WebSocket connection to BMad service
- **Authentication**: Session-based with Google Cloud Identity
- **Integration Notes**: ADK events bridged to WebSocket for real-time updates

## Core Workflows

### Hybrid Agent Execution Workflow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant BMadAPI
    participant Bridge
    participant ADKAgent
    participant VertexAI
    participant BMadHITL
    participant BMadAudit

    User->>Frontend: Submit task request
    Frontend->>BMadAPI: POST /api/v1/adk/agents/analyst/execute
    BMadAPI->>Bridge: execute_adk_agent_with_bmad_oversight()

    Note over Bridge: Initialize hybrid session
    Bridge->>ADKAgent: Create session with BMad context
    Bridge->>BMadHITL: Create HITL approval request

    BMadHITL-->>Frontend: WebSocket: HITL request created
    Frontend-->>User: Show approval interface
    User->>Frontend: Approve task execution
    Frontend->>BMadAPI: POST /api/v1/hitl/{request_id}/approve

    BMadAPI->>Bridge: Resume ADK agent execution
    Bridge->>ADKAgent: Execute with task data
    ADKAgent->>VertexAI: LLM API call (via ADK)
    VertexAI-->>ADKAgent: LLM response

    ADKAgent->>ADKAgent: Store result in Memory Service
    ADKAgent->>ADKAgent: Create artifacts for outputs
    ADKAgent-->>Bridge: Return execution result

    Bridge->>BMadAudit: Log execution to immutable trail
    Bridge-->>Frontend: WebSocket: Agent completed
    Bridge-->>BMadAPI: Return success response
    BMadAPI-->>Frontend: HTTP response
    Frontend-->>User: Show completion
```

### ADK Context Flow Diagram

```mermaid
sequenceDiagram
    participant Analyst as Analyst Agent (ADK)
    participant Session as ADK Session State
    participant Memory as ADK Memory Service
    participant Artifacts as ADK Artifacts
    participant Bridge as ADK-BMad Bridge
    participant BMadStore as BMad Context Store

    Note over Analyst: Task execution begins

    Analyst->>Session: ctx.session.state["current_analysis"] = data
    Analyst->>Memory: Store learning experience
    Analyst->>Artifacts: Create PRD document artifact

    Note over Analyst: Hand off to Architect

    Analyst->>Session: ctx.session.state["handoff_to_architect"] = context
    Bridge->>BMadStore: Persist milestone to long-term storage
    Bridge->>Session: Get handoff context

    Note over Bridge: Initialize Architect with context

    Session-->>Bridge: Return handoff data
    BMadStore-->>Bridge: Return project history
    Bridge->>Architect: Initialize with hybrid context

    Architect->>Memory: Search for relevant architecture patterns
    Memory-->>Architect: Return similar project experiences
    Architect->>Session: Update session with architecture decisions
    Architect->>Artifacts: Create architecture diagrams
```

## Database Schema

### Hybrid Data Architecture

**ADK Data (Managed by ADK Services)**:
```python
# ADK Session State (Redis-backed)
{
  "session_id": "uuid",
  "state": {
    "agent_coordination": {},
    "current_handoffs": [],
    "temporary_data": {}
  },
  "ttl": 3600  # 1 hour session timeout
}

# ADK Memory Service (Vector store)
{
  "memory_id": "uuid",
  "content": "text",
  "embedding": [float],  # Vector embedding
  "metadata": {
    "agent_type": "string",
    "project_id": "uuid",
    "timestamp": "datetime"
  }
}

# ADK Artifacts (Cloud Storage)
{
  "artifact_id": "uuid",
  "data": bytes,
  "metadata": {
    "type": "string",
    "agent": "string",
    "project_id": "uuid",
    "created_at": "datetime"
  }
}
```

**BMad Data (PostgreSQL)**:
```sql
-- Existing BMad schema preserved
-- HITL System Tables
CREATE TABLE hitl_requests (
    request_id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    -- ADK integration fields
    adk_session_id VARCHAR(255),
    adk_memory_ids TEXT[],
    adk_artifact_ids TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Trail Tables
CREATE TABLE audit_events (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50),
    payload JSONB NOT NULL,
    -- ADK event metadata
    adk_session_id VARCHAR(255),
    adk_integration_version VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Context Store (Long-term persistence)
CREATE TABLE context_artifacts (
    context_id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    source_agent VARCHAR(50) NOT NULL,
    artifact_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    -- ADK artifact references
    adk_artifact_ids TEXT[],
    adk_memory_references TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Frontend Architecture

### Component Architecture with ADK Integration

**Component Organization**:
```
src/
├── components/
│   ├── agents/
│   │   ├── ADKAgentStatus.tsx        # ADK agent status display
│   │   ├── ADKSessionViewer.tsx      # Session state visualization
│   │   ├── ADKMemoryBrowser.tsx      # Memory service search interface
│   │   └── ADKArtifactViewer.tsx     # Artifact management UI
│   ├── hitl/
│   │   ├── HITLApprovalCard.tsx      # Enhanced with ADK context
│   │   └── ADKAgentPauseDialog.tsx   # ADK agent pause interface
│   └── realtime/
│       ├── ADKEventStream.tsx        # ADK event visualization
│       └── HybridStatusDashboard.tsx # Combined ADK + BMad status
├── hooks/
│   ├── useADKAgentStatus.ts          # ADK agent state management
│   ├── useHybridContext.ts           # Combined ADK + BMad context
│   └── useADKWebSocketBridge.ts      # ADK event bridging
└── services/
    ├── adkApiClient.ts               # ADK API integration
    ├── hybridContextService.ts       # Context unification service
    └── adkWebSocketBridge.ts         # Real-time event bridging
```

**ADK Agent Status Component**:
```typescript
export function ADKAgentStatus({ agentType }: { agentType: string }) {
  const { status, sessionId, currentTask, memoryCount, artifactCount } = useADKAgentStatus(agentType);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{agentType} Agent (ADK)</CardTitle>
        <Badge variant={status === 'working' ? 'default' : 'secondary'}>
          {status}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div>Session: {sessionId?.slice(0, 8)}...</div>
          <div>Current Task: {currentTask?.slice(0, 40)}...</div>
          <div>Memories: {memoryCount}</div>
          <div>Artifacts: {artifactCount}</div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### State Management Architecture

**Hybrid State Structure**:
```typescript
interface HybridApplicationState {
  // ADK Agent State
  adkAgents: {
    [agentType: string]: {
      status: 'idle' | 'working' | 'paused' | 'error';
      sessionId?: string;
      currentTask?: string;
      memoryContext: Memory[];
      artifacts: ADKArtifact[];
    };
  };

  // ADK Session State (read-only view)
  adkSessions: {
    [sessionId: string]: {
      agentCoordination: Record<string, any>;
      handoffs: HandoffData[];
      temporaryData: Record<string, any>;
    };
  };

  // BMad Enterprise State (preserved)
  bmadState: {
    hitlRequests: HITLRequest[];
    auditEvents: AuditEvent[];
    webSocketConnected: boolean;
    projectContext: ProjectContext;
  };

  // Hybrid Integration State
  hybridIntegration: {
    bridgeStatus: 'connected' | 'disconnected' | 'error';
    lastSync: string;
    pendingHITLForADK: string[];
  };
}
```

### Real-time Frontend Integration

**WebSocket Event Handling**:
```typescript
class ADKWebSocketBridge {
  private websocket: WebSocket;
  private adkEventHandlers: Map<string, (event: ADKEvent) => void> = new Map();

  constructor(private store: HybridStore) {
    this.websocket = new WebSocket('/ws/adk-bridge');
    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.event_type) {
        case 'adk_agent_status_changed':
          this.store.updateADKAgentStatus(data.agent_type, data.data);
          break;

        case 'adk_session_updated':
          this.store.updateADKSession(data.session_id, data.data);
          break;

        case 'adk_memory_created':
          this.store.addADKMemory(data.agent_type, data.data);
          break;

        case 'adk_artifact_generated':
          this.store.addADKArtifact(data.agent_type, data.data);
          break;

        case 'adk_hitl_pause_requested':
          this.store.createADKHITLRequest(data.data);
          break;
      }
    };
  }

  public subscribeToADKEvents(agentType: string, handler: (event: ADKEvent) => void) {
    this.adkEventHandlers.set(agentType, handler);
  }
}
```

## Backend Architecture

### ADK Integration Service Architecture

**Service Organization**:
```
backend/
├── services/
│   ├── adk_integration/
│   │   ├── adk_agent_service.py      # ADK agent lifecycle management
│   │   ├── adk_session_manager.py    # Session State coordination
│   │   ├── adk_memory_service.py     # Memory Service integration
│   │   └── adk_artifact_manager.py   # Artifact Service integration
│   ├── bmad_enterprise/
│   │   ├── hitl_service.py           # HITL system (preserved)
│   │   ├── audit_service.py          # Audit trails (preserved)
│   │   ├── websocket_service.py      # Real-time (preserved)
│   │   └── context_store_service.py  # Context persistence (preserved)
│   └── integration/
│       ├── adk_bmad_bridge.py        # Central integration layer
│       ├── hybrid_context_service.py # Context unification
│       └── event_bridge_service.py   # Event routing ADK->BMad
└── models/
    ├── adk_models.py                 # ADK data models
    ├── hybrid_models.py              # Integration models
    └── bmad_models.py                # BMad models (preserved)
```

### ADK Agent Service Implementation

```python
class ADKAgentService:
    """Manages ADK LlmAgent instances with BMad integration"""

    def __init__(self):
        self.agents: Dict[str, LlmAgent] = {}
        self.bmad_bridge = ADKBmadBridge()
        self.session_manager = ADKSessionManager()

    async def initialize_agent(self, agent_type: str, project_id: str) -> LlmAgent:
        """Initialize ADK agent with BMad context"""

        # Load BMad project context
        bmad_context = await self.bmad_bridge.get_project_context(project_id)

        # Create ADK session with BMad data
        session = await self.session_manager.create_session(
            initial_state={
                "project_id": project_id,
                "bmad_context": bmad_context,
                "agent_type": agent_type
            }
        )

        # Initialize ADK agent based on type
        agent_config = self._get_agent_config(agent_type)
        agent = LlmAgent(
            name=f"bmad_{agent_type}",
            model=agent_config["model"],
            instruction=agent_config["instruction"],
            tools=agent_config["tools"],
            session_service=self.session_manager.session_service,
            memory_service=self.session_manager.memory_service,
            artifact_service=self.session_manager.artifact_service
        )

        self.agents[f"{project_id}_{agent_type}"] = agent
        return agent

    async def execute_agent_task(
        self,
        agent_type: str,
        project_id: str,
        task_data: Dict,
        hitl_required: bool = True
    ) -> Dict[str, Any]:
        """Execute ADK agent task with full BMad integration"""

        agent_key = f"{project_id}_{agent_type}"

        if agent_key not in self.agents:
            await self.initialize_agent(agent_type, project_id)

        agent = self.agents[agent_key]

        # Create InvocationContext with BMad integration
        context = InvocationContext(
            session=await self.session_manager.get_session(project_id),
            deps=self.session_manager.get_dependencies()
        )

        # HITL checkpoint if required
        if hitl_required:
            await self.bmad_bridge.create_hitl_checkpoint(
                agent_type, task_data, context
            )

        # Execute ADK agent
        result = await agent.run_async(
            message=task_data["instructions"],
            ctx=context
        )

        # Post-execution BMad integration
        await self.bmad_bridge.process_agent_result(
            agent_type, result, task_data, context
        )

        return result
```

### Authentication and Authorization Architecture

**Google Cloud Identity Integration**:
```python
class HybridAuthService:
    """Authentication service supporting both ADK and BMad requirements"""

    async def authenticate_user(self, token: str) -> User:
        """Authenticate user for both ADK and BMad access"""

        # Validate Google Cloud Identity token
        user_info = await self.validate_gcp_token(token)

        # Check ADK permissions
        adk_permissions = await self.get_adk_permissions(user_info["email"])

        # Check BMad HITL permissions
        hitl_permissions = await self.get_hitl_permissions(user_info["email"])

        return User(
            email=user_info["email"],
            adk_permissions=adk_permissions,
            hitl_permissions=hitl_permissions,
            audit_access=user_info.get("audit_access", False)
        )

    async def authorize_adk_agent_action(
        self,
        user: User,
        action: str,
        agent_type: str
    ) -> bool:
        """Authorize ADK agent actions with BMad oversight"""

        # Check base ADK permissions
        if not user.adk_permissions.get(agent_type):
            return False

        # Check HITL bypass permissions for critical actions
        if action in ["deploy", "delete", "modify_production"]:
            return user.hitl_permissions.get("critical_override", False)

        return True
```

## Unified Project Structure

### Monorepo Architecture

```
bmad-adk-hybrid/
├── .github/
│   └── workflows/
│       ├── adk-ci.yaml               # ADK agent testing
│       ├── bmad-ci.yaml              # BMad enterprise testing
│       └── integration-ci.yaml       # Hybrid integration testing
├── apps/
│   ├── backend/                      # BMad enterprise services
│   │   ├── src/
│   │   │   ├── services/
│   │   │   │   ├── adk_integration/  # ADK service integration
│   │   │   │   ├── bmad_enterprise/  # HITL, audit, websocket
│   │   │   │   └── hybrid/           # Bridge services
│   │   │   ├── models/               # Hybrid data models
│   │   │   ├── api/                  # FastAPI endpoints
│   │   │   └── main.py               # Application entry
│   │   ├── tests/                    # BMad + integration tests
│   │   ├── alembic/                  # Database migrations
│   │   └── requirements.txt          # Python dependencies
│   ├── frontend/                     # Task 7 real-time UI
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── adk/              # ADK-specific UI components
│   │   │   │   ├── bmad/             # BMad UI components (HITL, etc)
│   │   │   │   └── hybrid/           # Integrated hybrid components
│   │   │   ├── hooks/                # React hooks for hybrid state
│   │   │   ├── services/             # API clients and WebSocket
│   │   │   ├── stores/               # Zustand stores for hybrid state
│   │   │   └── pages/                # Next.js pages
│   │   ├── tests/                    # Frontend testing
│   │   └── package.json              # Frontend dependencies
│   └── adk-bridge/                   # ADK integration microservice
│       ├── src/
│       │   ├── adk_setup/            # ADK framework initialization
│       │   ├── agent_configs/        # Agent configuration management
│       │   ├── bmad_integration/     # BMad service integration
│       │   └── bridge_service.py     # Main bridge service
│       ├── tests/                    # Bridge service tests
│       └── requirements.txt          # Bridge dependencies
├── packages/
│   ├── adk-agents/                   # ADK LlmAgent implementations
│   │   ├── src/
│   │   │   ├── agents/
│   │   │   │   ├── analyst.py        # Analyst ADK LlmAgent
│   │   │   │   ├── architect.py      # Architect ADK LlmAgent
│   │   │   │   ├── coder.py          # Coder ADK LlmAgent
│   │   │   │   ├── tester.py         # Tester ADK LlmAgent
│   │   │   │   └── deployer.py       # Deployer ADK LlmAgent
│   │   │   ├── tools/                # Custom ADK tools
│   │   │   └── configs/              # Agent configurations
│   │   └── tests/                    # ADK agent tests
│   ├── shared-types/                 # TypeScript interfaces
│   │   ├── src/
│   │   │   ├── adk-types.ts          # ADK-specific types
│   │   │   ├── bmad-types.ts         # BMad types
│   │   │   ├── hybrid-types.ts       # Integration types
│   │   │   └── index.ts              # Unified exports
│   │   └── package.json
│   ├── bmad-core/                    # Enterprise services (preserved)
│   │   ├── src/
│   │   │   ├── hitl/                 # HITL system
│   │   │   ├── audit/                # Audit trail
│   │   │   ├── websocket/            # Real-time services
│   │   │   └── context/              # Context store
│   │   └── tests/                    # BMad core tests
│   └── adk-config/                   # ADK configuration management
│       ├── src/
│       │   ├── agent_configs/        # YAML agent configurations
│       │   ├── tool_configs/         # ADK tool configurations
│       │   ├── deployment_configs/   # GCP deployment configs
│       │   └── validation/           # Configuration validation
│       └── schemas/                  # Configuration schemas
├── infrastructure/                   # GCP deployment
│   ├── terraform/                    # Infrastructure as code
│   │   ├── adk_services.tf           # ADK-specific resources
│   │   ├── bmad_services.tf          # BMad infrastructure
│   │   └── hybrid_integration.tf     # Integration infrastructure
│   ├── kubernetes/                   # K8s deployment manifests
│   │   ├── adk-bridge/               # ADK bridge service
│   │   ├── bmad-backend/             # BMad enterprise services
│   │   └── monitoring/               # Observability stack
│   └── scripts/                      # Deployment scripts
├── docs/                            # Documentation
│   ├── adk/                         # ADK-specific docs
│   ├── bmad/                        # BMad enterprise docs
│   ├── integration/                 # Hybrid architecture docs
│   └── api/                         # API documentation
├── .env.example                     # Environment template
├── package.json                     # Root workspace config
├── adk.config.yaml                  # ADK framework configuration
├── bmad.config.yaml                 # BMad system configuration
└── README.md                        # Project overview
```

## Development Workflow

### Local Development Setup

**Prerequisites**:
```bash
# Node.js and Python
node >= 18.0.0
python >= 3.11
pip >= 23.0

# Google Cloud SDK (required for ADK)
gcloud CLI >= 400.0.0

# ADK CLI installation
pip install google-adk-cli

# Docker for local services
docker >= 24.0
docker-compose >= 2.0
```

**Initial Setup**:
```bash
# Clone and setup workspace
git clone <repository-url>
cd bmad-adk-hybrid
npm install  # Install all workspace dependencies

# Setup Python virtual environments
python -m venv venv
source venv/bin/activate
pip install -r apps/backend/requirements.txt
pip install -r apps/adk-bridge/requirements.txt
pip install -r packages/adk-agents/requirements.txt

# Initialize ADK framework
adk init --project=bmad-hybrid
adk config set project.id=your-gcp-project

# Setup Google Cloud authentication
gcloud auth application-default login
gcloud config set project your-gcp-project

# Initialize databases
cd apps/backend
alembic upgrade head  # BMad database
redis-server --daemonize yes  # Session state storage

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

**Development Commands**:
```bash
# Start all services (hybrid development)
npm run dev:all

# Start individual components
npm run dev:backend      # BMad enterprise services
npm run dev:frontend     # Task 7 UI with real-time
npm run dev:adk-bridge   # ADK integration service
npm run dev:agents       # ADK agent development UI

# ADK-specific commands
adk run analyst          # Test Analyst agent
adk eval --agent=coder   # Evaluate Coder agent
adk debug session <id>   # Debug ADK session

# BMad-specific commands
npm run test:hitl        # Test HITL system
npm run test:audit       # Test audit trail
npm run test:websocket   # Test real-time services

# Integration testing
npm run test:integration # Full hybrid system tests
npm run test:e2e         # End-to-end workflow tests
```

### Environment Configuration

**Frontend Environment** (`.env.local`):
```bash
# ADK Integration
NEXT_PUBLIC_ADK_BRIDGE_URL=http://localhost:8001
NEXT_PUBLIC_ADK_DEV_UI_URL=http://localhost:8002

# BMad Services
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000/ws

# Authentication
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
NEXT_PUBLIC_AUTH_DOMAIN=your_auth_domain
```

**Backend Environment** (`.env`):
```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/bmad_hybrid
REDIS_URL=redis://localhost:6379/0

# ADK Integration
ADK_PROJECT_ID=your_gcp_project
ADK_SERVICE_ACCOUNT_KEY=path/to/service-account.json
ADK_MEMORY_SERVICE_URL=https://adk-memory.googleapis.com
ADK_ARTIFACT_SERVICE_URL=https://adk-artifacts.googleapis.com

# ADK Session State
ADK_SESSION_REDIS_URL=redis://localhost:6379/1
ADK_SESSION_TTL=3600

# Google Cloud Services
GOOGLE_CLOUD_PROJECT=your_gcp_project
VERTEX_AI_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# LLM Provider Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# BMad Enterprise Configuration
HITL_APPROVAL_TIMEOUT=1800  # 30 minutes
AUDIT_RETENTION_DAYS=365
WEBSOCKET_MAX_CONNECTIONS=1000

# Integration Settings
BRIDGE_SERVICE_URL=http://localhost:8001
ENABLE_ADK_INTEGRATION=true
ADK_BRIDGE_AUTH_TOKEN=your_bridge_token
```

**ADK Bridge Service** (`.env.bridge`):
```bash
# ADK Framework
ADK_CONFIG_FILE=adk.config.yaml
ADK_AGENT_CONFIGS_DIR=packages/adk-agents/src/configs
ADK_TOOLS_DIR=packages/adk-agents/src/tools

# BMad Integration
BMAD_API_URL=http://localhost:8000
BMAD_API_TOKEN=your_bmad_api_token
BMAD_WEBSOCKET_URL=ws://localhost:8000/ws/bridge

# Service Configuration
BRIDGE_PORT=8001
BRIDGE_HOST=0.0.0.0
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

## Deployment Architecture

### Deployment Strategy

**Frontend Deployment**:
- **Platform**: Vercel (optimized for Next.js)
- **Build Command**: `npm run build:frontend`
- **Output Directory**: `apps/frontend/.next`
- **CDN/Edge**: Global Vercel Edge Network with ADK integration
- **Environment**: Separate staging and production with ADK service endpoints

**Backend Deployment**:
- **Platform**: Google Cloud Run (native ADK integration)
- **Build Command**: `docker build -f apps/backend/Dockerfile`
- **Deployment Method**: Container deployment with ADK dependencies
- **Scaling**: Auto-scaling based on ADK agent workload and HITL requests

**ADK Bridge Service**:
- **Platform**: Google Cloud Run (co-located with ADK services)
- **Build Command**: `docker build -f apps/adk-bridge/Dockerfile`
- **Deployment Method**: Microservice deployment with ADK SDK
- **Integration**: Direct ADK framework integration with minimal latency

### CI/CD Pipeline

**GitHub Actions Workflow** (`.github/workflows/hybrid-deploy.yaml`):
```yaml
name: BMad ADK Hybrid Deployment

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

env:
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  ADK_PROJECT_ID: ${{ secrets.ADK_PROJECT_ID }}

jobs:
  test-adk-agents:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      # Setup ADK CLI
      - name: Install ADK CLI
        run: pip install google-adk-cli

      # Test ADK agents
      - name: Test ADK Agents
        run: |
          cd packages/adk-agents
          adk test --all-agents
          adk eval --baseline-comparison

      # Validate ADK configurations
      - name: Validate ADK Configs
        run: |
          adk config validate
          adk tools validate

  test-bmad-enterprise:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      # Test BMad enterprise services
      - name: Test HITL System
        run: |
          cd apps/backend
          pytest tests/integration/test_hitl_integration.py -v

      - name: Test Audit Trail
        run: |
          cd apps/backend
          pytest tests/integration/test_audit_integration.py -v

      - name: Test WebSocket Service
        run: |
          cd apps/backend
          pytest tests/integration/test_websocket_integration.py -v

  test-integration:
    needs: [test-adk-agents, test-bmad-enterprise]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Setup both environments
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      # Install dependencies
      - name: Install Dependencies
        run: |
          npm install
          pip install google-adk-cli
          pip install -r apps/backend/requirements.txt
          pip install -r apps/adk-bridge/requirements.txt

      # Test hybrid integration
      - name: Test ADK-BMad Integration
        run: |
          # Start services
          docker-compose -f docker-compose.test.yml up -d

          # Wait for services
          sleep 30

          # Run integration tests
          pytest tests/integration/test_adk_bmad_bridge.py -v
          pytest tests/integration/test_hybrid_workflows.py -v

          # Cleanup
          docker-compose -f docker-compose.test.yml down

  deploy-staging:
    if: github.ref == 'refs/heads/staging'
    needs: [test-integration]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      # Deploy ADK bridge service
      - name: Deploy ADK Bridge
        run: |
          cd apps/adk-bridge
          gcloud run deploy adk-bridge-staging \
            --source . \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated \
            --set-env-vars="ADK_PROJECT_ID=$ADK_PROJECT_ID"

      # Deploy BMad backend
      - name: Deploy BMad Backend
        run: |
          cd apps/backend
          gcloud run deploy bmad-backend-staging \
            --source . \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated

      # Deploy frontend to Vercel
      - name: Deploy Frontend
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: apps/frontend
          scope: staging

  deploy-production:
    if: github.ref == 'refs/heads/main'
    needs: [test-integration]
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      # Production deployment with additional validations
      - name: Validate Production Readiness
        run: |
          # ADK agent performance benchmarks
          adk benchmark --all-agents --threshold 0.95

          # BMad service health checks
          pytest tests/health/test_production_readiness.py

      # Deploy to production
      - name: Deploy ADK Bridge Production
        run: |
          cd apps/adk-bridge
          gcloud run deploy adk-bridge-prod \
            --source . \
            --platform managed \
            --region us-central1 \
            --cpu 2 \
            --memory 4Gi \
            --max-instances 100 \
            --set-env-vars="ADK_PROJECT_ID=$ADK_PROJECT_ID"

      - name: Deploy BMad Backend Production
        run: |
          cd apps/backend
          gcloud run deploy bmad-backend-prod \
            --source . \
            --platform managed \
            --region us-central1 \
            --cpu 2 \
            --memory 8Gi \
            --max-instances 50

      - name: Deploy Frontend Production
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: apps/frontend
          vercel-args: '--prod'
```

### Environments

| Environment | Frontend URL | Backend URL | ADK Bridge URL | Purpose |
|-------------|-------------|-------------|----------------|---------|
| Development | http://localhost:3000 | http://localhost:8000 | http://localhost:8001 | Local development |
| Staging | https://bmad-staging.vercel.app | https://bmad-backend-staging.run.app | https://adk-bridge-staging.run.app | Pre-production testing |
| Production | https://bmad.ai | https://api.bmad.ai | https://adk-bridge.bmad.ai | Live environment |

## Security and Performance

### Security Requirements

**Frontend Security**:
- **CSP Headers**: Strict content security policy with ADK integration domains
- **XSS Prevention**: Input sanitization for ADK agent outputs and BMad HITL content
- **Secure Storage**: Token-based auth with secure HTTP-only cookies for ADK sessions

**Backend Security**:
- **Input Validation**: Comprehensive validation for ADK agent inputs and BMad API requests
- **Rate Limiting**: Per-user and per-agent rate limiting to prevent ADK quota exhaustion
- **CORS Policy**: Restricted CORS policy for ADK bridge service and BMad API endpoints

**ADK Integration Security**:
- **Service Account**: Dedicated GCP service account with minimal ADK permissions
- **Token Rotation**: Automatic rotation of ADK authentication tokens
- **Network Security**: VPC-native deployment with private ADK service communication

**Authentication Security**:
- **Token Storage**: JWT tokens stored securely with short expiration for ADK access
- **Session Management**: Redis-backed sessions with automatic cleanup for ADK Session State
- **MFA Support**: Multi-factor authentication for HITL approvals and production access

### Performance Optimization

**Frontend Performance**:
- **Bundle Size Target**: < 500KB initial bundle (ADK UI components code-split)
- **Loading Strategy**: Lazy loading for ADK-specific components and BMad enterprise features
- **Caching Strategy**: Aggressive caching for ADK agent status and BMad context data

**Backend Performance**:
- **Response Time Target**: < 200ms for BMad API, < 500ms for ADK bridge operations
- **Database Optimization**: Indexed queries for HITL requests, audit trails, and context artifacts
- **ADK Caching**: Redis caching for ADK Session State and Memory Service queries

**Integration Performance**:
- **Bridge Latency**: < 50ms for ADK-BMad event bridging
- **Session State**: Optimized Redis operations for ADK Session State with connection pooling
- **Memory Service**: Cached vector searches for ADK Memory Service with 95% hit rate

## Testing Strategy

### Testing Pyramid

```
                E2E Tests (Hybrid Workflows)
               /                            \
            ADK Integration Tests        BMad Integration Tests
           /                    \      /                      \
        ADK Agent Tests      Bridge Tests    HITL Tests    Audit Tests
       /         |         \             /        |         \
   Unit Tests (ADK)   Unit Tests (Bridge)    Unit Tests (BMad)
```

### Test Organization

**ADK Agent Tests**:
```
packages/adk-agents/tests/
├── unit/
│   ├── test_analyst_agent.py        # Analyst agent logic
│   ├── test_architect_agent.py      # Architect agent logic
│   ├── test_coder_agent.py          # Coder agent logic
│   ├── test_tester_agent.py         # Tester agent logic
│   └── test_deployer_agent.py       # Deployer agent logic
├── integration/
│   ├── test_adk_session_state.py    # Session State integration
│   ├── test_adk_memory_service.py   # Memory Service integration
│   └── test_adk_artifact_service.py # Artifact Service integration
└── evaluation/
    ├── test_agent_benchmarks.py     # Performance benchmarks
    └── test_agent_quality.py        # Output quality tests
```

**Bridge Service Tests**:
```
apps/adk-bridge/tests/
├── unit/
│   ├── test_bridge_service.py       # Core bridge logic
│   ├── test_adk_integration.py      # ADK service integration
│   └── test_bmad_integration.py     # BMad service integration
├── integration/
│   ├── test_hybrid_workflows.py     # End-to-end bridge workflows
│   ├── test_event_bridging.py       # ADK->BMad event routing
│   └── test_context_synchronization.py # Context sync between systems
└── load/
    ├── test_bridge_performance.py   # Performance under load
    └── test_concurrent_agents.py    # Multiple agent coordination
```

**BMad Enterprise Tests** (Preserved):
```
apps/backend/tests/
├── unit/
│   ├── test_hitl_service.py         # HITL system logic
│   ├── test_audit_service.py        # Audit trail logic
│   └── test_websocket_service.py    # Real-time service logic
├── integration/
│   ├── test_hitl_integration.py     # HITL workflows
│   ├── test_audit_integration.py    # Audit trail workflows
│   └── test_websocket_integration.py # WebSocket workflows
└── e2e/
    ├── test_bmad_workflows.py       # Complete BMad workflows
    └── test_adk_bmad_integration.py # Hybrid system integration
```

### Test Examples

**ADK Agent Test**:
```python
import pytest
from packages.adk_agents.src.agents.analyst import BmadAnalystAgent
from google.adk.core import InvocationContext

@pytest.mark.asyncio
async def test_analyst_agent_requirements_analysis():
    """Test Analyst agent with BMad integration"""

    # Setup test context
    agent = BmadAnalystAgent()
    context = InvocationContext(
        session=create_test_session(),
        deps=create_test_dependencies()
    )

    # Test data
    task_data = {
        "project_id": "test-project-123",
        "instructions": "Analyze requirements for e-commerce platform",
        "user_input": "Build an online store with payment processing"
    }

    # Execute agent
    result = await agent.execute_bmad_task(task_data, context)

    # Verify ADK integration
    assert result["success"] is True
    assert "prd_document" in result
    assert len(result["user_stories"]) > 0

    # Verify Memory Service storage
    memories = await context.deps.memory_service.search_memory(
        query="requirements analysis",
        filters={"project_id": "test-project-123"}
    )
    assert len(memories) > 0

    # Verify Artifact Service storage
    artifacts = await context.deps.artifact_service.list_artifacts(
        filters={"type": "prd", "project_id": "test-project-123"}
    )
    assert len(artifacts) > 0
```

**Bridge Integration Test**:
```python
import pytest
from apps.adk_bridge.src.bridge_service import ADKBmadBridge
from apps.backend.src.services.hitl_service import HitlService

@pytest.mark.asyncio
async def test_adk_bmad_hitl_integration():
    """Test ADK agent pause/resume with BMad HITL"""

    bridge = ADKBmadBridge()

    # Execute agent with HITL requirement
    task_data = {
        "project_id": "test-project-456",
        "agent_type": "architect",
        "instructions": "Design system architecture"
    }

    # Start execution (should pause for HITL)
    execution_id = await bridge.execute_adk_agent_with_bmad_oversight(
        "architect", task_data, hitl_required=True
    )

    # Verify HITL request created
    hitl_requests = await bridge.hitl_service.get_pending_requests(
        project_id="test-project-456"
    )
    assert len(hitl_requests) == 1
    assert hitl_requests[0].agent_type == "architect"

    # Approve HITL request
    await bridge.hitl_service.approve_request(
        hitl_requests[0].request_id,
        approval_data={"approved": True, "comment": "Architecture looks good"}
    )

    # Verify agent execution resumes
    result = await bridge.wait_for_completion(execution_id, timeout=30)
    assert result["success"] is True
    assert "architecture_document" in result
```

**E2E Hybrid Workflow Test**:
```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
async def test_complete_hybrid_workflow():
    """Test complete workflow: Frontend -> ADK Agents -> BMad HITL -> Completion"""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to application
        await page.goto("http://localhost:3000")

        # Create new project
        await page.click("[data-testid=new-project-button]")
        await page.fill("[data-testid=project-name]", "E2E Test Project")
        await page.fill("[data-testid=project-description]", "Build a task management app")
        await page.click("[data-testid=create-project]")

        # Wait for ADK Analyst agent to start
        await page.wait_for_selector("[data-testid=analyst-status-working]")

        # Wait for HITL approval request
        await page.wait_for_selector("[data-testid=hitl-approval-card]")

        # Verify ADK agent context in HITL request
        hitl_content = await page.text_content("[data-testid=hitl-content]")
        assert "ADK Session ID:" in hitl_content
        assert "Memory References:" in hitl_content
        assert "Generated Artifacts:" in hitl_content

        # Approve HITL request
        await page.click("[data-testid=approve-button]")
        await page.fill("[data-testid=approval-comment]", "Requirements look comprehensive")
        await page.click("[data-testid=submit-approval]")

        # Wait for agent to complete
        await page.wait_for_selector("[data-testid=analyst-status-completed]")

        # Verify artifacts generated
        await page.click("[data-testid=view-artifacts]")
        artifacts = await page.query_selector_all("[data-testid=artifact-item]")
        assert len(artifacts) >= 2  # PRD + user stories

        # Continue workflow to Architect
        await page.wait_for_selector("[data-testid=architect-status-working]")

        # Verify hybrid state synchronization
        adk_session = await page.text_content("[data-testid=adk-session-id]")
        bmad_context = await page.text_content("[data-testid=bmad-context-count]")
        assert adk_session is not None
        assert int(bmad_context) > 0

        await browser.close()
```

## Monitoring and Observability

### Monitoring Stack

**ADK Native Monitoring**:
- **Agent Performance**: ADK evaluation framework with continuous benchmarking
- **Session State Monitoring**: Redis metrics for ADK Session State operations
- **Memory Service Monitoring**: Vector search performance and hit rates
- **Artifact Service Monitoring**: Storage utilization and retrieval times

**BMad Enterprise Monitoring** (Preserved):
- **HITL System**: Approval request volume, response times, escalation rates
- **Audit Trail**: Event ingestion rates, query performance, compliance metrics
- **WebSocket Service**: Connection counts, message delivery rates, real-time latency
- **Context Store**: Artifact retrieval performance, storage utilization

**Integration Monitoring**:
- **Bridge Performance**: ADK-BMad integration latency, event processing rates
- **Hybrid Context**: Context synchronization times, data consistency metrics
- **Cross-System Events**: Event routing performance, message delivery guarantees

### Key Metrics

**ADK Agent Metrics**:
- **Task Success Rate**: % of ADK agent tasks completed successfully
- **Average Response Time**: Mean time for ADK agent task completion
- **Memory Utilization**: ADK Memory Service storage and retrieval efficiency
- **Artifact Generation**: Rate of artifact creation and storage utilization
- **Model Performance**: LLM usage efficiency and cost optimization

**BMad Enterprise Metrics** (Preserved):
- **HITL Efficiency**: Time to approval, approval rates, escalation frequency
- **Audit Compliance**: Event capture rate, query performance, retention compliance
- **Real-time Performance**: WebSocket connection stability, message delivery latency
- **Context Accuracy**: Context retrieval accuracy, artifact versioning consistency

**Integration Metrics**:
- **Bridge Latency**: Time for ADK events to reach BMad systems
- **Context Sync**: Consistency between ADK Session State and BMad Context Store
- **Hybrid Workflows**: End-to-end workflow completion times and success rates
- **System Health**: Overall hybrid system availability and performance

## Migration Timeline and Implementation Plan

### Phase 1: ADK Foundation Setup (2 weeks)

**Week 1: ADK Infrastructure**
- [ ] Install and configure ADK CLI and SDK
- [ ] Setup Google Cloud project with ADK services enabled
- [ ] Configure Vertex AI integration for multi-LLM access
- [ ] Initialize ADK Memory Service and Artifact Service
- [ ] Create basic ADK agent configurations

**Week 2: Bridge Service Development**
- [ ] Develop ADK-BMad bridge service architecture
- [ ] Implement Session State integration with Redis
- [ ] Create BMad context synchronization mechanisms
- [ ] Build event routing from ADK to BMad systems
- [ ] Setup basic monitoring and logging

### Phase 2: Agent Migration (2 weeks)

**Week 3: Core Agent Implementation**
- [ ] Migrate Analyst agent to ADK LlmAgent
- [ ] Migrate Architect agent to ADK LlmAgent
- [ ] Implement Memory Service integration for agent learning
- [ ] Setup Artifact Service for agent-generated content
- [ ] Test agent-to-agent coordination via Session State

**Week 4: Advanced Agents**
- [ ] Migrate Coder agent with code execution capabilities
- [ ] Migrate Tester agent with ADK evaluation integration
- [ ] Migrate Deployer agent with Google Cloud tools
- [ ] Implement comprehensive agent testing suite
- [ ] Validate agent performance benchmarks

### Phase 3: Enterprise Integration (1 week)

**Week 5: HITL and Audit Integration**
- [ ] Integrate ADK agents with BMad HITL system
- [ ] Implement ADK event logging to BMad audit trail
- [ ] Setup WebSocket bridging for ADK agent status
- [ ] Create hybrid context management system
- [ ] Test complete enterprise workflow integration

### Phase 4: Frontend Integration (1 week)

**Week 6: UI Development**
- [ ] Develop ADK agent status components
- [ ] Implement hybrid context visualization
- [ ] Create ADK Memory Service browser interface
- [ ] Build Artifact Service management UI
- [ ] Integrate WebSocket updates for ADK events

### Migration Risk Mitigation

**Rollback Strategy**:
- Maintain parallel BMad agent system during migration
- Feature flags to switch between ADK and BMad agents
- Gradual migration per agent type with A/B testing
- Complete rollback capability within 24 hours

**Data Migration**:
- Export existing BMad context to ADK-compatible format
- Migrate agent conversation history to ADK Memory Service
- Transfer agent-generated artifacts to ADK Artifact Service
- Preserve all HITL and audit trail data in BMad systems

**Performance Validation**:
- Benchmark ADK agents against current BMad agents
- Validate enterprise feature compatibility
- Load test hybrid system under production conditions
- Monitor system performance during migration

## Conclusion

This hybrid architecture represents a strategic evolution of BMad that leverages Google ADK's agent excellence while preserving our critical enterprise differentiators. By selectively adopting ADK for core agent capabilities and maintaining BMad for enterprise governance, we create a uniquely powerful platform that combines:

**✅ Google's AI Innovation**: Production-ready agents, advanced tooling, multi-model orchestration
**✅ Enterprise Governance**: Human oversight, compliance, audit trails, real-time capabilities
**✅ Competitive Advantage**: Features no other platform provides (HITL + ADK combination)
**✅ Technical Excellence**: Best-in-class architecture with minimal technical debt
**✅ Market Leadership**: First enterprise-grade AI development platform with comprehensive human oversight

The result is a platform that will define the future of enterprise AI development - combining the reliability of Google's framework with the governance requirements of enterprise deployment.

---

**Status**: Architecture Approved ✅
**Implementation**: Ready to Begin
**Timeline**: 6 weeks to full deployment
**Risk Level**: Medium (mitigated by incremental approach)
**Business Impact**: High (market differentiator + technical excellence)