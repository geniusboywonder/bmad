# BMAD Communication Architecture Review

**Date**: October 2025
**Status**: Architecture Analysis & Simplification Recommendations
**Reviewer**: Claude Code

---

## Executive Summary

The BMAD platform currently implements a **dual communication architecture** with CopilotKit/AG-UI for agent conversations and a custom WebSocket layer for HITL approvals and policy enforcement. This creates unnecessary complexity, dependency fragility, and maintenance burden.

**Key Recommendation**: Migrate to **pure AG-UI protocol** using native CopilotKit tools, eliminating custom WebSocket infrastructure and protocol overrides.

---

## Current Architecture Analysis

### Communication Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
├─────────────────────────────────────────────────────────────┤
│  CopilotKit UI → Next.js API Route → AG-UI HttpAgent       │
│  Custom WebSocket Client → WebSocket Manager (Backend)      │
│  Custom Markdown Tag Renderers (<hitl-approval>)            │
│  Manual HITL Store Management (useHITLStore)                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
├─────────────────────────────────────────────────────────────┤
│  6 AG-UI ADK Endpoints (/api/copilotkit/{agent})           │
│  HITLAwareLlmAgent (Custom ADK Override)                    │
│  HitlCounterService (Redis State Management)                │
│  Custom WebSocket Manager (Policy + HITL Notifications)     │
│  Google ADK Agents                                          │
└─────────────────────────────────────────────────────────────┘
```

### Component Analysis

#### **1. Frontend Components**

**File**: `frontend/app/copilot-demo/page.tsx`

**Current Implementation**:
- CopilotKit sidebar with custom markdown tag renderer for HITL
- Manual request creation via `addRequest()` when `<hitl-approval>` tag detected
- Duplicate tracking via `createdApprovalIds` ref to prevent infinite loops
- Custom WebSocket listener for policy violations
- Separate HITL store management independent of CopilotKit state

**Issues**:
- Markdown tag rendering triggers request creation in component render cycle
- Manual synchronization between CopilotKit state and HITL store
- Duplicate prevention logic indicates architectural flaw
- Policy violations handled separately from agent protocol

#### **2. Next.js API Route**

**File**: `frontend/app/api/copilotkit/route.ts`

**Current Implementation**:
```typescript
const agents = {
  analyst: new HttpAgent({ url: `${BACKEND_BASE_URL}/api/copilotkit/analyst` }),
  architect: new HttpAgent({ url: `${BACKEND_BASE_URL}/api/copilotkit/architect` }),
  // ... other agents
};

const runtime = new CopilotRuntime({ agents });
```

**Issues**:
- Fresh runtime creation per request to prevent agent list mutation
- Multiple HttpAgent instances for single backend
- No error handling for policy violations at protocol level

#### **3. Backend AG-UI Integration**

**File**: `backend/app/copilot/adk_runtime.py`

**Current Implementation**:
```python
class BMADAGUIRuntime:
    def setup_fastapi_endpoints_sync(self, app: FastAPI):
        analyst = HITLAwareLlmAgent(
            name="analyst",
            model=LiteLlm(model=settings.analyst_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("analyst")
        )

        analyst_adk = ADKAgent(adk_agent=analyst, ...)
        add_adk_fastapi_endpoint(app, analyst_adk, path="/api/copilotkit/analyst")
```

**Issues**:
- Custom `HITLAwareLlmAgent` violates standard ADK protocol
- HITL instructions embedded in markdown files, not structured tools
- Session management via InMemorySessionService (no persistence)

#### **4. Custom HITL Agent Override**

**File**: `backend/app/copilot/hitl_aware_agent.py`

**Current Implementation**:
```python
class HITLAwareLlmAgent(LlmAgent):
    def run(self, messages: List[Message], **kwargs) -> Message:
        if messages[-1].role == "tool" and messages[-1].name == "reconfigureHITL":
            # Custom tool result processing
            # Update Redis counter settings
            # Truncate message history
            return super().run(messages=messages[:-2], **kwargs)

        return super().run(messages=messages, **kwargs)
```

**Issues**:
- Overrides standard ADK `run()` method
- Manual message history manipulation
- Tight coupling to `reconfigureHITL` tool implementation
- Breaks Google ADK protocol expectations

#### **5. Custom WebSocket Manager**

**File**: `backend/app/websocket/manager.py`

**Current Implementation**:
- Priority notification queues (CRITICAL, HIGH, NORMAL, LOW)
- Project-scoped connection management
- Separate event broadcasting for HITL and policy violations
- Delivery tracking and retry logic

**Issues**:
- Duplicate functionality with AG-UI protocol streaming
- Manual synchronization with database notifications
- Separate message bus requires coordination with agent conversations

#### **6. HITL Counter Service**

**File**: `backend/app/services/hitl_counter_service.py`

**Current Implementation**:
- Redis-based state management for per-project counters
- `enabled`, `limit`, `remaining` tracked separately
- Governor pattern intercepts agent actions
- Frontend tool call (`reconfigureHITL`) updates Redis state

**Issues**:
- State management outside agent conversation context
- Redis dependency for simple counter logic
- Complex reconfiguration flow via tool calls

---

## Core Problems Identified

### 1. **Dual Communication Channels**

**Problem**: Two independent message buses require manual synchronization

- **CopilotKit/AG-UI Protocol**: Agent conversations, tool execution
- **Custom WebSocket**: HITL notifications, policy violations, status updates

**Impact**:
- Frontend must listen to both channels
- Message ordering not guaranteed between channels
- State synchronization complexity
- Duplicate error handling logic

### 2. **Custom HITL Implementation Complexity**

**Problem**: Non-standard HITL workflow using custom patterns

- Frontend markdown tag renderer creates HITL requests manually
- Duplicate tracking via `createdApprovalIds` ref
- Store management (`useHITLStore`) independent of CopilotKit
- Navigation logic spread across components

**Impact**:
- Fragile render cycle dependencies
- Infinite loop prevention logic indicates design flaw
- Manual cleanup required for resolved requests
- Poor developer experience

### 3. **Backend Protocol Fragmentation**

**Problem**: Custom agent overrides break standard ADK patterns

- `HITLAwareLlmAgent` overrides `run()` method
- Manual message history manipulation
- Redis state management outside conversation context
- Policy enforcement separated from agent execution

**Impact**:
- Google ADK protocol violations
- Difficult to upgrade dependencies
- Custom debugging required
- Knowledge silos (custom code vs. framework)

### 4. **Dependency Conflicts**

**Problem**: Version pinning creates fragility

- CopilotKit 1.10.5 + AG-UI ADK 0.3.1 + Google ADK
- Custom wrappers (HITLAwareLlmAgent) assume specific API contracts
- Frontend relies on non-standard markdown tag rendering
- Breaking changes in any dependency cascade across custom code

**Impact**:
- Difficult dependency upgrades
- Security patch delays
- Framework feature adoption blocked
- Technical debt accumulation

---

## Recommended Architecture: **Native AG-UI with Minimal Custom Logic**

### **Option 1: Pure AG-UI Protocol** (Recommended)

**Philosophy**: Use AG-UI's built-in capabilities, eliminate custom communication layers.

#### **Backend Simplification**

**New File**: `backend/app/copilot/agents.py` (replaces `adk_runtime.py` + `hitl_aware_agent.py`)

```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from app.utils.agent_prompt_loader import agent_prompt_loader

def create_agent(name: str, model: str, instruction: str) -> LlmAgent:
    """Standard ADK agent - no custom overrides."""
    return LlmAgent(
        name=name,
        model=LiteLlm(model=model),
        instruction=instruction
    )

def setup_agents(app: FastAPI):
    """Register standard AG-UI endpoints."""
    agents = {
        "analyst": create_agent("analyst", "gpt-4-turbo", agent_prompt_loader.get_agent_prompt("analyst")),
        "architect": create_agent("architect", "gpt-4-turbo", agent_prompt_loader.get_agent_prompt("architect")),
        "coder": create_agent("coder", "gpt-4-turbo", agent_prompt_loader.get_agent_prompt("coder")),
        "tester": create_agent("tester", "gpt-4-turbo", agent_prompt_loader.get_agent_prompt("tester")),
        "deployer": create_agent("deployer", "gpt-4-turbo", agent_prompt_loader.get_agent_prompt("deployer")),
        "orchestrator": create_agent("orchestrator", "gpt-4-turbo", agent_prompt_loader.get_agent_prompt("orchestrator")),
    }

    for name, agent in agents.items():
        adk_agent = ADKAgent(adk_agent=agent, app_name=f"bmad_{name}")
        add_adk_fastapi_endpoint(app, adk_agent, path=f"/api/copilotkit/{name}")
```

#### **Frontend Simplification**

**Updated File**: `frontend/app/copilot-demo/page.tsx`

```tsx
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotAction } from "@copilotkit/react-core";
import { useAgent } from "@/lib/context/agent-context";

export default function CopilotDemoPage() {
  const { selectedAgent } = useAgent();

  // HITL via native CopilotKit action (not custom markdown tags)
  useCopilotAction({
    name: "requestApproval",
    description: "Request human approval for agent action",
    parameters: [
      {
        name: "action",
        type: "string",
        description: "Action requiring approval"
      },
      {
        name: "agentName",
        type: "string",
        description: "Agent requesting approval"
      },
      {
        name: "estimatedCost",
        type: "number",
        description: "Estimated cost/impact of action"
      }
    ],
    handler: async ({ action, agentName, estimatedCost }) => {
      // Native approval dialog using CopilotKit UI
      const approved = await showApprovalDialog({
        action,
        agentName,
        estimatedCost
      });

      return {
        approved,
        action,
        timestamp: new Date().toISOString()
      };
    }
  });

  return (
    <div className="min-h-screen">
      <CopilotSidebar
        agent={selectedAgent}
        labels={{
          title: `BMAD ${selectedAgent} Agent`,
          initial: `I'm your ${selectedAgent} agent. How can I help?`
        }}
        // No custom markdown tag renderers
        // No manual WebSocket management
        // Pure CopilotKit patterns
      />
    </div>
  );
}
```

**Key Changes**:
- ❌ Remove custom markdown tag renderers
- ❌ Remove `createdApprovalIds` tracking
- ❌ Remove manual HITL store management
- ❌ Remove WebSocket listeners
- ✅ Use native `useCopilotAction` for approvals
- ✅ Rely on AG-UI protocol for all communication

#### **HITL Integration via Tools**

**New File**: `backend/app/agents/tools/hitl_tools.py`

```python
from google.adk.tools import Tool
from app.database.connection import get_session
from app.database.models import HitlAgentApprovalDB
from uuid import uuid4
from datetime import datetime, timedelta

@Tool
async def request_approval(
    action: str,
    agent_name: str,
    project_id: str,
    estimated_cost: float = 0.0
) -> dict:
    """Tool that agents call to request human approval.

    AG-UI protocol automatically:
    1. Pauses agent execution
    2. Sends tool call to frontend
    3. Waits for frontend handler response
    4. Resumes agent with tool result

    Args:
        action: Description of action requiring approval
        agent_name: Name of agent requesting approval
        project_id: Project context ID
        estimated_cost: Estimated cost/impact

    Returns:
        Approval status and metadata
    """
    session = next(get_session())

    try:
        # Create approval record in database
        approval = HitlAgentApprovalDB(
            id=uuid4(),
            project_id=project_id,
            agent_type=agent_name,
            request_type="PRE_EXECUTION",
            action_description=action,
            estimated_cost=estimated_cost,
            status="PENDING",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        session.add(approval)
        session.commit()

        # AG-UI will pause here until frontend responds
        return {
            "approval_id": str(approval.id),
            "status": "pending",
            "message": f"Approval request created: {action}",
            "expires_at": approval.expires_at.isoformat()
        }

    finally:
        session.close()
```

**Tool Registration**:

```python
# backend/app/copilot/agents.py

from app.agents.tools.hitl_tools import request_approval

def create_agent(name: str, model: str, instruction: str) -> LlmAgent:
    """Standard ADK agent with HITL tool."""
    agent = LlmAgent(
        name=name,
        model=LiteLlm(model=model),
        instruction=instruction
    )

    # Register HITL approval tool
    agent.add_tool(request_approval)

    return agent
```

#### **Policy Enforcement via Middleware**

**New File**: `backend/app/copilot/policy_middleware.py`

```python
from fastapi import Request, HTTPException
from app.services.phase_policy_service import PhasePolicyService
import structlog

logger = structlog.get_logger(__name__)

async def enforce_policy_middleware(request: Request, call_next):
    """Middleware to enforce phase-based policy before agent execution.

    Returns 403 errors that CopilotKit can surface to user.
    """
    if request.url.path.startswith("/api/copilotkit/"):
        # Extract agent type from path
        agent_type = request.url.path.split("/")[-1]

        # Get project ID from header or session
        project_id = request.headers.get("X-Project-ID")

        if project_id:
            policy_service = PhasePolicyService()
            decision = await policy_service.evaluate_agent_request(
                project_id=project_id,
                agent_type=agent_type
            )

            if decision.status == "denied":
                logger.warning(
                    "Policy violation blocked agent request",
                    agent_type=agent_type,
                    project_id=project_id,
                    current_phase=decision.current_phase
                )

                raise HTTPException(
                    status_code=403,
                    detail={
                        "type": "policy_violation",
                        "message": decision.message,
                        "current_phase": decision.current_phase,
                        "allowed_agents": decision.allowed_agents
                    }
                )

    response = await call_next(request)
    return response
```

**Middleware Registration**:

```python
# backend/app/main.py

from app.copilot.policy_middleware import enforce_policy_middleware

app = FastAPI()
app.middleware("http")(enforce_policy_middleware)
```

**Frontend Error Handling**:

```tsx
// frontend/app/copilot-demo/page.tsx

import { useCopilotChat } from "@copilotkit/react-core";

const { isLoading, error } = useCopilotChat();

useEffect(() => {
  if (error?.status === 403) {
    const policyError = error.detail;

    toast.error("Policy Violation", {
      description: `${policyError.message}\n\nCurrent Phase: ${policyError.current_phase}\nAllowed Agents: ${policyError.allowed_agents.join(", ")}`
    });

    // Update UI to show policy guidance
    setPolicyGuidance({
      status: "denied",
      message: policyError.message,
      currentPhase: policyError.current_phase,
      allowedAgents: policyError.allowed_agents
    });
  }
}, [error]);
```

### **Benefits of Option 1:**

1. ✅ **Zero Custom WebSocket Logic**: AG-UI protocol handles all real-time communication
2. ✅ **Native Tool Execution**: HITL approvals use standard CopilotKit actions
3. ✅ **No Custom Agent Overrides**: Standard Google ADK agents without HITLAwareLlmAgent
4. ✅ **Simplified Frontend**: No markdown tag renderers, no manual store management
5. ✅ **Policy via Middleware**: Clean separation using FastAPI middleware pattern
6. ✅ **Dependency Clarity**: Only CopilotKit + AG-UI ADK + Google ADK (no custom bridges)
7. ✅ **Upgrade Path**: Can adopt new framework features without custom code changes
8. ✅ **Standard Debugging**: Framework tooling works without custom considerations

---

### **Option 2: Hybrid with Minimal WebSocket** (Fallback if AG-UI Insufficient)

Keep AG-UI for agent conversations, WebSocket **only** for:
- Policy violation notifications (non-blocking alerts)
- Emergency stop signals
- Background task progress (non-agent related)

```python
# Use AG-UI for:
# - Agent conversations
# - HITL approvals (via tools)
# - Real-time streaming responses

# Use WebSocket ONLY for:
# - Async notifications that don't require agent pause
# - Emergency stop broadcasts
# - Background job progress
```

**Criteria for WebSocket Usage**:
- ✅ Cannot be handled by AG-UI protocol streaming
- ✅ Requires broadcast to multiple clients
- ✅ No agent execution dependency
- ❌ Do not use for HITL approvals (use tools instead)
- ❌ Do not use for policy violations (use middleware instead)

---

## Migration Plan & Risk Assessment

### **Phase 1: Backend Tool-Based HITL** (Low Risk - 1 day)

**Objective**: Replace custom HITL agent override with standard ADK tools.

**Changes**:
1. Create `backend/app/agents/tools/hitl_tools.py` with `@Tool` decorated functions
2. Register tools with ADK agents in `adk_runtime.py`
3. Remove `HITLAwareLlmAgent` custom override
4. Test tool execution via AG-UI protocol

**Files Modified**:
- ➕ `backend/app/agents/tools/hitl_tools.py` (new)
- 🔧 `backend/app/copilot/adk_runtime.py` (register tools)
- ❌ `backend/app/copilot/hitl_aware_agent.py` (delete)

**Testing**:
```bash
# Backend: Verify tool registration
curl -X POST http://localhost:8000/api/copilotkit/analyst \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Request approval for analysis"}]}'

# Expected: Tool call in response with requestApproval function
```

**Risk**: Low - Tools are standard ADK pattern, no protocol changes
**Rollback**: Keep `HITLAwareLlmAgent`, disable new tools
**Success Criteria**: Agent calls `request_approval` tool when needing approval

---

### **Phase 2: Frontend Native Actions** (Medium Risk - 2 days)

**Objective**: Replace custom markdown tags with native CopilotKit actions.

**Changes**:
1. Replace custom markdown tag renderers with `useCopilotAction`
2. Convert HITL store to respond to CopilotKit tool calls
3. Remove `createdApprovalIds` tracking logic
4. Test approval flow end-to-end

**Files Modified**:
- 🔧 `frontend/app/copilot-demo/page.tsx` (replace markdown renderers)
- 🔧 `frontend/lib/stores/hitl-store.ts` (simplify for tool responses)
- ❌ `frontend/components/hitl/inline-hitl-approval.tsx` (refactor or delete)

**Testing**:
```tsx
// Verify tool call reaches frontend handler
useCopilotAction({
  name: "requestApproval",
  handler: async ({ action }) => {
    console.log("Tool call received:", action);
    // Verify approval dialog appears
    // Verify response reaches backend
  }
});
```

**Risk**: Medium - Changes user-facing HITL UI behavior
**Rollback**: Revert to markdown tag pattern
**Validation**:
- ✅ HITL approval dialog appears on tool call
- ✅ Approval response sent back to agent
- ✅ Agent resumes with tool result

---

### **Phase 3: Policy Middleware** (Low Risk - 1 day)

**Objective**: Move policy enforcement to HTTP layer.

**Changes**:
1. Create FastAPI middleware for policy enforcement
2. Move policy checks from WebSocket to HTTP layer
3. Return 403 errors with policy violation details
4. Frontend handles 403 responses with error UI

**Files Modified**:
- ➕ `backend/app/copilot/policy_middleware.py` (new)
- 🔧 `backend/app/main.py` (register middleware)
- 🔧 `frontend/app/copilot-demo/page.tsx` (handle 403 errors)

**Testing**:
```bash
# Test policy violation returns 403
curl -X POST http://localhost:8000/api/copilotkit/coder \
  -H "X-Project-ID: <project-in-analyze-phase>" \
  -H "Content-Type: application/json"

# Expected: 403 response with policy violation details
```

**Risk**: Low - Middleware is standard FastAPI pattern
**Rollback**: Keep policy checks in current location
**Success Criteria**: 403 errors surface in CopilotKit UI with policy details

---

### **Phase 4: WebSocket Elimination** (High Risk - 3 days)

**Objective**: Remove custom WebSocket infrastructure entirely.

**Changes**:
1. Remove custom WebSocket manager
2. Remove `enhanced-websocket-client.ts`
3. Remove policy violation WebSocket events
4. Rely entirely on AG-UI protocol + HTTP errors

**Files Deleted**:
- ❌ `backend/app/websocket/manager.py`
- ❌ `backend/app/websocket/events.py`
- ❌ `backend/app/api/websocket.py`
- ❌ `frontend/lib/services/websocket/enhanced-websocket-client.ts`
- ❌ `frontend/lib/services/websocket/websocket-service.ts`

**Testing Matrix**:

| Scenario | Expected Behavior | Validation |
|----------|-------------------|------------|
| Real-time agent responses | Stream via AG-UI protocol | ✅ Messages appear in real-time |
| HITL approval request | Tool call pauses agent | ✅ Agent waits for approval |
| Policy violation | 403 error surfaces immediately | ✅ User sees policy message |
| Network interruption | AG-UI auto-reconnect | ✅ No message loss |
| Multiple clients | Each receives events | ✅ Broadcast works via HTTP |

**Risk**: High - Complete communication paradigm shift
**Rollback Plan**: Keep WebSocket for notifications, use AG-UI for agent conversations (Hybrid approach)
**Validation Required**:
- ✅ Real-time agent responses still work
- ✅ HITL approvals pause agent execution correctly
- ✅ Policy violations surface to user immediately
- ✅ No message loss during network issues
- ✅ Error handling maintains user context

---

### **Phase 5: Counter Service Migration** (Medium Risk - 2 days)

**Objective**: Move counter logic into agent instructions.

**Changes**:
1. Move `HitlCounterService` logic into agent instructions
2. Agents track their own action counts via conversation memory
3. Remove Redis counter state management
4. Use tool calls to request counter reset approval

**Agent Instruction Update**:

```markdown
# Analyst Agent Instructions

You are the BMAD Analyst agent...

## Action Counter Tracking

Track the number of actions you've performed in this conversation:
- Start each conversation with counter = 0
- Increment counter for each analysis, recommendation, or artifact creation
- When counter reaches 10, call `request_approval` with action="Reset action counter for next 10 actions"
- After approval, reset internal counter to 0

Example:
- Action 1: Create PRD outline (counter=1)
- Action 2: Define user personas (counter=2)
- ...
- Action 10: Generate final PRD (counter=10)
- Call request_approval("Reset action counter")
- Action 11: [After approval] Start new work (counter=1)
```

**Files Modified**:
- 🔧 `backend/app/agents/analyst.md` (add counter instructions)
- 🔧 `backend/app/agents/architect.md` (add counter instructions)
- 🔧 `backend/app/agents/coder.md` (add counter instructions)
- ❌ `backend/app/services/hitl_counter_service.py` (delete)
- ❌ Redis counter keys (cleanup)

**Testing**:
```
User: "Create a PRD for project management tool"
Agent: [Performs 10 actions, incrementing internal counter]
Agent: [Calls request_approval tool] "Reset action counter for next 10 actions"
User: [Approves]
Agent: [Resets counter to 0, continues work]
```

**Risk**: Medium - Changes stateful approval logic
**Rollback**: Keep Redis-based counter service
**Success Criteria**:
- ✅ Agent tracks actions in conversation memory
- ✅ Counter resets work without Redis
- ✅ No state loss on conversation restore

---

## Implementation Timeline

### **Week 1: Core Tool Migration**
- **Day 1-2**: Phase 1 (Backend tool-based HITL)
- **Day 3-4**: Phase 2 (Frontend native actions)
- **Day 5**: Phase 3 (Policy middleware)

### **Week 2: WebSocket Elimination**
- **Day 1-3**: Phase 4 (Remove WebSocket infrastructure)
- **Day 4**: Comprehensive integration testing
- **Day 5**: Documentation and rollback plan refinement

### **Week 3: Counter Migration & Polish**
- **Day 1-2**: Phase 5 (Counter service migration)
- **Day 3**: Performance testing and optimization
- **Day 4**: Security review and edge case handling
- **Day 5**: Final validation and production readiness

---

## Success Metrics

### **Code Simplification**
- ✅ Remove 500+ LOC custom WebSocket code
- ✅ Remove 150+ LOC custom HITL agent override
- ✅ Remove 300+ LOC frontend markdown tag rendering
- ✅ **Total**: ~950 LOC reduction (15% of communication layer)

### **Dependency Health**
- ✅ Zero custom protocol overrides
- ✅ All framework patterns standard
- ✅ Dependency upgrades unblocked
- ✅ Security patches can be applied immediately

### **Developer Experience**
- ✅ Onboarding time reduced (no custom patterns to learn)
- ✅ Debugging uses standard framework tooling
- ✅ New features use documented framework capabilities
- ✅ Knowledge transfer simplified (framework docs applicable)

### **System Reliability**
- ✅ Message delivery guaranteed by AG-UI protocol
- ✅ Error handling standardized
- ✅ Auto-reconnection works without custom code
- ✅ State synchronization eliminated (single source of truth)

---

## Key Principles

### **1. Use Framework Capabilities First**

> AG-UI protocol already supports:
> - Tool execution with frontend handlers
> - Agent pause/resume on tool results
> - Real-time streaming responses
> - Error handling and retries
> - Session management and persistence

**Before building custom solution, ask**:
- Does the framework already provide this?
- Can we achieve this with standard patterns?
- What is the maintenance cost of custom code?

### **2. Minimize Custom Protocol Implementations**

Custom WebSocket, markdown tag renderers, and agent overrides create maintenance burden without clear benefit.

**Custom code costs**:
- Documentation debt
- Onboarding complexity
- Dependency upgrade friction
- Framework feature adoption delays
- Debugging overhead

### **3. Align with Standard Patterns**

**Good**: Use `useCopilotAction` for HITL approvals
**Bad**: Custom markdown tag rendering with manual store sync

**Good**: FastAPI middleware for policy enforcement
**Bad**: Separate WebSocket channel for policy violations

**Good**: Standard ADK tools for agent capabilities
**Bad**: Override `run()` method with custom message manipulation

---

## Next Steps

### **Immediate Actions**

1. **Validate AG-UI Tool Execution** (4 hours)
   - Confirm frontend `useCopilotAction` receives backend `@Tool` calls
   - Test approval flow with tool results
   - Verify agent pause/resume behavior

2. **Prototype HITL Approval Tool** (1 day)
   - Implement `request_approval` tool
   - Replace one markdown tag with native tool pattern
   - Compare user experience

3. **Test Policy Middleware** (4 hours)
   - Implement policy middleware
   - Verify 403 errors surface correctly in CopilotKit UI
   - Test with various policy violation scenarios

4. **Measure Impact** (2 hours)
   - Compare message flow complexity before/after
   - Measure LOC reduction
   - Document dependency simplification

### **Decision Points**

**After Phase 1-2 Completion**:
- ✅ If tool-based HITL works well → Proceed to Phase 3-4
- ⚠️ If AG-UI limitations discovered → Evaluate Hybrid approach (Option 2)
- ❌ If critical gaps → Reassess architecture strategy

**After Phase 4 (WebSocket Elimination)**:
- ✅ If no message loss → Proceed to Phase 5
- ⚠️ If edge cases found → Implement targeted WebSocket for specific use cases
- ❌ If fundamental issues → Rollback to Hybrid approach

---

## Conclusion

The current BMAD communication architecture has evolved into a **dual-channel system** with significant custom protocol implementations. This creates unnecessary complexity, dependency fragility, and maintenance burden.

**Recommended path**: **Migrate to pure AG-UI protocol** using native CopilotKit tools for HITL, FastAPI middleware for policy enforcement, and standard ADK agents without custom overrides.

**Expected outcomes**:
- 950+ LOC reduction in communication layer
- Zero custom protocol implementations
- Unblocked dependency upgrades
- Simplified developer onboarding
- Improved system reliability

**Risk mitigation**: Phased migration with rollback plans at each stage ensures production stability while achieving architectural simplification.

---

**Document Version**: 1.0
**Last Updated**: October 2025
**Next Review**: After Phase 2 completion (estimated 1 week)
