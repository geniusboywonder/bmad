# HITL and Policy Enforcement: Verified Actual State

**Date:** January 2025
**Status:** ✅ **VERIFIED AGAINST CODE**
**Purpose:** Ground truth document created after Winston's review

---

## Executive Summary

**Both Winston and Claude were partially correct:**

- ✅ **Policy enforcement EXISTS** - Implemented in `AgentCoordinator` (backend/app/services/orchestrator/agent_coordinator.py:14-38)
- ✅ **HITL counter EXISTS** - Implemented in agent task processor (backend/app/tasks/agent_tasks.py:204-286)
- ❌ **Policy enforcement NOT in HITLAwareLlmAgent** - Winston correct on this specific claim
- ⚠️ **Policy and HITL are SEPARATE layers** - Policy at task creation, HITL at task execution

---

## What Actually Exists (Verified)

### 1. Policy Enforcement (Phase-Based Agent Restrictions)

**Location:** `backend/app/services/orchestrator/phase_policy_service.py`

**Implementation:**
```python
class PhasePolicyService:
    """Enforces policies based on the project's current SDLC phase."""

    def __init__(self, db: Session):
        self.db = db
        self.project_manager = ProjectManager(db)
        self.policies = self._load_policies()  # Loads policy_config.yaml

    def evaluate(self, project_id: str, agent_type: str) -> PolicyDecision:
        """
        Evaluates if an agent is allowed to act in the project's current phase.

        Returns:
            PolicyDecision with status "allowed" or "denied"
        """
        current_phase = self.project_manager.get_current_phase(project_id)
        phase_policy = self.policies.get(current_phase.lower())
        allowed_agents = phase_policy.get("allowed_agents", [])

        if agent_type in allowed_agents:
            return PolicyDecision(status="allowed", ...)
        else:
            return PolicyDecision(status="denied", ...)
```

**File:** backend/app/services/orchestrator/phase_policy_service.py:24-93

**Integration Point:** `AgentCoordinator.create_task()`

```python
class AgentCoordinator:
    def __init__(self, db: Session):
        self.db = db
        self.phase_policy_service = PhasePolicyService(db)  # Line 24

    def create_task(self, project_id, agent_type, instructions, context_ids) -> Task:
        """Create a new task for an agent, enforcing phase policies."""

        # Enforce phase policy
        policy_decision = self.phase_policy_service.evaluate(project_id, agent_type)  # Line 36
        if policy_decision.status == "denied":
            raise PolicyViolationException(policy_decision)  # Line 38

        # Create task if allowed
        db_task = TaskDB(...)
        self.db.add(db_task)
        self.db.commit()
        return task
```

**File:** backend/app/services/orchestrator/agent_coordinator.py:22-74

**Configuration:** `backend/app/services/orchestrator/policy_config.yaml`

```yaml
# Example policy configuration
requirements:
  allowed_agents:
    - analyst
    - architect

design:
  allowed_agents:
    - architect
    - coder

implementation:
  allowed_agents:
    - coder
    - tester
```

**When Policy Enforcement Runs:**
- **Timing:** BEFORE task creation
- **Location:** `OrchestratorCore.create_task()` → `AgentCoordinator.create_task()` → Policy check
- **Effect:** If denied, task is NEVER created, exception raised immediately
- **User Notification:** PolicyViolationException propagates to API endpoint

---

### 2. HITL Counter System (Auto-Approval Budget)

**Location:** `backend/app/tasks/agent_tasks.py` (lines 204-286)

**Implementation:**
```python
# Inside process_agent_task Celery task
def process_agent_task(self, task_data):
    # ... task setup ...

    # HITL Counter Governor (Line 204)
    hitl_counter_service = HitlCounterService()
    is_auto_approved, _ = hitl_counter_service.check_and_decrement_counter(project_uuid)

    approval_granted = False

    if is_auto_approved:
        logger.info("Task auto-approved by HITL counter.")
        approval_granted = True
        approval_comment = "Auto-approved by HITL counter"
    else:
        logger.info("HITL counter limit reached. Falling back to manual approval.")

        # Create HitlAgentApprovalDB record (Line 234)
        approval_record = HitlAgentApprovalDB(
            project_id=project_uuid,
            task_id=task_uuid,
            agent_type=agent_type,
            request_type="PRE_EXECUTION",
            estimated_tokens=estimated_tokens,
            status="PENDING"
        )
        db.add(approval_record)
        db.commit()

        # Broadcast WebSocket event (Line 250)
        hitl_event = WebSocketEvent(
            event_type=EventType.HITL_REQUEST_CREATED,
            project_id=project_uuid,
            task_id=task_uuid,
            data={"approval_id": str(approval_id)}
        )
        loop.run_until_complete(websocket_manager.broadcast_event(hitl_event))

        # Poll for approval (Line 264)
        for _ in range(max_polls):
            db.refresh(approval_record)
            if approval_record.status == "APPROVED":
                approval_granted = True
                break
            elif approval_record.status == "REJECTED":
                approval_granted = False
                break

    if not approval_granted:
        raise AgentExecutionDenied("Human rejected agent execution")

    # Execute task with ADK (Line 289)
    result = loop.run_until_complete(adk_executor.execute_task(...))
```

**File:** backend/app/tasks/agent_tasks.py:204-289

**Counter Service:** `backend/app/services/hitl_counter_service.py`

```python
class HitlCounterService:
    """Redis-backed atomic counter for auto-approvals."""

    def check_and_decrement_counter(self, project_id: UUID) -> tuple[bool, int]:
        """
        Check if project has remaining auto-approvals and decrement if available.
        Uses Lua script for atomicity.

        Returns:
            (is_approved, remaining_count)
        """
        # Atomic Redis operation via Lua script
        remaining = self.redis_client.evalsha(...)
        if remaining > 0:
            return (True, remaining - 1)
        else:
            return (False, 0)
```

**File:** backend/app/services/hitl_counter_service.py:1-159

**When HITL Runs:**
- **Timing:** AFTER task created, DURING Celery task execution, BEFORE agent runs
- **Location:** `process_agent_task` Celery task
- **Effect:** If counter exhausted, creates HITL approval request, blocks task until human responds
- **User Notification:** WebSocket event with approval UI

---

### 3. Frontend HITL Display (Markdown Tags)

**Location:** `frontend/app/copilot-demo/page.tsx`

**Implementation:**
```typescript
// Markdown tag renderer (Line 259-301)
const renderers = {
  'hitl-approval': (props: any) => {
    const { approvalid, agenttype, taskid, estimatedtokens, estimatedcost } = props;

    // Duplicate prevention (Line 50)
    const createdApprovalIds = useRef(new Set<string>());

    // Check if already created
    if (createdApprovalIds.current.has(approvalid)) {
      return null;
    }

    // Create approval request in store
    addRequest({
      id: approvalid,
      projectId: projectId,
      agentType: agenttype,
      taskId: taskid,
      status: 'pending',
      ...
    });

    createdApprovalIds.current.add(approvalid);

    // Render inline approval component
    return <InlineHITLApproval requestId={approvalid} />;
  }
};
```

**File:** frontend/app/copilot-demo/page.tsx:259-301

**Approval Component:** `frontend/components/hitl/inline-hitl-approval.tsx`

```typescript
export function InlineHITLApproval({ requestId }: { requestId: string }) {
  const request = useHITLStore(state => state.requests.find(r => r.id === requestId));

  const handleApprove = async () => {
    await fetch(`/api/hitl/approve/${requestId}`, { method: 'POST' });
    updateRequestStatus(requestId, 'approved');
  };

  const handleReject = async () => {
    await fetch(`/api/hitl/reject/${requestId}`, { method: 'POST' });
    updateRequestStatus(requestId, 'rejected');
  };

  return (
    <div className="hitl-approval-card">
      <p>Agent {request.agentType} requests approval</p>
      <Button onClick={handleApprove}>Approve</Button>
      <Button onClick={handleReject}>Reject</Button>
    </div>
  );
}
```

**State Management:** `frontend/lib/stores/hitl-store.ts`

```typescript
interface HITLStore {
  requests: HITLRequest[];
  addRequest: (request: HITLRequest) => void;
  updateRequestStatus: (id: string, status: HITLStatus) => void;
  removeExpiredRequests: () => void;
}

export const useHITLStore = create<HITLStore>((set) => ({
  requests: [],
  addRequest: (request) => set(state => ({
    requests: [...state.requests, request]
  })),
  updateRequestStatus: (id, status) => set(state => ({
    requests: state.requests.map(r => r.id === id ? {...r, status} : r)
  })),
  removeExpiredRequests: () => set(state => ({
    requests: state.requests.filter(r => !isExpired(r))
  }))
}));
```

**File:** frontend/lib/stores/hitl-store.ts:1-150

---

### 4. Database Tables (7 HITL Tables)

**File:** `backend/app/database/models.py`

**HITL Tables:**
1. **`hitl_requests`** (Line 116) - Base HITL request tracking
2. **`hitl_agent_approvals`** (Line 141) - Agent execution approvals (USED BY CURRENT SYSTEM)
3. **`agent_budget_control`** (Line 167) - Token/cost budget management
4. **`emergency_stops`** (Line 188) - System-wide emergency stops
5. **`response_approvals`** (Line 203) - Agent output approvals (currently skipped)
6. **`recovery_sessions`** (Line 240) - Error recovery sessions
7. **`websocket_notifications`** (Line 279) - WebSocket event log

**Primary Table for HITL Counter:**
```python
class HitlAgentApprovalDB(Base):
    __tablename__ = "hitl_agent_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    agent_type = Column(String, nullable=False)
    request_type = Column(String, nullable=False)  # "PRE_EXECUTION", "RESPONSE"
    request_data = Column(JSONB, nullable=True)
    estimated_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    actual_tokens_used = Column(Integer, nullable=True)
    actual_cost = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="PENDING")  # PENDING/APPROVED/REJECTED/EXPIRED
    user_comment = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
```

**File:** backend/app/database/models.py:141-166

---

### 5. HITLAwareLlmAgent (Tool Result Processor)

**Location:** `backend/app/copilot/hitl_aware_agent.py`

**Reality Check:**
```python
class HITLAwareLlmAgent(LlmAgent):
    """
    An LlmAgent that intercepts and processes HITL tool calls before standard execution.
    """

    def run(self, messages: List[Message], **kwargs) -> Message:
        session_id = kwargs.get("session_id")

        # ONLY handles reconfigureHITL tool result processing
        if messages and messages[-1].role == "tool" and messages[-1].name == "reconfigureHITL":
            logger.info("HITL-aware agent detected 'reconfigureHITL' tool call result.")
            # ... processes tool result ...
            return super().run(messages=new_messages, **kwargs)

        # Direct execution for all other cases
        return super().run(messages=messages, **kwargs)
```

**File:** backend/app/copilot/hitl_aware_agent.py:1-81

**What It Does:**
- ✅ Processes `reconfigureHITL` tool results (CopilotKit action)
- ✅ Parses `enabled` and `counter_limit` from tool response
- ✅ Updates Redis via `HitlCounterService`

**What It Does NOT Do:**
- ❌ No policy enforcement (Winston correct)
- ❌ No PhasePolicyService import
- ❌ No WebSocket event emission
- ❌ No HITL approval creation

**Purpose:** Handle frontend HITL reconfiguration tool calls (Toggle + Counter UI changes)

---

## Architecture Flow (Complete Picture)

### Task Creation Flow (Policy Enforcement)

```
User/Orchestrator Request
    ↓
OrchestratorCore.create_task(project_id, agent_type, instructions)
    ↓
AgentCoordinator.create_task()
    ├─→ PhasePolicyService.evaluate(project_id, agent_type)
    │   ├─→ Get current SDLC phase (requirements/design/implementation/testing/deployment)
    │   ├─→ Load policy_config.yaml
    │   ├─→ Check if agent_type in allowed_agents for current phase
    │   └─→ Return PolicyDecision (allowed/denied)
    │
    ├─→ If denied: raise PolicyViolationException ❌
    │   └─→ Task NEVER created, user receives error
    │
    └─→ If allowed: Create TaskDB record ✅
        └─→ Return Task object
```

**File References:**
- OrchestratorCore: backend/app/services/orchestrator/orchestrator_core.py:87-89
- AgentCoordinator: backend/app/services/orchestrator/agent_coordinator.py:26-74
- PhasePolicyService: backend/app/services/orchestrator/phase_policy_service.py:47-93

---

### Task Execution Flow (HITL Counter)

```
Task Created (passed policy check)
    ↓
AgentCoordinator.submit_task(task)
    ├─→ Submit to Celery queue
    └─→ Returns celery_task_id
    ↓
process_agent_task(task_data) [Celery Worker]
    ├─→ Update TaskDB status to WORKING
    ├─→ Broadcast TASK_STARTED WebSocket event
    │
    ├─→ HitlCounterService.check_and_decrement_counter(project_id)
    │   ├─→ Atomic Redis operation (Lua script)
    │   └─→ Returns (is_auto_approved, remaining_count)
    │
    ├─→ If is_auto_approved == True: ✅
    │   ├─→ approval_granted = True
    │   └─→ Skip manual approval workflow
    │
    ├─→ If is_auto_approved == False: ⏸️
    │   ├─→ Create HitlAgentApprovalDB record (status=PENDING)
    │   ├─→ Broadcast HITL_REQUEST_CREATED WebSocket event
    │   ├─→ Frontend receives event → Renders <hitl-approval> tag
    │   ├─→ Frontend displays InlineHITLApproval component
    │   ├─→ Poll database every 5 seconds for 30 minutes
    │   ├─→ User clicks Approve/Reject in UI
    │   ├─→ API endpoint updates HitlAgentApprovalDB.status
    │   └─→ Poll detects status change → approval_granted = True/False
    │
    ├─→ If approval_granted == False: ❌
    │   └─→ raise AgentExecutionDenied → Task FAILED
    │
    └─→ If approval_granted == True: ✅
        ├─→ ADKAgentExecutor.execute_task(task, handoff, context)
        ├─→ Update TaskDB status to COMPLETED
        ├─→ Broadcast TASK_COMPLETED WebSocket event
        └─→ Store result artifacts in ContextStoreService
```

**File References:**
- AgentCoordinator.submit_task: backend/app/services/orchestrator/agent_coordinator.py:76-149
- process_agent_task: backend/app/tasks/agent_tasks.py:80-350
- HitlCounterService: backend/app/services/hitl_counter_service.py:1-159
- ADKAgentExecutor: backend/app/agents/adk_executor.py:1-200

---

### HITL Reconfiguration Flow (Frontend Toggle + Counter)

```
User Changes HITL Settings in UI
    ↓
Frontend: useHITLStore.updateSettings(enabled, counter_limit)
    ├─→ Local state update (optimistic)
    └─→ useCopilotAction("reconfigureHITL", { enabled, counter_limit })
    ↓
CopilotKit AG-UI Runtime
    ├─→ Sends tool call to backend
    └─→ BMADAGUIRuntime.execute_with_governor() receives tool call
    ↓
HITLAwareLlmAgent.run(messages=[..., tool_result])
    ├─→ Detects messages[-1].name == "reconfigureHITL"
    ├─→ Parses enabled and counter_limit from tool result
    └─→ HitlCounterService.set_counter(project_id, counter_limit)
        └─→ Redis SET operation
    ↓
Frontend receives confirmation
    └─→ UI updates to show new settings
```

**File References:**
- useHITLStore: frontend/lib/stores/hitl-store.ts:1-150
- HITLAwareLlmAgent: backend/app/copilot/hitl_aware_agent.py:25-81
- HitlCounterService.set_counter: backend/app/services/hitl_counter_service.py:60-80

**Note:** Frontend comment (copilot-demo/page.tsx:113) says `reconfigureHITL` action was REMOVED due to "tool calling errors". Current reconfiguration mechanism unclear.

---

## What Does NOT Exist

### 1. Policy Enforcement in HITLAwareLlmAgent

**Winston's Claim:** ✅ **CORRECT**

**Evidence:**
```bash
grep -r "PhasePolicyService" backend/app/copilot/ --include="*.py"
# Result: No output (No files found)
```

**Reality:**
- HITLAwareLlmAgent: 81 lines total
- Only imports: `LlmAgent`, `Message`, `HitlCounterService`
- No policy check logic
- No policy-related WebSocket events

**Verdict:** Policy enforcement and HITLAwareLlmAgent are SEPARATE. Policy happens at task creation (AgentCoordinator), not during agent execution (HITLAwareLlmAgent).

---

### 2. MAF (Microsoft Agent Framework) Integration

**Winston's Claim:** ✅ **CORRECT**

**Evidence:**
```bash
grep -i "microsoft.*agent.*framework" backend/requirements.txt backend/pyproject.toml
# Result: No matches

find backend -name "*maf*" -o -name "*MAF*"
# Result: No files found
```

**Reality:**
- Google ADK is the primary agent framework
- `backend/app/agents/adk_executor.py` handles all agent execution
- No MAF dependencies or wrapper classes

**Verdict:** MAF migration was never attempted. ONEPLAN.md references to "ABANDONED" are misleading - it was never started.

---

### 3. Native useCopilotAction for HITL Reconfiguration

**Winston's Claim:** ⚠️ **PARTIALLY CORRECT**

**Evidence:**
```typescript
// frontend/app/copilot-demo/page.tsx:113
// REMOVED: reconfigureHITL action - causes tool calling errors
```

**Reality:**
- Comment confirms action was removed
- Current reconfiguration mechanism unclear from code review
- Markdown tag renderer exists but `reconfigureHITL` action registration missing

**Question for User:**
- How do users currently change HITL settings (toggle + counter)?
- Is there a UI for this, or is it database-only configuration?

**Verdict:** Winston correct that native action was removed. Unclear what replaced it.

---

## Winston vs Claude Reconciliation

### Where Winston Was Correct

1. ✅ **Policy enforcement NOT in HITLAwareLlmAgent** - Verified via grep and file inspection
2. ✅ **MAF migration never started** - No dependencies, no wrapper classes
3. ✅ **Frontend abandoned useCopilotAction** - Comment confirms removal
4. ✅ **7 existing HITL tables** - Comprehensive database schema exists
5. ✅ **My documents described non-existent code** - I trusted planning documents as status reports

### Where Claude Was Correct (After Investigation)

1. ✅ **Policy enforcement DOES exist** - Just not in HITLAwareLlmAgent (in AgentCoordinator instead)
2. ✅ **PhasePolicyService is real** - Loads policy_config.yaml, evaluates phase policies
3. ✅ **Policy and HITL are integrated** - Policy at task creation, HITL at task execution
4. ✅ **HITL counter system works** - Redis-backed atomic counter, WebSocket broadcasting

### Where Both Were Wrong

1. ❌ **Integration point assumption** - Claude thought policy was in agent run(), Winston thought it didn't exist at all
2. ❌ **Architecture completeness** - Neither recognized policy (task creation) vs HITL (task execution) separation
3. ❌ **Document status interpretation** - Claude trusted plans as reality, Winston dismissed everything as fiction

---

## Real Issues That Need Fixing

### Issue 1: Redis Volatility (Winston Correct)

**Problem:** HITL counter stored in Redis, lost on server restart

**Impact:** Users lose auto-approval budget if Redis restarts

**Solution:** Migrate HitlCounterService from Redis to PostgreSQL

**Approach:**
- Use existing `HitlAgentApprovalDB` table
- Add `counter_limit` and `counter_current` columns to `projects` table
- Keep atomic decrement logic (database transaction replaces Lua script)
- Maintain backward compatibility

**Timeline:** 2 days
- Day 1: Add columns, migrate HitlCounterService logic
- Day 2: Testing, rollout

**Files to Modify:**
- backend/alembic/versions/XXX_add_hitl_counter_to_projects.py (new migration)
- backend/app/services/hitl_counter_service.py (replace Redis with SQLAlchemy)
- backend/app/database/models.py (add columns to ProjectDB)

---

### Issue 2: Frontend Duplicate Tracking Manual (Winston Correct)

**Problem:** `createdApprovalIds` ref in page component is fragile

**Current Implementation:**
```typescript
// frontend/app/copilot-demo/page.tsx:50
const createdApprovalIds = useRef(new Set<string>());

// frontend/app/copilot-demo/page.tsx:272
if (createdApprovalIds.current.has(approvalid)) {
  return null; // Prevent duplicate
}
createdApprovalIds.current.add(approvalid);
```

**Problem:**
- Ref survives re-renders but NOT page navigations
- No persistence across browser refreshes
- Manual set management in component

**Solution:** Move to `useHITLStore`

**Approach:**
```typescript
// In hitl-store.ts
interface HITLStore {
  requests: HITLRequest[];
  processedApprovalIds: Set<string>; // NEW
  addRequest: (request: HITLRequest) => void;
  isApprovalProcessed: (id: string) => boolean; // NEW
  markApprovalProcessed: (id: string) => void; // NEW
}

// In copilot-demo/page.tsx
const { isApprovalProcessed, markApprovalProcessed } = useHITLStore();

if (isApprovalProcessed(approvalid)) {
  return null;
}
markApprovalProcessed(approvalid);
```

**Timeline:** 1 day
- Update hitl-store.ts with new fields
- Replace ref logic in page.tsx
- Test duplicate prevention

**Files to Modify:**
- frontend/lib/stores/hitl-store.ts
- frontend/app/copilot-demo/page.tsx

---

### Issue 3: Removed useCopilotAction Investigation (Winston Correct)

**Problem:** Comment says "causes tool calling errors" but no details

**Current State:**
- `reconfigureHITL` action was removed
- HITLAwareLlmAgent still processes `reconfigureHITL` tool results
- No obvious UI for changing HITL settings

**Questions:**
1. How do users currently change HITL toggle + counter?
2. Was removal permanent or temporary?
3. What were the "tool calling errors"?
4. Should we re-implement with fix, or use different pattern?

**Investigation Required:**
- Check git history for removal commit
- Find original error messages
- Determine if CopilotKit/AG-UI version upgrade fixed issue
- Test `reconfigureHITL` tool registration with current versions

**Timeline:** 2 days
- Day 1: Git history analysis, root cause investigation
- Day 2: Test implementation with current CopilotKit version

**Files to Review:**
- Git log for frontend/app/copilot-demo/page.tsx
- Git log for backend/app/copilot/hitl_aware_agent.py
- CopilotKit package.json version history

---

## Recommendations

### Priority 1: Fix Redis Volatility (2 Days)

**Why:** Data loss issue affecting user experience

**Approach:** Winston's Phase 1 recommendation is correct
- Migrate HitlCounterService from Redis to PostgreSQL
- Use existing HITL database tables
- Maintain atomic operations
- Zero breaking changes to API

**Files:**
- backend/app/services/hitl_counter_service.py
- backend/app/database/models.py
- backend/alembic/versions/XXX_add_hitl_counter.py (new migration)

---

### Priority 2: Simplify Duplicate Tracking (1 Day)

**Why:** Fragile manual tracking in component

**Approach:** Move to Zustand store
- Centralized duplicate detection
- Automatic cleanup
- Persists across re-renders

**Files:**
- frontend/lib/stores/hitl-store.ts
- frontend/app/copilot-demo/page.tsx

---

### Priority 3: Investigate Removed Action (2 Days)

**Why:** Understand why `reconfigureHITL` was removed

**Approach:** Git forensics + current testing
- Find removal commit and error messages
- Test with current CopilotKit version
- Determine if re-implementation is safe

**Files:**
- Git history analysis
- frontend/app/copilot-demo/page.tsx
- backend/app/copilot/hitl_aware_agent.py

---

### Priority 4: Policy Integration Documentation (1 Day)

**Why:** Policy enforcement exists but not well documented

**Approach:** Create user-facing documentation
- How phase policies work
- How to configure policy_config.yaml
- What happens when agent denied
- How to override policies (if needed)

**Files:**
- docs/POLICY_ENFORCEMENT_USER_GUIDE.md (new)
- docs/architecture/architecture.md (update)

---

## Summary

### What Winston Got Right
- HITLAwareLlmAgent does NOT contain policy enforcement
- Redis volatility is a real issue
- Frontend duplicate tracking is manual and fragile
- My documents were based on planning docs, not actual code

### What Winston Got Wrong
- Policy enforcement DOES exist (just in AgentCoordinator, not HITLAwareLlmAgent)
- PhasePolicyService is real and integrated
- Architecture is not "broken" - it's working as designed

### What Claude Got Wrong
- Trusted planning documents as implementation status
- Did not verify code before creating implementation guides
- Missed the separation of policy (creation) vs HITL (execution)

### Ground Truth
- **Policy enforcement:** Task creation layer (AgentCoordinator + PhasePolicyService)
- **HITL counter:** Task execution layer (process_agent_task + HitlCounterService)
- **Frontend display:** Markdown tags + InlineHITLApproval component
- **Database:** 7 comprehensive HITL tables (HitlAgentApprovalDB primary)
- **HITLAwareLlmAgent:** Tool result processor for reconfiguration only

### What Needs Fixing
1. Redis → PostgreSQL migration (2 days) - **PRIORITY 1**
2. Duplicate tracking to Zustand store (1 day) - **PRIORITY 2**
3. Investigate removed useCopilotAction (2 days) - **PRIORITY 3**
4. Document policy enforcement (1 day) - **PRIORITY 4**

**Total Timeline:** 6 days to fix all real issues

---

## Appendix: Verified File References

### Backend
- **Policy Enforcement:**
  - backend/app/services/orchestrator/phase_policy_service.py (Lines 24-93)
  - backend/app/services/orchestrator/agent_coordinator.py (Lines 14-38)
  - backend/app/services/orchestrator/policy_config.yaml

- **HITL Counter:**
  - backend/app/tasks/agent_tasks.py (Lines 204-286)
  - backend/app/services/hitl_counter_service.py (Lines 1-159)

- **Database:**
  - backend/app/database/models.py (Lines 116, 141, 167, 188, 203, 240, 279)

- **Agent Execution:**
  - backend/app/agents/adk_executor.py (Lines 1-200)
  - backend/app/copilot/hitl_aware_agent.py (Lines 1-81)

### Frontend
- **HITL Display:**
  - frontend/app/copilot-demo/page.tsx (Lines 50, 113, 259-301)
  - frontend/components/hitl/inline-hitl-approval.tsx (Lines 1-150)
  - frontend/lib/stores/hitl-store.ts (Lines 1-150)

### Configuration
- backend/app/services/orchestrator/policy_config.yaml

---

**Status:** This document represents verified ground truth as of January 2025. All file references checked against actual code.
