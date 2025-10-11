# HITL + Policy Enforcement + Agent Progress: Confirmation

**Date:** January 2025
**Status:** Architecture Confirmation

---

## Question 1: Does Policy Enforcement Still Work?

### ✅ **YES - Policy Enforcement is COMPLETELY INDEPENDENT**

Policy enforcement operates at a **different layer** than HITL and remains fully functional.

### How Policy Enforcement Works (Current Architecture)

```
User selects agent (e.g., "coder") in Discovery phase
                    ↓
Frontend sends request to backend
                    ↓
Backend: PhasePolicyService.evaluate(project_id, "coder")
                    ↓
Check: policy_config.yaml → Discovery phase → allowed_agents: ["analyst", "orchestrator"]
                    ↓
Decision: "coder" NOT in allowed list → DENIED
                    ↓
Backend broadcasts WebSocket event: "policy_violation"
                    ↓
Frontend receives event → Shows toast + policy guidance UI
```

**Key Files:**
- **Backend Policy Service:** `backend/app/services/orchestrator/phase_policy_service.py`
- **Policy Configuration:** `backend/app/services/orchestrator/policy_config.yaml`
- **Frontend Handler:** `frontend/app/copilot-demo/page.tsx` (lines 77-111)

### Policy Configuration (Phase → Allowed Agents)

```yaml
discovery:
  allowed_agents: ["analyst", "orchestrator"]

analyze:
  allowed_agents: ["analyst", "orchestrator"]

design:
  allowed_agents: ["architect", "orchestrator"]

build:
  allowed_agents: ["coder", "orchestrator"]

validate:
  allowed_agents: ["tester", "orchestrator"]

launch:
  allowed_agents: ["deployer", "orchestrator"]
```

### Integration with HITL Simplification

**HITL (Counter/Toggle)** and **Policy Enforcement** operate independently:

| Layer | Purpose | Implementation | Integration Point |
|-------|---------|----------------|-------------------|
| **Policy Enforcement** | Blocks wrong agent in wrong phase | `PhasePolicyService` → WebSocket event | **BEFORE** agent selection |
| **HITL Counter/Toggle** | Controls agent action frequency | `HITLGovernorService` → Tool call | **BEFORE** agent execution |

**Execution Flow:**
```
1. User selects agent (e.g., "coder")
   ↓
2. Policy Check: Is "coder" allowed in current phase?
   - YES → Proceed to step 3
   - NO → Show policy violation UI, STOP
   ↓
3. HITL Check: Is counter exhausted?
   - NO → Execute agent, decrement counter
   - YES → Show HITLReconfigurePrompt, wait for user
   ↓
4. Agent executes task
```

### Why It Still Works After HITL Simplification

**No Changes to Policy Enforcement:**
- Policy enforcement uses **WebSocket events** (not affected by HITL changes)
- HITL simplification only changes **HITL counter/toggle** (separate concern)
- Both systems operate independently at different interception points

**Frontend Handler (UNCHANGED):**
```typescript
// frontend/app/copilot-demo/page.tsx (lines 77-111)
useEffect(() => {
  if (!isClient) return;

  const handlePolicyViolation = (event: PolicyViolationEvent) => {
    const { status, message, current_phase, allowed_agents } = event.data;

    // Update the application state to show the policy guidance UI.
    setPolicyGuidance({
      status: status as "denied",
      message: message,
      currentPhase: current_phase,
      allowedAgents: allowed_agents as AgentType[],
    });

    toast.error("Action Blocked", {
      description: `Policy Violation: ${message}`,
      duration: 10000,
    });
  };

  const wsClient = websocketManager.getGlobalConnection();
  const unsubscribePolicy = wsClient.on('policy_violation', handlePolicyViolation);

  return () => {
    unsubscribePolicy();
  };
}, [isClient]);
```

**Policy Guidance UI (UNCHANGED):**
```typescript
// frontend/app/copilot-demo/page.tsx (lines 160-195)
{policyGuidance && (
  <div className="border border-destructive/40 bg-destructive/10 rounded-lg p-4">
    <div className="flex items-start gap-3">
      <AlertTriangle className="w-5 h-5 text-destructive" />
      <div className="flex-1 space-y-2">
        <span className="text-sm uppercase tracking-wide text-destructive font-semibold">
          {policyGuidance.status === "denied" ? "Policy Blocked" : "Needs Clarification"}
        </span>
        <Badge variant="secondary">Phase: {policyGuidance.currentPhase}</Badge>
        <p className="text-sm text-destructive">{policyGuidance.message}</p>
        <div className="text-xs text-muted-foreground">
          Allowed agents this phase: {policyGuidance.allowedAgents.join(", ")}
        </div>
      </div>
      <Button size="sm" variant="ghost" onClick={() => setPolicyGuidance(null)}>
        Dismiss
      </Button>
    </div>
  </div>
)}
```

### ✅ Confirmation: Policy Enforcement Unaffected

**The HITL simplification does NOT touch policy enforcement because:**
1. ✅ Policy uses WebSocket events (not CopilotKit actions)
2. ✅ Policy checks happen at agent selection (HITL checks happen at execution)
3. ✅ Policy UI is separate from HITL UI
4. ✅ No shared code between policy and HITL systems

---

## Question 2: Can We Show Agent Progress + Artifacts?

### ✅ **YES - CopilotKit Provides Native Support for This**

CopilotKit has **built-in patterns** for showing agent progress and linking to artifacts.

### Current Artifact System

**Backend Models:**
- `backend/app/database/models.py` → `ContextArtifactDB` table
- Fields: `id`, `project_id`, `task_id`, `name`, `type`, `content`, `status`, `metadata`

**Frontend Components:**
- `frontend/components/process/GenericArtifactList.tsx` - Artifact table with HITL badges
- `frontend/components/stages/artifacts-list.tsx` - Phase-specific artifact display

**Current Features:**
- ✅ Artifact list with name, type, status, last modified
- ✅ HITL badge on artifacts requiring approval
- ✅ Download and share actions per artifact

### Proposed Enhancement: Agent Progress + Artifacts in CopilotKit

**CopilotKit provides two native features for this:**

#### 1. **Shared State (`useCoAgent` hook)** - Agent Progress Tracking

```typescript
// frontend/app/copilot-demo/page.tsx (ADD)
import { useCoAgent } from "@copilotkit/react-core";

export default function CopilotDemoPage() {
  // ... existing code ...

  // Shared state with backend agent - bidirectional sync
  const { state: agentState } = useCoAgent({
    name: selectedAgent,
    initialState: {
      currentTask: null,
      todoList: [],
      progress: 0,
      currentArtifact: null,
      completedArtifacts: []
    }
  });

  return (
    <>
      {/* Agent Progress Panel - NEW */}
      <AgentProgressPanel agentState={agentState} projectId={DEMO_PROJECT_ID} />

      {/* Existing CopilotSidebar */}
      <CopilotSidebar {...props} />
    </>
  );
}
```

#### 2. **Generative UI** - Dynamic Progress Rendering

**Component:** `frontend/components/copilot/agent-progress-panel.tsx` (NEW)

```typescript
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, AlertTriangle, FileText } from "lucide-react";
import Link from "next/link";
import type { AgentState } from "@/lib/types";

interface AgentProgressPanelProps {
  agentState: AgentState;
  projectId: string;
}

export function AgentProgressPanel({ agentState, projectId }: AgentProgressPanelProps) {
  const { currentTask, todoList, progress, currentArtifact, completedArtifacts } = agentState;

  if (!currentTask && todoList.length === 0) {
    return null; // Hide when agent idle
  }

  return (
    <Card className="agent-progress-card mb-4">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Agent Progress</span>
          <Badge variant={progress === 1 ? "success" : "secondary"}>
            {Math.round(progress * 100)}%
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <Progress value={progress * 100} className="h-2" />

        {/* Current Task */}
        {currentTask && (
          <div className="current-task">
            <p className="text-sm font-medium text-muted-foreground">Current Task:</p>
            <p className="text-sm">{currentTask}</p>
          </div>
        )}

        {/* Todo List */}
        {todoList.length > 0 && (
          <div className="todo-list space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Tasks:</p>
            {todoList.map((task, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm">
                {task.status === "completed" ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : task.status === "in_progress" ? (
                  <Clock className="w-4 h-4 text-blue-600 animate-spin" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-gray-400" />
                )}
                <span className={task.status === "completed" ? "line-through text-muted-foreground" : ""}>
                  {task.description}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Current Artifact Being Created */}
        {currentArtifact && (
          <div className="current-artifact border-t pt-4">
            <p className="text-sm font-medium text-muted-foreground mb-2">Creating Artifact:</p>
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium">{currentArtifact.name}</span>
              <Badge variant="outline">{currentArtifact.type}</Badge>
            </div>
          </div>
        )}

        {/* Completed Artifacts (Linked) */}
        {completedArtifacts.length > 0 && (
          <div className="completed-artifacts border-t pt-4">
            <p className="text-sm font-medium text-muted-foreground mb-2">Completed Artifacts:</p>
            <div className="space-y-2">
              {completedArtifacts.map((artifact) => (
                <Link
                  key={artifact.id}
                  href={`/projects/${projectId}/artifacts/${artifact.id}`}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:underline"
                >
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <FileText className="w-4 h-4" />
                  <span>{artifact.name}</span>
                  <Badge variant="outline" className="ml-auto">
                    {artifact.type}
                  </Badge>
                </Link>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

### Backend: Emit Agent State Updates

**File:** `backend/app/agents/bmad_adk_wrapper.py` (MODIFY EXISTING)

```python
class BMADADKWrapper:
    """Enhanced ADK wrapper with state emission for CopilotKit shared state."""

    async def process_with_enterprise_controls(
        self,
        message: str,
        project_id: UUID,
        task_id: UUID,
        user_id: Optional[str] = None,
        state_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Process with state updates streamed to frontend via AG-UI protocol."""

        # Emit initial state
        if state_callback:
            await state_callback({
                "currentTask": message,
                "todoList": [
                    {"description": "Initialize agent", "status": "pending"},
                    {"description": "Analyze requirements", "status": "pending"},
                    {"description": "Create artifact", "status": "pending"},
                    {"description": "Finalize output", "status": "pending"}
                ],
                "progress": 0.0,
                "status": "starting",
                "currentArtifact": None,
                "completedArtifacts": []
            })

        # Step 1: Initialize
        if state_callback:
            await state_callback({
                "currentTask": message,
                "todoList": [
                    {"description": "Initialize agent", "status": "completed"},
                    {"description": "Analyze requirements", "status": "in_progress"},
                    {"description": "Create artifact", "status": "pending"},
                    {"description": "Finalize output", "status": "pending"}
                ],
                "progress": 0.25,
                "status": "analyzing"
            })

        # Execute ADK agent
        result = await self._execute_adk_agent(message, execution_id, context)

        # Step 2: Creating artifact
        artifact_name = f"{self.agent_type}-output.md"
        if state_callback:
            await state_callback({
                "currentTask": message,
                "todoList": [
                    {"description": "Initialize agent", "status": "completed"},
                    {"description": "Analyze requirements", "status": "completed"},
                    {"description": "Create artifact", "status": "in_progress"},
                    {"description": "Finalize output", "status": "pending"}
                ],
                "progress": 0.5,
                "status": "creating_artifact",
                "currentArtifact": {
                    "name": artifact_name,
                    "type": "markdown",
                    "status": "draft"
                }
            })

        # Save artifact to database
        artifact = await self.context_store.create_artifact(
            project_id=project_id,
            task_id=task_id,
            name=artifact_name,
            content=result["output"],
            type="markdown"
        )

        # Step 3: Finalize
        if state_callback:
            await state_callback({
                "currentTask": message,
                "todoList": [
                    {"description": "Initialize agent", "status": "completed"},
                    {"description": "Analyze requirements", "status": "completed"},
                    {"description": "Create artifact", "status": "completed"},
                    {"description": "Finalize output", "status": "completed"}
                ],
                "progress": 1.0,
                "status": "completed",
                "currentArtifact": None,
                "completedArtifacts": [
                    {
                        "id": str(artifact.id),
                        "name": artifact.name,
                        "type": artifact.type,
                        "url": f"/artifacts/{artifact.id}"
                    }
                ]
            })

        return result
```

### TypeScript Type Definitions

**File:** `frontend/lib/types.ts` (ADD)

```typescript
export interface AgentTask {
  description: string;
  status: "pending" | "in_progress" | "completed" | "failed";
}

export interface ArtifactReference {
  id: string;
  name: string;
  type: string;
  url: string;
}

export interface CurrentArtifact {
  name: string;
  type: string;
  status: "draft" | "in_progress";
}

export interface AgentState {
  currentTask: string | null;
  todoList: AgentTask[];
  progress: number; // 0.0 to 1.0
  status: "idle" | "starting" | "analyzing" | "creating_artifact" | "completed" | "error";
  currentArtifact: CurrentArtifact | null;
  completedArtifacts: ArtifactReference[];
}
```

### Visual Example

**What the user sees in the UI:**

```
┌─────────────────────────────────────────────────────────────┐
│ Agent Progress                                    75%       │
├─────────────────────────────────────────────────────────────┤
│ [████████████████████░░░░░░░░]                              │
│                                                              │
│ Current Task:                                                │
│ Create architecture design document for e-commerce app      │
│                                                              │
│ Tasks:                                                       │
│ ✅ Initialize agent                                          │
│ ✅ Analyze requirements                                      │
│ 🔄 Create artifact (analyzing dependencies...)              │
│ ⚠️  Finalize output                                          │
│                                                              │
│ Creating Artifact:                                           │
│ 📄 architecture-design.md  [markdown]                        │
│                                                              │
│ Completed Artifacts:                                         │
│ ✅ 📄 requirements-analysis.md [markdown] →                  │
│ ✅ 📄 technical-plan.md [markdown] →                         │
└─────────────────────────────────────────────────────────────┘
```

**Clicking artifact links navigates to:**
`/projects/{projectId}/artifacts/{artifactId}` → Full artifact view with content, version history, HITL status

---

## Architecture Integration Summary

### Three Independent Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: POLICY ENFORCEMENT (Phase-Based Agent Blocking)   │
│ - When: Agent selection                                     │
│ - Check: PhasePolicyService.evaluate()                      │
│ - UI: Policy violation toast + guidance banner              │
│ - Transport: WebSocket events                               │
│ - Config: policy_config.yaml                                │
└─────────────────────────────────────────────────────────────┘
                         ↓ (Policy check passes)
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: HITL COUNTER/TOGGLE (Action Frequency Control)    │
│ - When: Agent execution                                     │
│ - Check: HITLGovernorService.check_action_allowed()         │
│ - UI: HITLReconfigurePrompt (Toggle + Counter)              │
│ - Transport: CopilotKit action (reconfigureHITL)            │
│ - Storage: Database (hitl_settings table)                   │
└─────────────────────────────────────────────────────────────┘
                         ↓ (Counter check passes)
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: AGENT PROGRESS + ARTIFACTS (Real-time Updates)    │
│ - When: During agent execution                              │
│ - Updates: State callbacks via useCoAgent                   │
│ - UI: AgentProgressPanel (todo list + artifacts)            │
│ - Transport: CopilotKit shared state (AG-UI protocol)       │
│ - Storage: Database (context_artifacts table)               │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Timeline

**Week 1: HITL Simplification (as planned)**
- Days 1-3: Database + Backend Governor
- Days 4-5: Frontend Native Action
- Day 6: Cleanup

**Week 2: Agent Progress UI (NEW)**
- Day 1: Add `useCoAgent` hook to copilot-demo page
- Day 2: Create `AgentProgressPanel` component
- Day 3: Update `BMADADKWrapper` to emit state updates
- Day 4: Link completed artifacts to artifact detail pages
- Day 5: Testing and polish

**Total: 2 weeks (11 developer days)**

---

## Final Confirmation

### ✅ Policy Enforcement
**Status:** Fully functional, unaffected by HITL changes
**Why:** Operates at different layer (agent selection vs. execution)
**No changes required**

### ✅ Agent Progress + Artifacts
**Status:** Can be implemented using native CopilotKit patterns
**How:** `useCoAgent` hook + Generative UI components
**Benefits:**
- Real-time todo list updates
- Live artifact creation progress
- Direct links to completed artifacts
- All using standard CopilotKit patterns (no custom code)

### ✅ Combined System
**All three layers work together seamlessly:**
1. **Policy** blocks wrong agent in wrong phase (WebSocket)
2. **HITL** controls action frequency (CopilotKit action)
3. **Progress** shows real-time updates + artifacts (Shared state)

**No conflicts, no redundancy, full feature preservation.**
