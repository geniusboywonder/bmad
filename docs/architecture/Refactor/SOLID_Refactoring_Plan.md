# SOLID Refactoring Plan: Breaking Down Monolithic Services

**Priority**: CRITICAL - Development velocity impact
**Timeline**: 6 weeks phased approach
**Risk Level**: Medium (with proper testing)

---

## 🚨 **CURRENT VIOLATIONS SUMMARY**

| File | LOC | Over Limit | Responsibilities | SOLID Violations |
|------|-----|------------|------------------|------------------|
| orchestrator.py | 2,431 | +1,931 (486%) | 8 distinct jobs | SRP, ISP, DIP |
| hitl_service.py | 1,325 | +825 (265%) | 7 distinct jobs | SRP, ISP |
| workflow_engine.py | 1,226 | +726 (245%) | 6 distinct jobs | SRP, OCP |
| autogen_service.py | 681 | +181 (136%) | 4 distinct jobs | SRP |
| base_agent.py | 657 | +157 (131%) | 4 distinct jobs | SRP |
| template_service.py | 526 | +26 (105%) | 3 distinct jobs | SRP |

**Total**: 6,845 LOC in 6 files (should be ~30 focused files of 150-200 LOC each)

---

## 📋 **PHASE 1: CRITICAL SERVICE DECOMPOSITION** (Weeks 1-3)

### 🎯 **1.1 Orchestrator Service Breakup** (Week 1-2)
**Current**: 2,431 LOC → **Target**: 7 services × 150-200 LOC

#### New Structure:
```
app/services/orchestrator/
├── __init__.py
├── orchestrator_core.py           # 200 LOC - Main coordination logic
├── project_lifecycle_manager.py   # 180 LOC - Project state management
├── agent_coordinator.py           # 190 LOC - Agent assignment & coordination
├── workflow_integrator.py         # 170 LOC - Workflow execution integration
├── handoff_manager.py             # 160 LOC - Agent handoff logic
├── status_tracker.py              # 150 LOC - Status monitoring
└── context_manager.py             # 140 LOC - Context artifact management
```

#### Implementation Steps:

**Step 1.1: Extract Project Lifecycle Manager** (Day 1-2)
```python
# NEW: app/services/orchestrator/project_lifecycle_manager.py
class ProjectLifecycleManager:
    """Manages project state transitions and lifecycle events."""

    def __init__(self, db: Session, event_dispatcher: IEventDispatcher):
        self.db = db
        self.event_dispatcher = event_dispatcher

    async def create_project(self, project_data: CreateProjectRequest) -> Project:
        """Create new project with initial state."""

    async def update_project_status(self, project_id: UUID, status: ProjectStatus) -> Project:
        """Update project status with event notification."""

    async def get_project_status(self, project_id: UUID) -> ProjectStatusResponse:
        """Get comprehensive project status."""
```

**Step 1.2: Extract Agent Coordinator** (Day 3-4)
```python
# NEW: app/services/orchestrator/agent_coordinator.py
class AgentCoordinator:
    """Coordinates agent assignments and execution."""

    def __init__(self, agent_factory: IAgentFactory, task_scheduler: ITaskScheduler):
        self.agent_factory = agent_factory
        self.task_scheduler = task_scheduler

    async def assign_agent_to_task(self, task: Task) -> AgentAssignment:
        """Assign appropriate agent to task based on requirements."""

    async def coordinate_multi_agent_workflow(self, workflow_id: UUID) -> CoordinationResult:
        """Coordinate multiple agents for complex workflows."""
```

**Step 1.3: Extract Workflow Integrator** (Day 5-6)
```python
# NEW: app/services/orchestrator/workflow_integrator.py
class WorkflowIntegrator:
    """Integrates orchestrator with workflow engine."""

    def __init__(self, workflow_engine: IWorkflowEngine, hitl_service: IHitlService):
        self.workflow_engine = workflow_engine
        self.hitl_service = hitl_service

    async def execute_workflow_phase(self, phase: WorkflowPhase) -> PhaseResult:
        """Execute workflow phase with HITL integration."""

    async def handle_phase_transition(self, from_phase: str, to_phase: str) -> bool:
        """Handle workflow phase transitions with validation."""
```

**Step 1.4: Refactor Core Orchestrator** (Day 7-8)
```python
# UPDATED: app/services/orchestrator/orchestrator_core.py (200 LOC max)
class OrchestratorCore:
    """Core orchestration logic - delegates to specialized managers."""

    def __init__(self,
                 project_manager: ProjectLifecycleManager,
                 agent_coordinator: AgentCoordinator,
                 workflow_integrator: WorkflowIntegrator,
                 handoff_manager: HandoffManager,
                 status_tracker: StatusTracker):
        # Dependency injection of specialized services

    async def run_project_workflow(self, project_id: UUID, workflow_id: str) -> WorkflowResult:
        """Main orchestration method - delegates to specialists."""
        # 1. Project lifecycle management
        project_status = await self.project_manager.get_project_status(project_id)

        # 2. Agent coordination
        agents = await self.agent_coordinator.get_required_agents(workflow_id)

        # 3. Workflow execution
        result = await self.workflow_integrator.execute_workflow(workflow_id, agents)

        # 4. Status tracking
        await self.status_tracker.update_workflow_status(project_id, result)

        return result
```

### 🎯 **1.2 HITL Service Breakup** (Week 2)
**Current**: 1,325 LOC → **Target**: 5 services × 150-200 LOC

#### New Structure:
```
app/services/hitl/
├── __init__.py
├── hitl_core.py                   # 180 LOC - Core HITL management
├── trigger_processor.py           # 170 LOC - Trigger evaluation logic
├── phase_gate_manager.py          # 200 LOC - Phase gate validation
├── response_processor.py          # 160 LOC - Response handling
└── validation_engine.py           # 190 LOC - Quality validation
```

### 🎯 **1.3 Workflow Engine Breakup** (Week 3)
**Current**: 1,226 LOC → **Target**: 4 services × 150-200 LOC

#### New Structure:
```
app/services/workflow/
├── __init__.py
├── execution_engine.py            # 200 LOC - Core execution
├── state_manager.py               # 180 LOC - State persistence
├── sdlc_orchestrator.py           # 170 LOC - SDLC-specific logic
└── event_dispatcher.py            # 160 LOC - Event management
```

---

## 📋 **PHASE 2: MEDIUM PRIORITY CLEANUP** (Weeks 4-5)

### 🎯 **2.1 Base Agent Refactoring** (Week 4)
**Current**: 657 LOC → **Target**: 3 files × 150-220 LOC

```
app/agents/base/
├── __init__.py
├── base_agent.py              # 200 LOC - Core agent functionality
├── reliability_manager.py     # 220 LOC - LLM reliability features
└── hitl_controller.py         # 200 LOC - HITL integration
```

### 🎯 **2.2 AutoGen Service Split** (Week 4)
**Current**: 681 LOC → **Target**: 3 files × 150-200 LOC

```
app/services/autogen/
├── __init__.py
├── autogen_core.py                # 200 LOC - Core functionality
├── agent_factory.py               # 190 LOC - Agent creation
└── conversation_manager.py        # 180 LOC - Conversation handling
```

### 🎯 **2.3 Template Service Split** (Week 5)
**Current**: 526 LOC → **Target**: 3 files × 150-180 LOC

```
app/services/template/
├── __init__.py
├── template_core.py               # 180 LOC - Core operations
├── renderer.py                    # 170 LOC - Rendering logic
└── validator.py                   # 150 LOC - Validation
```

---

## 📋 **PHASE 3: ARCHITECTURE FOUNDATION** (Week 6)

### 🎯 **3.1 Service Interfaces**
Create proper abstractions for dependency injection:

```python
# app/interfaces/orchestrator_interface.py
from abc import ABC, abstractmethod

class IOrchestratorService(ABC):
    @abstractmethod
    async def run_project_workflow(self, project_id: UUID, workflow_id: str) -> WorkflowResult:
        pass

    @abstractmethod
    async def create_project(self, project_data: CreateProjectRequest) -> Project:
        pass

# app/interfaces/workflow_interface.py
class IWorkflowEngine(ABC):
    @abstractmethod
    async def execute_workflow(self, workflow_id: str, context: WorkflowContext) -> WorkflowResult:
        pass

# app/interfaces/hitl_interface.py
class IHitlService(ABC):
    @abstractmethod
    async def create_approval_request(self, request: ApprovalRequest) -> UUID:
        pass
```

### 🎯 **3.2 Dependency Injection Container**
```python
# app/di/container.py
from dependency_injector import containers, providers

class ApplicationContainer(containers.DeclarativeContainer):
    # Database
    db_session = providers.Factory(get_session)

    # Core services
    project_lifecycle_manager = providers.Factory(
        ProjectLifecycleManager,
        db=db_session,
        event_dispatcher=providers.Factory(EventDispatcher)
    )

    agent_coordinator = providers.Factory(
        AgentCoordinator,
        agent_factory=providers.Factory(AgentFactory),
        task_scheduler=providers.Factory(TaskScheduler)
    )

    # Main orchestrator
    orchestrator = providers.Factory(
        OrchestratorCore,
        project_manager=project_lifecycle_manager,
        agent_coordinator=agent_coordinator,
        # ... other dependencies
    )
```

---

## 🛠 **IMPLEMENTATION GUIDELINES**

### **Daily Implementation Checklist**

**For Each Service Split:**
1. ✅ Create interface first
2. ✅ Extract logic into new service class
3. ✅ Update dependency injection
4. ✅ Write unit tests for new service
5. ✅ Update main service to use new dependency
6. ✅ Run integration tests
7. ✅ Update import statements across codebase

### **Code Quality Standards**
- **Max 200 LOC per file** (strict enforcement)
- **Single responsibility** per class
- **Interface-based dependencies**
- **Unit test coverage > 80%**
- **No circular dependencies**

### **Testing Strategy**
```python
# Test each extracted service in isolation
def test_project_lifecycle_manager():
    # Mock dependencies
    mock_db = Mock()
    mock_event_dispatcher = Mock()

    manager = ProjectLifecycleManager(mock_db, mock_event_dispatcher)

    # Test isolated functionality
    result = await manager.create_project(project_data)

    assert result.status == "created"
    mock_event_dispatcher.dispatch.assert_called_once()
```

---

## 🚨 **RISK MITIGATION**

### **High-Risk Areas**
1. **Circular Dependencies**: orchestrator ↔ workflow ↔ hitl
2. **Database Session Management**: Multiple services sharing sessions
3. **Event Propagation**: Cross-service event dependencies

### **Mitigation Strategies**
1. **Event Bus Pattern**: Decouple services with events
2. **Repository Pattern**: Abstract database access
3. **Interface Segregation**: Clear service boundaries
4. **Comprehensive Testing**: Unit + integration tests

### **Rollback Plan**
- Keep original files as `.backup` during refactoring
- Feature flags for new vs old implementations
- Gradual migration with A/B testing

---

## 📊 **SUCCESS METRICS**

### **Before Refactoring**
- Average file size: 1,141 LOC
- Development velocity: Slow (large file navigation)
- Test coverage: Limited (tight coupling)
- Bug isolation: Difficult (multiple responsibilities)

### **After Refactoring (Target)**
- Average file size: 170 LOC (66% reduction)
- Development velocity: 60% faster
- Test coverage: >80% (isolated components)
- Bug isolation: 90% faster (focused responsibilities)

### **Measurable Benefits**
- **Code Review Time**: 50% reduction (smaller changesets)
- **Feature Development**: 60% faster (focused components)
- **Bug Fix Time**: 70% faster (isolated failures)
- **Onboarding Time**: 40% faster (easier to understand)

---

## 🎯 **IMPLEMENTATION PRIORITY**

### **Week 1-2: Orchestrator Breakup** (CRITICAL)
This is the biggest violator and impacts everything else.

### **Week 2: HITL Service Breakup** (HIGH)
HITL integration touches many services - needs clean interfaces.

### **Week 3: Workflow Engine Breakup** (HIGH)
Core execution logic needs separation from state management.

### **Week 4-5: Agent & AutoGen Cleanup** (MEDIUM)
Important for agent development velocity.

### **Week 6: Architecture Foundation** (LOW)
Establishes patterns for future development.

---

## ✅ **DAILY TASKS FOR DEVELOPER**

### **Day 1: Orchestrator - Extract Project Lifecycle Manager**
1. Create `app/services/orchestrator/project_lifecycle_manager.py`
2. Move project CRUD operations from orchestrator
3. Create `IProjectLifecycleManager` interface
4. Write unit tests
5. Update orchestrator to use new service

### **Day 2: Orchestrator - Extract Agent Coordinator**
1. Create `app/services/orchestrator/agent_coordinator.py`
2. Move agent assignment logic
3. Create interface and tests
4. Update orchestrator

### **Day 3-8: Continue Orchestrator Breakup**
- Follow same pattern for each extracted service
- Maintain backward compatibility during transition
- Comprehensive testing at each step

This refactoring plan will transform your monolithic services into a clean, maintainable architecture following SOLID principles and the 500 LOC limit.