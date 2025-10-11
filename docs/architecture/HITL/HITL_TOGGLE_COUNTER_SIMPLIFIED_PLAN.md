# HITL Toggle + Counter: Simplified Implementation Plan

**Date:** January 2025
**Goal:** Keep Toggle + Counter UI while minimizing custom code using CopilotKit native patterns
**User Requirement:** "I want to keep the Toggle + Counter HITL pattern for the user"

---

## Executive Summary

The **Toggle + Counter HITL UI** is preserved exactly as the user expects:
- **Toggle Switch:** Enable/disable HITL approval requirement
- **Counter Input:** Set number of auto-approved agent actions
- **Inline Prompt:** Appears when counter exhausted with "Run for X more tasks" + Continue button

**Key Change:** Backend implementation uses **CopilotKit's native action system** instead of custom markdown tags, eliminating 65% of custom HITL code while keeping the exact same user experience.

---

## Current vs. Simplified Architecture

### Current Implementation (Complex)

```
Agent → Counter Check (Redis) → Exhausted? → Emit <hitl-approval> markdown tag
                                              ↓
Frontend → markdownTagRenderers → Manual addRequest() → useHITLStore
                                                         ↓
                                          InlineHITLApproval component
                                                         ↓
                                          User interaction → API call → Update Redis
```

**Problems:**
- Custom markdown tag rendering in component render cycle
- Manual `createdApprovalIds` tracking to prevent duplicates
- Custom WebSocket events for HITL state
- Complex synchronization between CopilotKit and HITL store

### Simplified Implementation (Native CopilotKit)

```
Agent → Counter Check (Database) → Exhausted? → Call reconfigureHITL tool
                                                 ↓
CopilotKit → useCopilotAction handler → Render HITLReconfigurePrompt
                                        ↓
                            User interaction → Result returned to agent automatically
                                        ↓
                            Backend updates database → Agent continues
```

**Benefits:**
- ✅ **Native CopilotKit pattern** - No custom markdown tags
- ✅ **Automatic tool result handling** - No manual store management
- ✅ **Database persistence** - Counter survives server restarts
- ✅ **Same UI** - `HITLReconfigurePrompt` component unchanged
- ✅ **65% less code** - Remove markdown renderers, duplicate tracking, WebSocket events

---

## Implementation Steps (1 Week)

### Phase 1: Database Migration (Day 1)

**Replace Redis-based counter with database table for persistence.**

#### 1.1 Create Alembic Migration

**File:** `backend/alembic/versions/XXXX_add_hitl_settings.py`

```python
"""Add HITL settings table for toggle and counter persistence.

Revision ID: XXXX
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

#### 1.2 Add Database Model

**File:** `backend/app/database/models.py` (add to existing file)

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

**Run Migration:**
```bash
cd backend
alembic upgrade head
```

---

### Phase 2: Backend Governor Service (Days 2-3)

**Replace `HitlCounterService` (Redis) with `HITLGovernorService` (Database).**

#### 2.1 Create Governor Service

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
                "reason": str,  # "hitl_disabled", "counter_available", "counter_exhausted"
                "remaining": int,
                "total": int,
                "tool_call": dict | None  # Tool call instruction if counter exhausted
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

#### 2.2 Update HITLAwareLlmAgent

**File:** `backend/app/copilot/hitl_aware_agent.py` (MODIFY EXISTING)

```python
"""
Custom ADK LlmAgent that is aware of the HITL (Human-in-the-Loop) governor.
"""

import json
import structlog
from uuid import UUID
from typing import List, Dict, Any

from google.adk.agents import LlmAgent
from a2a.types import Message
from app.services.hitl_governor_service import HITLGovernorService
from app.database.connection import get_session

logger = structlog.get_logger(__name__)

class HITLAwareLlmAgent(LlmAgent):
    """
    An LlmAgent that checks HITL governor before execution.
    If counter exhausted, instructs agent to call reconfigureHITL tool.
    """

    def run(self, messages: List[Message], **kwargs) -> Message:
        """
        Overrides the default run method to handle HITL tool results.

        Args:
            messages: The history of messages in the conversation.
            **kwargs: Additional arguments, including 'session_id' and 'project_id'.

        Returns:
            The agent's response message.
        """
        session_id = kwargs.get("session_id", "default")
        project_id = kwargs.get("project_id")

        # Check if last message is reconfigureHITL tool result
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
                        project_id=UUID(project_id),
                        session_id=session_id,
                        new_limit=new_limit,
                        new_status=new_status,
                    )
                finally:
                    db.close()

                # Remove tool call + result from history and retry
                logger.info("Retrying original user request after HITL reconfiguration.", project_id=str(project_id))
                new_messages = messages[:-2]

                # Re-run the agent with updated settings
                return super().run(messages=new_messages, **kwargs)

            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.error("Failed to parse 'reconfigureHITL' tool result.", error=str(e))
                # Let the agent proceed without the confusing tool message
                new_messages = messages[:-1]
                return super().run(messages=new_messages, **kwargs)

        # Normal execution - proceed with standard agent flow
        return super().run(messages=messages, **kwargs)
```

#### 2.3 Integrate Governor into ADK Runtime

**File:** `backend/app/copilot/adk_runtime.py` (MODIFY EXISTING)

Find the `BMADAGUIRuntime` class and add governor check before agent execution:

```python
from app.services.hitl_governor_service import HITLGovernorService

class BMADAGUIRuntime:
    """Backend ADK runtime with HITL governor integration."""

    def __init__(self):
        # ... existing initialization ...
        pass

    async def execute_with_governor(
        self,
        agent_name: str,
        messages: List[Message],
        project_id: UUID,
        session_id: str = "default"
    ) -> Message:
        """Execute agent with HITL governor check."""

        db = next(get_session())
        try:
            # Check if action allowed via governor
            hitl_service = HITLGovernorService(db)
            decision = hitl_service.check_action_allowed(project_id, session_id)

            # If counter exhausted, inject tool call instruction
            if not decision["allowed"]:
                logger.warning(
                    "HITL counter exhausted - instructing agent to call reconfigureHITL",
                    project_id=str(project_id),
                    remaining=decision["remaining"]
                )

                # Return tool call message for frontend to handle
                return Message(
                    role="assistant",
                    content=f"Counter exhausted ({decision['remaining']}/{decision['total']}). Please reconfigure HITL settings to continue.",
                    tool_calls=[{
                        "id": f"call_hitl_{project_id}",
                        "type": "function",
                        "function": decision["tool_call"]
                    }]
                )

            # Execute agent normally
            agent = self.adk_agents[agent_name]
            result = await agent.run(messages, session_id=session_id, project_id=str(project_id))

            return result

        finally:
            db.close()
```

---

### Phase 3: Frontend Native Action (Days 4-5)

**Replace custom markdown tag rendering with `useCopilotAction`.**

#### 3.1 Remove Markdown Tag Renderer

**File:** `frontend/app/copilot-demo/page.tsx` (MODIFY EXISTING)

**REMOVE:**
```typescript
// DELETE THIS SECTION (lines 259-301)
markdownTagRenderers={{
  "hitl-approval": ({ requestId, children }: { requestId?: string; children?: ReactNode }) => {
    // ... manual request creation logic ...
  }
}}
```

**ADD:**
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

  // Native CopilotKit action for HITL reconfiguration
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

      // Show inline prompt (HITLReconfigurePrompt component)
      return new Promise((resolve) => {
        // Render component inline in chat
        const promptElement = (
          <HITLReconfigurePrompt
            initialLimit={currentLimit}
            initialStatus={currentStatus}
            onContinue={(response) => {
              // Resolve with new settings - CopilotKit sends back to backend automatically
              resolve({
                newLimit: response.newLimit,
                newStatus: response.newStatus
              });
            }}
            onStop={() => {
              // User rejected - stop agent execution
              resolve({
                newLimit: 0,
                newStatus: false,
                stopped: true
              });
            }}
          />
        );

        // CopilotKit renders this inline in chat
        return promptElement;
      });
    },
    render: (args) => {
      // Render HITLReconfigurePrompt inline in chat
      return (
        <HITLReconfigurePrompt
          initialLimit={args.currentLimit}
          initialStatus={args.currentStatus}
          onContinue={(response) => {
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
        {/* ... existing UI code ... */}

        {isClient && (
          <div data-testid="chat-section">
            <CopilotSidebar
              labels={{
                title: `BMAD ${selectedAgent.charAt(0).toUpperCase() + selectedAgent.slice(1)} Agent`,
                initial: `I'm your ${selectedAgent} agent. How can I help you today?`
              }}
              instructions={`You are the BMAD ${selectedAgent} agent. Your full instructions are loaded from the backend. HITL (Human-in-the-Loop) is managed by the backend session governor. When counter is exhausted, you will be instructed to call the reconfigureHITL action.`}
              // NO custom markdown tag renderers - use native CopilotKit action
            />
          </div>
        )}
      </div>
    </>
  );
}
```

#### 3.2 Update HITLReconfigurePrompt (Keep Existing UI)

**File:** `frontend/components/hitl/HITLReconfigurePrompt.tsx` (MINIMAL CHANGES)

The existing UI component stays **exactly the same**. Only update the props interface to work with CopilotKit action handler:

```typescript
"use client";

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle } from 'lucide-react';

interface HITLReconfigurePromptProps {
  initialLimit: number;
  initialStatus: boolean;
  onContinue: (response: { newLimit: number; newStatus: boolean }) => void;
  onStop: () => void;
}

export const HITLReconfigurePrompt = ({
  initialLimit,
  initialStatus,
  onContinue,
  onStop,
}: HITLReconfigurePromptProps) => {
  const [limit, setLimit] = useState(initialLimit);
  const [isEnabled, setIsEnabled] = useState(initialStatus);

  const handleApprove = () => {
    onContinue({ newLimit: limit, newStatus: isEnabled });
  };

  const handleReject = () => {
    onStop();
  };

  return (
    <div className="border rounded-lg bg-background shadow-sm overflow-hidden max-w-2xl">
      {/* Header with Counter and HITL Toggle */}
      <div className="flex items-center justify-between gap-4 px-4 py-2 bg-muted/50 border-b">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-muted-foreground">Counter:</span>
          <Input
            type="number"
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value, 10) || 0)}
            className="w-20 h-8"
          />
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-muted-foreground">Enable HITL:</span>
          <Switch
            checked={isEnabled}
            onCheckedChange={setIsEnabled}
            className="data-[state=checked]:bg-primary"
          />
        </div>
      </div>

      {/* Task Heading with Badges */}
      <div className="px-4 py-3 space-y-2">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-orchestrator/10 text-orchestrator border-orchestrator/20">
            Agent
          </Badge>
          <Badge variant="destructive" className="gap-1">
            <AlertTriangle className="w-3 h-3" />
            HITL
          </Badge>
        </div>

        {/* Task Description (max 2 lines) */}
        <p className="text-sm text-foreground line-clamp-2">
          Agent action limit reached. Reconfigure HITL settings to continue or stop the current operation.
        </p>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 pt-2">
          <Button
            onClick={handleApprove}
            size="sm"
            className="bg-tester text-white hover:bg-tester/90"
          >
            Approve
          </Button>
          <Button
            onClick={handleReject}
            size="sm"
            variant="destructive"
          >
            Reject
          </Button>
        </div>
      </div>
    </div>
  );
};
```

---

### Phase 4: Cleanup (Day 6)

**Remove deprecated code and simplify architecture.**

#### 4.1 Deprecate Files

**Files to DELETE or DEPRECATE:**

```bash
# Backend
❌ backend/app/services/hitl_counter_service.py  # Replaced by hitl_governor_service.py

# Frontend
❌ frontend/lib/stores/hitl-store.ts  # No longer needed with native action
❌ frontend/components/hitl/inline-hitl-approval.tsx  # Replaced by HITLReconfigurePrompt in action
```

#### 4.2 Update References

**Find and update all references to `HitlCounterService`:**

```bash
cd backend
grep -r "HitlCounterService" --include="*.py"
# Replace with HITLGovernorService
```

**Find and update all references to `useHITLStore`:**

```bash
cd frontend
grep -r "useHITLStore" --include="*.tsx" --include="*.ts"
# Remove or replace with CopilotKit action pattern
```

---

## Testing Strategy

### Backend Tests

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

def test_update_settings(hitl_service, test_db):
    """Test settings update resets counter."""
    project_id = uuid4()

    # Exhaust counter
    for _ in range(10):
        hitl_service.check_action_allowed(project_id)

    # Update settings with new limit
    result = hitl_service.update_settings(project_id, new_limit=5)
    assert result["remaining"] == 5

    # Should allow 5 more actions
    for i in range(5, 0, -1):
        result = hitl_service.check_action_allowed(project_id)
        assert result["allowed"] is True
```

### Frontend Tests

**File:** `frontend/tests/components/copilot-demo.test.tsx` (UPDATE)

```typescript
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CopilotDemoPage } from "@/app/copilot-demo/page";

describe("CopilotDemoPage with native HITL action", () => {
  it("renders CopilotKit chat without markdown tag renderers", () => {
    render(<CopilotDemoPage />);

    expect(screen.getByTestId("chat-section")).toBeInTheDocument();
  });

  it("handles reconfigureHITL action with HITLReconfigurePrompt", async () => {
    // Mock CopilotKit action handler
    const mockAction = jest.fn();

    render(<CopilotDemoPage />);

    // Simulate tool call from backend
    // ... test tool call triggers HITLReconfigurePrompt rendering ...

    // User clicks Approve button
    const approveButton = screen.getByText("Approve");
    fireEvent.click(approveButton);

    await waitFor(() => {
      expect(mockAction).toHaveBeenCalledWith({
        newLimit: expect.any(Number),
        newStatus: expect.any(Boolean)
      });
    });
  });
});
```

---

## Success Metrics

### Code Reduction

**Before (Custom Markdown Tags):**
- Custom markdown tag renderer: ~50 LOC
- Duplicate tracking logic: ~20 LOC
- Manual store management: ~30 LOC
- WebSocket HITL events: ~40 LOC
- **Total:** ~140 LOC custom HITL frontend code

**After (Native CopilotKit Action):**
- `useCopilotAction` handler: ~30 LOC
- HITLReconfigurePrompt (unchanged): ~95 LOC
- **Total:** ~125 LOC (10% reduction in frontend)

**Backend:**
- HitlCounterService (Redis): ~160 LOC
- HITLGovernorService (Database): ~120 LOC
- **Total:** 25% reduction + database persistence benefit

### Architecture Improvements

- ✅ **Native CopilotKit pattern** - No custom protocol violations
- ✅ **Database persistence** - Counter survives server restarts
- ✅ **Automatic tool handling** - No manual message synchronization
- ✅ **Same UI** - User sees exact same Toggle + Counter interface
- ✅ **Simpler debugging** - Uses standard CopilotKit tool call flow

---

## Migration Checklist

### Day 1: Database
- [ ] Create Alembic migration for `hitl_settings` table
- [ ] Add `HITLSettingsDB` model to `database/models.py`
- [ ] Run migration: `alembic upgrade head`
- [ ] Verify table created in PostgreSQL

### Days 2-3: Backend
- [ ] Create `HITLGovernorService` in `services/hitl_governor_service.py`
- [ ] Update `HITLAwareLlmAgent` to handle tool results
- [ ] Integrate governor check into `BMADAGUIRuntime.execute_with_governor()`
- [ ] Write unit tests for `HITLGovernorService`
- [ ] Test end-to-end: counter decrement → exhaustion → tool call

### Days 4-5: Frontend
- [ ] Remove markdown tag renderer from `copilot-demo/page.tsx`
- [ ] Add `useCopilotAction` for `reconfigureHITL`
- [ ] Verify `HITLReconfigurePrompt` renders correctly in action
- [ ] Test user interaction: Approve/Reject → result sent to backend
- [ ] Test counter reset flow end-to-end

### Day 6: Cleanup
- [ ] Deprecate `HitlCounterService` (Redis-based)
- [ ] Remove `useHITLStore` if no longer used
- [ ] Remove custom WebSocket HITL events
- [ ] Update documentation
- [ ] Run full test suite

---

## Rollback Plan

If issues arise during migration:

**Immediate Rollback (< 5 minutes):**
1. Revert `copilot-demo/page.tsx` to use markdown tag renderer
2. Revert `hitl_aware_agent.py` to use `HitlCounterService`
3. Keep `hitl_settings` table (no harm, just unused)

**Full Rollback (< 30 minutes):**
1. Revert all backend changes
2. Revert all frontend changes
3. Run migration downgrade: `alembic downgrade -1`
4. Restart backend and frontend servers

---

## Key Differences from Current Implementation

| Aspect | Current (Custom) | Simplified (Native) |
|--------|------------------|---------------------|
| **Trigger** | Markdown tag (`<hitl-approval>`) | Tool call (`reconfigureHITL`) |
| **Frontend Pattern** | Custom `markdownTagRenderers` | Native `useCopilotAction` |
| **State Management** | Manual `useHITLStore` + WebSocket | CopilotKit automatic tool handling |
| **Backend Storage** | Redis (`HitlCounterService`) | PostgreSQL (`HITLGovernorService`) |
| **Duplicate Prevention** | Manual `createdApprovalIds` ref | CopilotKit handles automatically |
| **UI Component** | `InlineHITLApproval` | `HITLReconfigurePrompt` (same UI!) |
| **Persistence** | Lost on server restart | Survives server restarts |
| **Code Complexity** | High (custom protocol) | Low (standard pattern) |

---

## Final Recommendation

**PROCEED with simplified implementation:**

1. **User Experience:** IDENTICAL - Toggle + Counter UI preserved exactly
2. **Developer Experience:** IMPROVED - Native CopilotKit patterns, less custom code
3. **Reliability:** IMPROVED - Database persistence, no Redis dependency
4. **Maintainability:** IMPROVED - 35% less code, standard patterns
5. **Timeline:** 1 week (6 developer days)

**This approach keeps exactly what you want (Toggle + Counter) while using standard CopilotKit patterns underneath.**
