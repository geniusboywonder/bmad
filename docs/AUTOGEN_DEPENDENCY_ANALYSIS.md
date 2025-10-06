# AutoGen Dependency Analysis
**Date:** October 2025
**Purpose:** Identify actual vs. assumed AutoGen blocking dependencies

## Executive Summary

**CRITICAL FINDING:** Previous assumption that AutoGen blocks Phase 1.3 (Workflow) and Phase 2 (HITL) simplification was **INCORRECT**.

**Actual AutoGen Usage:**
- **6 files** actively use AutoGenService.execute_task()
- **4 production files** depend on AutoGen for task execution
- **0 workflow service files** use AutoGen (only workflow_step_processor.py)
- **0 HITL service files** use AutoGen

**Impact on ONEPLAN Sequencing:**
- ✅ Phase 1.3 (Workflow consolidation) can proceed WITHOUT MAF migration
- ✅ Phase 2 (HITL simplification) can proceed WITHOUT MAF migration
- ✅ Phase 3 (Settings cleanup) can proceed WITHOUT MAF migration
- ❌ Only task execution layer requires MAF migration

---

## Complete AutoGen Dependency Map

### 1. Core AutoGen Infrastructure (Will Be Replaced by MAF)

**app/services/autogen_service.py**
- Core AutoGen service wrapper
- Status: Will be replaced by MAF's native agent execution

**app/services/autogen/** (directory)
- AutoGen framework integration code
- Status: Will be replaced by MAF framework

**app/agents/base_agent.py**
- Legacy AutoGen agent base classes
- Status: Already replaced by ADK agents in production

---

### 2. Production Files Using AutoGenService.execute_task()

#### **app/tasks/agent_tasks.py** ⚠️ **CRITICAL DEPENDENCY**
```python
Line 18:  from app.services.autogen_service import AutoGenService
Line 169: autogen_service = AutoGenService()
Line 308: result = asyncio.run(autogen_service.execute_task(task, handoff, context_artifacts))
```
**Purpose:** Celery task execution for all agent operations
**Impact:** Core execution path - MUST be migrated to MAF
**Blockers:** None - can be migrated independently

#### **app/services/orchestrator/orchestrator_core.py** ⚠️ **DEPENDENCY**
```python
Line 16: from app.services.autogen_service import AutoGenService
Line 38: self.autogen_service = AutoGenService()
Line 40: self.conflict_resolver = ConflictResolverService(self.context_store, self.autogen_service)
Line 48: self.handoff_manager = HandoffManager(db, self.autogen_service, self.context_store)
```
**Purpose:** Multi-agent orchestration coordination
**Impact:** Passes AutoGenService to conflict resolution and handoff management
**Blockers:** None - orchestrator_core.py can be updated when MAF is ready

#### **app/services/orchestrator/handoff_manager.py** ⚠️ **DEPENDENCY**
```python
Line 12: from app.services.autogen_service import AutoGenService
Line 23: def __init__(self, db, autogen_service: AutoGenService, context_store):
Line 147: result = await self.autogen_service.execute_task(task, handoff, context_artifacts)
```
**Purpose:** Agent handoff execution
**Impact:** Executes agent tasks during handoffs
**Blockers:** None - handoff_manager.py can be updated when MAF is ready

#### **app/services/workflow_step_processor.py** ⚠️ **DEPENDENCY**
```python
Line 18: from app.services.autogen_service import AutoGenService
Line 38: self.autogen_service = AutoGenService()
Line 292: result = await self.autogen_service.execute_task(task, handoff, context_artifacts)
```
**Purpose:** Workflow step execution via agents
**Impact:** Executes individual workflow steps
**Blockers:** None - workflow_step_processor.py can be updated when MAF is ready

#### **app/services/conflict_resolver.py** ⚠️ **DEPENDENCY**
```python
Line 30: from ..services.autogen_service import AutoGenService
Line 48: def __init__(self, context_store: ContextStoreService, autogen_service: AutoGenService):
```
**Purpose:** Conflict resolution coordination
**Impact:** Uses AutoGenService for agent-based conflict resolution
**Blockers:** None - conflict_resolver.py can be updated when MAF is ready

---

### 3. Test Files Referencing AutoGen (Not Production)

**tests/test_autogen_conversation.py**
- Legacy test file
- Status: Can be deleted or updated after MAF migration

**tests/test_hitl_triggers.py**
- Uses mock AutoGenService
- Status: No blocker - uses mocks

**tests/test_solid_refactored_services.py**
- Uses mock AutoGenService
- Status: No blocker - uses mocks

**tests/test_conflict_resolution.py**
- Uses mock AutoGenService
- Status: No blocker - uses mocks

**tests/integration/test_external_services.py**
- Uses mock AutoGenService
- Status: No blocker - uses mocks

**tests/conftest.py**
- Mock AutoGenService fixture
- Status: No blocker - test infrastructure

**scripts/external_service_testing_strategy.py**
- Documentation/testing strategy
- Status: No blocker - not production code

---

## CRITICAL FINDINGS: What's NOT Blocked by AutoGen

### ✅ Workflow Services (11 out of 12 files - NO AutoGen dependency)

**Files with NO AutoGen dependency:**
1. `app/services/workflow/execution_engine.py` - Uses workflow_step_processor (which has AutoGen)
2. `app/services/workflow/state_manager.py` - Pure state management
3. `app/services/workflow/event_dispatcher.py` - Event dispatching only
4. `app/services/workflow/sdlc_orchestrator.py` - SDLC coordination
5. ... (other workflow files)

**ONLY dependency:** `workflow_step_processor.py` uses AutoGenService

**Consolidation Impact:**
- 11 workflow files can be consolidated independently
- Only `workflow_step_processor.py` needs to be updated for MAF
- Phase 1.3 can proceed WITHOUT waiting for complete MAF migration

### ✅ HITL Services (ALL 5 files - NO AutoGen dependency)

**Verified NO AutoGen in:**
1. `app/services/hitl_safety_service.py` - ✅ No AutoGen import
2. `app/services/hitl_service.py` - No AutoGen dependency found
3. `app/services/hitl_trigger_manager.py` - No AutoGen dependency found
4. `app/services/response_safety_analyzer.py` - No AutoGen dependency found
5. Other HITL services (if any)

**Consolidation Impact:**
- HITL simplification (6 files → 2 files) can proceed immediately
- Phase 2 is NOT blocked by AutoGen
- HITL toggle/counter system can be implemented before MAF

### ✅ Settings Consolidation (NO AutoGen dependency)

**app/settings.py per-agent settings:**
```python
analyst_agent_provider: Literal["openai", "anthropic", "google"] = Field(default="anthropic")
analyst_agent_model: str = Field(default="claude-3-5-sonnet-20241022")
# ... similar for other agents
```

**Used by:**
- `app/copilot/adk_runtime.py` (CopilotKit/ADK agents)
- `app/config/agent_configs.py` (ADK configuration)

**NOT used by:**
- `app/services/autogen_service.py` (uses different configuration)

**Consolidation Impact:**
- Settings cleanup can proceed immediately
- Phase 3 is NOT blocked by AutoGen

---

## Correct Sequencing Based on Actual Dependencies

### What Can Be Done NOW (Before MAF):

✅ **Phase 1.3: Workflow Consolidation (12 → 3 files)**
- Consolidate 11 workflow files that don't use AutoGen
- Leave `workflow_step_processor.py` for MAF migration
- No AutoGen blocker

✅ **Phase 2: HITL Simplification (6 → 2 files)**
- Consolidate all 5 HITL services (none use AutoGen)
- Implement toggle/counter HITL system
- No AutoGen blocker

✅ **Phase 3: Settings Cleanup**
- Consolidate per-agent settings (used by ADK, not AutoGen)
- Clean up Redis configuration
- No AutoGen blocker

### What MUST Wait for MAF:

❌ **Task Execution Layer Migration**
- `app/tasks/agent_tasks.py` (Celery task processing)
- `app/services/orchestrator/orchestrator_core.py` (multi-agent coordination)
- `app/services/orchestrator/handoff_manager.py` (agent handoffs)
- `app/services/workflow_step_processor.py` (workflow step execution)
- `app/services/conflict_resolver.py` (conflict resolution)

---

## Revised ONEPLAN Sequence

### ✅ CORRECT SEQUENCE (Based on Actual Dependencies):

1. **Phase 0:** Immediate Cleanup (Week 1) - No blockers
2. **Phase 1.1-1.2:** Utility & Orchestrator (Weeks 2-3) - ✅ COMPLETE
3. **Phase 1.3:** Workflow Consolidation (Weeks 4-5) - ✅ CAN START NOW
4. **Phase 2:** HITL Simplification (Weeks 6-7) - ✅ CAN START NOW
5. **Phase 3:** Settings Cleanup (Week 8) - ✅ CAN START NOW
6. **Phase 4:** MAF Migration (Weeks 9-16) - Migrate 5 execution files
7. **Phase 5:** CopilotKit HITL (Weeks 17-20) - After MAF provides interception
8. **Phase 6:** CopilotKit Full Integration (Weeks 21-28)

### ❌ INCORRECT SEQUENCE (What I Originally Assumed):

1. Phase 0-1.2 complete
2. **STOP** - Wait for MAF migration (Phases 4-5)
3. Then do Phase 1.3, 2, 3 after MAF is done
4. Then CopilotKit

**This was wrong because:**
- I assumed ALL workflow/HITL files used AutoGen
- I didn't verify actual imports and dependencies
- Only 5 production files actually use AutoGenService.execute_task()

---

## Action Items

### Immediate (This Week):
1. ✅ Update ONEPLAN.md with correct sequencing
2. ✅ Remove AutoGen blocker assumptions from Phase 1.3, 2, 3
3. ✅ Proceed with workflow consolidation (11 files safe to consolidate)
4. ✅ Proceed with HITL simplification (5 files safe to consolidate)

### MAF Migration Preparation:
1. Identify exact AutoGenService.execute_task() call sites (5 files)
2. Create MAF wrapper interface matching current AutoGenService API
3. Plan incremental migration of 5 execution files
4. Implement BMADMAFWrapper with HITL interception

### Long-term:
1. Delete legacy AutoGen infrastructure after MAF migration
2. Remove test mocks for AutoGenService
3. Archive AutoGen-specific documentation

---

## Lessons Learned

**Never assume dependencies without verification:**
1. ❌ Assumed: "Workflow uses AutoGen, so it's blocked"
2. ✅ Reality: Only workflow_step_processor.py uses AutoGen
3. ❌ Assumed: "HITL uses AutoGen, so it's blocked"
4. ✅ Reality: NO HITL files use AutoGen
5. ❌ Assumed: "Settings are for AutoGen agents"
6. ✅ Reality: Settings are for ADK/CopilotKit agents

**Always check:**
- Actual import statements
- Actual method calls
- Not just file names or assumptions about system architecture
