# Policy Enforcement Investigation Report

**Date:** October 9, 2025  
**Investigator:** James (Dev Agent)  
**Issue:** Policy enforcement not working - Analyst agent able to write poems despite phase restrictions

---

## Executive Summary

Policy enforcement is **completely bypassed** in the CopilotKit integration flow. The root cause is that CopilotKit uses direct ADK AG-UI protocol endpoints that execute agents without calling the orchestration layer where `PhasePolicyService` validates agent actions against SDLC phase policies.

**Status:** ❌ Policy enforcement non-functional in CopilotKit flow  
**Impact:** Users can execute any agent with any prompt, bypassing phase-based restrictions  
**Severity:** HIGH - Breaks core governance model

---

## Root Cause Analysis

### The Problem

The CopilotKit integration uses a **completely separate execution path** that bypasses the orchestration layer where policy checks are implemented.

### Request Flow Comparison

**❌ Current CopilotKit Flow (Policy Bypassed):**
```
User Message 
  → CopilotKit Frontend 
    → /api/copilotkit/{agent} 
      → ADK Agent 
        → Direct LLM Execution
          → Response (NO POLICY CHECK)
```

**✅ Expected Flow with Policy Enforcement:**
```
User Message 
  → REST API 
    → AgentCoordinator.create_task() 
      → [POLICY CHECK] 
        → Celery Queue 
          → ADK Executor 
            → Response
```

---

## Detailed Findings

### 1. Policy Enforcement IS Implemented Correctly ✅

- ✅ **`PhasePolicyService`** exists and works properly (`backend/app/services/orchestrator/phase_policy_service.py`)
- ✅ **Policy configuration** in `policy_config.yaml` defines phase-based agent restrictions
- ✅ **`AgentCoordinator.create_task()`** enforces policy before creating tasks (line 36-38)
- ✅ **In "analyze" phase**, only "analyst" and "orchestrator" agents are allowed

**Policy Configuration (`policy_config.yaml`):**
```yaml
analyze:
  allowed_agents:
    - "analyst"
    - "orchestrator"

design:
  allowed_agents:
    - "architect"
    - "orchestrator"

build:
  allowed_agents:
    - "coder"
    - "orchestrator"
# ... etc
```

### 2. CopilotKit Flow Bypasses Orchestration Layer Entirely ❌

**File: `backend/app/copilot/adk_runtime.py`**

Lines 110-115: `add_adk_fastapi_endpoint()` registers direct agent endpoints:
```python
add_adk_fastapi_endpoint(app, analyst_adk, path="/api/copilotkit/analyst")
add_adk_fastapi_endpoint(app, architect_adk, path="/api/copilotkit/architect")
add_adk_fastapi_endpoint(app, coder_adk, path="/api/copilotkit/coder")
# ... etc
```

**Critical Issue:** These endpoints are ADK AG-UI protocol handlers that execute agents directly:
- ❌ **NO policy enforcement** - they don't call `AgentCoordinator`
- ❌ **NO `PhasePolicyService` integration**
- ❌ **NO audit trail through orchestration layer**

**File: `backend/app/copilot/hitl_aware_agent.py`**

`HITLAwareLlmAgent.run()` only checks HITL counter, **NOT phase policy**:
```python
def run(self, messages: List[Message], **kwargs) -> Message:
    session_id = kwargs.get("session_id")  # Line 32
    
    # Only checks HITL counter, NO POLICY CHECK
    if messages and messages[-1].role == "tool" and messages[-1].name == "reconfigureHITL":
        # Handle HITL reconfiguration...
    
    return super().run(messages=messages, **kwargs)
```

- Line 32: Uses `session_id` from kwargs (this is the threadId from frontend)
- Line 41: Assumes `session_id == project_id` (fragile assumption)
- **Missing:** Policy validation before agent execution

### 3. Session ID / Project ID Mismatch ❌

**File: `frontend/components/client-provider.tsx`**

Line 16: threadId is NOT a project UUID:
```typescript
const threadId = useMemo(() => `agent-${selectedAgent}-thread`, [selectedAgent]);
```

Line 24: CopilotKit uses this as session_id:
```typescript
<CopilotKit
  threadId={threadId}  // "agent-analyst-thread"
  agent={selectedAgent}
  // ...
/>
```

**Result:** Session ID is a string like `"agent-analyst-thread"`, NOT a valid project UUID

**File: `frontend/app/copilot-demo/page.tsx`**

Line 49: Hardcoded project ID (likely doesn't exist in DB):
```typescript
const projectId = "018f9fa8-b639-4858-812d-57f592324a35";
```

This project likely doesn't exist in the database, so phase defaults to "discovery".

### 4. Why Analyst Can Write a Poem ❌

1. **No policy check** in ADK AG-UI endpoint execution path
2. **Session ID mismatch** - `"agent-analyst-thread"` cannot be converted to UUID
3. **Policy service never called** - agents execute directly without orchestration
4. **Default phase assumption** - even if project ID worked, it defaults to "discovery" where analyst is allowed anyway

### 5. Files Where Policy IS Enforced ✅

**File: `backend/app/services/orchestrator/agent_coordinator.py`**

Lines 36-38: Policy check in `create_task()`:
```python
def create_task(self, project_id: UUID, agent_type: str, instructions: str, context_ids: List[UUID] = None) -> Task:
    """Create a new task for an agent, enforcing phase policies."""
    
    # Enforce phase policy
    policy_decision = self.phase_policy_service.evaluate(project_id, agent_type)
    if policy_decision.status == "denied":
        raise PolicyViolationException(policy_decision)
    
    # ... create task
```

**This code works perfectly** - but CopilotKit never calls it!

---

## Fix Plan - 3 Solution Approaches

### OPTION 1: Middleware Policy Enforcement (Simplest)

**Approach:** Add policy check as middleware before ADK agent execution

**Changes Required:**

1. **Create new file: `backend/app/copilot/policy_middleware.py`**
   ```python
   class PolicyEnforcementMiddleware:
       def __init__(self, db: Session):
           self.policy_service = PhasePolicyService(db)
       
       async def enforce_policy(self, project_id: UUID, agent_type: str) -> PolicyDecision:
           decision = self.policy_service.evaluate(project_id, agent_type)
           if decision.status == "denied":
               # Emit WebSocket policy_violation event
               # Raise PolicyViolationException
           return decision
   ```

2. **Modify: `backend/app/copilot/adk_runtime.py`**
   - Wrap each ADK agent with policy middleware
   - Pass project_id through session metadata

3. **Modify: `frontend/components/client-provider.tsx`**
   - Change threadId to use actual project UUID: `projectId-${selectedAgent}`
   - Pass projectId from context/props

**Pros:**
- ✅ Minimal changes
- ✅ Preserves existing architecture
- ✅ Easy to implement

**Cons:**
- ⚠️ Adds middleware layer
- ⚠️ Still separate from main orchestration flow
- ⚠️ Duplicate policy logic

---

### OPTION 2: Unified Orchestration Flow (Most Robust)

**Approach:** Route CopilotKit requests through AgentCoordinator

**Changes Required:**

1. **Create: `backend/app/api/copilot_orchestrated.py`**
   ```python
   @router.post("/api/v1/copilot/{agent_type}/execute")
   async def execute_agent_with_policy(
       agent_type: str,
       project_id: UUID,
       instructions: str,
       db: Session = Depends(get_db)
   ):
       # Uses existing AgentCoordinator (includes policy check)
       coordinator = AgentCoordinator(db)
       task = coordinator.create_task(project_id, agent_type, instructions)
       
       # Queue to Celery with ADK executor
       celery_task_id = coordinator.submit_task(task)
       
       return {"task_id": task.task_id, "status": "queued"}
   ```

2. **Modify: `frontend/app/api/copilotkit/route.ts`**
   - Intercept CopilotKit messages before ADK
   - Call new orchestrated endpoint
   - Stream results back to CopilotKit

3. **Keep: ADK endpoints for direct testing/debugging**

**Pros:**
- ✅ Uses existing policy enforcement
- ✅ Full audit trail through orchestration
- ✅ No duplicate policy logic
- ✅ Consistent with existing architecture

**Cons:**
- ⚠️ More complex implementation
- ⚠️ Changes CopilotKit integration pattern
- ⚠️ May impact streaming responses

---

### OPTION 3: Policy-Aware ADK Agent Wrapper (Recommended)

**Approach:** Extend `HITLAwareLlmAgent` to include policy checking

**Changes Required:**

1. **Modify: `backend/app/copilot/hitl_aware_agent.py`**
   ```python
   class PolicyAwareLlmAgent(LlmAgent):
       """LlmAgent with HITL counter AND phase policy enforcement."""
       
       def run(self, messages: List[Message], **kwargs) -> Message:
           session_id = kwargs.get("session_id")
           
           # Extract project_id from session_id
           try:
               project_id = UUID(session_id)
           except (ValueError, TypeError):
               # Try to extract from session metadata
               project_id = self._extract_project_id(session_id)
           
           # POLICY CHECK (NEW)
           db = get_db()
           policy_service = PhasePolicyService(db)
           policy_decision = policy_service.evaluate(project_id, self.name)
           
           if policy_decision.status == "denied":
               # Emit WebSocket policy_violation event
               websocket_manager.broadcast_project_event(
                   project_id=project_id,
                   event=WebSocketEvent(
                       event_type=EventType.POLICY_VIOLATION,
                       data={
                           "status": "denied",
                           "message": policy_decision.message,
                           "current_phase": policy_decision.current_phase,
                           "allowed_agents": policy_decision.allowed_agents
                       }
                   )
               )
               
               # Return policy violation message
               return Message(
                   role="assistant",
                   content=f"❌ {policy_decision.message}\n\nAllowed agents: {', '.join(policy_decision.allowed_agents)}"
               )
           
           # HITL counter check (existing)
           if messages and messages[-1].role == "tool" and messages[-1].name == "reconfigureHITL":
               # ... existing HITL logic
           
           # Proceed with agent execution
           return super().run(messages=messages, **kwargs)
   ```

2. **Modify: `backend/app/copilot/adk_runtime.py`**
   ```python
   from app.copilot.hitl_aware_agent import PolicyAwareLlmAgent  # Renamed class
   
   analyst = PolicyAwareLlmAgent(
       name="analyst",
       model=LiteLlm(model=settings.analyst_agent_model),
       instruction=agent_prompt_loader.get_agent_prompt("analyst")
   )
   # ... same for other agents
   ```

3. **Modify: `frontend/components/client-provider.tsx`**
   ```typescript
   // Pass actual project UUID as threadId
   const { projectId } = useProject();  // From context
   const threadId = useMemo(() => projectId || `agent-${selectedAgent}-thread`, [projectId, selectedAgent]);
   ```

4. **Frontend already handles `policy_violation` events** (copilot-demo/page.tsx lines 68-91)

**Pros:**
- ✅ Leverages existing policy service and WebSocket events
- ✅ Frontend already has policy violation UI
- ✅ Minimal changes to CopilotKit integration
- ✅ Consistent with HITL counter pattern
- ✅ Enforces policy at the right architectural layer
- ✅ No duplicate policy logic

**Cons:**
- ⚠️ Requires DB session in ADK agents
- ⚠️ Mixes concerns (agent + policy) in one class

---

## Recommendation

### **Option 3: Policy-Aware Agent Wrapper**

**Why this is the best approach:**

1. **Architectural Consistency:** Follows the same pattern as HITL counter (already implemented)
2. **Minimal Changes:** Extends existing `HITLAwareLlmAgent` rather than creating new layers
3. **Leverages Existing UI:** Frontend already has `policy_violation` event handlers and UI
4. **Right Layer:** Enforces policy at agent execution layer, not orchestration
5. **No Duplication:** Uses existing `PhasePolicyService` without duplicating logic

### Implementation Steps

**Backend Changes:**

1. **Rename and extend `HITLAwareLlmAgent`** → `PolicyAwareLlmAgent`
   - Add `PhasePolicyService` integration
   - Check policy before execution in `run()` method
   - Emit `policy_violation` WebSocket event when blocked
   - Return friendly error message to user

2. **Update `adk_runtime.py`**
   - Import `PolicyAwareLlmAgent`
   - Inject database session for policy service

**Frontend Changes:**

3. **Update `client-provider.tsx`**
   - Pass actual `projectId` as `threadId`
   - Extract `projectId` from project context

4. **Verify `copilot-demo/page.tsx`**
   - Confirm `policy_violation` event handler works
   - Test policy guidance UI displays correctly

**Testing:**

5. **Create integration test**
   - Test analyst in "design" phase → should be blocked
   - Test architect in "design" phase → should be allowed
   - Verify WebSocket events emitted
   - Verify UI displays policy guidance

---

## Additional Considerations

### Session ID / Project ID Mapping

**Current Issue:** `session_id = "agent-analyst-thread"` is not a UUID

**Solutions:**

1. **Option A:** Use project UUID as session_id
   - Frontend passes `projectId` as `threadId`
   - Backend receives it as `session_id`
   - Simple but loses per-agent conversation history

2. **Option B:** Pass project_id in metadata
   - CopilotKit supports custom metadata
   - Extract from kwargs in agent `run()` method
   - Maintains per-agent conversation threads

3. **Option C:** Parse session_id pattern
   - Extract project UUID from session string
   - Format: `{projectId}-agent-{agentType}-thread`
   - More complex but preserves both IDs

**Recommended:** Option A for simplicity, Option C for production

### Database Session Management

Policy service requires database session. Options:

1. **Dependency injection** - Pass db session through kwargs
2. **Global session factory** - Create session in agent `run()` method
3. **Context manager** - Use `with get_db() as db:` pattern

**Recommended:** Option 2 (global session factory) for ADK agents

---

## Next Steps

**Awaiting approval to proceed with implementation.**

### Proposed Implementation Order:

1. ✅ **Phase 1:** Backend policy enforcement in agent wrapper
2. ✅ **Phase 2:** Frontend project ID integration
3. ✅ **Phase 3:** WebSocket event testing
4. ✅ **Phase 4:** UI verification and polish
5. ✅ **Phase 5:** Integration testing and documentation

**Estimated Effort:** 4-6 hours

**Files to Modify:**
- `backend/app/copilot/hitl_aware_agent.py` (rename + extend)
- `backend/app/copilot/adk_runtime.py` (update imports)
- `frontend/components/client-provider.tsx` (project ID passing)
- `frontend/app/copilot-demo/page.tsx` (verify event handlers)

---

## Appendix: Code References

### Policy Service Implementation

**File:** `backend/app/services/orchestrator/phase_policy_service.py`

```python
class PhasePolicyService:
    def __init__(self, db: Session):
        self.db = db
        self.project_manager = ProjectManager(db)
        self.policies = self._load_policies()
    
    def evaluate(self, project_id: str, agent_type: str) -> PolicyDecision:
        """Evaluates if an agent is allowed to act in the project's current phase."""
        current_phase = self.project_manager.get_current_phase(project_id)
        phase_policy = self.policies.get(current_phase.lower())
        allowed_agents = phase_policy.get("allowed_agents", [])
        
        if agent_type in allowed_agents:
            return PolicyDecision(status="allowed", current_phase=current_phase, allowed_agents=allowed_agents)
        else:
            return PolicyDecision(
                status="denied",
                reason_code="agent_not_allowed",
                message=f"Agent '{agent_type}' is not allowed in the '{current_phase}' phase.",
                current_phase=current_phase,
                allowed_agents=allowed_agents
            )
```

### Frontend Policy Violation Handler

**File:** `frontend/app/copilot-demo/page.tsx` (lines 68-91)

```typescript
const handlePolicyViolation = (event: PolicyViolationEvent) => {
  const { status, message, current_phase, allowed_agents } = event.data;

  // Update the application state to show the policy guidance UI.
  setPolicyGuidance({
    status: status as "denied",
    message: message,
    currentPhase: current_phase,
    allowedAgents: allowed_agents as AgentType[],
  });

  const allowedAgentsString = allowed_agents.join(', ');
  const toastMessage = `
    **Policy Violation**
    ${message}
    **Current Phase:** ${current_phase}
    **Allowed Agents:** ${allowedAgentsString}
  `;

  toast.error("Action Blocked", {
    description: toastMessage,
    duration: 10000,
  });
};

const wsClient = websocketManager.getGlobalConnection();
const unsubscribePolicy = wsClient.on('policy_violation', handlePolicyViolation);
```

---

## Conclusion

The policy enforcement system is well-designed and functional, but completely bypassed by the CopilotKit integration architecture. The recommended fix (Option 3) integrates policy checking into the ADK agent execution layer with minimal changes and maximum leverage of existing infrastructure.

**Ready to implement upon approval.**
