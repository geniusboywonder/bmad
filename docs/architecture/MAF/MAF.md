# Microsoft Agent Framework (MAF) Migration Plan

## Executive Summary

Microsoft is transitioning from AutoGen to the new **Microsoft Agent Framework (MAF)**, a production-ready framework designed for building, deploying, and scaling AI agents. This document outlines a strategic migration plan for BMAD's multi-agent orchestration platform.

**Migration Status**: Planning Phase  
**Target Completion**: Q2 2025  
**Risk Level**: Medium (Hybrid approach minimizes disruption)

---

## 1. Current Architecture Analysis

### 1.1 Existing Framework Stack

**Current Multi-Framework Architecture:**
- **AutoGen (Primary)**: 1,954 references, 967 tests, 95%+ pass rate
  - Core task execution engine
  - Multi-agent conversation management
  - Group chat capabilities
  - Battle-tested production infrastructure
  
- **Google ADK (Complementary)**: Specialized use cases
  - Enterprise tool integration via `bmad_adk_wrapper.py`
  - Native Gemini integration
  - Session management
  
- **AG-UI Protocol**: Frontend integration layer
  - CopilotKit integration attempts
  - Protocol mismatch issues (422 errors)
  
- **BMAD Core**: Template and workflow orchestration
  - YAML-based workflow definitions
  - Dynamic template loading

### 1.2 Critical Dependencies

**AutoGen-Dependent Components:**
- `backend/app/services/autogen_service.py` (AutoGenCore)
- `backend/app/tasks/agent_tasks.py:308` (execute_task)
- `backend/app/services/orchestrator.py` (HandoffManager)
- Agent conversation patterns across 967 tests

**Integration Points:**
- HITL safety controls
- WebSocket event broadcasting
- Celery task queue
- Context artifact management

---

## 2. Microsoft Agent Framework Overview

### 2.1 MAF Core Capabilities

**Key Features:**

1. **Agent Runtime**: Production-grade agent execution with state management
2. **Multi-Agent Orchestration**: Native support for agent teams and handoffs
3. **Tool Integration**: Extensible tool system with OpenAPI support
4. **Streaming & Events**: Real-time event streaming for UI integration
5. **State Management**: Built-in conversation and session persistence
6. **Observability**: Native telemetry and monitoring
7. **Security**: Enterprise-grade authentication and authorization

**Architecture Improvements Over AutoGen:**
- Simplified agent creation with declarative configuration
- Native async/await support throughout
- Better error handling and recovery mechanisms
- Production-ready deployment patterns
- Improved tool calling and function execution
- Built-in support for agent handoffs and delegation

### 2.2 MAF vs AutoGen Comparison

| Feature | AutoGen | MAF | Impact on BMAD |
|---------|---------|-----|----------------|
| **Agent Creation** | Class-based, complex | Declarative, simple | Easier maintenance |
| **Multi-Agent** | GroupChat pattern | Native orchestration | Better handoffs |
| **State Management** | Manual | Built-in | Simplified code |
| **Tool Calling** | Custom implementation | Native support | Reduced complexity |
| **Streaming** | Limited | Full support | Better UX |
| **Production Ready** | Community-driven | Microsoft-backed | Enterprise support |
| **Migration Path** | N/A | Official guide | Lower risk |

---

## 3. Framework Responsibility Boundaries

### 3.1 Proposed Architecture: MAF + ADK + AG-UI + CopilotKit



**Clear Separation of Concerns:**

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  CopilotKit (UI Components & State Management)                  │
│  - Chat interface and message rendering                         │
│  - User interaction handling                                    │
│  - Frontend state management (Zustand)                          │
│  - WebSocket client for real-time updates                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                    PROTOCOL INTEGRATION LAYER                   │
├─────────────────────────────────────────────────────────────────┤
│  AG-UI Protocol (Agent-UI Communication Standard)               │
│  - Standardized message format                                  │
│  - Event streaming protocol                                     │
│  - State synchronization                                        │
│  - Tool invocation protocol                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓ AG-UI Events
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATION LAYER                    │
├─────────────────────────────────────────────────────────────────┤
│  Microsoft Agent Framework (MAF) - PRIMARY ORCHESTRATOR         │
│  ✅ MANAGES:                                                     │
│    - Multi-agent conversation coordination                      │
│    - Agent-to-agent handoffs and delegation                     │
│    - Conversation state and session management                  │
│    - Agent lifecycle (create, execute, terminate)               │
│    - Event streaming to frontend via AG-UI                      │
│    - Tool calling orchestration                                 │
│                                                                  │
│  ❌ DOES NOT MANAGE:                                            │
│    - LLM provider selection (delegates to ADK)                  │
│    - Enterprise safety controls (delegates to BMAD)             │
│    - Workflow templates (delegates to BMAD Core)                │
└─────────────────────────────────────────────────────────────────┘
                    ↓ Agent Execution Requests
┌─────────────────────────────────────────────────────────────────┐
│                      LLM INTEGRATION LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│  Google ADK (LLM Provider Abstraction)                          │
│  ✅ MANAGES:                                                     │
│    - Multi-provider LLM access (OpenAI, Anthropic, Google)     │
│    - LLM-specific tool integration                              │
│    - Model configuration and parameters                         │
│    - Native Gemini integration                                  │
│    - Response streaming from LLMs                               │
│                                                                  │
│  ❌ DOES NOT MANAGE:                                            │
│    - Agent orchestration (MAF responsibility)                   │
│    - Conversation state (MAF responsibility)                    │
│    - HITL controls (BMAD responsibility)                        │
└─────────────────────────────────────────────────────────────────┘
                    ↓ LLM Responses
┌─────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE CONTROL LAYER                     │
├─────────────────────────────────────────────────────────────────┤
│  BMAD Core Services (Enterprise Features)                       │
│  ✅ MANAGES:                                                     │
│    - HITL safety controls and approval workflows               │
│    - Budget management and emergency stops                      │
│    - Audit trails and compliance logging                        │
│    - Context artifact storage and retrieval                     │
│    - Workflow templates (YAML-based)                            │
│    - Agent persona management (markdown files)                  │
│    - Database persistence (PostgreSQL)                          │
│    - Task queue management (Celery/Redis)                       │
│                                                                  │
│  ❌ DOES NOT MANAGE:                                            │
│    - Agent conversation logic (MAF responsibility)              │
│    - LLM provider calls (ADK responsibility)                    │
│    - UI rendering (CopilotKit responsibility)                   │
└─────────────────────────────────────────────────────────────────┘
```



### 3.2 Framework Overlap Analysis

**Identified Overlaps and Resolutions:**

| Capability | AutoGen (Current) | MAF (Proposed) | ADK | BMAD Core | Resolution |
|------------|-------------------|----------------|-----|-----------|------------|
| **Agent Orchestration** | ✅ Primary | ✅ Primary | ❌ | ❌ | **MAF replaces AutoGen** |
| **Multi-Agent Coordination** | ✅ GroupChat | ✅ Native | ❌ | ❌ | **MAF native support** |
| **LLM Provider Access** | ✅ Direct | ⚠️ Possible | ✅ Primary | ❌ | **ADK remains primary** |
| **Tool Calling** | ✅ Custom | ✅ Native | ✅ Native | ❌ | **MAF + ADK hybrid** |
| **State Management** | ⚠️ Manual | ✅ Built-in | ✅ Sessions | ✅ Database | **MAF for conversation, BMAD for persistence** |
| **HITL Controls** | ❌ | ❌ | ❌ | ✅ Primary | **BMAD exclusive** |
| **Workflow Templates** | ❌ | ❌ | ❌ | ✅ Primary | **BMAD exclusive** |
| **Event Streaming** | ⚠️ Limited | ✅ Native | ✅ Native | ✅ WebSocket | **MAF → AG-UI → CopilotKit** |

**Key Decisions:**

1. **MAF Replaces AutoGen**: Complete migration for agent orchestration
   - **Rationale**: Microsoft's official successor with better production support
   - **Risk**: Medium (official migration guide available)

2. **ADK Remains for LLM Access**: Keep ADK as LLM provider abstraction
   - **Rationale**: Multi-provider support (OpenAI, Anthropic, Google)
   - **Risk**: Low (ADK and MAF designed to work together)

3. **BMAD Core Retains Enterprise Features**: No changes to safety/workflow systems
   - **Rationale**: These are BMAD-specific business logic, not framework concerns
   - **Risk**: None (clear separation of concerns)

4. **AG-UI Protocol for Frontend**: Standardized agent-UI communication
   - **Rationale**: Industry standard, works with MAF and CopilotKit
   - **Risk**: Low (protocol is framework-agnostic)

---

## 4. Migration Strategy

### 4.1 Phased Migration Approach

**Phase 1: Foundation (Weeks 1-2)**
- Install MAF SDK and dependencies
- Create MAF agent wrappers alongside existing AutoGen agents
- Implement MAF → ADK integration layer
- Set up parallel testing infrastructure

**Phase 2: Core Migration (Weeks 3-6)**
- Migrate agent creation from AutoGen to MAF
- Replace GroupChat with MAF orchestration
- Update handoff logic to use MAF delegation
- Migrate conversation state management

**Phase 3: Integration (Weeks 7-8)**
- Connect MAF to BMAD HITL safety controls
- Integrate MAF events with WebSocket broadcasting
- Update AG-UI protocol handlers for MAF
- Migrate Celery task execution to MAF

**Phase 4: Testing & Validation (Weeks 9-10)**
- Run parallel AutoGen/MAF tests
- Performance benchmarking
- Load testing with production scenarios
- Security and compliance validation

**Phase 5: Cutover (Weeks 11-12)**
- Gradual rollout with feature flags
- Monitor production metrics
- Remove AutoGen dependencies
- Update documentation



### 4.2 Risk Mitigation

**High-Risk Areas:**

1. **AutoGen Conversation Patterns** (967 tests)
   - **Mitigation**: Maintain AutoGen tests as acceptance criteria for MAF
   - **Strategy**: Create MAF equivalents that pass same test scenarios

2. **HITL Integration Points**
   - **Mitigation**: Wrap MAF agents with BMAD safety controls
   - **Strategy**: Create `MAFAgentWrapper` similar to `BMADADKWrapper`

3. **Production Stability** (95%+ pass rate)
   - **Mitigation**: Feature flags for gradual rollout
   - **Strategy**: Run AutoGen and MAF in parallel during transition

4. **WebSocket Event Broadcasting**
   - **Mitigation**: MAF native event streaming maps to existing WebSocket system
   - **Strategy**: Create event adapter layer

**Rollback Plan:**
- Feature flags allow instant revert to AutoGen
- Maintain AutoGen code for 3 months post-migration
- Database schema remains unchanged (framework-agnostic)

---

## 5. Technical Implementation

### 5.1 MAF Agent Wrapper (New)

```python
# backend/app/agents/maf_agent_wrapper.py
"""MAF Agent Wrapper with BMAD Enterprise Controls."""

from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime

from microsoft.agent_framework import Agent, AgentRuntime, AgentConfig
from microsoft.agent_framework.tools import Tool

# BMAD enterprise services
from app.services.hitl_safety_service import HITLSafetyService
from app.services.llm_service import LLMService
from app.services.audit_trail_service import AuditTrailService
from app.services.context_store import ContextStoreService
from app.utils.agent_prompt_loader import agent_prompt_loader

# ADK integration for LLM access
from app.agents.bmad_adk_wrapper import BMADADKWrapper

logger = structlog.get_logger(__name__)


class BMADMAFWrapper:
    """Integration wrapper combining MAF agents with BMAD enterprise features."""

    def __init__(self,
                 agent_name: str,
                 agent_type: str = "general",
                 tools: Optional[List[Tool]] = None,
                 context_store: Optional[ContextStoreService] = None):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.tools = tools or []

        # Load agent persona from markdown
        self.instruction = agent_prompt_loader.get_agent_prompt(agent_type)

        # MAF components
        self.maf_agent = None
        self.maf_runtime = None

        # ADK for LLM access (MAF delegates to ADK)
        self.adk_wrapper = None

        # BMAD enterprise services
        self.hitl_service = HITLSafetyService()
        self.llm_service = LLMService({"enable_monitoring": True})
        self.audit_service = AuditTrailService()
        self.context_store = context_store or ContextStoreService()

        # State tracking
        self.is_initialized = False
        self.execution_count = 0

    async def initialize(self) -> bool:
        """Initialize MAF agent with ADK LLM backend."""
        try:
            # Initialize ADK wrapper for LLM access
            self.adk_wrapper = BMADADKWrapper(
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                instruction=self.instruction
            )
            await self.adk_wrapper.initialize()

            # Create MAF agent configuration
            agent_config = AgentConfig(
                name=self.agent_name,
                description=f"BMAD {self.agent_type} agent",
                instructions=self.instruction,
                tools=self.tools,
                # MAF delegates LLM calls to ADK
                llm_provider=self._create_adk_llm_provider()
            )

            # Create MAF agent
            self.maf_agent = Agent(config=agent_config)

            # Create MAF runtime
            self.maf_runtime = AgentRuntime()

            self.is_initialized = True
            logger.info("BMAD-MAF wrapper initialized successfully",
                       agent_name=self.agent_name,
                       agent_type=self.agent_type)
            return True

        except Exception as e:
            logger.error("Failed to initialize BMAD-MAF wrapper",
                        agent_name=self.agent_name,
                        error=str(e))
            return False

    def _create_adk_llm_provider(self):
        """Create LLM provider that delegates to ADK."""
        # This adapter allows MAF to use ADK for LLM calls
        # Maintains multi-provider support (OpenAI, Anthropic, Google)
        
        class ADKLLMProvider:
            def __init__(self, adk_wrapper):
                self.adk_wrapper = adk_wrapper

            async def generate(self, messages, **kwargs):
                # MAF calls this, we delegate to ADK
                result = await self.adk_wrapper._execute_adk_agent(
                    message=messages[-1].content,
                    execution_id=f"maf_{datetime.now().timestamp()}",
                    context=[]
                )
                return result.get("response", "")

        return ADKLLMProvider(self.adk_wrapper)

    async def process_with_enterprise_controls(self,
                                             message: str,
                                             project_id: str,
                                             task_id: str,
                                             user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process message with full BMAD enterprise controls."""
        if not self.is_initialized:
            return {"success": False, "error": "Wrapper not initialized"}

        execution_id = f"{self.agent_name}_{self.execution_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.execution_count += 1

        try:
            # 1. HITL Safety Check (BMAD responsibility)
            approval_result = await self._request_hitl_approval(
                message, project_id, task_id, execution_id
            )
            if not approval_result["approved"]:
                return {
                    "success": False,
                    "error": "Request denied by human oversight",
                    "execution_id": execution_id
                }

            # 2. Audit Trail - Start (BMAD responsibility)
            await self.audit_service.log_agent_execution_start(
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                execution_id=execution_id,
                project_id=project_id,
                task_id=task_id,
                user_id=user_id,
                input_message=message
            )

            # 3. Fetch context (BMAD responsibility)
            context = await self.context_store.get_artifacts_by_project(project_id)

            # 4. Execute MAF Agent (MAF orchestration, ADK for LLM)
            start_time = datetime.now()
            maf_result = await self._execute_maf_agent(message, execution_id, context)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            if not maf_result.get("success", False):
                await self.audit_service.log_agent_execution_complete(
                    execution_id=execution_id,
                    success=False,
                    error_message=maf_result.get("error", "MAF execution failed"),
                    execution_time=execution_time
                )
                return {
                    "success": False,
                    "error": maf_result.get("error"),
                    "execution_id": execution_id
                }

            # 5. Usage Tracking (BMAD responsibility)
            response_text = maf_result.get("response", "")
            self.llm_service.track_usage(
                agent_type=self.agent_type,
                provider="maf_adk",
                model="multi_provider",
                input_tokens=len(message.split()),
                output_tokens=len(response_text.split()),
                response_time_ms=execution_time * 1000,
                success=True,
                project_id=project_id,
                task_id=task_id
            )

            # 6. Audit Trail - Complete (BMAD responsibility)
            await self.audit_service.log_agent_execution_complete(
                execution_id=execution_id,
                success=True,
                output_message=response_text,
                execution_time=execution_time
            )

            logger.info("BMAD-MAF message processed successfully",
                       agent_name=self.agent_name,
                       execution_id=execution_id,
                       execution_time=execution_time)

            return {
                "success": True,
                "response": response_text,
                "execution_id": execution_id,
                "agent_name": self.agent_name,
                "execution_time": execution_time
            }

        except Exception as e:
            await self.audit_service.log_agent_execution_complete(
                execution_id=execution_id,
                success=False,
                error_message=str(e),
                execution_time=0
            )

            logger.error("BMAD-MAF message processing failed",
                        agent_name=self.agent_name,
                        execution_id=execution_id,
                        error=str(e))

            return {
                "success": False,
                "error": str(e),
                "execution_id": execution_id
            }

    async def _execute_maf_agent(self, message: str, execution_id: str, 
                                context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute MAF agent with context."""
        try:
            # Prepare context message
            context_message = ""
            if context:
                context_message = "Context:\n"
                for artifact in context:
                    context_message += f"- {artifact.artifact_type}: {artifact.content}\n"

            full_message = f"{context_message}\n{message}"

            # Execute with MAF runtime (which delegates to ADK for LLM)
            result = await self.maf_runtime.run(
                agent=self.maf_agent,
                message=full_message,
                session_id=execution_id
            )

            if result and result.content:
                return {
                    "success": True,
                    "response": result.content,
                    "session_id": execution_id
                }
            else:
                return {
                    "success": False,
                    "error": "No response generated"
                }

        except Exception as e:
            logger.error("MAF agent execution failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def _request_hitl_approval(self, message: str, project_id: str,
                                    task_id: str, execution_id: str) -> Dict[str, Any]:
        """Request HITL approval (BMAD enterprise control)."""
        try:
            approval_id = await self.hitl_service.create_approval_request(
                project_id=project_id,
                task_id=task_id,
                agent_type=self.agent_type,
                request_type="AGENT_EXECUTION",
                request_data={
                    "agent_name": self.agent_name,
                    "message": message,
                    "execution_id": execution_id,
                    "framework": "MAF"
                }
            )

            approval = await self.hitl_service.wait_for_approval(
                approval_id, timeout_minutes=10
            )

            return {
                "approved": approval.approved,
                "approval_id": approval_id
            }

        except Exception as e:
            logger.warning("HITL approval request failed",
                         execution_id=execution_id,
                         error=str(e))
            return {"approved": False, "error": str(e)}
```



### 5.2 MAF Orchestration Service (Replaces AutoGen)

```python
# backend/app/services/maf_orchestration_service.py
"""MAF Multi-Agent Orchestration Service."""

from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime

from microsoft.agent_framework import AgentTeam, Handoff, HandoffConfig

from app.agents.maf_agent_wrapper import BMADMAFWrapper

logger = structlog.get_logger(__name__)


class MAFOrchestrationService:
    """Multi-agent orchestration using MAF for collaborative workflows."""

    def __init__(self):
        self.active_teams: Dict[str, AgentTeam] = {}
        self.orchestration_count = 0

        logger.info("MAF Orchestration Service initialized")

    async def create_multi_agent_team(self,
                                     agents: List[BMADMAFWrapper],
                                     team_type: str,
                                     project_id: str,
                                     team_config: Optional[Dict[str, Any]] = None) -> str:
        """Create multi-agent team using MAF native orchestration.
        
        Replaces AutoGen GroupChat with MAF AgentTeam.
        """
        if not agents:
            raise ValueError("At least one agent required for team")

        # Generate unique team ID
        self.orchestration_count += 1
        team_id = f"maf_team_{project_id}_{team_type}_{self.orchestration_count}"

        # Create MAF agent team
        maf_agents = [agent.maf_agent for agent in agents if agent.is_initialized]
        
        team = AgentTeam(
            name=team_id,
            agents=maf_agents,
            handoff_config=self._create_handoff_config(team_type, team_config or {})
        )

        self.active_teams[team_id] = team

        logger.info("MAF agent team created",
                   team_id=team_id,
                   agent_count=len(maf_agents))

        return team_id

    def _create_handoff_config(self, team_type: str,
                              custom_config: Dict[str, Any]) -> HandoffConfig:
        """Create handoff configuration for agent team."""
        
        # MAF native handoff configuration
        config = HandoffConfig(
            strategy="sequential",  # or "parallel", "hierarchical"
            max_iterations=10,
            allow_delegation=True,
            timeout_seconds=1800
        )

        # Team-specific configurations
        if team_type == "requirements_analysis":
            config.strategy = "collaborative"
            config.max_iterations = 8
        elif team_type == "system_design":
            config.strategy = "hierarchical"
            config.max_iterations = 12

        # Apply custom overrides
        for key, value in custom_config.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    async def execute_team_task(self,
                               team_id: str,
                               initial_message: str,
                               user_id: str = "bmad_user") -> Dict[str, Any]:
        """Execute task with MAF agent team."""
        if team_id not in self.active_teams:
            return {"error": f"Team {team_id} not found"}

        team = self.active_teams[team_id]

        try:
            # Execute with MAF team orchestration
            result = await team.run(
                message=initial_message,
                user_id=user_id
            )

            logger.info("MAF team task completed", team_id=team_id)
            
            return {
                "team_id": team_id,
                "status": "completed",
                "result": result.content,
                "agents_involved": [agent.name for agent in team.agents]
            }

        except Exception as e:
            logger.error("MAF team task failed",
                        team_id=team_id, error=str(e))
            return {"error": f"Team execution failed: {str(e)}"}
```



### 5.3 Migration Mapping

**AutoGen → MAF Equivalents:**

| AutoGen Concept | MAF Equivalent | Migration Notes |
|----------------|----------------|-----------------|
| `AssistantAgent` | `Agent` | Direct replacement with simpler API |
| `UserProxyAgent` | `Agent` with user role | Configure agent role in AgentConfig |
| `GroupChat` | `AgentTeam` | Native multi-agent support |
| `GroupChatManager` | `AgentTeam.run()` | Built-in orchestration |
| `register_function` | `Tool` | Native tool system |
| `initiate_chat` | `AgentRuntime.run()` | Simplified execution |
| Manual state tracking | `Session` | Built-in state management |
| Custom event handling | `EventStream` | Native event streaming |

**Code Migration Example:**

```python
# BEFORE (AutoGen)
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

analyst = AssistantAgent(
    name="analyst",
    system_message=agent_prompt_loader.get_agent_prompt("analyst"),
    llm_config={"model": "gpt-4"}
)

architect = AssistantAgent(
    name="architect",
    system_message=agent_prompt_loader.get_agent_prompt("architect"),
    llm_config={"model": "gpt-4"}
)

user_proxy = UserProxyAgent(name="user", human_input_mode="NEVER")

group_chat = GroupChat(
    agents=[analyst, architect, user_proxy],
    messages=[],
    max_round=10
)

manager = GroupChatManager(groupchat=group_chat)
user_proxy.initiate_chat(manager, message="Analyze requirements")

# AFTER (MAF + ADK)
from app.agents.maf_agent_wrapper import BMADMAFWrapper
from app.services.maf_orchestration_service import MAFOrchestrationService

# Create MAF agents with ADK LLM backend
analyst = BMADMAFWrapper(
    agent_name="analyst",
    agent_type="analyst"
)
await analyst.initialize()

architect = BMADMAFWrapper(
    agent_name="architect",
    agent_type="architect"
)
await architect.initialize()

# Create MAF team (replaces GroupChat)
orchestrator = MAFOrchestrationService()
team_id = await orchestrator.create_multi_agent_team(
    agents=[analyst, architect],
    team_type="requirements_analysis",
    project_id="project_123"
)

# Execute task (replaces initiate_chat)
result = await orchestrator.execute_team_task(
    team_id=team_id,
    initial_message="Analyze requirements"
)
```

---

## 6. Integration Points

### 6.1 MAF + ADK Integration

**Why Keep ADK:**
- Multi-provider LLM support (OpenAI, Anthropic, Google)
- Existing enterprise tool integrations
- Native Gemini integration
- Proven production reliability

**Integration Pattern:**
```
MAF Agent → ADK LLM Provider → OpenAI/Anthropic/Google
```

**Benefits:**
- MAF handles orchestration
- ADK handles LLM provider abstraction
- Clean separation of concerns
- Maintains multi-provider flexibility

### 6.2 MAF + AG-UI Protocol

**Current Issue:**
- CopilotKit + AG-UI + ADK has 422 protocol mismatch errors

**MAF Solution:**
- MAF has native AG-UI protocol support
- Better event streaming integration
- Standardized message format

**Implementation:**
```python
# backend/app/copilot/maf_agui_runtime.py
from microsoft.agent_framework.protocols import AGUIProtocol
from app.agents.maf_agent_wrapper import BMADMAFWrapper

class BMADMAFAGUIRuntime:
    """MAF runtime with AG-UI protocol for CopilotKit."""
    
    def __init__(self):
        self.agui_protocol = AGUIProtocol()
        self.maf_agents = {}
    
    def setup_fastapi_endpoints(self, app):
        """Register AG-UI endpoints with MAF agents."""
        
        # Create MAF agents
        analyst = BMADMAFWrapper(agent_name="analyst", agent_type="analyst")
        architect = BMADMAFWrapper(agent_name="architect", agent_type="architect")
        # ... other agents
        
        # Register with AG-UI protocol (MAF native support)
        self.agui_protocol.register_agent(analyst.maf_agent, path="/api/copilotkit/analyst")
        self.agui_protocol.register_agent(architect.maf_agent, path="/api/copilotkit/architect")
        
        # Add to FastAPI
        app.include_router(self.agui_protocol.router)
```

**Expected Outcome:**
- ✅ Resolves 422 protocol mismatch errors
- ✅ Native event streaming to CopilotKit
- ✅ Better error messages and debugging

### 6.3 MAF + BMAD Enterprise Controls

**HITL Integration:**
```python
# Wrap MAF agents with HITL controls
class HITLMAFAgent(BMADMAFWrapper):
    async def execute(self, message, project_id, task_id):
        # 1. HITL approval (BMAD)
        approval = await self.hitl_service.request_approval(...)
        if not approval.approved:
            return {"error": "Denied by HITL"}
        
        # 2. Execute MAF agent
        result = await self.maf_agent.run(message)
        
        # 3. Audit trail (BMAD)
        await self.audit_service.log_execution(...)
        
        return result
```

**Budget Controls:**
- MAF execution wrapped with BMAD budget checks
- Emergency stop integration
- Token usage tracking via LLMService

**Workflow Templates:**
- BMAD Core YAML templates remain unchanged
- MAF agents execute workflow steps
- Template system orchestrates MAF agent calls

---

## 7. Performance & Scalability

### 7.1 Expected Improvements

**MAF Advantages:**
- **Native Async**: Better concurrency than AutoGen
- **Event Streaming**: Reduced latency for UI updates
- **State Management**: Less memory overhead
- **Tool Calling**: Faster function execution

**Benchmarks (Estimated):**
| Metric | AutoGen | MAF | Improvement |
|--------|---------|-----|-------------|
| Agent Creation | 200ms | 50ms | 4x faster |
| Multi-Agent Coordination | 500ms | 200ms | 2.5x faster |
| Event Streaming | Limited | Native | Better UX |
| Memory Usage | High | Medium | 30% reduction |

### 7.2 Scalability Considerations

**MAF Scaling Features:**
- Distributed agent execution
- Load balancing across agent instances
- Connection pooling for LLM providers (via ADK)
- Efficient state serialization

**BMAD Infrastructure:**
- Celery task queue remains unchanged
- Redis caching benefits from MAF's efficient state
- PostgreSQL persistence unaffected
- WebSocket broadcasting enhanced by MAF events

---

## 8. Testing Strategy

### 8.1 Test Migration Plan

**Maintain Test Coverage:**
- 967 existing AutoGen tests become acceptance criteria
- Create MAF equivalents that pass same scenarios
- Parallel testing during migration

**Test Categories:**

1. **Unit Tests**: MAF agent wrapper functionality
2. **Integration Tests**: MAF + ADK + BMAD integration
3. **Orchestration Tests**: Multi-agent team coordination
4. **HITL Tests**: Safety control integration
5. **Performance Tests**: Benchmarking vs AutoGen
6. **E2E Tests**: Full workflow execution

**Test Infrastructure:**
```python
# backend/tests/unit/test_maf_agent_wrapper.py
import pytest
from app.agents.maf_agent_wrapper import BMADMAFWrapper

@pytest.mark.asyncio
async def test_maf_agent_initialization():
    """Test MAF agent wrapper initialization."""
    wrapper = BMADMAFWrapper(
        agent_name="test_agent",
        agent_type="analyst"
    )
    
    assert await wrapper.initialize()
    assert wrapper.is_initialized
    assert wrapper.maf_agent is not None

@pytest.mark.asyncio
async def test_maf_agent_execution_with_hitl():
    """Test MAF agent execution with HITL controls."""
    wrapper = BMADMAFWrapper(agent_name="analyst", agent_type="analyst")
    await wrapper.initialize()
    
    result = await wrapper.process_with_enterprise_controls(
        message="Analyze market trends",
        project_id="test_project",
        task_id="test_task"
    )
    
    assert result["success"]
    assert "response" in result
    assert "execution_id" in result
```

### 8.2 Validation Criteria

**Migration Success Metrics:**
- ✅ All 967 AutoGen tests have MAF equivalents
- ✅ 95%+ test pass rate maintained
- ✅ Performance equal or better than AutoGen
- ✅ HITL integration fully functional
- ✅ WebSocket events working correctly
- ✅ AG-UI protocol 422 errors resolved
- ✅ Production deployment successful

---

## 9. Deployment Plan

### 9.1 Feature Flag Strategy

```python
# backend/app/settings.py
class Settings(BaseSettings):
    # Feature flag for MAF migration
    use_maf_orchestration: bool = Field(default=False)
    maf_rollout_percentage: int = Field(default=0)  # 0-100
    maf_enabled_agents: List[str] = Field(default=[])  # ["analyst", "architect"]
```

**Rollout Phases:**

1. **Phase 1 (Week 11)**: 10% traffic, analyst agent only
2. **Phase 2 (Week 11.5)**: 25% traffic, analyst + architect
3. **Phase 3 (Week 12)**: 50% traffic, all agents
4. **Phase 4 (Week 12.5)**: 100% traffic, full cutover

**Monitoring:**
- Error rates (target: <1%)
- Response times (target: <200ms)
- HITL approval success rate (target: 100%)
- WebSocket event delivery (target: <100ms)

### 9.2 Rollback Procedures

**Instant Rollback:**
```python
# Set feature flag to False
use_maf_orchestration = False
```

**Gradual Rollback:**
```python
# Reduce rollout percentage
maf_rollout_percentage = 25  # Down from 50%
```

**Full Rollback:**
- Revert to AutoGen codebase
- Maintain for 3 months post-migration
- Database schema unchanged (no rollback needed)

---

## 10. Timeline & Resources

### 10.1 Project Timeline

**Total Duration**: 12 weeks (Q2 2025)

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Foundation** | Weeks 1-2 | MAF SDK installed, agent wrappers created |
| **Phase 2: Core Migration** | Weeks 3-6 | Agent creation, orchestration, handoffs migrated |
| **Phase 3: Integration** | Weeks 7-8 | HITL, WebSocket, AG-UI integration complete |
| **Phase 4: Testing** | Weeks 9-10 | All tests passing, performance validated |
| **Phase 5: Deployment** | Weeks 11-12 | Gradual rollout, monitoring, cutover |

### 10.2 Resource Requirements

**Development Team:**
- 2 Senior Backend Engineers (full-time)
- 1 DevOps Engineer (50% time)
- 1 QA Engineer (full-time)

**Infrastructure:**
- Development environment for parallel testing
- Staging environment for integration testing
- Production monitoring and alerting

**External Dependencies:**
- Microsoft MAF SDK (official support)
- Google ADK (existing)
- CopilotKit (existing)

---

## 11. Success Criteria

### 11.1 Technical Metrics

- ✅ **Test Coverage**: 967 tests migrated with 95%+ pass rate
- ✅ **Performance**: Response times ≤ AutoGen baseline
- ✅ **Reliability**: Error rate <1%
- ✅ **Integration**: HITL, WebSocket, AG-UI fully functional
- ✅ **Protocol**: AG-UI 422 errors resolved

### 11.2 Business Metrics

- ✅ **Zero Downtime**: Migration with no production outages
- ✅ **Feature Parity**: All AutoGen features available in MAF
- ✅ **Developer Experience**: Simplified codebase, easier maintenance
- ✅ **Enterprise Support**: Microsoft-backed framework
- ✅ **Future-Proof**: Official migration path from AutoGen

---

## 12. Conclusion

### 12.1 Strategic Rationale

**Why Migrate to MAF:**

1. **Official Successor**: Microsoft's recommended path from AutoGen
2. **Production Ready**: Enterprise-grade support and documentation
3. **Better Architecture**: Native async, event streaming, state management
4. **Simplified Code**: Declarative agent creation, less boilerplate
5. **Protocol Compatibility**: Native AG-UI support resolves CopilotKit issues
6. **Future-Proof**: Active development and long-term support

**Why Keep ADK:**

1. **Multi-Provider**: OpenAI, Anthropic, Google support
2. **Proven Reliability**: Production-tested LLM abstraction
3. **Clean Separation**: MAF orchestrates, ADK provides LLM access
4. **No Overlap**: Complementary responsibilities

**Why Keep BMAD Core:**

1. **Enterprise Features**: HITL, budgets, audit trails are business logic
2. **Workflow Templates**: YAML-based templates are BMAD-specific
3. **Database Persistence**: Framework-agnostic data layer
4. **No Framework Overlap**: Clear separation of concerns

### 12.2 Risk Assessment

**Overall Risk**: Medium

**Mitigations:**
- Official Microsoft migration guide
- Phased rollout with feature flags
- Parallel testing infrastructure
- Instant rollback capability
- 3-month AutoGen code retention

**Confidence Level**: 85%

### 12.3 Recommendation

**Proceed with MAF migration** using the phased approach outlined in this document.

**Key Success Factors:**
1. Maintain ADK for LLM provider abstraction
2. Keep BMAD Core enterprise features unchanged
3. Use MAF native AG-UI protocol for CopilotKit
4. Gradual rollout with comprehensive monitoring
5. Maintain AutoGen tests as acceptance criteria

**Expected Outcome:**
- Simplified, more maintainable codebase
- Resolved AG-UI protocol issues
- Better performance and scalability
- Enterprise-grade support from Microsoft
- Future-proof agent orchestration platform

---

## Appendix A: Framework Comparison Matrix

| Feature | AutoGen | MAF | ADK | BMAD Core | Recommendation |
|---------|---------|-----|-----|-----------|----------------|
| **Agent Orchestration** | ✅ | ✅ | ❌ | ❌ | **MAF** |
| **Multi-Agent Teams** | ✅ GroupChat | ✅ Native | ❌ | ❌ | **MAF** |
| **LLM Provider Access** | ✅ | ⚠️ | ✅ | ❌ | **ADK** |
| **Multi-Provider Support** | ⚠️ | ⚠️ | ✅ | ❌ | **ADK** |
| **Tool Calling** | ✅ Custom | ✅ Native | ✅ | ❌ | **MAF + ADK** |
| **State Management** | ⚠️ Manual | ✅ Built-in | ✅ Sessions | ✅ DB | **MAF + BMAD** |
| **Event Streaming** | ⚠️ Limited | ✅ Native | ✅ | ✅ WebSocket | **MAF** |
| **AG-UI Protocol** | ❌ | ✅ Native | ⚠️ Issues | ❌ | **MAF** |
| **HITL Controls** | ❌ | ❌ | ❌ | ✅ | **BMAD** |
| **Budget Management** | ❌ | ❌ | ❌ | ✅ | **BMAD** |
| **Audit Trails** | ❌ | ❌ | ❌ | ✅ | **BMAD** |
| **Workflow Templates** | ❌ | ❌ | ❌ | ✅ | **BMAD** |
| **Production Support** | Community | Microsoft | Google | Internal | **MAF + ADK** |

---

## Appendix B: Migration Checklist

### Pre-Migration
- [ ] Install MAF SDK and dependencies
- [ ] Set up parallel testing environment
- [ ] Create feature flags in settings
- [ ] Document current AutoGen usage patterns
- [ ] Identify all AutoGen integration points

### Phase 1: Foundation
- [ ] Create `BMADMAFWrapper` class
- [ ] Implement MAF → ADK integration
- [ ] Set up MAF agent initialization
- [ ] Create basic unit tests

### Phase 2: Core Migration
- [ ] Migrate agent creation logic
- [ ] Replace GroupChat with AgentTeam
- [ ] Update handoff mechanisms
- [ ] Migrate conversation state management
- [ ] Update all agent factory methods

### Phase 3: Integration
- [ ] Integrate MAF with HITL safety controls
- [ ] Connect MAF events to WebSocket broadcasting
- [ ] Update AG-UI protocol handlers
- [ ] Migrate Celery task execution
- [ ] Update context artifact management

### Phase 4: Testing
- [ ] Run parallel AutoGen/MAF tests
- [ ] Performance benchmarking
- [ ] Load testing
- [ ] Security validation
- [ ] HITL workflow testing
- [ ] WebSocket event testing

### Phase 5: Deployment
- [ ] Deploy to staging environment
- [ ] Enable feature flag for 10% traffic
- [ ] Monitor metrics and errors
- [ ] Gradual rollout to 100%
- [ ] Remove AutoGen dependencies
- [ ] Update documentation

### Post-Migration
- [ ] Monitor production metrics for 2 weeks
- [ ] Collect team feedback
- [ ] Document lessons learned
- [ ] Archive AutoGen code
- [ ] Update architecture documentation

---

**Document Version**: 1.0  
**Last Updated**: March 10, 2025  
**Author**: BMAD Architecture Team  
**Status**: Planning Phase
