# CopilotKit ADK Integration Plan
## BMAD Enterprise AI Orchestration Platform

**Document Version:** 1.0
**Date:** October 2025
**Status:** Architecture Recommendation

---

## Executive Summary

After comprehensive analysis of CopilotKit's ADK integration capabilities and BMAD's current architecture, **significant architectural changes are warranted** to leverage native AG-UI protocol, Generative UI, and shared state management patterns. Current implementation uses custom WebSocket architecture; CopilotKit provides standardized agent-frontend communication that simplifies development and enhances user experience.

**Recommendation:** Adopt CopilotKit's native ADK integration patterns while preserving BMAD's enterprise controls (HITL, audit trails, multi-LLM support).

---

## Gap Analysis

### Current BMAD Architecture

**Strengths:**
- ✅ Robust HITL safety controls with mandatory approval workflows
- ✅ Multi-LLM provider support (OpenAI, Anthropic, Google)
- ✅ Comprehensive audit trails and enterprise compliance
- ✅ Real-time WebSocket communication with project-scoped events
- ✅ ADK integration via `BMADADKWrapper` with enterprise service integration

**Gaps vs. CopilotKit Patterns:**
- ❌ **No AG-UI Protocol**: Custom WebSocket implementation instead of standardized agent-user protocol
- ❌ **No Generative UI**: Agent progress/status rendered via custom components, not dynamic UI generation
- ❌ **No Shared State**: Frontend (Zustand) and backend (PostgreSQL) state not bidirectionally synchronized
- ❌ **No useCoAgent Hook**: Missing React hook for bidirectional agent state sharing
- ❌ **No CopilotRuntime Integration**: Backend ADK agents not exposed via CopilotRuntime
- ❌ **Manual State Management**: Frontend manually polls backend for agent status instead of streaming updates
- ❌ **Limited To-do Visibility**: Agent task lists not rendered dynamically as Generative UI components

### CopilotKit ADK Integration Benefits

**AG-UI Protocol Advantages:**
1. **Standardized Communication**: Industry-standard protocol for agent-user interactions
2. **Streaming State Updates**: Progressive agent state updates without custom WebSocket logic
3. **Framework Agnostic**: Works with LangGraph, Mastra, ADK, and custom frameworks
4. **Built-in HITL Support**: Native "Human in the Loop" interaction models

**Generative UI Advantages:**
1. **Dynamic Component Rendering**: Agent state rendered as live React components in chat
2. **Progress Visualization**: Built-in support for rendering agent task lists, progress bars, and status indicators
3. **Tool Call Visualization**: Custom UI components for agent tool executions
4. **Context-Aware Interfaces**: UI adapts to agent state changes in real-time

**Shared State Advantages:**
1. **Bidirectional Sync**: Application state and agent state synchronized automatically
2. **useCoAgent Hook**: React hook for reading/writing agent state from frontend
3. **Reduced Boilerplate**: Eliminates custom state synchronization logic
4. **Type Safety**: TypeScript interfaces for agent state contracts

---

## Proposed Architecture Changes

### Phase 1: CopilotRuntime Integration (Backend)

**Objective:** Expose ADK agents via CopilotKit's CopilotRuntime instead of custom HTTP endpoints.

**Implementation Steps:**

#### 1.1 Create CopilotRuntime Server
**File:** `backend/app/copilot/copilot_runtime_server.py`

```python
"""CopilotKit Runtime Server for BMAD ADK Agents."""

from copilotkit import CopilotKitSDK, LangGraphAgent
from fastapi import FastAPI
from app.agents.bmad_adk_wrapper import BMADADKWrapper
from app.services.hitl_safety_service import HITLSafetyService

class BMADCopilotRuntime:
    """CopilotKit runtime with BMAD enterprise controls."""

    def __init__(self):
        self.sdk = CopilotKitSDK()
        self.hitl_service = HITLSafetyService()

    async def register_agents(self):
        """Register BMAD ADK agents with CopilotRuntime."""
        # Analyst agent
        analyst_wrapper = BMADADKWrapper(
            agent_name="analyst",
            agent_type="analyst",
            instruction="You are a requirements analyst..."
        )
        await analyst_wrapper.initialize()

        # Register with CopilotRuntime using AG-UI adapter
        self.sdk.add_agent(
            name="analyst",
            agent=self._create_adk_adapter(analyst_wrapper)
        )

        # Repeat for architect, coder, tester, deployer agents

    def _create_adk_adapter(self, wrapper: BMADADKWrapper):
        """Adapter to convert BMAD ADK wrapper to AG-UI compatible agent."""
        async def agent_handler(message, state, context):
            # HITL check before execution
            if context.get("enable_hitl", True):
                approval = await self.hitl_service.create_approval_request(
                    project_id=context["project_id"],
                    task_id=context["task_id"],
                    agent_type=wrapper.agent_type,
                    request_type="PRE_EXECUTION",
                    request_data={"message": message}
                )

                if not approval.approved:
                    return {"success": False, "error": "HITL approval denied"}

            # Execute ADK agent with enterprise controls
            result = await wrapper.process_with_enterprise_controls(
                message=message,
                project_id=context["project_id"],
                task_id=context["task_id"],
                user_id=context.get("user_id")
            )

            return result

        return agent_handler
```

**SOLID Compliance:**
- **Single Responsibility:** `BMADCopilotRuntime` manages agent registration only
- **Open/Closed:** New agents added via `register_agents()` without modifying core logic
- **Dependency Inversion:** Depends on `BMADADKWrapper` abstraction, not concrete implementations

**Testing Requirements:**
- Unit tests for agent registration logic
- Integration tests for AG-UI protocol compliance
- HITL approval workflow tests with CopilotRuntime

---

#### 1.2 Add CopilotRuntime API Endpoint
**File:** `backend/app/api/copilot_runtime.py`

```python
"""CopilotKit Runtime API endpoint."""

from fastapi import APIRouter, Request
from app.copilot.copilot_runtime_server import BMADCopilotRuntime

router = APIRouter()
runtime = BMADCopilotRuntime()

@router.post("/copilotkit")
async def copilotkit_endpoint(request: Request):
    """CopilotKit GraphQL endpoint for agent communication."""
    # CopilotRuntime handles AG-UI protocol automatically
    return await runtime.sdk.handle_request(request)

@router.get("/copilotkit/health")
async def copilotkit_health():
    """Health check for CopilotRuntime."""
    return {"status": "healthy", "agents": runtime.sdk.list_agents()}
```

**API Changes:**
- New endpoint: `POST /api/v1/copilotkit` (AG-UI protocol handler)
- Deprecate: Custom task creation endpoints (Phase 3 migration)
- Maintain: HITL safety endpoints for backward compatibility

---

#### 1.3 Update FastAPI Application
**File:** `backend/app/main.py`

```python
# Add CopilotRuntime router
from app.api.copilot_runtime import router as copilot_router
app.include_router(copilot_router, prefix="/api/v1")

# Initialize CopilotRuntime on startup
@app.on_event("startup")
async def initialize_copilot_runtime():
    from app.copilot.copilot_runtime_server import runtime
    await runtime.register_agents()
    logger.info("CopilotRuntime initialized with BMAD agents")
```

---

### Phase 2: Frontend AG-UI Integration

**Objective:** Replace custom WebSocket chat with CopilotKit's AG-UI components and hooks.

**Implementation Steps:**

#### 2.1 Install CopilotKit Dependencies
**File:** `frontend/package.json`

```json
{
  "dependencies": {
    "@copilotkit/react-core": "^1.0.0",
    "@copilotkit/react-ui": "^1.0.0",
    "@copilotkit/runtime-client-gql": "^1.0.0"
  }
}
```

**Command:** `cd frontend && npm install @copilotkit/react-core @copilotkit/react-ui @copilotkit/runtime-client-gql`

---

#### 2.2 Create CopilotKit Provider Wrapper
**File:** `frontend/app/providers/copilot-provider.tsx`

```typescript
"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

interface CopilotProviderProps {
  children: React.ReactNode;
  projectId: string;
}

export function CopilotProvider({ children, projectId }: CopilotProviderProps) {
  const runtimeUrl = `http://localhost:8000/api/v1/copilotkit`;

  return (
    <CopilotKit
      runtimeUrl={runtimeUrl}
      agent="analyst" // Default agent, can be switched dynamically
      publicApiKey={process.env.NEXT_PUBLIC_COPILOT_API_KEY}
    >
      {children}
    </CopilotKit>
  );
}
```

**SOLID Compliance:**
- **Interface Segregation:** Provider exposes minimal interface (`children`, `projectId`)
- **Dependency Inversion:** Components depend on CopilotKit abstraction, not implementation details

---

#### 2.3 Replace Custom Chat with CopilotKit Chat
**File:** `frontend/components/chat/copilot-chat-v2.tsx` (new file, preserve old as `copilot-chat-legacy.tsx`)

```typescript
"use client";

import { useCopilotChat, useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useHITLStore } from "@/lib/stores/hitl-store";
import { InlineHITLApproval } from "@/components/hitl/inline-hitl-approval";

interface CopilotChatV2Props {
  projectId: string;
}

export function CopilotChatV2({ projectId }: CopilotChatV2Props) {
  const { messages, sendMessage, isLoading } = useCopilotChat();
  const { requests } = useHITLStore();

  // Shared state with agent - bidirectional sync
  const { state: agentState, setState: setAgentState } = useCoAgent({
    name: "analyst",
    initialState: {
      currentTask: null,
      todoList: [],
      progress: 0
    }
  });

  // Custom message renderer for HITL approval messages
  const renderMessage = (message: any) => {
    if (message.type === "hitl_request") {
      const request = requests.find(r => r.context?.approvalId === message.approvalId);

      return (
        <div className="hitl-message">
          <div className="message-content">{message.content}</div>
          {request && <InlineHITLApproval request={request} />}
        </div>
      );
    }

    return null; // Use default CopilotChat rendering
  };

  return (
    <div className="flex flex-col h-full">
      {/* Agent State Visualization - Generative UI */}
      <div className="agent-state-panel">
        <AgentTodoList items={agentState.todoList} progress={agentState.progress} />
        <AgentProgressBar value={agentState.progress} />
      </div>

      {/* CopilotKit Chat UI with custom HITL rendering */}
      <CopilotChat
        labels={{
          title: "BotArmy Chat",
          initial: "How can I help you build your project?"
        }}
        makeSystemMessage={(message) => renderMessage(message)}
      />
    </div>
  );
}

// Generative UI component for agent task list
function AgentTodoList({ items, progress }: { items: string[], progress: number }) {
  return (
    <div className="todo-list">
      <h3>Current Tasks</h3>
      {items.map((item, idx) => (
        <div key={idx} className="todo-item">
          <Checkbox checked={idx < progress * items.length} />
          <span>{item}</span>
        </div>
      ))}
    </div>
  );
}
```

**Benefits:**
- **Generative UI:** Agent task lists rendered dynamically from shared state
- **Shared State:** `useCoAgent` hook provides bidirectional state sync
- **HITL Integration:** Preserved BMAD's inline HITL approval components
- **Reduced Code:** Eliminates 200+ lines of custom chat/WebSocket logic

---

#### 2.4 Create Generative UI Components
**File:** `frontend/components/copilot/agent-generative-ui.tsx`

```typescript
"use client";

import { useCoAgentStateRender } from "@copilotkit/react-core";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, AlertTriangle } from "lucide-react";

/**
 * Generative UI component that renders agent state dynamically.
 * Replaces custom Process Summary with CopilotKit-powered dynamic rendering.
 */
export function AgentGenerativeUI() {
  // useCoAgentStateRender streams agent state updates and renders UI
  const { render } = useCoAgentStateRender({
    name: "analyst",
    render: (state) => {
      const { currentStage, artifacts, todoList, progress } = state;

      return (
        <Card className="agent-state-card">
          {/* Stage Progress */}
          <div className="stage-header">
            <h3>{currentStage?.name || "Initializing..."}</h3>
            <Badge>{currentStage?.status || "pending"}</Badge>
          </div>

          <Progress value={progress * 100} className="my-4" />

          {/* Dynamic To-do List */}
          <div className="todo-section">
            <h4>Current Tasks</h4>
            {todoList?.map((task, idx) => (
              <div key={idx} className="task-item">
                {task.status === "completed" ? <CheckCircle /> :
                 task.status === "in_progress" ? <Clock className="animate-spin" /> :
                 <AlertTriangle />}
                <span>{task.description}</span>
              </div>
            ))}
          </div>

          {/* Artifacts Preview */}
          <div className="artifacts-section">
            <h4>Deliverables</h4>
            {artifacts?.map((artifact, idx) => (
              <ArtifactPreview key={idx} artifact={artifact} />
            ))}
          </div>
        </Card>
      );
    }
  });

  return render;
}
```

**SOLID Compliance:**
- **Single Responsibility:** Component only renders agent state, doesn't manage state logic
- **Open/Closed:** New UI elements added without modifying core rendering logic

---

### Phase 3: Shared State Architecture

**Objective:** Implement bidirectional state synchronization between backend ADK agents and frontend UI.

**Implementation Steps:**

#### 3.1 Update ADK Wrapper for State Emission
**File:** `backend/app/agents/bmad_adk_wrapper.py` (modify existing)

```python
class BMADADKWrapper:
    """Enhanced with state emission for CopilotKit shared state."""

    async def process_with_enterprise_controls(self, message: str, project_id: str,
                                              task_id: str, user_id: Optional[str] = None,
                                              state_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process with state updates streamed to frontend via AG-UI protocol."""

        # Emit initial state
        if state_callback:
            await state_callback({
                "currentTask": message,
                "todoList": ["Initialize", "Analyze", "Generate Output"],
                "progress": 0.0,
                "status": "starting"
            })

        # Execute ADK agent
        result = await self._execute_adk_agent(message, execution_id, context)

        # Emit progress updates during execution
        if state_callback:
            await state_callback({
                "currentTask": message,
                "todoList": ["Initialize ✓", "Analyze (in progress)", "Generate Output"],
                "progress": 0.33,
                "status": "analyzing"
            })

        # Final state
        if state_callback:
            await state_callback({
                "currentTask": message,
                "todoList": ["Initialize ✓", "Analyze ✓", "Generate Output ✓"],
                "progress": 1.0,
                "status": "completed",
                "artifacts": [{"name": "Analysis Report", "url": "/artifacts/123"}]
            })

        return result
```

**State Contract (TypeScript):**
```typescript
interface AgentState {
  currentTask: string | null;
  todoList: string[];
  progress: number; // 0.0 to 1.0
  status: "idle" | "starting" | "analyzing" | "completed" | "error";
  artifacts?: Array<{ name: string; url: string; type: string }>;
}
```

---

#### 3.2 Frontend State Synchronization
**File:** `frontend/lib/hooks/use-agent-state.ts`

```typescript
import { useCoAgent } from "@copilotkit/react-core";

interface AgentState {
  currentTask: string | null;
  todoList: string[];
  progress: number;
  status: string;
  artifacts?: Array<{ name: string; url: string; type: string }>;
}

export function useAgentState(agentName: string = "analyst") {
  const { state, setState } = useCoAgent<AgentState>({
    name: agentName,
    initialState: {
      currentTask: null,
      todoList: [],
      progress: 0,
      status: "idle"
    }
  });

  // Helper methods for state updates
  const updateProgress = (progress: number) => {
    setState((prev) => ({ ...prev, progress }));
  };

  const addTodoItem = (item: string) => {
    setState((prev) => ({
      ...prev,
      todoList: [...prev.todoList, item]
    }));
  };

  const completeTodoItem = (index: number) => {
    setState((prev) => {
      const updated = [...prev.todoList];
      updated[index] = `${updated[index]} ✓`;
      return { ...prev, todoList: updated };
    });
  };

  return {
    state,
    setState,
    updateProgress,
    addTodoItem,
    completeTodoItem
  };
}
```

---

### Phase 4: HITL Integration with AG-UI

**Objective:** Preserve BMAD's HITL safety controls while using CopilotKit's native HITL patterns.

**Implementation Steps:**

#### 4.1 AG-UI HITL Adapter
**File:** `backend/app/copilot/hitl_adapter.py`

```python
"""Adapter to integrate BMAD HITL with CopilotKit's AG-UI HITL protocol."""

from copilotkit import HITLRequest, HITLResponse
from app.services.hitl_safety_service import HITLSafetyService

class BMADHITLAdapter:
    """Adapter for BMAD HITL safety controls in AG-UI protocol."""

    def __init__(self):
        self.hitl_service = HITLSafetyService()

    async def handle_hitl_request(self, request: HITLRequest) -> HITLResponse:
        """Convert AG-UI HITL request to BMAD approval request."""

        # Create BMAD HITL approval record
        approval_id = await self.hitl_service.create_approval_request(
            project_id=request.context["project_id"],
            task_id=request.context["task_id"],
            agent_type=request.agent_name,
            request_type="PRE_EXECUTION",
            request_data={
                "instructions": request.message,
                "estimated_tokens": request.estimated_tokens,
                "estimated_cost": request.estimated_cost
            }
        )

        # Wait for human approval (with timeout)
        approval = await self.hitl_service.wait_for_approval(
            approval_id, timeout_minutes=30
        )

        # Convert to AG-UI response
        return HITLResponse(
            approved=approval.status == "APPROVED",
            response_message=approval.response_message,
            metadata={
                "approval_id": str(approval_id),
                "approved_by": approval.approved_by,
                "approved_at": approval.approved_at.isoformat()
            }
        )
```

---

#### 4.2 Frontend HITL Component Integration
**File:** `frontend/components/hitl/copilot-hitl-integration.tsx`

```typescript
"use client";

import { useCopilotAction } from "@copilotkit/react-core";
import { InlineHITLApproval } from "./inline-hitl-approval";
import { useHITLStore } from "@/lib/stores/hitl-store";

/**
 * Integrates BMAD's HITL approval UI with CopilotKit's action system.
 */
export function CopilotHITLIntegration() {
  const { requests, resolveRequest } = useHITLStore();

  // Register HITL action with CopilotKit
  useCopilotAction({
    name: "request_hitl_approval",
    description: "Request human approval for agent action",
    parameters: [
      { name: "task_description", type: "string", required: true },
      { name: "estimated_cost", type: "number", required: true },
      { name: "risk_level", type: "string", enum: ["low", "medium", "high"] }
    ],
    handler: async ({ task_description, estimated_cost, risk_level }) => {
      // This handler is called when agent requests HITL approval
      // BMAD backend creates approval record via AG-UI adapter

      return {
        message: "Approval requested - waiting for human response",
        approval_pending: true
      };
    }
  });

  // Render pending HITL requests
  return (
    <div className="hitl-requests-panel">
      {requests.filter(r => r.status === "pending").map(request => (
        <InlineHITLApproval
          key={request.id}
          request={request}
          onResolve={(status, response) => {
            // Resolves both in Zustand store AND notifies CopilotKit
            resolveRequest(request.id, status, response);
          }}
        />
      ))}
    </div>
  );
}
```

---

### Phase 5: Migration Strategy

**Objective:** Gradual migration from custom architecture to CopilotKit patterns without breaking existing functionality.

**Migration Steps:**

#### 5.1 Feature Flags
**File:** `backend/app/settings.py`

```python
class Settings(BaseSettings):
    # Feature flags for gradual migration
    enable_copilotkit_runtime: bool = False  # Phase 1
    enable_copilot_chat_ui: bool = False     # Phase 2
    enable_shared_state: bool = False        # Phase 3
    enable_copilot_hitl: bool = False        # Phase 4

    # Backward compatibility
    enable_legacy_websocket: bool = True
    enable_legacy_chat: bool = True
```

#### 5.2 Parallel Deployment
**Strategy:**
1. **Week 1-2:** Deploy CopilotRuntime backend (Phase 1) with feature flag OFF
2. **Week 3-4:** Test CopilotRuntime with Postman/integration tests, enable for dev environment
3. **Week 5-6:** Deploy CopilotKit frontend (Phase 2) as `/chat-v2` route alongside existing `/chat`
4. **Week 7-8:** A/B test both chat UIs with internal users
5. **Week 9-10:** Enable shared state (Phase 3) and HITL integration (Phase 4)
6. **Week 11-12:** Full migration, deprecate legacy WebSocket/chat components

#### 5.3 Rollback Plan
**If issues arise:**
- Set feature flags to `False` immediately
- Legacy WebSocket and custom chat remain fully functional
- No database migrations required (CopilotKit uses existing tables)
- Frontend can switch between `copilot-chat.tsx` (legacy) and `copilot-chat-v2.tsx` (CopilotKit)

---

## Architecture Compliance

### SOLID Principles Review

#### Single Responsibility Principle (SRP)
- ✅ **BMADCopilotRuntime:** Manages agent registration only
- ✅ **BMADHITLAdapter:** Handles HITL protocol conversion only
- ✅ **AgentGenerativeUI:** Renders agent state only, no state management logic
- ✅ **CopilotProvider:** Provides CopilotKit context only

#### Open/Closed Principle (OCP)
- ✅ **Agent Registration:** New agents added via `register_agents()` without modifying runtime core
- ✅ **Generative UI:** New UI components added via `useCoAgentStateRender` without changing renderer
- ✅ **HITL Adapters:** New approval types handled via strategy pattern in adapter

#### Liskov Substitution Principle (LSP)
- ✅ **Agent Adapters:** `_create_adk_adapter` produces handlers compatible with AG-UI interface
- ✅ **HITL Responses:** `BMADHITLAdapter` returns standard `HITLResponse` objects

#### Interface Segregation Principle (ISP)
- ✅ **CopilotProvider Props:** Minimal interface (`children`, `projectId`) - no fat interfaces
- ✅ **useAgentState Hook:** Focused interface for state management, separate from rendering

#### Dependency Inversion Principle (DIP)
- ✅ **CopilotKit Dependency:** Frontend depends on `@copilotkit/react-core` abstraction, not implementation
- ✅ **Agent Wrapper Dependency:** CopilotRuntime depends on `BMADADKWrapper` interface, not concrete agent classes

### Service Decomposition

**New Services Created:**
1. **BMADCopilotRuntime** (Backend): Agent registration and AG-UI protocol handling
2. **BMADHITLAdapter** (Backend): HITL protocol conversion
3. **CopilotProvider** (Frontend): CopilotKit context provider
4. **useAgentState** (Frontend): Shared state management hook

**Maximum Service Size:** All services <300 LOC, compliant with BMAD standards.

---

## Testing Strategy

### Backend Testing

#### Unit Tests
**File:** `backend/tests/unit/test_copilot_runtime.py`

```python
import pytest
from app.copilot.copilot_runtime_server import BMADCopilotRuntime

@pytest.mark.asyncio
async def test_agent_registration():
    runtime = BMADCopilotRuntime()
    await runtime.register_agents()

    agents = runtime.sdk.list_agents()
    assert "analyst" in agents
    assert "architect" in agents
    assert len(agents) >= 5  # 5 BMAD core agents

@pytest.mark.asyncio
async def test_adk_adapter_hitl_integration():
    runtime = BMADCopilotRuntime()
    wrapper = BMADADKWrapper(agent_name="test", agent_type="analyst")
    await wrapper.initialize()

    adapter = runtime._create_adk_adapter(wrapper)
    result = await adapter(
        message="Test task",
        state={},
        context={"project_id": "test_proj", "task_id": "test_task", "enable_hitl": False}
    )

    assert result["success"] == True
```

#### Integration Tests
**File:** `backend/tests/integration/test_copilot_ag_ui_protocol.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_copilotkit_endpoint_ag_ui_compliance():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/copilotkit", json={
            "query": "{ agents { name status } }"  # GraphQL query
        })

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data["data"]
```

### Frontend Testing

#### Component Tests
**File:** `frontend/tests/components/copilot-chat-v2.test.tsx`

```typescript
import { render, screen } from "@testing-library/react";
import { CopilotChatV2 } from "@/components/chat/copilot-chat-v2";

describe("CopilotChatV2", () => {
  it("renders agent state panel with todo list", async () => {
    render(<CopilotChatV2 projectId="test-project" />);

    expect(screen.getByText("Current Tasks")).toBeInTheDocument();
    expect(screen.getByText("Agent State")).toBeInTheDocument();
  });

  it("displays HITL approval components for pending requests", async () => {
    // Mock HITL store with pending request
    mockHITLStore({ requests: [{ id: "req1", status: "pending" }] });

    render(<CopilotChatV2 projectId="test-project" />);

    expect(screen.getByText("Approve")).toBeInTheDocument();
    expect(screen.getByText("Reject")).toBeInTheDocument();
  });
});
```

#### Integration Tests
**File:** `frontend/tests/integration/copilot-shared-state.test.tsx`

```typescript
import { renderHook, act } from "@testing-library/react";
import { useAgentState } from "@/lib/hooks/use-agent-state";

describe("useAgentState shared state", () => {
  it("updates progress bidirectionally", async () => {
    const { result } = renderHook(() => useAgentState("analyst"));

    act(() => {
      result.current.updateProgress(0.5);
    });

    expect(result.current.state.progress).toBe(0.5);

    // Simulate backend state update via CopilotKit
    act(() => {
      result.current.setState({ progress: 0.75 });
    });

    expect(result.current.state.progress).toBe(0.75);
  });
});
```

---

## Performance Considerations

### Expected Performance Impact

**Positive:**
- ✅ **Reduced Bundle Size:** Eliminates 200+ LOC of custom WebSocket/state management code
- ✅ **Optimized State Updates:** CopilotKit uses streaming instead of polling, reducing API calls by ~80%
- ✅ **Better Caching:** AG-UI protocol includes built-in response caching

**Neutral:**
- ⚠️ **New Dependency:** CopilotKit adds ~150KB to frontend bundle (offset by removed custom code)
- ⚠️ **GraphQL Overhead:** AG-UI uses GraphQL vs. REST, minimal latency increase (~5-10ms)

**Monitoring:**
- Track frontend bundle size before/after migration
- Monitor API response times for `/copilotkit` endpoint
- Measure WebSocket message volume reduction

---

## Security & Compliance

### Security Review

#### Authentication
**Current:** Environment-based API keys
**CopilotKit:** Supports API key authentication via `publicApiKey` prop
**Action:** No changes required, maintain existing auth patterns

#### Data Privacy
**Current:** GDPR-compliant audit trails
**CopilotKit:** Agent state stored in memory (InMemorySessionService) or custom session storage
**Action:** Implement custom session service using PostgreSQL for compliance

#### HITL Safety
**Current:** Mandatory pre-execution approval
**CopilotKit:** Native HITL support via AG-UI protocol
**Action:** Use `BMADHITLAdapter` to maintain existing safety controls

---

## Cost-Benefit Analysis

### Development Effort

**Phase 1 (Backend):** 3-4 developer days
**Phase 2 (Frontend):** 4-5 developer days
**Phase 3 (Shared State):** 2-3 developer days
**Phase 4 (HITL):** 2-3 developer days
**Phase 5 (Migration):** 4-5 developer days

**Total Effort:** 15-20 developer days (~3-4 weeks with testing)

### Maintenance Reduction

**Current Custom Architecture:**
- ~500 LOC of WebSocket management code
- ~300 LOC of custom chat UI logic
- ~200 LOC of manual state synchronization
- **Total:** ~1000 LOC requiring maintenance

**CopilotKit Architecture:**
- ~150 LOC of CopilotRuntime integration
- ~100 LOC of AG-UI adapters
- ~50 LOC of shared state hooks
- **Total:** ~300 LOC (70% reduction)

**Long-term Savings:** ~15-20 developer days/year in maintenance

---

## Recommended Next Steps

1. **Approval:** Review this plan with engineering leadership and product team
2. **Proof of Concept (1 week):**
   - Implement Phase 1 (CopilotRuntime backend) with feature flag OFF
   - Test AG-UI protocol compliance with Postman
   - Validate HITL adapter with existing approval workflows
3. **Pilot Deployment (2 weeks):**
   - Implement Phase 2 (Frontend CopilotKit chat) as `/chat-v2` route
   - A/B test with 10-20 internal users
   - Collect feedback on Generative UI experience
4. **Full Migration (4 weeks):**
   - Phases 3-5 based on pilot results
   - Deprecate legacy WebSocket architecture
   - Update documentation and developer guides

---

## Critical Follow-Up Analysis

### Question 1: Orchestrator vs. CopilotKit Workflow Management

**Current BMAD Orchestrator:**
- **OrchestratorCore** delegates to 6 specialized services (ProjectLifecycleManager, AgentCoordinator, WorkflowIntegrator, etc.)
- Manages SDLC phase transitions, task queuing, agent coordination, and multi-agent workflows
- Reads YAML workflow definitions (`greenfield-fullstack.yaml`) with 17 sequential steps
- Provides dynamic phase validation, conflict resolution, and progress tracking

**CopilotKit Pattern:**
- No built-in orchestrator - agents operate independently or via simple tool chaining
- Workflow logic embedded in agent prompts/instructions, not external orchestration layer
- State coordination via shared state hooks (`useCoAgent`), not centralized orchestrator

**VERDICT: Keep Orchestrator - CopilotKit Does NOT Replace It**

**Why:**
1. **Static vs. Dynamic Workflows:** YAML workflow is prescriptive (17 steps, analyst→architect→dev sequence). CopilotKit agents are reactive (respond to user prompts, no inherent workflow).
2. **Phase Management:** Orchestrator enforces SDLC phase gates (Analyze→Design→Build→Validate→Launch). CopilotKit has no concept of project phases.
3. **Multi-Agent Coordination:** Orchestrator coordinates 5+ agents with handoffs, dependency resolution, and conflict detection. CopilotKit agents don't inherently communicate with each other.
4. **HITL Integration Points:** Orchestrator enforces HITL at specific workflow steps (e.g., "analyze-plan.md requires approval before proceeding"). CopilotKit's HITL is request-based, not workflow-aware.

**Revised Recommendation:**
- **Keep Orchestrator for Structured Workflows:** Projects following greenfield-fullstack.yaml use Orchestrator to manage sequential agent execution
- **Use CopilotKit for Ad-Hoc Agent Interactions:** User-initiated single-agent tasks (e.g., "Ask analyst to review this requirement") bypass Orchestrator and use CopilotKit directly
- **Hybrid Pattern:** Orchestrator can invoke CopilotKit-wrapped agents for execution while maintaining workflow control

**Example:**
```python
# Orchestrator invokes CopilotKit agent via AG-UI adapter
async def execute_workflow_step(self, step: WorkflowStep):
    # Orchestrator logic: validate phase, check HITL approval
    if step.requires_hitl:
        await self.hitl_service.create_approval_request(...)

    # Invoke CopilotKit-wrapped agent for execution
    result = await self.copilot_runtime.execute_agent(
        agent_name=step.agent,
        message=step.instructions,
        context=step.context
    )

    # Orchestrator logic: store artifact, update phase progress
    await self.context_store.create_artifact(result)
    await self.project_manager.update_phase_progress(...)
```

---

### Question 2: Celery Still Required?

**Current Role of Celery:**
- Asynchronous task queue for long-running agent executions (avoid HTTP timeout)
- Retry logic for failed agent tasks (5 retries with exponential backoff)
- Distributed task processing (multiple workers for parallel agent execution)
- Task status tracking and result storage via Redis backend

**CopilotKit Pattern:**
- Synchronous agent execution via AG-UI protocol (blocking HTTP/WebSocket connection)
- No built-in task queue - frontend waits for agent response
- Streaming responses via WebSocket, but still synchronous at runtime layer

**VERDICT: Celery STILL REQUIRED (Modified Role)**

**Why:**
1. **Long-Running Agents:** Some agents (architect creating fullstack-architecture.md) may take 2-5 minutes. HTTP/WebSocket timeout risks without async queue.
2. **HITL Approval Workflow:** Agent task queued → HITL approval requested → Task waits → Human approves → Agent executes. Requires async task management.
3. **Multi-Agent Orchestration:** Orchestrator submits multiple agent tasks to Celery queue for parallel execution (e.g., dev and qa agents working simultaneously).
4. **Resilience:** Celery retry logic ensures failed agent tasks don't require manual re-execution.

**Revised Architecture:**
```
User → CopilotKit Chat → CopilotRuntime → Orchestrator → Celery Queue → Agent Execution
                                                ↓
                                           HITL Approval
```

**Modified Celery Usage:**
- **Before:** Direct Celery task submission via REST API (`POST /tasks`)
- **After:** CopilotRuntime submits to Celery internally when Orchestrator detects long-running operation
- **Short Tasks:** CopilotKit executes synchronously (< 30 seconds)
- **Long Tasks:** CopilotKit delegates to Celery, streams progress via WebSocket

**Simplification Opportunity:**
- Remove `REDIS_CELERY_URL` (use single Redis DB per @REDIS_SIMPLIFICATION_PROPOSAL.md)
- Reduce Celery queue complexity (single queue: `agent_tasks`)

---

### Question 3: AG-UI Value & REST→GraphQL Implications

**AG-UI Protocol Benefits:**
1. **Streaming State Updates:** Progressive agent state without custom WebSocket event broadcasting
2. **Standardized Communication:** Industry-standard protocol reduces custom integration code
3. **Tool Call Visualization:** Built-in support for rendering agent tool executions
4. **Session Management:** Automatic conversation context handling

**GraphQL vs. REST Tradeoffs:**

| Aspect | REST (Current) | GraphQL (AG-UI) |
|--------|---------------|-----------------|
| **Endpoint Count** | 81 endpoints (13 categories) | Single `/copilotkit` endpoint |
| **Query Flexibility** | Multiple API calls for complex data | Single query fetches nested data |
| **Type Safety** | OpenAPI schema validation | GraphQL schema introspection |
| **Caching** | HTTP caching (CDN-friendly) | Query-level caching (complex) |
| **Learning Curve** | Familiar for most developers | GraphQL expertise required |
| **Tooling** | Postman, curl, standard HTTP tools | GraphQL clients (Apollo, Relay) |

**VERDICT: AG-UI Provides Moderate Value - REST→GraphQL is ACCEPTABLE**

**Why AG-UI is Worth It:**
- Eliminates 200+ LOC of custom WebSocket state synchronization
- Generative UI for agent progress reduces frontend complexity
- Streaming agent state is difficult to replicate with REST

**Why GraphQL is Acceptable:**
- Only ONE GraphQL endpoint (`/copilotkit`) coexists with 81 REST endpoints
- REST APIs remain for non-agent operations (projects, artifacts, health checks)
- CopilotKit provides GraphQL client libraries (minimal custom code)
- GraphQL complexity isolated to AG-UI integration, not entire backend

**Revised Recommendation:**
- **Hybrid API Architecture:** Keep REST for CRUD operations, use GraphQL only for AG-UI protocol
- **No REST Deprecation:** 81 existing endpoints remain for backward compatibility and non-CopilotKit clients
- **Example:**
  - `POST /api/v1/projects` (REST) - Create project
  - `POST /api/v1/copilotkit` (GraphQL) - Agent communication
  - `GET /api/v1/projects/{id}/artifacts` (REST) - Fetch artifacts

---

### Question 4: HITL Simplification Opportunities

**Current HITL Complexity:**
- Dual approval types: `PRE_EXECUTION` and `RESPONSE_APPROVAL` (October 2025 fix removed redundant RESPONSE_APPROVAL)
- Database table: `hitl_agent_approvals` with 12 columns
- Frontend store: 30-minute request expiration, automatic cleanup, error recovery
- WebSocket events: `HITL_REQUEST_CREATED`, status updates, project-scoped broadcasting
- Alert bar navigation: Direct routing to specific HITL messages with visual highlighting

**Simplification Options:**

#### Option A: Remove HITL Entirely
**Impact:** ❌ **UNACCEPTABLE** - HITL is core enterprise safety feature
**Risk:** Uncontrolled agent spending, dangerous operations without oversight

#### Option B: Simplified HITL with Toggle & Auto-Approve Counter (RECOMMENDED)
**User-Controlled HITL Approach - Maximum Simplification**

**Core Concept:**
- Move HITL control to user settings instead of complex per-request approval workflow
- Toggle-based enable/disable for immediate control
- Counter-based auto-approve mechanism for batch workflows
- Remove cost estimation and priority complexity entirely

**Changes:**

1. **HITL Toggle Control (Chat Window & Settings)**
   - **Enabled:** Every agent action requires explicit user approval before execution
   - **Disabled:** Agents execute autonomously without approval prompts
   - Toggle visible in chat header for quick switching
   - Persistent setting stored per user/project

2. **Auto-Approve Counter (Batch Mode)**
   - **Counter Variable:** Set number of agent actions that can run automatically before requiring approval
   - **Example:** Counter = 5 → Agents execute 5 tasks → Pause for approval → User resets counter → Agents continue
   - **In-Chat Prompt:** When counter reaches zero, display compact inline message:
     ```
     🛑 Auto-approve limit reached (5/5 tasks completed)

     Run for [  5  ] more tasks  [Continue]    HITL: [Toggle Switch]
     ```
     - **Inline Input:** User types number directly in input field before continuing
     - **Toggle Next To Action:** HITL enable/disable switch immediately adjacent to Continue button
     - **Streamlined UX:** Single-line control reduces visual clutter
   - **Settings Integration:** Counter variable adjustable in Settings page (default: 10)
   - **Use Case:** Long workflows (17-step greenfield-fullstack.yaml) benefit from batch auto-approval

3. **Remove Complexity:**
   - ❌ **Eliminate:** `estimated_tokens`, `estimated_cost` fields (no cost calculation overhead)
   - ❌ **Eliminate:** Priority levels (high/medium/low) - all requests equal
   - ❌ **Eliminate:** 30-minute expiration logic - counter/toggle is immediate
   - ✅ **RETAIN (Enhanced):** Alert bar for **dual-purpose HITL notifications:**
     - **Type 1:** Counter exhausted (planned pause) → "Project X: Reset counter to continue"
     - **Type 2:** Explicit approval request (safety-critical) → "Project X: Agent requests approval for [action]"
   - ⚠️ **HYBRID:** Minimal per-request tracking **only** for explicit approval requests (not counter exhaustion)

4. **Emergency Stop Control:**
   - **Stop Button:** Visible in chat when HITL disabled and tasks running
   - **Immediate Task Cancellation:** Stops current agent execution and clears queue
   - **Counter Preserved:** Resume point maintained after stop

**Architecture Simplification:**

**Before (14 components):**
- `hitl_agent_approvals` table (12 columns)
- `HITLSafetyService` (5 sub-services: Core, TriggerProcessor, ResponseProcessor, PhaseGateManager, ValidationEngine)
- `hitl-store.ts` with expiration/cleanup/navigation
- `hitl-alerts-bar.tsx` with project routing
- `inline-hitl-approval.tsx` with cost/priority display
- WebSocket event handling (HITL_REQUEST_CREATED, status updates)
- Badge utility system
- Budget control system (AgentBudgetControlDB)

**After (8 components - Dual-Purpose Alert System):**
- `hitl_settings` table (5 columns: `project_id`, `user_id`, `hitl_enabled`, `auto_approve_counter`, `actions_remaining`)
- `hitl_approval_requests` table (6 columns: `id`, `project_id`, `task_id`, `agent_type`, `request_reason`, `status`)
  - **Purpose:** Track **explicit approval requests only** (not counter exhaustion)
  - **Lightweight:** No cost/priority/expiration fields
- `HITLToggleService` (single service, ~200 LOC)
  - `check_hitl_required(project_id, user_id) → dict`
  - `create_approval_request(project_id, task_id, reason) → request_id` (explicit approvals only)
  - `resolve_approval(request_id, approved) → bool`
  - `reset_counter(project_id, user_id, new_value) → int`
  - `toggle_hitl(project_id, user_id, enabled) → bool`
  - `get_pending_alerts() → List[alert]` (both types for alert bar)
- `hitl-store.ts` (dual-purpose alert state)
  - `pendingAlerts: Array<{type, project_id, data}>`
  - `addAlert(type, project_id, data)`
  - `removeAlert(alert_id)`
- `hitl-alerts-bar.tsx` (dual-purpose: counter exhaustion + explicit approvals)
- `hitl-toggle.tsx` (chat header toggle component)
- `hitl-counter-prompt.tsx` (inline counter reset prompt)
- `hitl-approval-prompt.tsx` (inline explicit approval prompt with approve/reject)
- `hitl-stop-button.tsx` (emergency stop for running tasks)
- `hitl-settings-panel.tsx` (settings page configuration)

**Estimated Reduction:** **55% less HITL code (~400 LOC removed)** - retains lightweight approval tracking for safety-critical requests

**Database Schema:**

```sql
-- HITL settings for toggle and counter
CREATE TABLE hitl_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL DEFAULT 'default',
    hitl_enabled BOOLEAN NOT NULL DEFAULT true,
    auto_approve_counter INTEGER NOT NULL DEFAULT 10,
    actions_remaining INTEGER NOT NULL DEFAULT 10,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);

CREATE INDEX idx_hitl_settings_project ON hitl_settings(project_id);

-- Lightweight approval requests (explicit approvals only, NOT counter exhaustion)
CREATE TABLE hitl_approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    request_reason TEXT NOT NULL,  -- Why approval needed (e.g., "Delete production database")
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, approved, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX idx_hitl_approvals_project ON hitl_approval_requests(project_id);
CREATE INDEX idx_hitl_approvals_status ON hitl_approval_requests(status);
```

**Key Difference from Original:**
- **hitl_approval_requests:** Only 6 columns (vs original 12)
- **No cost/priority/expiration:** Removed complexity
- **Purpose-specific:** Only for **explicit agent/orchestrator requests**, NOT counter exhaustion
- **Counter exhaustion:** Handled entirely via `hitl_settings.actions_remaining` (no approval record)

**Frontend Implementation:**

```typescript
// hitl-toggle.tsx - Chat header toggle
interface HITLToggleProps {
  projectId: string;
  userId: string;
}

export function HITLToggle({ projectId, userId }: HITLToggleProps) {
  const [enabled, setEnabled] = useState(true);
  const [counter, setCounter] = useState(10);
  const [remaining, setRemaining] = useState(10);

  return (
    <div className="hitl-controls">
      <Switch
        checked={enabled}
        onCheckedChange={async (checked) => {
          await api.toggleHITL(projectId, userId, checked);
          setEnabled(checked);
        }}
      />
      <Badge variant={enabled ? "destructive" : "success"}>
        {enabled ? "HITL ON" : "HITL OFF"}
      </Badge>
      {!enabled && (
        <Badge variant="outline">
          Auto: {remaining}/{counter} remaining
        </Badge>
      )}
    </div>
  );
}
```

```typescript
// hitl-counter-prompt.tsx - Streamlined inline counter reset
export function HITLCounterPrompt({ projectId, userId, counter, onReset, onToggle }: Props) {
  const [inputValue, setInputValue] = useState(counter.toString());

  return (
    <div className="hitl-counter-prompt flex items-center gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
      <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />

      <p className="text-sm font-medium text-amber-900">
        🛑 Auto-approve limit reached ({counter}/{counter} tasks completed)
      </p>

      <div className="flex items-center gap-2 ml-auto">
        <span className="text-sm text-gray-600">Run for</span>

        <Input
          type="number"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          className="w-16 h-8 text-center"
          min="1"
          max="999"
        />

        <span className="text-sm text-gray-600">more tasks</span>

        <Button
          size="sm"
          onClick={() => onReset(parseInt(inputValue) || counter)}
        >
          Continue
        </Button>

        <Separator orientation="vertical" className="h-6" />

        <span className="text-sm text-gray-600">HITL:</span>

        <Switch
          checked={false}  // Currently disabled if counter is active
          onCheckedChange={onToggle}
        />
      </div>
    </div>
  );
}
```

```typescript
// hitl-stop-button.tsx - Emergency stop for running tasks
export function HITLStopButton({ projectId, onStop }: Props) {
  const [isRunning, setIsRunning] = useState(false);
  const [hitlEnabled, setHitlEnabled] = useState(false);

  // Only show stop button when HITL is disabled AND tasks are running
  if (hitlEnabled || !isRunning) return null;

  return (
    <Button
      variant="destructive"
      size="sm"
      onClick={async () => {
        await api.stopAgentTasks(projectId);
        setIsRunning(false);
      }}
      className="flex items-center gap-2"
    >
      <StopCircle className="w-4 h-4" />
      Stop Tasks
    </Button>
  );
}
```

**Backend Implementation (Simplified Store):**

```python
# app/services/hitl_toggle_service.py
class HITLToggleService:
    """Simplified HITL control via toggle and counter."""

    def __init__(self, db: Session):
        self.db = db

    def check_hitl_required(self, project_id: UUID, user_id: str = "default") -> dict:
        """
        Check if HITL approval is required for next action.
        Returns dict with status and metadata for frontend.
        """
        settings = self._get_or_create_settings(project_id, user_id)

        # If HITL explicitly enabled, always require approval
        if settings.hitl_enabled:
            return {
                "required": True,
                "reason": "hitl_enabled",
                "remaining": 0,
                "total": settings.auto_approve_counter
            }

        # If disabled, check counter
        if settings.actions_remaining > 0:
            # Decrement counter and allow execution
            settings.actions_remaining -= 1
            self.db.commit()

            # Broadcast counter update to frontend (lightweight event)
            if settings.actions_remaining == 0:
                websocket_manager.broadcast_event(WebSocketEvent(
                    event_type=EventType.HITL_COUNTER_EXHAUSTED,
                    data={"project_id": str(project_id), "counter": settings.auto_approve_counter}
                ))

            return {
                "required": False,
                "reason": "counter_available",
                "remaining": settings.actions_remaining,
                "total": settings.auto_approve_counter
            }
        else:
            # Counter exhausted - require reset
            return {
                "required": True,
                "reason": "counter_exhausted",
                "remaining": 0,
                "total": settings.auto_approve_counter
            }

    def reset_counter(self, project_id: UUID, user_id: str, new_value: int):
        """Reset auto-approve counter with new value."""
        settings = self._get_or_create_settings(project_id, user_id)
        settings.auto_approve_counter = new_value
        settings.actions_remaining = new_value
        self.db.commit()
        return {"remaining": new_value, "total": new_value}

    def toggle_hitl(self, project_id: UUID, user_id: str, enabled: bool):
        """Toggle HITL on/off."""
        settings = self._get_or_create_settings(project_id, user_id)
        settings.hitl_enabled = enabled
        self.db.commit()
        return {"enabled": enabled}

    def create_approval_request(self, project_id: UUID, task_id: UUID,
                                agent_type: str, reason: str) -> UUID:
        """
        Create explicit approval request (safety-critical actions only).
        NOT used for counter exhaustion - only for agent/orchestrator-initiated requests.
        """
        request = HITLApprovalRequestDB(
            project_id=project_id,
            task_id=task_id,
            agent_type=agent_type,
            request_reason=reason,
            status="pending"
        )
        self.db.add(request)
        self.db.commit()

        # Broadcast to alert bar
        websocket_manager.broadcast_event(WebSocketEvent(
            event_type=EventType.HITL_APPROVAL_REQUESTED,
            data={
                "project_id": str(project_id),
                "request_id": str(request.id),
                "agent_type": agent_type,
                "reason": reason
            }
        ))

        return request.id

    def resolve_approval(self, request_id: UUID, approved: bool) -> bool:
        """Resolve explicit approval request."""
        request = self.db.query(HITLApprovalRequestDB).get(request_id)
        if not request:
            return False

        request.status = "approved" if approved else "rejected"
        request.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def get_pending_alerts(self, user_id: str = "default") -> List[dict]:
        """
        Get ALL pending HITL alerts for alert bar (both types).
        Returns unified alert list combining counter exhaustion + explicit approvals.
        """
        alerts = []

        # Type 1: Counter exhausted (settings-based)
        counter_exhausted = self.db.query(HITLSettingsDB).filter(
            HITLSettingsDB.user_id == user_id,
            HITLSettingsDB.hitl_enabled == False,
            HITLSettingsDB.actions_remaining == 0
        ).all()

        for setting in counter_exhausted:
            alerts.append({
                "type": "counter_exhausted",
                "project_id": str(setting.project_id),
                "project_name": setting.project.name,
                "data": {"counter": setting.auto_approve_counter}
            })

        # Type 2: Explicit approval requests
        approval_requests = self.db.query(HITLApprovalRequestDB).filter(
            HITLApprovalRequestDB.status == "pending"
        ).all()

        for request in approval_requests:
            alerts.append({
                "type": "approval_request",
                "project_id": str(request.project_id),
                "project_name": request.project.name,
                "data": {
                    "request_id": str(request.id),
                    "agent_type": request.agent_type,
                    "reason": request.request_reason,
                    "task_id": str(request.task_id)
                }
            })

        return alerts

    def stop_agent_tasks(self, project_id: UUID):
        """Emergency stop for running agent tasks."""
        # Cancel Celery tasks for this project
        from app.tasks.celery_app import celery_app
        celery_app.control.revoke_by_project(str(project_id), terminate=True)

        # Update task statuses to CANCELLED
        self.db.query(TaskDB).filter(
            TaskDB.project_id == project_id,
            TaskDB.status.in_(["PENDING", "WORKING"])
        ).update({"status": "CANCELLED"})
        self.db.commit()
```

**Frontend Store (Dual-Purpose Alerts):**

```typescript
// lib/stores/hitl-store.ts - Handles both counter exhaustion + explicit approvals
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface HITLAlert {
  type: 'counter_exhausted' | 'approval_request';
  projectId: string;
  projectName: string;
  data: {
    // For counter_exhausted
    counter?: number;
    // For approval_request
    requestId?: string;
    agentType?: string;
    reason?: string;
    taskId?: string;
  };
}

interface HITLStore {
  pendingAlerts: HITLAlert[];

  // Alert bar management (both types)
  addAlert: (alert: HITLAlert) => void;
  removeAlert: (projectId: string, requestId?: string) => void;
  refreshAlerts: () => Promise<void>;

  // Approval actions (for explicit requests)
  approveRequest: (requestId: string) => Promise<void>;
  rejectRequest: (requestId: string) => Promise<void>;

  // Counter actions (for exhausted counters)
  resetCounter: (projectId: string, newValue: number) => Promise<void>;
}

export const useHITLStore = create<HITLStore>()(
  persist(
    (set, get) => ({
      pendingAlerts: [],

      addAlert: (alert) => {
        set((state) => {
          // Remove existing alert for same project/request before adding
          const filtered = state.pendingAlerts.filter(a => {
            if (alert.type === 'counter_exhausted') {
              return !(a.type === 'counter_exhausted' && a.projectId === alert.projectId);
            } else {
              return a.data.requestId !== alert.data.requestId;
            }
          });
          return { pendingAlerts: [...filtered, alert] };
        });
      },

      removeAlert: (projectId, requestId) => {
        set((state) => ({
          pendingAlerts: state.pendingAlerts.filter(a => {
            if (requestId) {
              return a.data.requestId !== requestId;
            } else {
              return !(a.type === 'counter_exhausted' && a.projectId === projectId);
            }
          })
        }));
      },

      refreshAlerts: async () => {
        const response = await fetch('/api/v1/hitl/pending-alerts');
        const alerts = await response.json();
        set({ pendingAlerts: alerts });
      },

      approveRequest: async (requestId) => {
        await fetch(`/api/v1/hitl/approvals/${requestId}`, {
          method: 'POST',
          body: JSON.stringify({ approved: true })
        });
        get().removeAlert('', requestId);
      },

      rejectRequest: async (requestId) => {
        await fetch(`/api/v1/hitl/approvals/${requestId}`, {
          method: 'POST',
          body: JSON.stringify({ approved: false })
        });
        get().removeAlert('', requestId);
      },

      resetCounter: async (projectId, newValue) => {
        await fetch(`/api/v1/hitl/counter/${projectId}`, {
          method: 'POST',
          body: JSON.stringify({ counter: newValue })
        });
        get().removeAlert(projectId);
      }
    }),
    {
      name: 'hitl-store',
      partialize: (state) => ({ pendingAlerts: state.pendingAlerts })
    }
  )
);

// Auto-refresh alerts every 30 seconds
setInterval(() => {
  useHITLStore.getState().refreshAlerts();
}, 30000);
```

**Alert Bar (Dual-Purpose: Counter + Explicit Approvals):**

```typescript
// components/hitl/hitl-alerts-bar.tsx
export function HITLAlertsBar() {
  const { pendingAlerts, removeAlert } = useHITLStore();
  const router = useRouter();

  if (pendingAlerts.length === 0) return null;

  // Separate alerts by type for visual distinction
  const counterAlerts = pendingAlerts.filter(a => a.type === 'counter_exhausted');
  const approvalAlerts = pendingAlerts.filter(a => a.type === 'approval_request');

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex flex-col">
      {/* Approval requests (red - higher priority) */}
      {approvalAlerts.length > 0 && (
        <div className="bg-red-600 text-white px-4 py-2 flex items-center gap-4">
          <ShieldAlert className="w-5 h-5" />

          <span className="font-medium">
            {approvalAlerts.length} agent approval{approvalAlerts.length > 1 ? 's' : ''} required
          </span>

          <div className="flex gap-2 ml-auto">
            {approvalAlerts.map((alert) => (
              <Button
                key={alert.data.requestId}
                variant="secondary"
                size="sm"
                onClick={() => {
                  router.push(`/projects/${alert.projectId}`);
                  // Don't remove - let user approve/reject in project view
                }}
              >
                {alert.projectName}: {alert.data.agentType} - {alert.data.reason}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Counter exhausted (amber - lower priority) */}
      {counterAlerts.length > 0 && (
        <div className="bg-amber-500 text-white px-4 py-2 flex items-center gap-4">
          <AlertCircle className="w-5 h-5" />

          <span className="font-medium">
            {counterAlerts.length} project{counterAlerts.length > 1 ? 's' : ''} awaiting counter reset
          </span>

          <div className="flex gap-2 ml-auto">
            {counterAlerts.map((alert) => (
              <Button
                key={alert.projectId}
                variant="secondary"
                size="sm"
                onClick={() => {
                  router.push(`/projects/${alert.projectId}`);
                  // Don't remove - let user reset counter in project view
                }}
              >
                {alert.projectName} ({alert.data.counter} tasks)
              </Button>
            ))}
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              // Dismiss counter alerts only (don't dismiss approval requests)
              counterAlerts.forEach(a => removeAlert(a.projectId));
            }}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
```

**Additional Component: Explicit Approval Prompt**

```typescript
// components/hitl/hitl-approval-prompt.tsx - For explicit approval requests in chat
interface HITLApprovalPromptProps {
  requestId: string;
  agentType: string;
  reason: string;
  taskId: string;
}

export function HITLApprovalPrompt({ requestId, agentType, reason, taskId }: HITLApprovalPromptProps) {
  const { approveRequest, rejectRequest } = useHITLStore();
  const [isResolving, setIsResolving] = useState(false);

  return (
    <div className="hitl-approval-prompt flex flex-col gap-3 p-4 bg-red-50 border-2 border-red-200 rounded-lg">
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0" />
        <p className="text-sm font-bold text-red-900">
          🚨 Agent Approval Required
        </p>
      </div>

      <div className="text-sm text-gray-700">
        <p><strong>Agent:</strong> {agentType}</p>
        <p><strong>Task:</strong> {taskId.slice(-8)}</p>
        <p><strong>Reason:</strong> {reason}</p>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="destructive"
          size="sm"
          onClick={async () => {
            setIsResolving(true);
            await rejectRequest(requestId);
          }}
          disabled={isResolving}
        >
          <X className="w-4 h-4 mr-1" />
          Reject
        </Button>

        <Button
          variant="default"
          size="sm"
          onClick={async () => {
            setIsResolving(true);
            await approveRequest(requestId);
          }}
          disabled={isResolving}
        >
          <Check className="w-4 h-4 mr-1" />
          Approve
        </Button>

        <span className="text-xs text-gray-500 ml-auto">
          Task will wait for your decision
        </span>
      </div>
    </div>
  );
}
```

**Agent Task Execution Integration:**

```python
# app/tasks/agent_tasks.py (modified)
@celery_app.task
def process_agent_task(self, task_data: Dict[str, Any]):
    """Process agent task with simplified HITL check."""

    # Simplified HITL check - single method call
    hitl_service = HITLToggleService(db)
    if hitl_service.check_hitl_required(project_id, user_id):
        # Wait for user to approve (toggle ON or reset counter)
        while hitl_service.check_hitl_required(project_id, user_id):
            await asyncio.sleep(2)  # Poll every 2 seconds

            # Check for timeout (30 min)
            if (datetime.now() - start_time).seconds > 1800:
                raise ApprovalTimeoutError("HITL approval timeout")

    # Execute agent task
    result = await agent.execute(task_data)
    return result
```

**Benefits:**

1. **Massive Complexity Reduction:**
   - No per-request approval records in database
   - No cost estimation or budget tracking overhead
   - No WebSocket events for approval workflow
   - No expiration/cleanup logic
   - **65% less code** (~500 LOC removed)

2. **Superior User Experience:**
   - **Toggle Control:** Instant enable/disable without navigating away from chat
   - **Batch Mode:** Set counter to 50, agents execute 50 tasks autonomously
   - **Transparent:** Counter status always visible in chat header
   - **Flexible:** Adjust counter mid-workflow based on confidence level

3. **Workflow Optimization:**
   - **Long Workflows:** greenfield-fullstack.yaml (17 steps) benefits from counter = 17 (approve once)
   - **Exploratory Mode:** Set counter = 5 for cautious exploration, increase to 20 when confident
   - **Production Safety:** Enable HITL toggle for production deployments, disable for dev/test

4. **Development Simplicity:**
   - Single database table (5 columns vs 12)
   - Single service (~150 LOC vs 5 services with 600+ LOC)
   - No complex state management in frontend
   - Minimal integration with CopilotKit (just check before agent execution)

5. **SOLID Compliance:**
   - **SRP:** HITLToggleService has single responsibility (manage settings)
   - **OCP:** Toggle/counter mechanism extensible without modifying core logic
   - **DIP:** Agent tasks depend on HITLToggleService abstraction

**Migration Strategy:**

1. **Create `hitl_settings` table** via Alembic migration
2. **Migrate existing HITL preferences:** Convert current HITL enabled/disabled state to toggle settings
3. **Deprecate `hitl_agent_approvals` table:** No longer needed for approval tracking
4. **Update frontend:** Replace complex HITL components with toggle + counter prompt
5. **Simplify backend:** Replace HITLSafetyService (5 services) with HITLToggleService (1 service)

**Estimated Migration Effort:** 2 days (vs 3-4 days for Option B partial simplification)

#### Option C: CopilotKit Native HITL (Experimental)
**Use CopilotKit's built-in HITL protocol instead of custom implementation**

**Benefits:**
- Eliminates custom HITL database table
- Uses AG-UI's native approval request mechanism
- Reduces integration code

**Risks:**
- CopilotKit's HITL may not support enterprise features (budget tracking, audit trails)
- Less control over approval workflow
- May not integrate with existing HITL history/reporting

**Verdict:** **Option B (Toggle + Counter HITL) STRONGLY RECOMMENDED**
- **65% complexity reduction** vs 40% for original Option B
- Preserves enterprise safety controls (toggle = mandatory approval)
- Superior UX for batch workflows (counter = approve once, run 17 steps)
- Minimal integration complexity with CopilotKit (single service, no WebSocket events)
- Compatible with both CopilotKit and Orchestrator patterns
- Eliminates cost/priority tracking overhead entirely

---

### Question 5: Redis Simplification Impact on CopilotKit

**Redis Simplification Proposal:**
- Consolidate from 2 Redis databases (DB0: WebSocket, DB1: Celery) to single DB0
- Use key prefixes for logical separation instead of database separation
- Simplify configuration from 3+ environment variables to single `REDIS_URL`

**CopilotKit Redis Usage:**
- Session storage: `InMemorySessionService` (default) or custom `SessionService`
- Agent state caching: Optional Redis-based session service
- AG-UI protocol: Does not mandate specific Redis configuration

**VERDICT: Redis Simplification HIGHLY COMPATIBLE with CopilotKit**

**Why:**
1. **No Conflict:** CopilotKit's session data uses different key patterns than Celery/WebSocket
2. **Performance:** Single Redis database has no performance penalty for BMAD's scale
3. **Simplification Benefit:** Eliminates #1 recurring configuration issue (Celery worker DB mismatch)
4. **CopilotKit Session Service:** Can be configured to use single Redis DB with custom prefix

**Revised Configuration:**
```python
# settings.py - SINGLE Redis configuration
class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"  # Single DB for all services

    # Key prefixes for logical separation
    redis_websocket_prefix: str = "ws:"
    redis_celery_prefix: str = "celery:"
    redis_copilotkit_prefix: str = "copilot:"
```

```python
# CopilotKit session service configuration
from copilotkit import RedisSessionService

session_service = RedisSessionService(
    redis_url=settings.redis_url,
    key_prefix=settings.redis_copilotkit_prefix
)

runtime = CopilotKitSDK(session_service=session_service)
```

**Implementation Priority:**
1. ✅ **IMMEDIATE:** Implement Redis simplification (fixes recurring Celery issues)
2. ⏳ **THEN:** Integrate CopilotKit with simplified Redis configuration
3. ✅ **BENEFIT:** No need to reconfigure Redis when adding CopilotKit

**Estimated Impact:**
- **Before:** 3 Redis URLs, 2 databases, complex worker commands
- **After:** 1 Redis URL, 1 database, simple worker command: `celery worker`
- **CopilotKit Compatibility:** 100% - works with any Redis configuration

---

## Revised Conclusion & Recommendations

After critical analysis, CopilotKit integration provides **MODERATE-TO-HIGH** value but requires **SIGNIFICANT ARCHITECTURAL CHANGES** to original proposal:

### Revised Architecture Pattern: **Orchestrator + CopilotKit Hybrid**

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend: CopilotKit Chat UI                               │
│  - useCoAgent for shared state                              │
│  - Generative UI for agent progress                         │
│  - Inline HITL approval (simplified)                        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ↓ (AG-UI Protocol / GraphQL)
┌─────────────────────────────────────────────────────────────┐
│  CopilotRuntime (NEW)                                       │
│  - AG-UI protocol handler                                   │
│  - Routes to Orchestrator OR direct agent execution         │
└─────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ↓                                 ↓
┌───────────────────┐         ┌──────────────────────┐
│  Orchestrator     │         │  Direct Agent Call   │
│  (KEEP - Needed)  │         │  (Ad-Hoc Tasks)      │
│                   │         │                      │
│  - YAML Workflows │         │  - Single agent      │
│  - Phase Gates    │         │  - < 30s execution   │
│  - Multi-Agent    │         │  - No workflow       │
│  - Conflict Res.  │         └──────────────────────┘
└───────────────────┘
        ↓
┌───────────────────┐
│  Celery Queue     │
│  (KEEP - Needed)  │
│                   │
│  - Long tasks     │
│  - HITL waits     │
│  - Retry logic    │
│  - Parallel exec  │
└───────────────────┘
        ↓
┌───────────────────┐
│  Redis (DB 0)     │
│  (SIMPLIFY)       │
│                   │
│  - Single DB      │
│  - Key prefixes   │
│  - Celery+WS+CK   │
└───────────────────┘
```

### Revised Recommendation Matrix

| Component | Action | Reason |
|-----------|--------|--------|
| **Orchestrator** | ✅ **KEEP** | Required for YAML workflow execution, phase management, multi-agent coordination |
| **Celery** | ✅ **KEEP** | Required for long-running agents, HITL approval waits, async task processing |
| **CopilotKit** | ✅ **ADOPT** | Simplifies frontend chat UI, provides Generative UI, reduces WebSocket code by 70% |
| **AG-UI Protocol** | ✅ **ADOPT** | Standardized communication, streaming state updates, worth GraphQL addition |
| **REST APIs** | ✅ **KEEP** | Maintain 81 existing endpoints for backward compatibility and non-agent operations |
| **HITL** | ⚠️ **SIMPLIFY** | Toggle + Counter approach: Reduce from 14 to 6 components (65% reduction), remove cost/priority/expiration, keep safety via toggle |
| **Redis** | ✅ **SIMPLIFY** | Consolidate to single DB0, eliminate recurring Celery misconfiguration issue |

### Revised Implementation Effort

| Phase | Effort | Priority |
|-------|--------|----------|
| **Phase 0: Redis Simplification** | 1 day | 🔴 **CRITICAL** (Fixes recurring issues) |
| **Phase 1: CopilotRuntime + Orchestrator Integration** | 4-5 days | 🟠 **HIGH** |
| **Phase 2: Frontend CopilotKit Chat** | 4-5 days | 🟠 **HIGH** |
| **Phase 3: Shared State & Generative UI** | 3-4 days | 🟡 **MEDIUM** |
| **Phase 4: HITL Simplification (Toggle + Counter)** | 2 days | 🟠 **HIGH** (65% reduction) |
| **Phase 5: Migration & Testing** | 4-5 days | 🟢 **LOW** |

**Total Revised Effort:** 17-26 developer days (~3.5-5 weeks) - HITL simplification saves 1 day

### Key Differences from Original Proposal

1. **Orchestrator Retained:** Original proposal didn't address Orchestrator role. Revised plan integrates Orchestrator with CopilotKit.
2. **Celery Retained:** Original plan ambiguous on Celery. Revised plan confirms Celery necessity for async operations.
3. **Redis Simplification Added:** New Phase 0 implements critical Redis configuration fix before CopilotKit integration.
4. **HITL Simplified:** Reduces HITL complexity by 40% while preserving safety controls.
5. **Hybrid REST/GraphQL:** Clarifies that REST endpoints remain, GraphQL only for AG-UI protocol.

### Final Recommendation

**PROCEED with CopilotKit integration using revised Orchestrator+CopilotKit hybrid pattern, AFTER completing Redis simplification (Phase 0).**

**Critical Success Factors:**
1. ✅ Complete Redis simplification first (prevents Celery issues during CopilotKit rollout)
2. ✅ Preserve Orchestrator for structured workflows (don't assume CopilotKit replaces it)
3. ✅ Keep Celery for async operations (essential for HITL and long-running agents)
4. ✅ Simplify HITL before integration (reduces migration complexity)
5. ✅ Maintain REST APIs alongside GraphQL (backward compatibility)

**Expected Outcomes:**
- 70% reduction in custom WebSocket/chat code
- Improved agent progress visibility via Generative UI
- Eliminated Celery configuration issues via Redis simplification
- Preserved enterprise controls (Orchestrator, HITL, audit trails)
- Maintained flexibility for both structured workflows and ad-hoc agent tasks

---

## Appendix A: Workflow Architecture Refactoring (CRITICAL)

### Current Problem: 5 Duplicate `WorkflowStep` Classes

**Root Cause Analysis:**
```bash
# FIVE different WorkflowStep classes found!
backend/app/workflows/adk_workflow_templates.py:  class WorkflowStep (dataclass)
backend/app/utils/yaml_parser.py:                 class WorkflowStep (Pydantic)
backend/app/models/workflow_state.py:             class WorkflowStepExecutionState (Pydantic)
backend/app/models/workflow.py:                   class WorkflowStep (Pydantic)
backend/app/services/workflow_step_processor.py:  class WorkflowStepProcessor (service)
```

**Why This Happened:**
1. **Historical Accumulation:** ADK integration added `adk_workflow_templates.py` without consolidating with existing YAML-based workflows
2. **Separation of Concerns Gone Wrong:** Execution state separated from step definition, but duplicated across `workflow.py` and `workflow_state.py`
3. **YAML Parser Independence:** YAML parser defines its own `WorkflowStep` for parsing greenfield-fullstack.yaml, not reusing model
4. **Missing Single Source of Truth:** No canonical `WorkflowStep` model that all services reference

### Impact Assessment

**Complexity Cost:**
- **~2500 LOC** across 15 workflow-related files
- **5 competing definitions** of essentially the same concept
- **3 workflow engines:** `workflow_engine.py` (backward compat alias), `workflow/execution_engine.py`, `workflow_service.py`
- **Developer Confusion:** Which `WorkflowStep` to use when adding new features?
- **Maintenance Burden:** Bug fixes must be applied to multiple classes

**Current Workflow Files:**
```
app/workflows/adk_workflow_templates.py           (ADK-specific workflows)
app/workflows/greenfield-fullstack.yaml           (YAML workflow definition)
app/models/workflow.py                            (Pydantic models)
app/models/workflow_state.py                      (Execution state models)
app/utils/yaml_parser.py                          (YAML parsing with own models)
app/services/workflow_engine.py                   (Backward compat alias)
app/services/workflow_service.py                  (Main workflow service)
app/services/workflow_execution_manager.py
app/services/workflow_persistence_manager.py
app/services/workflow_step_processor.py
app/services/workflow_hitl_integrator.py
app/services/workflow/execution_engine.py         (Refactored engine)
app/services/workflow/state_manager.py
app/services/workflow/event_dispatcher.py
app/services/workflow/sdlc_orchestrator.py
app/services/orchestrator/workflow_integrator.py  (Orchestrator integration)
```

### Proposed Unified Architecture

**Single Source of Truth: `app/models/workflow.py`**

```python
# app/models/workflow.py - CANONICAL workflow models

from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

# ===== WORKFLOW DEFINITION MODELS =====

class WorkflowStep(BaseModel):
    """
    Canonical workflow step definition.
    Used by YAML parser, ADK templates, and execution engine.
    """
    agent: str = Field(..., description="Agent type (analyst, architect, etc.)")
    creates: str = Field(..., description="Output artifact (analyze-plan.md)")
    requires: Union[str, List[str]] = Field(default_factory=list, description="Input dependencies")
    notes: Optional[str] = Field(None, description="Instructions and guidance")
    condition: Optional[str] = Field(None, description="Conditional execution")
    hitl_required: bool = Field(False, description="Requires human approval")
    timeout_minutes: int = Field(default=30, description="Step timeout")

class Workflow(BaseModel):
    """Complete workflow definition loaded from YAML or code."""
    id: str
    name: str
    type: str  # greenfield, brownfield, generic
    sequence: List[WorkflowStep]
    project_types: List[str] = Field(default_factory=list)

# ===== EXECUTION STATE MODELS =====

class WorkflowStepExecution(BaseModel):
    """
    Runtime execution state for a single step.
    Extends WorkflowStep with execution metadata.
    """
    step_index: int
    step: WorkflowStep  # Reference to definition
    status: str  # pending, running, completed, failed
    task_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class WorkflowExecution(BaseModel):
    """Complete workflow execution state."""
    execution_id: str
    workflow: Workflow  # Reference to definition
    project_id: str
    status: str
    current_step: int = 0
    steps: List[WorkflowStepExecution]
    context: Dict[str, Any] = Field(default_factory=dict)
```

**Eliminate Redundant Files:**
```
❌ DELETE: app/workflows/adk_workflow_templates.py        (Move to YAML)
❌ DELETE: app/models/workflow_state.py                   (Merge into workflow.py)
❌ DELETE: app/utils/yaml_parser.py WorkflowStep          (Use models/workflow.py)
❌ DEPRECATE: app/services/workflow_engine.py             (Keep alias only)
❌ CONSOLIDATE: Multiple workflow services into 2-3 focused services
```

**Simplified Service Architecture:**

```python
# app/services/workflow_service.py - Main entry point
class WorkflowService:
    """
    Single service for workflow operations.
    Delegates to specialized sub-services.
    """
    def __init__(self, db: Session):
        self.loader = WorkflowLoader()           # Load from YAML
        self.executor = WorkflowExecutor(db)     # Execute steps
        self.persister = WorkflowPersister(db)   # Save state

    def load_workflow(self, workflow_id: str) -> Workflow:
        """Load workflow from YAML (greenfield-fullstack.yaml)."""
        return self.loader.load(f"app/workflows/{workflow_id}.yaml")

    def execute_workflow(self, workflow: Workflow, project_id: str) -> WorkflowExecution:
        """Execute workflow with orchestrator integration."""
        return self.executor.execute(workflow, project_id)

    def get_execution_state(self, execution_id: str) -> WorkflowExecution:
        """Retrieve execution state from database."""
        return self.persister.load_state(execution_id)

# app/services/workflow_loader.py (~100 LOC)
class WorkflowLoader:
    """Load workflows from YAML using canonical models."""
    def load(self, yaml_path: str) -> Workflow:
        data = yaml.safe_load(open(yaml_path))
        return Workflow(
            id=data['workflow']['id'],
            name=data['workflow']['name'],
            type=data['workflow']['type'],
            sequence=[WorkflowStep(**step) for step in data['workflow']['sequence']]
        )

# app/services/workflow_executor.py (~200 LOC)
class WorkflowExecutor:
    """Execute workflows step-by-step with orchestrator."""
    def execute(self, workflow: Workflow, project_id: str) -> WorkflowExecution:
        execution = WorkflowExecution(
            execution_id=uuid4(),
            workflow=workflow,
            project_id=project_id,
            steps=[
                WorkflowStepExecution(step_index=i, step=step)
                for i, step in enumerate(workflow.sequence)
            ]
        )

        for step_exec in execution.steps:
            # Delegate to orchestrator for actual execution
            task = orchestrator.create_task(
                project_id=project_id,
                agent_type=step_exec.step.agent,
                instructions=step_exec.step.notes
            )
            step_exec.task_id = task.id
            step_exec.status = "running"

            # Wait for completion (via Celery)
            # ...

        return execution
```

**Migration Path:**

**Phase 1: Create Canonical Models (1 day)**
1. Consolidate all `WorkflowStep` definitions into `app/models/workflow.py`
2. Add `WorkflowStepExecution` for runtime state
3. Update `Workflow` model to use canonical `WorkflowStep`

**Phase 2: Update YAML Parser (0.5 days)**
1. Modify `yaml_parser.py` to use `models/workflow.py::WorkflowStep`
2. Remove duplicate `WorkflowStep` class from parser
3. Test YAML loading with greenfield-fullstack.yaml

**Phase 3: Consolidate Services (1 day)**
1. Create unified `WorkflowService` as single entry point
2. Refactor `workflow_executor.py` to use canonical models
3. Deprecate `adk_workflow_templates.py` (convert to YAML if needed)
4. Remove duplicate execution state models from `workflow_state.py`

**Phase 4: Update Orchestrator Integration (0.5 days)**
1. Update `orchestrator/workflow_integrator.py` to use `WorkflowService`
2. Ensure orchestrator calls use canonical models
3. Remove direct references to old `WorkflowStep` classes

**Phase 5: Testing & Cleanup (1 day)**
1. Update all workflow-related tests
2. Verify greenfield-fullstack.yaml execution
3. Delete deprecated files and classes
4. Update documentation

**Total Effort:** 4 days

### Benefits of Refactoring

**Code Reduction:**
- **From:** 2500 LOC across 15 files with 5 duplicate classes
- **To:** ~800 LOC across 6 files with 1 canonical model
- **Savings:** 68% reduction (~1700 LOC removed)

**Maintainability:**
- Single source of truth for `WorkflowStep`
- Bug fixes applied once, not 5 times
- Clear separation: Definition (models) vs Execution (services)

**Developer Experience:**
- Obvious which class to use: `from app.models.workflow import WorkflowStep`
- Simplified import paths
- Easier onboarding for new developers

**SOLID Compliance:**
- **SRP:** Models define structure, services handle logic
- **DIP:** All services depend on canonical models, not duplicates

### Integration with CopilotKit

**Workflow execution remains independent of CopilotKit:**
- Orchestrator manages YAML workflow execution
- CopilotKit handles ad-hoc agent interactions
- Both use same canonical `WorkflowStep` model for consistency

**No conflict:** Workflow refactoring is orthogonal to CopilotKit integration.

### Recommendation

**PRIORITY: HIGH (Before CopilotKit Integration)**

Refactor workflow architecture BEFORE integrating CopilotKit to:
1. Eliminate technical debt that complicates integration
2. Provide clean foundation for orchestrator + CopilotKit hybrid
3. Reduce maintenance burden during CopilotKit migration

**Revised Phase 0:**
- Redis Simplification: 1 day
- **Workflow Refactoring: 4 days** (NEW)

**Revised Total Effort:** 22-31 developer days (~4.5-6 weeks)

---

## Appendix B: CopilotKit Integration Checklist

- [ ] Install CopilotKit dependencies (`@copilotkit/react-core`, `@copilotkit/react-ui`)
- [ ] Create `BMADCopilotRuntime` backend service
- [ ] Register ADK agents with CopilotRuntime
- [ ] Add `/api/v1/copilotkit` GraphQL endpoint
- [ ] Implement `BMADHITLAdapter` for safety controls
- [ ] Create `CopilotProvider` frontend wrapper
- [ ] Replace custom chat with `CopilotChat` component
- [ ] Implement `useAgentState` hook for shared state
- [ ] Create Generative UI components for agent progress
- [ ] Write integration tests for AG-UI protocol compliance
- [ ] Add feature flags for gradual rollout
- [ ] Update developer documentation
- [ ] Deploy pilot to dev environment
- [ ] Conduct A/B testing with internal users
- [ ] Full migration and legacy code deprecation

---

## Appendix B: Migration Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CopilotKit dependency introduces breaking changes | Medium | High | Pin specific versions, monitor releases, maintain rollback capability |
| HITL approval workflow breaks during migration | Low | High | Feature flags allow instant rollback, comprehensive integration tests |
| Performance regression due to GraphQL overhead | Low | Medium | Monitor API response times, optimize queries, use caching |
| User confusion from UI changes | Medium | Low | A/B testing, gradual rollout, user training documentation |
| Custom WebSocket functionality not replicated in AG-UI | Medium | Medium | Document feature parity gaps, implement adapters for missing functionality |

---

**Document Status:** Ready for Review
**Next Action:** Schedule architecture review meeting with engineering leads
