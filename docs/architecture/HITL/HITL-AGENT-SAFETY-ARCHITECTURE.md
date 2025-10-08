# HITL Agent Safety Architecture

## Overview

This document defines the mandatory Human-in-the-Loop (HITL) control architecture for preventing agent runaway scenarios while maintaining comprehensive testing capabilities. Every agent interaction requires explicit human approval before execution and before proceeding to the next step.

## Core Principle: Hard HITL Controls

**MANDATORY RULE**: No agent may execute any action or proceed to the next step without explicit human approval.

### Control Points

1. **Pre-Agent Call Approval**: Human must approve before agent is invoked
2. **Response Approval**: Human must approve agent response before workflow continues
3. **Next Step Authorization**: Human must explicitly authorize each subsequent action
4. **Budget Verification**: Human must approve token expenditure for each operation

## Architecture Components

### 1. Enhanced HITL Request System

#### Database Schema Extensions

```sql
-- Enhanced HITL requests with mandatory controls
CREATE TABLE hitl_agent_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    task_id UUID REFERENCES tasks(id),
    agent_type VARCHAR(50) NOT NULL,
    request_type VARCHAR(50) NOT NULL, -- 'PRE_EXECUTION', 'RESPONSE_APPROVAL', 'NEXT_STEP'
    request_data JSON NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'REJECTED', 'EXPIRED'
    estimated_tokens INTEGER,
    estimated_cost DECIMAL(10,4),
    user_response TEXT,
    user_comment TEXT,
    expires_at TIMESTAMP,
    responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Token budget tracking
CREATE TABLE agent_budget_controls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    agent_type VARCHAR(50) NOT NULL,
    daily_token_limit INTEGER DEFAULT 10000,
    session_token_limit INTEGER DEFAULT 2000,
    tokens_used_today INTEGER DEFAULT 0,
    tokens_used_session INTEGER DEFAULT 0,
    budget_reset_at TIMESTAMP DEFAULT NOW(),
    emergency_stop_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Emergency stop controls
CREATE TABLE emergency_stops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    agent_type VARCHAR(50), -- NULL for global stops
    stop_reason VARCHAR(200) NOT NULL,
    triggered_by VARCHAR(100) NOT NULL, -- 'USER', 'BUDGET', 'REPETITION', 'ERROR'
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    deactivated_at TIMESTAMP
);
```

#### API Endpoints

```python
# app/api/hitl_safety.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.hitl_safety import *

router = APIRouter(prefix="/api/v1/hitl-safety", tags=["hitl-safety"])

@router.post("/request-agent-execution")
async def request_agent_execution(request: AgentExecutionRequest):
    """Request permission to execute an agent with estimated costs."""
    approval_request = HitlAgentApproval(
        project_id=request.project_id,
        task_id=request.task_id,
        agent_type=request.agent_type,
        request_type="PRE_EXECUTION",
        request_data=request.dict(),
        estimated_tokens=request.estimated_tokens,
        estimated_cost=calculate_estimated_cost(request.estimated_tokens),
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )

    # Save to database
    db.add(approval_request)
    db.commit()

    # Send WebSocket notification
    await websocket_manager.broadcast_event(
        WebSocketEvent(
            event_type=EventType.HITL_REQUEST_CREATED,
            project_id=request.project_id,
            data={
                "approval_id": str(approval_request.id),
                "agent_type": request.agent_type,
                "estimated_tokens": request.estimated_tokens,
                "estimated_cost": float(request.estimated_cost),
                "expires_at": approval_request.expires_at.isoformat()
            }
        )
    )

    return {"approval_id": approval_request.id, "status": "awaiting_approval"}

@router.post("/approve-agent-execution/{approval_id}")
async def approve_agent_execution(approval_id: UUID, approval: ApprovalResponse):
    """Approve or reject agent execution request."""
    hitl_approval = db.query(HitlAgentApproval).filter(
        HitlAgentApproval.id == approval_id
    ).first()

    if not hitl_approval:
        raise HTTPException(404, "Approval request not found")

    if hitl_approval.expires_at < datetime.utcnow():
        raise HTTPException(400, "Approval request has expired")

    hitl_approval.status = "APPROVED" if approval.approved else "REJECTED"
    hitl_approval.user_response = approval.response
    hitl_approval.user_comment = approval.comment
    hitl_approval.responded_at = datetime.utcnow()

    db.commit()

    # Broadcast approval decision
    await websocket_manager.broadcast_event(
        WebSocketEvent(
            event_type=EventType.HITL_RESPONSE,
            project_id=hitl_approval.project_id,
            data={
                "approval_id": str(approval_id),
                "decision": hitl_approval.status,
                "comment": approval.comment
            }
        )
    )

    return {"status": hitl_approval.status}

@router.post("/emergency-stop")
async def trigger_emergency_stop(stop_request: EmergencyStopRequest):
    """Immediately stop all agents or specific agent types."""
    emergency_stop = EmergencyStop(
        project_id=stop_request.project_id,
        agent_type=stop_request.agent_type,
        stop_reason=stop_request.reason,
        triggered_by="USER"
    )

    db.add(emergency_stop)
    db.commit()

    # Broadcast emergency stop
    await websocket_manager.broadcast_global(
        WebSocketEvent(
            event_type=EventType.ERROR,
            data={
                "emergency_stop": True,
                "reason": stop_request.reason,
                "agent_type": stop_request.agent_type,
                "project_id": str(stop_request.project_id) if stop_request.project_id else None
            }
        )
    )

    return {"status": "emergency_stop_activated"}
```

### 2. Enhanced Agent Framework

#### Modified BaseAgent with HITL Controls

```python
# app/agents/base_agent.py
from app.services.hitl_safety_service import HITLSafetyService

class BaseAgent:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.hitl_service = HITLSafetyService()

    async def execute_with_hitl_control(self, task: Task) -> AgentOutput:
        """Execute agent task with mandatory HITL approval at each step."""

        # Step 1: Request permission to execute
        execution_approval = await self.request_execution_approval(task)
        if not execution_approval:
            raise AgentExecutionDenied("Human rejected agent execution")

        # Step 2: Check budget limits
        budget_check = await self.hitl_service.check_budget_limits(
            task.project_id, self.agent_type, estimated_tokens=task.estimated_tokens
        )
        if not budget_check.approved:
            raise BudgetLimitExceeded(f"Budget limit exceeded: {budget_check.reason}")

        # Step 3: Execute with monitoring
        try:
            with self.hitl_service.execution_monitor(task.task_id):
                response = await self._execute_internal(task)

            # Step 4: Request approval for response
            response_approval = await self.request_response_approval(task, response)
            if not response_approval:
                raise ResponseRejected("Human rejected agent response")

            # Step 5: Request permission for next step (if applicable)
            if self.has_next_step(response):
                next_step_approval = await self.request_next_step_approval(task, response)
                if not next_step_approval:
                    return self.create_termination_response("Human stopped workflow")

            return response

        except Exception as e:
            # Log error and request recovery approval
            await self.hitl_service.log_error_and_request_recovery(task.task_id, str(e))
            raise

    async def request_execution_approval(self, task: Task) -> bool:
        """Request human approval before executing agent."""
        approval_id = await self.hitl_service.create_approval_request(
            project_id=task.project_id,
            task_id=task.task_id,
            agent_type=self.agent_type,
            request_type="PRE_EXECUTION",
            request_data={
                "instructions": task.instructions,
                "estimated_tokens": task.estimated_tokens,
                "context_ids": [str(cid) for cid in task.context_ids]
            }
        )

        # Wait for human approval (with timeout)
        approval = await self.hitl_service.wait_for_approval(
            approval_id, timeout_minutes=30
        )

        return approval.approved

    async def request_response_approval(self, task: Task, response: AgentOutput) -> bool:
        """Request human approval for agent response before proceeding."""
        approval_id = await self.hitl_service.create_approval_request(
            project_id=task.project_id,
            task_id=task.task_id,
            agent_type=self.agent_type,
            request_type="RESPONSE_APPROVAL",
            request_data={
                "agent_response": response.content,
                "output_artifacts": response.artifacts,
                "confidence_score": response.confidence,
                "tokens_used": response.tokens_used
            }
        )

        approval = await self.hitl_service.wait_for_approval(
            approval_id, timeout_minutes=15
        )

        return approval.approved

    async def request_next_step_approval(self, task: Task, response: AgentOutput) -> bool:
        """Request approval before proceeding to next workflow step."""
        approval_id = await self.hitl_service.create_approval_request(
            project_id=task.project_id,
            task_id=task.task_id,
            agent_type=self.agent_type,
            request_type="NEXT_STEP",
            request_data={
                "current_response": response.content,
                "proposed_next_action": response.next_action,
                "workflow_status": response.workflow_status
            }
        )

        approval = await self.hitl_service.wait_for_approval(
            approval_id, timeout_minutes=10
        )

        return approval.approved
```

### 3. HITL Safety Service

```python
# app/services/hitl_safety_service.py
class HITLSafetyService:
    def __init__(self):
        self.active_monitors = {}
        self.emergency_stops = set()

    async def create_approval_request(
        self, project_id: UUID, task_id: UUID, agent_type: str,
        request_type: str, request_data: dict
    ) -> UUID:
        """Create a new HITL approval request."""
        approval = HitlAgentApproval(
            project_id=project_id,
            task_id=task_id,
            agent_type=agent_type,
            request_type=request_type,
            request_data=request_data,
            estimated_tokens=request_data.get('estimated_tokens', 100),
            estimated_cost=self.calculate_cost(request_data.get('estimated_tokens', 100)),
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )

        db.add(approval)
        db.commit()

        # Send real-time notification
        await self.send_hitl_notification(approval)

        return approval.id

    async def wait_for_approval(self, approval_id: UUID, timeout_minutes: int) -> ApprovalResult:
        """Wait for human approval with timeout."""
        start_time = datetime.utcnow()
        timeout_time = start_time + timedelta(minutes=timeout_minutes)

        while datetime.utcnow() < timeout_time:
            # Check for emergency stops
            if self.is_emergency_stopped():
                raise EmergencyStopActivated("Emergency stop is active")

            # Check approval status
            approval = db.query(HitlAgentApproval).filter(
                HitlAgentApproval.id == approval_id
            ).first()

            if approval.status in ['APPROVED', 'REJECTED']:
                return ApprovalResult(
                    approved=(approval.status == 'APPROVED'),
                    response=approval.user_response,
                    comment=approval.user_comment
                )

            # Wait before checking again
            await asyncio.sleep(5)

        # Timeout - automatically reject
        approval.status = 'EXPIRED'
        db.commit()

        raise ApprovalTimeoutError(f"Approval request {approval_id} timed out")

    async def check_budget_limits(self, project_id: UUID, agent_type: str, estimated_tokens: int) -> BudgetCheckResult:
        """Check if operation is within budget limits."""
        budget = db.query(AgentBudgetControl).filter(
            AgentBudgetControl.project_id == project_id,
            AgentBudgetControl.agent_type == agent_type
        ).first()

        if not budget:
            # Create default budget
            budget = AgentBudgetControl(
                project_id=project_id,
                agent_type=agent_type
            )
            db.add(budget)
            db.commit()

        # Check daily limit
        if budget.tokens_used_today + estimated_tokens > budget.daily_token_limit:
            return BudgetCheckResult(
                approved=False,
                reason=f"Would exceed daily limit ({budget.daily_token_limit})"
            )

        # Check session limit
        if budget.tokens_used_session + estimated_tokens > budget.session_token_limit:
            return BudgetCheckResult(
                approved=False,
                reason=f"Would exceed session limit ({budget.session_token_limit})"
            )

        return BudgetCheckResult(approved=True)

    def is_emergency_stopped(self) -> bool:
        """Check if emergency stop is active."""
        active_stops = db.query(EmergencyStop).filter(
            EmergencyStop.active == True
        ).count()

        return active_stops > 0

    async def send_hitl_notification(self, approval: HitlAgentApproval):
        """Send real-time notification to human operators."""
        await websocket_manager.broadcast_event(
            WebSocketEvent(
                event_type=EventType.HITL_REQUEST_CREATED,
                project_id=approval.project_id,
                data={
                    "approval_id": str(approval.id),
                    "agent_type": approval.agent_type,
                    "request_type": approval.request_type,
                    "estimated_cost": float(approval.estimated_cost),
                    "expires_at": approval.expires_at.isoformat()
                }
            )
        )
```

### 4. Emergency Stop System

```python
# app/services/emergency_stop_service.py
class EmergencyStopService:

    @staticmethod
    async def trigger_global_stop(reason: str, triggered_by: str = "USER"):
        """Stop all agent activity immediately."""
        stop = EmergencyStop(
            project_id=None,  # Global stop
            agent_type=None,  # All agents
            stop_reason=reason,
            triggered_by=triggered_by,
            active=True
        )

        db.add(stop)
        db.commit()

        # Cancel all active agent tasks
        await CeleryTaskManager.cancel_all_agent_tasks()

        # Broadcast emergency stop
        await websocket_manager.broadcast_global(
            WebSocketEvent(
                event_type=EventType.ERROR,
                data={
                    "emergency_stop": True,
                    "global": True,
                    "reason": reason
                }
            )
        )

    @staticmethod
    async def trigger_budget_stop(project_id: UUID, agent_type: str):
        """Stop agents due to budget exhaustion."""
        stop = EmergencyStop(
            project_id=project_id,
            agent_type=agent_type,
            stop_reason="Budget limit exceeded",
            triggered_by="BUDGET",
            active=True
        )

        db.add(stop)
        db.commit()

        await CeleryTaskManager.cancel_project_agent_tasks(project_id, agent_type)
```

### 5. WebSocket Integration

```python
# Enhanced WebSocket events for HITL safety
class HITLEventType(str, Enum):
    APPROVAL_REQUEST = "hitl_approval_request"
    APPROVAL_RESPONSE = "hitl_approval_response"
    BUDGET_WARNING = "budget_warning"
    EMERGENCY_STOP = "emergency_stop"
    AGENT_WAITING = "agent_waiting_approval"

# app/websocket/hitl_events.py
async def notify_approval_required(approval_request: HitlAgentApproval):
    """Send immediate notification for approval request."""
    event = WebSocketEvent(
        event_type=HITLEventType.APPROVAL_REQUEST,
        project_id=approval_request.project_id,
        data={
            "approval_id": str(approval_request.id),
            "agent_type": approval_request.agent_type,
            "request_type": approval_request.request_type,
            "estimated_tokens": approval_request.estimated_tokens,
            "estimated_cost": float(approval_request.estimated_cost),
            "expires_at": approval_request.expires_at.isoformat(),
            "priority": "high"
        }
    )

    await websocket_manager.broadcast_to_project(event, str(approval_request.project_id))
```

### 6. Testing Framework

```python
# tests/integration/test_hitl_safety.py
class TestHITLSafety:

    async def test_mandatory_execution_approval(self):
        """Test that agents cannot execute without approval."""
        task = create_test_task()
        agent = TestAgent("TEST_AGENT")

        # Attempt execution without approval should fail
        with pytest.raises(AgentExecutionDenied):
            await agent.execute_with_hitl_control(task)

    async def test_budget_limit_enforcement(self):
        """Test that budget limits prevent execution."""
        task = create_test_task(estimated_tokens=15000)  # Over limit
        agent = TestAgent("TEST_AGENT")

        with pytest.raises(BudgetLimitExceeded):
            await agent.execute_with_hitl_control(task)

    async def test_emergency_stop_immediate_halt(self):
        """Test that emergency stop immediately halts all agents."""
        # Start agent execution
        task = create_test_task()
        agent = TestAgent("TEST_AGENT")

        # Trigger emergency stop during execution
        await EmergencyStopService.trigger_global_stop("Test emergency stop")

        # Any waiting agents should fail immediately
        with pytest.raises(EmergencyStopActivated):
            await agent.execute_with_hitl_control(task)

    async def test_approval_timeout_handling(self):
        """Test that approvals timeout and fail safely."""
        task = create_test_task()
        agent = TestAgent("TEST_AGENT")

        # Mock timeout scenario (don't approve)
        with pytest.raises(ApprovalTimeoutError):
            await agent.execute_with_hitl_control(task)
```

## Implementation Plan

### Phase 1: Core HITL Infrastructure (Week 1-2)
1. Database schema changes and migrations
2. Basic HITL approval API endpoints
3. Enhanced BaseAgent with approval checks
4. WebSocket integration for notifications

### Phase 2: Safety Controls (Week 3-4)
1. Budget tracking and limits
2. Emergency stop system
3. Timeout and error handling
4. Basic monitoring dashboard

### Phase 3: Advanced Features (Week 5-6)
1. Comprehensive testing framework
2. Advanced monitoring and analytics
3. Recovery procedures
4. Production deployment

### Phase 4: Optimization (Week 7-8)
1. Performance optimization
2. UI/UX improvements for approval workflow
3. Advanced safety features
4. Complete documentation

## Success Metrics

- **100% Agent Approval Coverage**: No agent executes without human approval
- **Zero Budget Overruns**: Hard budget limits prevent token waste
- **<30 Second Response Time**: Real-time notifications and fast approval workflow
- **99.9% Emergency Stop Effectiveness**: Immediate halt capability
- **Complete Audit Trail**: Every agent action logged and traceable

This architecture ensures complete human control over agent behavior while maintaining system performance and providing comprehensive safety mechanisms.