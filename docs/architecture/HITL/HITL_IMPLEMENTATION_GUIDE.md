# HITL Toggle + Counter: Implementation Guide

**Date:** January 2025
**Target Audience:** Developers
**Estimated Time:** 1 week (6 developer days)
**Status:** Ready for Implementation

---

## Overview

Implement a simplified HITL (Human-in-the-Loop) control system using:
- **Toggle Switch:** Enable/disable HITL approval requirement
- **Counter:** Set number of auto-approved agent actions
- **Database Persistence:** Replace Redis with PostgreSQL for reliability
- **Native CopilotKit Pattern:** Use `useCopilotAction` instead of custom markdown tags

**User Experience:** Unchanged - same Toggle + Counter UI
**Backend:** Simplified - 35% less code, database persistence
**Architecture:** Integrated with existing policy enforcement (October 2025)

---

## Prerequisites

**Existing Implementation (October 2025):**
- ✅ Policy enforcement in `HITLAwareLlmAgent.run()` (checks phase-based agent restrictions)
- ✅ Project ID extraction from session_id via `_extract_project_id()`
- ✅ WebSocket events for `policy_violation`
- ✅ Frontend policy violation handlers

**What We're Adding:**
- HITL counter check in `HITLAwareLlmAgent.run()` (AFTER policy check)
- Database-backed HITL settings (replacing Redis)
- Native CopilotKit action for reconfiguration

**What We're Removing:**
- Redis-based `HitlCounterService`
- Custom markdown tag renderers
- Manual duplicate tracking logic

---

## Architecture Integration

### Execution Flow (Corrected)

```
HITLAwareLlmAgent.run(messages, session_id)
├── Extract project_id from session_id
├── 1. POLICY CHECK (EXISTING - October 2025)
│   └── PhasePolicyService.evaluate()
│       └── Denied? → Emit policy_violation WS event → STOP
├── 2. HITL COUNTER CHECK (NEW - Adding Now)
│   └── HITLGovernorService.check_action_allowed()
│       └── Exhausted? → Return reconfigureHITL tool call → STOP
├── 3. TOOL RESULT HANDLER (EXISTING - October 2025)
│   └── If reconfigureHITL result? → Update settings → Retry
└── 4. EXECUTE AGENT (EXISTING)
    └── super().run(messages)
```

**Critical:** HITL counter check MUST be added AFTER policy check in the SAME `run()` method.

---

## Day 1: Database Migration

### Task 1.1: Create Migration File

**File:** `backend/alembic/versions/XXXX_add_hitl_settings.py`

```python
"""Add HITL settings table for toggle and counter persistence.

Revision ID: XXXX (generate with: alembic revision --autogenerate -m "add hitl settings")
Creates: 2025-01-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'hitl_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False, server_default='default'),
        sa.Column('hitl_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('action_limit', sa.Integer(), nullable=False, server_default=sa.text('10')),
        sa.Column('actions_remaining', sa.Integer(), nullable=False, server_default=sa.text('10')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('project_id', 'session_id', name='uq_hitl_settings_project_session')
    )

    op.create_index('idx_hitl_settings_project', 'hitl_settings', ['project_id'])

def downgrade():
    op.drop_index('idx_hitl_settings_project')
    op.drop_table('hitl_settings')
```

### Task 1.2: Add Database Model

**File:** `backend/app/database/models.py` (ADD to existing file)

```python
class HITLSettingsDB(Base):
    """HITL toggle and counter settings per project/session."""
    __tablename__ = "hitl_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), nullable=False, default="default")
    hitl_enabled = Column(Boolean, nullable=False, default=True)
    action_limit = Column(Integer, nullable=False, default=10)
    actions_remaining = Column(Integer, nullable=False, default=10)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    project = relationship("ProjectDB", back_populates="hitl_settings")

    __table_args__ = (
        UniqueConstraint('project_id', 'session_id', name='uq_hitl_settings_project_session'),
        Index('idx_hitl_settings_project', 'project_id'),
    )
```

### Task 1.3: Run Migration

```bash
cd backend
alembic upgrade head
```

**Verify:**
```bash
psql -d bmad_dev -c "\d hitl_settings"
```

---

## Days 2-3: Backend Governor Service

### Task 2.1: Create Governor Service

**File:** `backend/app/services/hitl_governor_service.py` (NEW)

```python
"""
HITL Governor Service - Database-backed counter and toggle control.
Replaces Redis-based HitlCounterService with database persistence.
"""

import structlog
from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.models import HITLSettingsDB

logger = structlog.get_logger(__name__)

class HITLGovernorService:
    """Manages HITL toggle and counter with database persistence."""

    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_settings(self, project_id: UUID, session_id: str = "default") -> HITLSettingsDB:
        """Get existing settings or create with defaults."""
        settings = self.db.query(HITLSettingsDB).filter_by(
            project_id=project_id,
            session_id=session_id
        ).first()

        if not settings:
            settings = HITLSettingsDB(
                project_id=project_id,
                session_id=session_id,
                hitl_enabled=True,
                action_limit=10,
                actions_remaining=10
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
            logger.info("Created default HITL settings", project_id=str(project_id))

        return settings

    def check_action_allowed(self, project_id: UUID, session_id: str = "default") -> Dict[str, Any]:
        """
        Check if agent action is allowed based on toggle and counter.

        Returns:
            {
                "allowed": bool,
                "reason": str,
                "remaining": int,
                "total": int,
                "tool_call": dict | None
            }
        """
        settings = self._get_or_create_settings(project_id, session_id)

        # If HITL disabled, allow all actions (counter ignored)
        if not settings.hitl_enabled:
            return {
                "allowed": True,
                "reason": "hitl_disabled",
                "remaining": settings.actions_remaining,
                "total": settings.action_limit,
                "tool_call": None
            }

        # If counter available, decrement and allow
        if settings.actions_remaining > 0:
            settings.actions_remaining -= 1
            self.db.commit()

            logger.info(
                "HITL counter decremented",
                project_id=str(project_id),
                remaining=settings.actions_remaining
            )

            return {
                "allowed": True,
                "reason": "counter_available",
                "remaining": settings.actions_remaining,
                "total": settings.action_limit,
                "tool_call": None
            }

        # Counter exhausted - return tool call instruction for frontend
        logger.warning("HITL counter exhausted", project_id=str(project_id))

        return {
            "allowed": False,
            "reason": "counter_exhausted",
            "remaining": 0,
            "total": settings.action_limit,
            "tool_call": {
                "name": "reconfigureHITL",
                "arguments": {
                    "projectId": str(project_id),
                    "sessionId": session_id,
                    "currentLimit": settings.action_limit,
                    "currentStatus": settings.hitl_enabled,
                    "remaining": 0
                }
            }
        }

    def update_settings(
        self,
        project_id: UUID,
        session_id: str = "default",
        new_limit: Optional[int] = None,
        new_status: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update HITL settings from frontend action result."""
        settings = self._get_or_create_settings(project_id, session_id)

        if new_limit is not None:
            settings.action_limit = new_limit
            settings.actions_remaining = new_limit  # Reset counter to new limit

        if new_status is not None:
            settings.hitl_enabled = new_status

        self.db.commit()

        logger.info(
            "HITL settings updated",
            project_id=str(project_id),
            new_limit=new_limit,
            new_status=new_status
        )

        return {
            "enabled": settings.hitl_enabled,
            "limit": settings.action_limit,
            "remaining": settings.actions_remaining
        }
```

### Task 2.2: Integrate into HITLAwareLlmAgent

**File:** `backend/app/copilot/hitl_aware_agent.py` (MODIFY EXISTING)

**CRITICAL:** This file already contains policy enforcement (October 2025). We are ADDING HITL counter check.

```python
"""
Custom ADK LlmAgent with policy enforcement AND HITL counter.
"""

import json
import structlog
from uuid import UUID
from typing import List, Dict, Any, Optional

from google.adk.agents import LlmAgent
from a2a.types import Message
from app.services.orchestrator.phase_policy_service import PhasePolicyService
from app.services.hitl_governor_service import HITLGovernorService  # NEW IMPORT
from app.database.connection import get_session
from app.websocket.manager import websocket_manager
from app.websocket.events import EventType

logger = structlog.get_logger(__name__)

class HITLAwareLlmAgent(LlmAgent):
    """
    An LlmAgent with BOTH phase policy enforcement AND HITL counter.

    Execution Order:
    1. Extract project_id from session_id
    2. Check phase policy (is agent allowed in current phase?)
    3. Check HITL counter (is auto-approval limit reached?)
    4. Handle reconfigureHITL tool results
    5. Execute agent if all checks pass
    """

    def run(self, messages: List[Message], **kwargs) -> Message:
        session_id = kwargs.get("session_id")

        # Extract project ID from session (EXISTING - October 2025)
        project_id = self._extract_project_id(session_id)

        # ========================================
        # CHECK 1: PHASE POLICY (EXISTING - KEEP)
        # ========================================
        if project_id:
            db = next(get_session())
            try:
                policy_service = PhasePolicyService(db)
                decision = policy_service.evaluate(str(project_id), self.name)

                if decision.status == "denied":
                    logger.warning(
                        "Policy violation: agent not allowed in current phase",
                        agent=self.name,
                        project_id=str(project_id),
                        phase=decision.current_phase,
                        allowed_agents=decision.allowed_agents
                    )

                    # Emit WebSocket policy_violation event
                    websocket_manager.broadcast_project_event(
                        project_id=project_id,
                        event_type=EventType.POLICY_VIOLATION,
                        data={
                            "status": "denied",
                            "message": decision.message,
                            "current_phase": decision.current_phase,
                            "allowed_agents": decision.allowed_agents,
                            "agent_type": self.name
                        }
                    )

                    # Return policy violation message
                    allowed_list = ", ".join(decision.allowed_agents)
                    return Message(
                        role="assistant",
                        content=(
                            f"❌ **Policy Violation**\n\n"
                            f"{decision.message}\n\n"
                            f"**Current Phase:** {decision.current_phase}\n"
                            f"**Allowed Agents:** {allowed_list}\n\n"
                            f"Please select an allowed agent to continue."
                        )
                    )
            finally:
                db.close()

        # ========================================
        # CHECK 2: HITL COUNTER (NEW - ADD THIS)
        # ========================================
        if project_id:
            db = next(get_session())
            try:
                hitl_service = HITLGovernorService(db)
                hitl_decision = hitl_service.check_action_allowed(
                    project_id=project_id,
                    session_id=session_id or "default"
                )

                if not hitl_decision["allowed"]:
                    logger.warning(
                        "HITL counter exhausted",
                        project_id=str(project_id),
                        remaining=hitl_decision["remaining"],
                        total=hitl_decision["total"]
                    )

                    # Return tool call instruction for frontend
                    return Message(
                        role="assistant",
                        content=(
                            f"Action limit reached ({hitl_decision['remaining']}/{hitl_decision['total']}). "
                            f"Please reconfigure HITL settings to continue."
                        ),
                        tool_calls=[{
                            "id": f"call_hitl_{project_id}",
                            "type": "function",
                            "function": hitl_decision["tool_call"]
                        }]
                    )
            finally:
                db.close()

        # ========================================
        # CHECK 3: HITL TOOL RESULT (EXISTING - KEEP)
        # ========================================
        if messages and messages[-1].role == "tool" and messages[-1].name == "reconfigureHITL":
            logger.info("HITL-aware agent detected 'reconfigureHITL' tool call result.")

            tool_message = messages[-1]

            try:
                # Parse tool result from frontend
                response_data = json.loads(tool_message.content)
                new_limit = response_data.get("newLimit")
                new_status = response_data.get("newStatus")

                logger.info(
                    "Processing HITL reconfiguration from tool call.",
                    project_id=str(project_id),
                    new_limit=new_limit,
                    new_status=new_status,
                )

                # Update settings in database
                db = next(get_session())
                try:
                    hitl_service = HITLGovernorService(db)
                    hitl_service.update_settings(
                        project_id=project_id,
                        session_id=session_id or "default",
                        new_limit=new_limit,
                        new_status=new_status,
                    )
                finally:
                    db.close()

                # Remove tool call + result from history and retry
                logger.info("Retrying original user request after HITL reconfiguration.", project_id=str(project_id))
                new_messages = messages[:-2]

                # Re-run the agent with updated settings (recursive call)
                return self.run(messages=new_messages, **kwargs)

            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.error("Failed to parse 'reconfigureHITL' tool result.", error=str(e))
                # Let the agent proceed without the confusing tool message
                new_messages = messages[:-1]
                return self.run(messages=new_messages, **kwargs)

        # ========================================
        # EXECUTE AGENT (EXISTING - KEEP)
        # ========================================
        return super().run(messages=messages, **kwargs)

    def _extract_project_id(self, session_id: Any) -> Optional[UUID]:
        """Extract project UUID from session_id (EXISTING - October 2025)."""
        if not session_id:
            return None

        try:
            # Try direct UUID conversion
            return UUID(str(session_id))
        except (ValueError, TypeError, AttributeError):
            pass

        # Try to extract UUID from compound session_id
        if isinstance(session_id, str):
            parts = session_id.split("-")
            if len(parts) >= 5:  # UUID has 5 parts
                try:
                    potential_uuid = "-".join(parts[:5])
                    return UUID(potential_uuid)
                except (ValueError, TypeError):
                    pass

        return None
```

### Task 2.3: Unit Tests

**File:** `backend/tests/unit/services/test_hitl_governor_service.py` (NEW)

```python
import pytest
from uuid import uuid4
from app.services.hitl_governor_service import HITLGovernorService
from app.database.models import HITLSettingsDB

@pytest.fixture
def hitl_service(test_db):
    return HITLGovernorService(test_db)

def test_check_action_allowed_with_counter(hitl_service, test_db):
    """Test counter decrement on each action."""
    project_id = uuid4()

    # First 10 actions should be allowed
    for i in range(10, 0, -1):
        result = hitl_service.check_action_allowed(project_id)
        assert result["allowed"] is True
        assert result["remaining"] == i - 1

    # 11th action should be blocked
    result = hitl_service.check_action_allowed(project_id)
    assert result["allowed"] is False
    assert result["reason"] == "counter_exhausted"
    assert result["tool_call"] is not None
    assert result["tool_call"]["name"] == "reconfigureHITL"

def test_check_action_allowed_with_hitl_disabled(hitl_service, test_db):
    """Test that HITL disabled allows all actions."""
    project_id = uuid4()

    # Disable HITL
    hitl_service.update_settings(project_id, new_status=False)

    # Should allow unlimited actions
    for _ in range(20):
        result = hitl_service.check_action_allowed(project_id)
        assert result["allowed"] is True
        assert result["reason"] == "hitl_disabled"

def test_update_settings_resets_counter(hitl_service, test_db):
    """Test settings update resets counter."""
    project_id = uuid4()

    # Exhaust counter
    for _ in range(10):
        hitl_service.check_action_allowed(project_id)

    # Counter should be exhausted
    result = hitl_service.check_action_allowed(project_id)
    assert result["allowed"] is False

    # Update settings with new limit
    update_result = hitl_service.update_settings(project_id, new_limit=5)
    assert update_result["remaining"] == 5

    # Should allow 5 more actions
    for i in range(5, 0, -1):
        result = hitl_service.check_action_allowed(project_id)
        assert result["allowed"] is True
        assert result["remaining"] == i - 1
```

---

## Days 4-5: Frontend Native Action

### Task 4.1: Remove Markdown Tag Renderer

**File:** `frontend/app/copilot-demo/page.tsx` (MODIFY EXISTING)

**REMOVE this section** (lines ~259-301):
```typescript
markdownTagRenderers={{
  "hitl-approval": ({ requestId, children }) => {
    // ... manual request creation logic ...
  }
}}
```

**ADD native CopilotKit action** (after imports, before return statement):

```typescript
import { useCopilotAction } from "@copilotkit/react-core";
import { HITLReconfigurePrompt } from "@/components/hitl/HITLReconfigurePrompt";

export default function CopilotDemoPage() {
  const [isClient, setIsClient] = useState(false);
  const { selectedAgent, setSelectedAgent, setProjectId } = useAgent();
  const policyGuidance = useAppStore((state) => state.policyGuidance);
  const setPolicyGuidance = useAppStore((state) => state.setPolicyGuidance);

  const DEMO_PROJECT_ID = "018f9fa8-b639-4858-812d-57f592324a35";

  useEffect(() => {
    setIsClient(true);
    setProjectId(DEMO_PROJECT_ID);
  }, [setProjectId]);

  // Policy violation handler (EXISTING - KEEP)
  useEffect(() => {
    if (!isClient) return;

    const handlePolicyViolation = (event: PolicyViolationEvent) => {
      const { status, message, current_phase, allowed_agents } = event.data;

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
  }, [isClient, setPolicyGuidance]);

  // HITL reconfiguration action (NEW - ADD THIS)
  useCopilotAction({
    name: "reconfigureHITL",
    description: "Reconfigure HITL settings when action limit reached",
    parameters: [
      { name: "projectId", type: "string", description: "Project ID", required: true },
      { name: "sessionId", type: "string", description: "Session ID", required: false },
      { name: "currentLimit", type: "number", description: "Current action limit", required: true },
      { name: "currentStatus", type: "boolean", description: "Current HITL enabled status", required: true },
      { name: "remaining", type: "number", description: "Actions remaining", required: true }
    ],
    handler: async (args) => {
      const { projectId, sessionId, currentLimit, currentStatus, remaining } = args;

      // CopilotKit will render this component inline in chat
      return new Promise((resolve) => {
        // Note: CopilotKit handles rendering via render property below
      });
    },
    render: (args) => {
      // Render HITLReconfigurePrompt inline in chat
      return (
        <HITLReconfigurePrompt
          initialLimit={args.currentLimit}
          initialStatus={args.currentStatus}
          onContinue={(response) => {
            // CopilotKit automatically sends this back to backend as tool result
            args.handler(response);
          }}
          onStop={() => {
            args.handler({ newLimit: 0, newStatus: false, stopped: true });
          }}
        />
      );
    }
  });

  return (
    <>
      <Toaster />
      <div className="min-h-screen flex flex-col">
        <div className="container mx-auto p-6 flex-1">
          {/* Policy guidance banner (EXISTING - KEEP) */}
          {policyGuidance && (
            <div className="mt-4 border border-destructive/40 bg-destructive/10 rounded-lg p-4">
              {/* ... existing policy UI ... */}
            </div>
          )}

          {/* Agent selector (EXISTING - KEEP) */}
          {isClient && (
            <div className="mt-4">
              <label className="text-sm font-medium mb-2 block">Select Agent:</label>
              <div className="flex gap-2 flex-wrap">
                {availableAgents.map((agent) => (
                  <button
                    key={agent.name}
                    onClick={() => setSelectedAgent(agent.name)}
                    className={/* ... existing styles ... */}
                    disabled={
                      !!policyGuidance &&
                      policyGuidance.allowedAgents.length > 0 &&
                      !policyGuidance.allowedAgents.includes(agent.name as AgentType)
                    }
                  >
                    {agent.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* CopilotKit chat (MODIFIED - NO MARKDOWN RENDERERS) */}
          {isClient && (
            <div data-testid="chat-section">
              <CopilotSidebar
                labels={{
                  title: `BMAD ${selectedAgent.charAt(0).toUpperCase() + selectedAgent.slice(1)} Agent`,
                  initial: `I'm your ${selectedAgent} agent. How can I help you today?`
                }}
                instructions={`You are the BMAD ${selectedAgent} agent. Your full instructions are loaded from the backend. HITL (Human-in-the-Loop) is managed by the backend session governor. When counter is exhausted, you will be instructed to call the reconfigureHITL action.`}
                // NO markdownTagRenderers - use native action pattern
              />
            </div>
          )}
        </div>
      </div>
    </>
  );
}
```

### Task 4.2: Verify HITLReconfigurePrompt Component

**File:** `frontend/components/hitl/HITLReconfigurePrompt.tsx` (VERIFY EXISTS - NO CHANGES NEEDED)

The component should already exist with Toggle + Counter UI. No modifications required.

---

## Day 6: Cleanup & Testing

### Task 6.1: Deprecate Old Code

**Remove/Deprecate:**
```bash
# Backend
❌ backend/app/services/hitl_counter_service.py  # Redis-based (replaced)

# Update references
grep -r "HitlCounterService" backend/app --include="*.py"
# Replace all with HITLGovernorService
```

### Task 6.2: Integration Testing

**Test Scenario 1: Policy Enforcement Still Works**
```bash
# 1. Start backend: cd backend && uvicorn app.main:app --reload
# 2. Start frontend: cd frontend && npm run dev
# 3. Open: http://localhost:3000/copilot-demo
# 4. Select "Analyst" agent
# 5. Verify policy violation shows if project is in "design" phase
```

**Test Scenario 2: HITL Counter Works**
```bash
# 1. Same setup as above
# 2. Ensure project is in correct phase for selected agent
# 3. Send 10 messages to agent
# 4. On 11th message, verify HITLReconfigurePrompt appears
# 5. Adjust counter, click Continue
# 6. Verify agent continues execution
```

**Test Scenario 3: Toggle Disables HITL**
```bash
# 1. Same setup
# 2. When HITLReconfigurePrompt appears, toggle HITL OFF
# 3. Click Continue
# 4. Send 20+ messages - should not prompt again
```

### Task 6.3: Update Documentation

**File:** `docs/CHANGELOG.md` (ADD entry)

```markdown
## [Version X.X.X] - 2025-01-XX

### Changed
- **HITL Simplification:** Replaced Redis-based HITL counter with database persistence
- Integrated HITL counter check into `HITLAwareLlmAgent` alongside policy enforcement
- Replaced custom markdown tag rendering with native `useCopilotAction` pattern
- Removed ~140 LOC of custom HITL frontend code

### Added
- Database table `hitl_settings` for persistent HITL configuration
- `HITLGovernorService` for database-backed HITL counter management
- Native CopilotKit action for HITL reconfiguration

### Removed
- `HitlCounterService` (Redis-based)
- Custom markdown tag renderer for HITL approvals
- Manual duplicate tracking logic (`createdApprovalIds`)

### Technical Notes
- HITL counter check now executes AFTER policy check in agent execution flow
- Execution order: Policy → HITL Counter → Tool Result → Execute
- Frontend policy violation handling unchanged (WebSocket events)
```

---

## Testing Checklist

- [ ] Database migration runs successfully
- [ ] `hitl_settings` table created with correct schema
- [ ] `HITLGovernorService` unit tests pass
- [ ] Policy enforcement still works (analyst blocked in design phase)
- [ ] HITL counter decrements on each agent execution
- [ ] Counter exhaustion triggers `reconfigureHITL` tool call
- [ ] `HITLReconfigurePrompt` appears in chat when counter exhausted
- [ ] Toggle switch enables/disables HITL
- [ ] Counter reset works correctly
- [ ] Agent resumes after reconfiguration
- [ ] Policy check happens BEFORE HITL counter check
- [ ] WebSocket `policy_violation` events still emitted
- [ ] Policy guidance UI displays correctly

---

## Rollback Plan

If issues arise:

**Immediate Rollback (<5 minutes):**
1. Revert `hitl_aware_agent.py` to remove HITL counter check
2. Keep policy enforcement (lines with `PhasePolicyService`)
3. Revert `copilot-demo/page.tsx` to use markdown tag renderer

**Full Rollback (<30 minutes):**
1. Run migration downgrade: `alembic downgrade -1`
2. Revert all backend changes
3. Revert all frontend changes
4. Restart services

---

## Key Files Modified

### Backend
- ✅ `backend/alembic/versions/XXXX_add_hitl_settings.py` (new)
- ✅ `backend/app/database/models.py` (add HITLSettingsDB)
- ✅ `backend/app/services/hitl_governor_service.py` (new)
- ✅ `backend/app/copilot/hitl_aware_agent.py` (add HITL counter check)
- ✅ `backend/tests/unit/services/test_hitl_governor_service.py` (new)

### Frontend
- ✅ `frontend/app/copilot-demo/page.tsx` (remove markdown renderer, add useCopilotAction)
- ✅ `frontend/components/hitl/HITLReconfigurePrompt.tsx` (verify exists, no changes)

### Deprecated
- ❌ `backend/app/services/hitl_counter_service.py` (delete)

---

## Success Criteria

1. ✅ Toggle + Counter UI preserved (user experience unchanged)
2. ✅ Database persistence (counter survives server restarts)
3. ✅ Policy enforcement still works (phase-based agent blocking)
4. ✅ Native CopilotKit pattern (no custom markdown tags)
5. ✅ 35% code reduction (fewer LOC, cleaner architecture)
6. ✅ Execution order correct: Policy → HITL → Execute

---

## Support & Questions

**Critical Integration Point:**
The HITL counter check MUST be added to `HITLAwareLlmAgent.run()` AFTER the existing policy check (October 2025 implementation). Do NOT create a separate integration point.

**Policy Enforcement:**
Policy enforcement is already implemented in `HITLAwareLlmAgent.run()`. Do NOT modify or remove it. Your HITL counter check should be added as CHECK 2 (after policy, before execution).

**Contact:** Review corrected architecture in `docs/HITL_POLICY_PROGRESS_CONFIRMATION_CORRECTED.md` if unclear.
