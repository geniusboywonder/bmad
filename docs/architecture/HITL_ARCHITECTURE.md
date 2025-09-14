# Human-in-the-Loop (HITL) Agent Safety Architecture

## Executive Summary

This document outlines the comprehensive architecture for implementing mandatory Human-in-the-Loop (HITL) controls for agent safety in the BotArmy Multi-Agent Development (BMAD) system. The implementation provides multi-layered safety mechanisms including hard HITL controls, mandatory approval workflows, token budget controls, emergency stop mechanisms, and recovery procedures.

## Current Infrastructure Analysis

### Existing HITL Components
- **Models**: `HitlRequest`, `HitlResponse`, `HitlStatus` (PENDING, APPROVED, REJECTED, AMENDED)
- **Database**: `HitlRequestDB` with full audit trail and history tracking
- **API**: `/api/v1/hitl` endpoints for request management and response processing
- **WebSocket**: Real-time HITL notifications via `WebSocketManager`
- **Orchestrator**: Basic HITL checkpoint integration in workflow orchestration

### Agent Infrastructure
- **Base Agent**: `BaseAgent` with LLM reliability features
- **Agent Types**: ORCHESTRATOR, ANALYST, ARCHITECT, CODER, TESTER, DEPLOYER
- **Status Tracking**: `AgentStatus` (IDLE, WORKING, WAITING_FOR_HITL, ERROR)
- **Task Management**: Full task lifecycle with status tracking and error handling

## 1. Hard HITL Controls Architecture

### 1.1 Pre-Agent Call Approval System

#### AgentCallApprovalRequest Model
```python
class AgentCallApprovalRequest(BaseModel):
    """Request for agent call approval before execution."""

    approval_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    task_id: UUID
    agent_type: AgentType
    proposed_action: str
    input_data: Dict[str, Any]
    context_summary: str
    estimated_tokens: int
    estimated_cost: float
    risk_assessment: Dict[str, Any]
    timeout_minutes: int = 30
    status: AgentCallApprovalStatus = AgentCallApprovalStatus.PENDING

class AgentCallApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
```

#### Database Schema Addition
```sql
CREATE TABLE agent_call_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    task_id UUID REFERENCES tasks(id) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    proposed_action TEXT NOT NULL,
    input_data JSONB NOT NULL,
    context_summary TEXT,
    estimated_tokens INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10,4) DEFAULT 0.0000,
    risk_assessment JSONB DEFAULT '{}',
    timeout_minutes INTEGER DEFAULT 30,
    status agent_call_approval_status DEFAULT 'pending',
    approved_by VARCHAR(255),
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    responded_at TIMESTAMP,
    expires_at TIMESTAMP,
    INDEX idx_project_status (project_id, status),
    INDEX idx_task_status (task_id, status)
);
```

### 1.2 Enhanced BaseAgent with Hard HITL Controls

#### Agent Call Interception
```python
class SafetyEnhancedBaseAgent(BaseAgent):
    """Enhanced BaseAgent with mandatory HITL controls."""

    async def execute_task(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute task with mandatory pre-approval and response validation."""

        # 1. Generate pre-execution approval request
        approval_request = await self._create_pre_execution_approval(task, context)

        # 2. Wait for mandatory approval
        approval_result = await self._wait_for_execution_approval(approval_request.approval_id)

        if approval_result.status != AgentCallApprovalStatus.APPROVED:
            return self._handle_execution_rejection(approval_result)

        # 3. Execute with monitoring
        execution_result = await self._monitored_execution(task, context, approval_request)

        # 4. Request response approval
        response_approval = await self._create_response_approval_request(
            task, execution_result, approval_request
        )

        # 5. Wait for response approval
        response_approval_result = await self._wait_for_response_approval(
            response_approval.approval_id
        )

        if response_approval_result.status != ResponseApprovalStatus.APPROVED:
            return self._handle_response_rejection(response_approval_result)

        return execution_result

    async def _create_pre_execution_approval(
        self,
        task: Task,
        context: List[ContextArtifact]
    ) -> AgentCallApprovalRequest:
        """Create pre-execution approval request with risk assessment."""

        # Analyze input and context for risk assessment
        risk_assessment = await self._assess_execution_risk(task, context)

        # Estimate resource usage
        estimated_tokens = self._estimate_token_usage(task, context)
        estimated_cost = await self._estimate_execution_cost(estimated_tokens)

        approval_request = AgentCallApprovalRequest(
            project_id=task.project_id,
            task_id=task.task_id,
            agent_type=self.agent_type,
            proposed_action=self._describe_proposed_action(task),
            input_data={"task": task.dict(), "context_count": len(context)},
            context_summary=self._summarize_context(context),
            estimated_tokens=estimated_tokens,
            estimated_cost=estimated_cost,
            risk_assessment=risk_assessment
        )

        # Store in database
        await self._store_approval_request(approval_request)

        # Emit WebSocket notification
        await self._emit_approval_request_event(approval_request)

        return approval_request
```

## 2. Mandatory Response Approval System

### 2.1 Response Approval Model
```python
class ResponseApprovalRequest(BaseModel):
    """Request for agent response approval before proceeding."""

    approval_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    task_id: UUID
    agent_type: AgentType
    original_call_approval_id: UUID
    agent_response: Dict[str, Any]
    response_summary: str
    next_steps: List[str]
    risk_flags: List[str]
    confidence_score: float
    tokens_used: int
    actual_cost: float
    status: ResponseApprovalStatus = ResponseApprovalStatus.PENDING

class ResponseApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_MODIFICATION = "requires_modification"
    TIMED_OUT = "timed_out"
```

### 2.2 Response Analysis and Safety Checks
```python
class ResponseSafetyAnalyzer:
    """Analyzes agent responses for safety and quality issues."""

    async def analyze_response(
        self,
        response: Dict[str, Any],
        task: Task,
        agent_type: AgentType
    ) -> Dict[str, Any]:
        """Comprehensive response analysis for safety and quality."""

        analysis = {
            "risk_flags": [],
            "confidence_score": 0.0,
            "safety_score": 0.0,
            "quality_metrics": {},
            "recommendations": []
        }

        # 1. Content Safety Analysis
        safety_flags = await self._analyze_content_safety(response)
        analysis["risk_flags"].extend(safety_flags)

        # 2. Code Safety Analysis (for CODER agents)
        if agent_type == AgentType.CODER:
            code_safety = await self._analyze_code_safety(response)
            analysis["risk_flags"].extend(code_safety.get("flags", []))
            analysis["quality_metrics"]["code_quality"] = code_safety.get("score", 0.0)

        # 3. Response Completeness Check
        completeness = await self._check_response_completeness(response, task)
        analysis["quality_metrics"]["completeness"] = completeness

        # 4. Consistency Validation
        consistency = await self._validate_response_consistency(response, task)
        analysis["quality_metrics"]["consistency"] = consistency

        # 5. Calculate Overall Confidence
        analysis["confidence_score"] = self._calculate_confidence_score(analysis)
        analysis["safety_score"] = self._calculate_safety_score(analysis)

        return analysis
```

## 3. Token Budget Controls and Resource Management

### 3.1 Project Budget Model
```python
class ProjectBudgetControl(BaseModel):
    """Project-level budget and resource controls."""

    project_id: UUID
    daily_token_limit: int
    monthly_token_limit: int
    daily_cost_limit: float
    monthly_cost_limit: float
    tokens_used_today: int = 0
    tokens_used_month: int = 0
    cost_incurred_today: float = 0.0
    cost_incurred_month: float = 0.0
    budget_alerts: List[BudgetAlert] = Field(default_factory=list)
    emergency_stop_triggered: bool = False
    last_reset_date: datetime = Field(default_factory=datetime.utcnow)

class BudgetAlert(BaseModel):
    alert_type: str  # "warning", "critical", "emergency"
    threshold_type: str  # "token_daily", "token_monthly", "cost_daily", "cost_monthly"
    threshold_value: float
    current_value: float
    triggered_at: datetime
```

### 3.2 Budget Enforcement Service
```python
class BudgetEnforcementService:
    """Enforces token and cost budgets with mandatory approvals."""

    async def check_budget_approval(
        self,
        project_id: UUID,
        estimated_tokens: int,
        estimated_cost: float
    ) -> BudgetApprovalResult:
        """Check if request is within budget or requires approval."""

        budget = await self._get_project_budget(project_id)

        # Calculate potential usage
        potential_daily_tokens = budget.tokens_used_today + estimated_tokens
        potential_daily_cost = budget.cost_incurred_today + estimated_cost

        approval_result = BudgetApprovalResult(project_id=project_id)

        # Check daily limits
        if potential_daily_tokens > budget.daily_token_limit:
            approval_result.requires_approval = True
            approval_result.violation_type = "daily_token_limit"
            approval_result.budget_exceeded = True

        if potential_daily_cost > budget.daily_cost_limit:
            approval_result.requires_approval = True
            approval_result.violation_type = "daily_cost_limit"
            approval_result.budget_exceeded = True

        # Check for emergency stop conditions
        if potential_daily_cost > budget.daily_cost_limit * 1.5:
            approval_result.emergency_stop_required = True

        return approval_result

    async def create_budget_override_request(
        self,
        project_id: UUID,
        violation_type: str,
        requested_amount: float,
        justification: str
    ) -> BudgetOverrideRequest:
        """Create request for budget override approval."""

        override_request = BudgetOverrideRequest(
            project_id=project_id,
            violation_type=violation_type,
            requested_amount=requested_amount,
            justification=justification,
            requires_manager_approval=requested_amount > 100.0
        )

        await self._store_override_request(override_request)
        await self._emit_budget_override_event(override_request)

        return override_request
```

## 4. Emergency Stop Mechanisms

### 4.1 Emergency Stop System
```python
class EmergencyStopSystem:
    """Comprehensive emergency stop system for agent operations."""

    def __init__(self):
        self.stop_conditions = {
            "budget_critical": self._check_budget_critical,
            "error_rate_high": self._check_error_rate,
            "security_threat": self._check_security_threat,
            "manual_stop": self._check_manual_stop,
            "resource_exhaustion": self._check_resource_exhaustion
        }

    async def check_emergency_conditions(self, project_id: UUID) -> EmergencyStopResult:
        """Check all emergency stop conditions."""

        result = EmergencyStopResult(project_id=project_id)

        for condition_name, check_func in self.stop_conditions.items():
            condition_result = await check_func(project_id)

            if condition_result.should_stop:
                result.triggered_conditions.append(condition_name)
                result.should_stop = True
                result.stop_reason = condition_result.reason
                result.severity = max(result.severity, condition_result.severity)

        if result.should_stop:
            await self._trigger_emergency_stop(result)

        return result

    async def _trigger_emergency_stop(self, result: EmergencyStopResult):
        """Execute emergency stop procedures."""

        # 1. Halt all running tasks
        await self._halt_project_tasks(result.project_id)

        # 2. Update agent statuses
        await self._set_agents_emergency_stop(result.project_id)

        # 3. Create emergency stop record
        await self._log_emergency_stop(result)

        # 4. Emit emergency notifications
        await self._emit_emergency_stop_event(result)

        # 5. Send critical alerts
        await self._send_emergency_alerts(result)
```

### 4.2 Recovery Procedures
```python
class RecoveryProcedureManager:
    """Manages recovery procedures after emergency stops or failures."""

    async def initiate_recovery(
        self,
        project_id: UUID,
        recovery_type: RecoveryType
    ) -> RecoverySession:
        """Initiate recovery session with mandatory approvals."""

        recovery_session = RecoverySession(
            project_id=project_id,
            recovery_type=recovery_type,
            status=RecoveryStatus.ASSESSMENT
        )

        # 1. Assess current state
        assessment = await self._assess_project_state(project_id)
        recovery_session.assessment = assessment

        # 2. Generate recovery plan
        recovery_plan = await self._generate_recovery_plan(assessment)
        recovery_session.recovery_plan = recovery_plan

        # 3. Request recovery approval
        approval_request = await self._create_recovery_approval_request(
            recovery_session
        )

        recovery_session.status = RecoveryStatus.WAITING_APPROVAL
        await self._emit_recovery_approval_request(approval_request)

        return recovery_session

    async def execute_recovery_step(
        self,
        session_id: UUID,
        step: RecoveryStep
    ) -> RecoveryStepResult:
        """Execute individual recovery step with monitoring."""

        # Each recovery step requires approval
        step_approval = await self._request_step_approval(session_id, step)

        if step_approval.status != ApprovalStatus.APPROVED:
            return RecoveryStepResult(
                step_id=step.step_id,
                status=RecoveryStepStatus.REJECTED,
                message="Recovery step rejected by user"
            )

        # Execute step with monitoring
        return await self._execute_monitored_recovery_step(session_id, step)
```

## 5. API Endpoints and Database Schema

### 5.1 New API Endpoints

#### Agent Call Approval Endpoints
```python
@router.post("/api/v1/agent-approvals", response_model=AgentCallApprovalRequest)
async def create_agent_approval_request(
    request: CreateAgentApprovalRequest,
    db: Session = Depends(get_session)
):
    """Create new agent call approval request."""

@router.post("/api/v1/agent-approvals/{approval_id}/respond")
async def respond_to_agent_approval(
    approval_id: UUID,
    response: AgentApprovalResponse,
    db: Session = Depends(get_session)
):
    """Respond to agent call approval request."""

@router.get("/api/v1/agent-approvals/project/{project_id}")
async def get_project_agent_approvals(
    project_id: UUID,
    status: Optional[str] = None,
    db: Session = Depends(get_session)
):
    """Get all agent approval requests for a project."""
```

#### Response Approval Endpoints
```python
@router.post("/api/v1/response-approvals", response_model=ResponseApprovalRequest)
async def create_response_approval_request(
    request: CreateResponseApprovalRequest,
    db: Session = Depends(get_session)
):
    """Create new response approval request."""

@router.post("/api/v1/response-approvals/{approval_id}/respond")
async def respond_to_response_approval(
    approval_id: UUID,
    response: ResponseApprovalResponse,
    db: Session = Depends(get_session)
):
    """Respond to response approval request."""
```

#### Emergency Management Endpoints
```python
@router.post("/api/v1/emergency/stop/{project_id}")
async def trigger_emergency_stop(
    project_id: UUID,
    reason: str,
    db: Session = Depends(get_session)
):
    """Trigger emergency stop for project."""

@router.post("/api/v1/emergency/recovery/{project_id}")
async def initiate_recovery(
    project_id: UUID,
    recovery_request: RecoveryRequest,
    db: Session = Depends(get_session)
):
    """Initiate recovery procedures."""

@router.get("/api/v1/emergency/status/{project_id}")
async def get_emergency_status(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """Get current emergency status for project."""
```

### 5.2 Database Schema Extensions

#### Complete Schema Updates
```sql
-- Agent Call Approvals
CREATE TABLE agent_call_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    task_id UUID REFERENCES tasks(id) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    proposed_action TEXT NOT NULL,
    input_data JSONB NOT NULL,
    context_summary TEXT,
    estimated_tokens INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10,4) DEFAULT 0.0000,
    risk_assessment JSONB DEFAULT '{}',
    timeout_minutes INTEGER DEFAULT 30,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by VARCHAR(255),
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    responded_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Response Approvals
CREATE TABLE response_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    task_id UUID REFERENCES tasks(id) NOT NULL,
    agent_call_approval_id UUID REFERENCES agent_call_approvals(id),
    agent_type VARCHAR(50) NOT NULL,
    agent_response JSONB NOT NULL,
    response_summary TEXT,
    next_steps JSONB DEFAULT '[]',
    risk_flags JSONB DEFAULT '[]',
    confidence_score DECIMAL(3,2) DEFAULT 0.00,
    tokens_used INTEGER DEFAULT 0,
    actual_cost DECIMAL(10,4) DEFAULT 0.0000,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by VARCHAR(255),
    rejection_reason TEXT,
    modifications_required JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    responded_at TIMESTAMP
);

-- Project Budget Controls
CREATE TABLE project_budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) UNIQUE NOT NULL,
    daily_token_limit INTEGER DEFAULT 100000,
    monthly_token_limit INTEGER DEFAULT 2000000,
    daily_cost_limit DECIMAL(10,4) DEFAULT 100.0000,
    monthly_cost_limit DECIMAL(10,4) DEFAULT 2000.0000,
    tokens_used_today INTEGER DEFAULT 0,
    tokens_used_month INTEGER DEFAULT 0,
    cost_incurred_today DECIMAL(10,4) DEFAULT 0.0000,
    cost_incurred_month DECIMAL(10,4) DEFAULT 0.0000,
    budget_alerts JSONB DEFAULT '[]',
    emergency_stop_triggered BOOLEAN DEFAULT FALSE,
    last_reset_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Emergency Stop Logs
CREATE TABLE emergency_stops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    triggered_conditions JSONB NOT NULL,
    stop_reason TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    triggered_by VARCHAR(255),
    stopped_tasks JSONB DEFAULT '[]',
    recovery_session_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Recovery Sessions
CREATE TABLE recovery_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    emergency_stop_id UUID REFERENCES emergency_stops(id),
    recovery_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'assessment',
    assessment JSONB,
    recovery_plan JSONB,
    steps_completed INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    current_step JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Budget Override Requests
CREATE TABLE budget_override_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    violation_type VARCHAR(50) NOT NULL,
    requested_amount DECIMAL(10,4) NOT NULL,
    justification TEXT NOT NULL,
    requires_manager_approval BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by VARCHAR(255),
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    responded_at TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_agent_call_approvals_project_status ON agent_call_approvals(project_id, status);
CREATE INDEX idx_agent_call_approvals_expires_at ON agent_call_approvals(expires_at) WHERE status = 'pending';
CREATE INDEX idx_response_approvals_project_status ON response_approvals(project_id, status);
CREATE INDEX idx_emergency_stops_project_created ON emergency_stops(project_id, created_at);
CREATE INDEX idx_recovery_sessions_project_status ON recovery_sessions(project_id, status);
CREATE INDEX idx_budget_override_requests_status ON budget_override_requests(status);
```

## 6. WebSocket Integration for Real-Time HITL Notifications

### 6.1 Enhanced WebSocket Events
```python
class HITLEventType(str, Enum):
    """HITL-specific WebSocket event types."""
    AGENT_APPROVAL_REQUESTED = "agent_approval_requested"
    RESPONSE_APPROVAL_REQUESTED = "response_approval_requested"
    BUDGET_OVERRIDE_REQUESTED = "budget_override_requested"
    EMERGENCY_STOP_TRIGGERED = "emergency_stop_triggered"
    RECOVERY_INITIATED = "recovery_initiated"
    APPROVAL_TIMEOUT_WARNING = "approval_timeout_warning"
    SAFETY_ALERT = "safety_alert"

class HITLWebSocketManager:
    """Enhanced WebSocket manager for HITL operations."""

    async def emit_agent_approval_request(
        self,
        approval_request: AgentCallApprovalRequest
    ):
        """Emit agent call approval request event."""

        event = WebSocketEvent(
            event_type=HITLEventType.AGENT_APPROVAL_REQUESTED,
            project_id=approval_request.project_id,
            task_id=approval_request.task_id,
            data={
                "approval_id": str(approval_request.approval_id),
                "agent_type": approval_request.agent_type,
                "proposed_action": approval_request.proposed_action,
                "estimated_cost": approval_request.estimated_cost,
                "risk_assessment": approval_request.risk_assessment,
                "expires_at": approval_request.expires_at.isoformat()
            }
        )

        await self.broadcast_to_project(event, str(approval_request.project_id))
        await self._send_priority_notification(event)

    async def emit_emergency_stop_event(
        self,
        emergency_result: EmergencyStopResult
    ):
        """Emit critical emergency stop event."""

        event = WebSocketEvent(
            event_type=HITLEventType.EMERGENCY_STOP_TRIGGERED,
            project_id=emergency_result.project_id,
            data={
                "triggered_conditions": emergency_result.triggered_conditions,
                "severity": emergency_result.severity,
                "stop_reason": emergency_result.stop_reason,
                "affected_tasks": emergency_result.affected_tasks
            }
        )

        # Broadcast globally for emergency events
        await self.broadcast_global(event)
        await self._send_emergency_alert(event)
```

## 7. Testing Frameworks for HITL Workflows

### 7.1 HITL Testing Strategy
```python
class HITLTestFramework:
    """Comprehensive testing framework for HITL workflows."""

    async def test_agent_approval_workflow(self):
        """Test complete agent approval workflow."""

        # 1. Setup test project and task
        project = await self.create_test_project()
        task = await self.create_test_task(project.id)

        # 2. Create agent approval request
        approval_request = await self.agent_service.create_approval_request(
            project.id, task.id, "test_action"
        )

        # 3. Test timeout handling
        await self.test_approval_timeout(approval_request.approval_id)

        # 4. Test approval workflow
        await self.approve_agent_request(approval_request.approval_id)

        # 5. Verify agent execution
        result = await self.wait_for_task_completion(task.id)
        assert result.status == TaskStatus.COMPLETED

    async def test_emergency_stop_scenarios(self):
        """Test various emergency stop scenarios."""

        test_scenarios = [
            {"type": "budget_exceeded", "condition": self._create_budget_violation},
            {"type": "security_threat", "condition": self._create_security_threat},
            {"type": "error_cascade", "condition": self._create_error_cascade},
            {"type": "manual_stop", "condition": self._trigger_manual_stop}
        ]

        for scenario in test_scenarios:
            await self._test_emergency_scenario(scenario)

    async def test_recovery_procedures(self):
        """Test recovery procedures after various failure types."""

        # 1. Create failure condition
        project = await self.create_test_project()
        await self.trigger_test_emergency_stop(project.id, "test_condition")

        # 2. Initiate recovery
        recovery_session = await self.recovery_manager.initiate_recovery(
            project.id, RecoveryType.AUTOMATED
        )

        # 3. Test step-by-step recovery
        for step in recovery_session.recovery_plan.steps:
            await self.approve_recovery_step(recovery_session.id, step.step_id)
            result = await self.execute_recovery_step(recovery_session.id, step)
            assert result.status == RecoveryStepStatus.COMPLETED
```

### 7.2 Integration Test Suite
```python
class HITLIntegrationTests:
    """Integration tests for HITL system components."""

    async def test_end_to_end_workflow(self):
        """Test complete end-to-end HITL workflow."""

        # 1. Project setup with budget controls
        project = await self.setup_test_project_with_budget()

        # 2. Start workflow with HITL checkpoints
        workflow_result = await self.orchestrator.run_project_workflow(
            project.id, "Build a simple web application"
        )

        # 3. Verify all HITL requests were created
        hitl_requests = await self.get_project_hitl_requests(project.id)
        assert len(hitl_requests) >= 3  # Minimum expected checkpoints

        # 4. Simulate user approvals
        for request in hitl_requests:
            await self.approve_hitl_request(request.id)

        # 5. Verify workflow completion
        assert workflow_result.status == "completed"

    async def test_concurrent_approval_handling(self):
        """Test handling of concurrent approval requests."""

        # Create multiple concurrent approval requests
        approval_tasks = []
        for i in range(10):
            task = asyncio.create_task(
                self.create_concurrent_approval_request(f"test_{i}")
            )
            approval_tasks.append(task)

        # Execute concurrently
        approval_requests = await asyncio.gather(*approval_tasks)

        # Verify all requests were handled correctly
        for request in approval_requests:
            assert request.status == AgentCallApprovalStatus.PENDING
            assert request.approval_id is not None
```

## 8. Implementation Phases and Rollout Strategy

### Phase 1: Foundation and Core HITL Controls (Weeks 1-3)
```markdown
**Week 1: Database and Model Implementation**
- [ ] Implement new database tables and indexes
- [ ] Create Pydantic models for approval requests
- [ ] Add database migration scripts
- [ ] Update existing models with new relationships

**Week 2: Core HITL Services**
- [ ] Implement AgentCallApprovalService
- [ ] Implement ResponseApprovalService
- [ ] Create ResponseSafetyAnalyzer
- [ ] Add approval workflow logic to BaseAgent

**Week 3: API Endpoints and Basic Testing**
- [ ] Create agent approval API endpoints
- [ ] Create response approval API endpoints
- [ ] Implement basic WebSocket events
- [ ] Add unit tests for core services
```

### Phase 2: Budget Controls and Emergency Systems (Weeks 4-6)
```markdown
**Week 4: Budget Control System**
- [ ] Implement BudgetEnforcementService
- [ ] Create budget monitoring and alerting
- [ ] Add budget override request system
- [ ] Integrate budget checks into approval workflow

**Week 5: Emergency Stop Mechanisms**
- [ ] Implement EmergencyStopSystem
- [ ] Create emergency condition monitoring
- [ ] Add emergency stop triggers and handlers
- [ ] Implement emergency notification system

**Week 6: Recovery Procedures**
- [ ] Implement RecoveryProcedureManager
- [ ] Create recovery workflow system
- [ ] Add recovery step approval process
- [ ] Test emergency stop and recovery cycles
```

### Phase 3: Advanced Features and Integration (Weeks 7-9)
```markdown
**Week 7: Enhanced WebSocket Integration**
- [ ] Implement HITLWebSocketManager
- [ ] Add real-time approval notifications
- [ ] Create priority notification system
- [ ] Add WebSocket event filtering and routing

**Week 8: Advanced Safety Features**
- [ ] Implement content safety analysis
- [ ] Add code safety validation for CODER agents
- [ ] Create response quality metrics
- [ ] Add confidence scoring system

**Week 9: Testing and Documentation**
- [ ] Complete integration test suite
- [ ] Add load testing for concurrent approvals
- [ ] Create comprehensive documentation
- [ ] Add deployment scripts and monitoring
```

### Phase 4: Production Deployment and Monitoring (Weeks 10-12)
```markdown
**Week 10: Production Preparation**
- [ ] Performance optimization and caching
- [ ] Security audit and penetration testing
- [ ] Create monitoring dashboards
- [ ] Add alerting for system health

**Week 11: Staged Rollout**
- [ ] Deploy to staging environment
- [ ] User acceptance testing
- [ ] Bug fixes and performance tuning
- [ ] Create user training materials

**Week 12: Full Production Deployment**
- [ ] Deploy to production with feature flags
- [ ] Monitor system performance and user adoption
- [ ] Gradual rollout to all projects
- [ ] Post-deployment support and optimization
```

## 9. Production Readiness Checklist

### Security and Compliance
- [ ] All HITL requests encrypted in transit and at rest
- [ ] Approval timeouts properly enforced
- [ ] Audit trail for all approval decisions
- [ ] Role-based access controls for approval permissions
- [ ] GDPR compliance for user approval data

### Performance and Scalability
- [ ] Database indexes optimized for approval queries
- [ ] WebSocket connections properly managed
- [ ] Approval request caching implemented
- [ ] Load testing completed for 1000+ concurrent approvals
- [ ] Auto-scaling configured for approval services

### Monitoring and Alerting
- [ ] Metrics for approval response times
- [ ] Alerts for stuck approval requests
- [ ] Emergency stop trigger monitoring
- [ ] Budget violation alerting
- [ ] System health dashboards

### Operational Procedures
- [ ] Runbooks for emergency procedures
- [ ] Approval escalation procedures
- [ ] Recovery workflow documentation
- [ ] User training for approval interfaces
- [ ] On-call procedures for HITL system issues

## 10. Success Metrics and KPIs

### Safety Metrics
- **Zero Unauthorized Agent Executions**: 100% agent calls require pre-approval
- **Response Approval Coverage**: 100% agent responses require approval before proceeding
- **Emergency Stop Response Time**: < 5 seconds from trigger to agent halt
- **Budget Compliance**: 100% adherence to token and cost budgets
- **Recovery Success Rate**: 95% successful recovery from emergency stops

### Performance Metrics
- **Approval Response Time**: < 2 minutes average for standard approvals
- **System Availability**: 99.9% uptime for approval system
- **Concurrent Approval Handling**: Support for 500+ concurrent approval requests
- **WebSocket Message Delivery**: 99.5% successful real-time notification delivery
- **Database Performance**: < 100ms average query time for approval operations

### User Experience Metrics
- **Approval Interface Usability**: < 30 seconds average time to review and approve
- **False Positive Rate**: < 5% for safety analysis flags
- **User Satisfaction**: > 4.0/5.0 rating for approval workflow
- **Training Effectiveness**: < 1 hour required for user onboarding

## Conclusion

This comprehensive HITL architecture provides multiple layers of safety controls, mandatory approval workflows, budget management, emergency procedures, and recovery mechanisms. The implementation leverages existing infrastructure while adding robust safety features that ensure human oversight at every critical decision point in the agent workflow.

The phased rollout strategy ensures systematic implementation with proper testing and validation at each stage. The production readiness checklist and success metrics provide clear criteria for deployment and ongoing operational excellence.

This architecture transforms the BotArmy system into a safety-first platform where human judgment guides and validates every agent action, providing the confidence needed for production deployment of autonomous agent systems.