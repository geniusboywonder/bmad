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

## Conclusion

CopilotKit's ADK integration provides significant architectural benefits through standardized AG-UI protocol, Generative UI for dynamic agent state rendering, and bidirectional shared state management. The proposed migration preserves BMAD's enterprise controls (HITL, audit trails, multi-LLM) while reducing maintenance burden by 70% and improving user experience.

**Recommendation: PROCEED with phased migration starting with Proof of Concept.**

---

## Appendix A: CopilotKit Integration Checklist

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
