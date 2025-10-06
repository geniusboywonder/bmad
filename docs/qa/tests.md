# BMAD Backend Testing Guide
## Post-Consolidation Test Coverage & Implementation Guide

*Generated: October 2025 - Post Service Consolidation & Configuration Simplification*

## Overview

This guide provides comprehensive testing requirements for the BMAD backend after major architectural consolidation phases completed in October 2025. The system has undergone significant simplification:

- **Service Consolidation**: 67% reduction in utility services (7 files → 4 consolidated services)
- **Configuration Simplification**: 60% reduction in settings (50+ → ~20 core settings)
- **Dead Code Elimination**: 800+ lines of unused code removed
- **Redis Simplification**: Single database architecture

## Current Test Status

**Test Suite Metrics:**
- **Total Test Files**: 50 test files
- **Current Pass Rate**: ~75% (676 passed, 226 failed)
- **Test Categories**: Unit (60%), Integration (30%), E2E (10%)
- **Classification**: All tests must use `@pytest.mark.real_data`, `@pytest.mark.mock_data`, or `@pytest.mark.external_service`

## Critical Testing Requirements

### 1. Mandatory Test Classification

**ALL TESTS MUST BE MARKED** with data source classification:

```python
@pytest.mark.real_data        # Uses real database/services
@pytest.mark.external_service # Mocks external dependencies only  
@pytest.mark.mock_data        # Uses mocks (legacy/comparison)
```

**Examples:**
```python
@pytest.mark.real_data
@pytest.mark.external_service
def test_document_service_with_real_db():
    """Test document processing with real database, mock external APIs."""
    pass

@pytest.mark.mock_data
def test_legacy_comparison():
    """Legacy test for comparison - may hide database issues."""
    pass
```

### 2. Service Consolidation Test Updates

#### 2.1 DocumentService Tests (NEW - MISSING)

**File**: `backend/tests/unit/test_document_service.py`

```python
"""
Test suite for consolidated DocumentService.
Covers document assembly, sectioning, and granularity analysis.
"""

import pytest
from app.services.document_service import DocumentService
from tests.utils.database_test_utils import DatabaseTestManager

class TestDocumentService:
    """Test consolidated document processing service."""
    
    @pytest.fixture
    def document_config(self):
        return {
            "enable_deduplication": True,
            "enable_conflict_resolution": True,
            "max_section_size": 8192,
            "min_section_size": 512,
            "enable_semantic_sectioning": True
        }
    
    @pytest.fixture
    def document_service(self, document_config):
        return DocumentService(document_config)
    
    # Document Assembly Tests
    @pytest.mark.real_data
    async def test_assemble_document_multiple_artifacts(self, document_service, db_manager):
        """Test document assembly from multiple artifacts."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data  
    async def test_assemble_document_deduplication(self, document_service):
        """Test content deduplication during assembly."""
        # Implementation needed
        pass
    
    # Document Sectioning Tests
    @pytest.mark.mock_data
    def test_section_document_markdown(self, document_service):
        """Test sectioning of markdown content."""
        # Implementation needed
        pass
    
    @pytest.mark.mock_data
    def test_section_document_size_constraints(self, document_service):
        """Test sectioning respects size constraints."""
        # Implementation needed
        pass
    
    # Granularity Analysis Tests  
    @pytest.mark.mock_data
    async def test_analyze_granularity_simple_content(self, document_service):
        """Test granularity analysis for simple content."""
        # Implementation needed
        pass
    
    @pytest.mark.mock_data
    async def test_analyze_granularity_complex_content(self, document_service):
        """Test granularity analysis for complex content."""
        # Implementation needed
        pass
```

#### 2.2 LLMService Tests (NEW - MISSING)

**File**: `backend/tests/unit/test_llm_service.py`

```python
"""
Test suite for consolidated LLMService.
Covers usage tracking, retry logic, and cost monitoring.
"""

import pytest
from app.services.llm_service import LLMService, LLMProvider
from tests.utils.database_test_utils import DatabaseTestManager

class TestLLMService:
    """Test consolidated LLM operations service."""
    
    @pytest.fixture
    def llm_service(self):
        return LLMService()
    
    # Usage Tracking Tests
    @pytest.mark.real_data
    def test_track_usage_basic(self, llm_service):
        """Test basic usage tracking."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    def test_track_usage_multiple_providers(self, llm_service):
        """Test usage tracking across multiple providers."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    def test_get_usage_summary(self, llm_service):
        """Test usage summary generation."""
        # Implementation needed
        pass
    
    # Retry Logic Tests
    @pytest.mark.external_service
    async def test_with_retry_decorator_success(self, llm_service):
        """Test retry decorator with successful operation."""
        # Implementation needed
        pass
    
    @pytest.mark.external_service
    async def test_with_retry_decorator_retryable_error(self, llm_service):
        """Test retry decorator with retryable errors."""
        # Implementation needed
        pass
    
    @pytest.mark.external_service
    async def test_with_retry_decorator_non_retryable_error(self, llm_service):
        """Test retry decorator with non-retryable errors."""
        # Implementation needed
        pass
    
    # Cost Monitoring Tests
    @pytest.mark.mock_data
    def test_cost_calculation_openai(self, llm_service):
        """Test cost calculation for OpenAI."""
        # Implementation needed
        pass
    
    @pytest.mark.mock_data
    def test_cost_calculation_anthropic(self, llm_service):
        """Test cost calculation for Anthropic."""
        # Implementation needed
        pass
```

#### 2.3 Orchestrator Recovery Tests (UPDATED)

**File**: `backend/tests/unit/test_orchestrator_recovery.py`

```python
"""
Test suite for orchestrator recovery management.
Recovery logic is now integrated into orchestrator.py.
"""

import pytest
from app.services.orchestrator import OrchestratorService
from app.services.orchestrator.recovery_manager import RecoveryManager

class TestOrchestratorRecovery:
    """Test orchestrator recovery integration."""
    
    @pytest.mark.real_data
    async def test_recovery_manager_initialization(self, db_manager):
        """Test recovery manager initialization."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    async def test_recovery_strategy_determination(self, db_manager):
        """Test recovery strategy determination logic."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    async def test_recovery_step_execution(self, db_manager):
        """Test recovery step execution."""
        # Implementation needed
        pass
```

### 3. Configuration Simplification Tests

#### 3.1 Settings Tests (UPDATED)

**File**: `backend/tests/unit/test_settings_simplified.py`

```python
"""
Test suite for simplified settings configuration.
Tests the consolidated 20-variable configuration system.
"""

import pytest
from app.settings import Settings

class TestSimplifiedSettings:
    """Test simplified configuration system."""
    
    @pytest.mark.mock_data
    def test_redis_single_url_configuration(self):
        """Test single Redis URL configuration."""
        # Implementation needed
        pass
    
    @pytest.mark.mock_data
    def test_llm_provider_agnostic_config(self):
        """Test provider-agnostic LLM configuration."""
        # Implementation needed
        pass
    
    @pytest.mark.mock_data
    def test_hitl_simplified_settings(self):
        """Test simplified HITL settings."""
        # Implementation needed
        pass
    
    @pytest.mark.mock_data
    def test_backward_compatibility_getattr(self):
        """Test backward compatibility with getattr defaults."""
        # Implementation needed
        pass
```

#### 3.2 Startup Service Tests (UPDATED)

**File**: `backend/tests/unit/test_startup_service_enhanced.py`

```python
"""
Test suite for enhanced startup service.
Includes HITL cleanup and simplified Redis configuration.
"""

import pytest
from app.services.startup_service import StartupService

class TestEnhancedStartupService:
    """Test enhanced startup service with HITL cleanup."""
    
    @pytest.mark.real_data
    async def test_startup_hitl_cleanup(self, db_manager):
        """Test HITL approval cleanup on startup."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    async def test_startup_redis_single_db_cleanup(self, db_manager):
        """Test Redis cleanup with single database."""
        # Implementation needed
        pass
```

### 4. Missing Integration Tests

#### 4.1 Workflow Deliverables Tests (NEW)

**File**: `backend/tests/integration/test_workflow_deliverables.py`

```python
"""
Test suite for dynamic workflow deliverables system.
Tests the new 17-artifact SDLC workflow.
"""

import pytest
from app.api.workflows import get_workflow_deliverables

class TestWorkflowDeliverables:
    """Test dynamic workflow deliverables integration."""
    
    @pytest.mark.real_data
    async def test_greenfield_fullstack_deliverables(self, client):
        """Test loading of greenfield fullstack deliverables."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    async def test_deliverables_stage_mapping(self, client):
        """Test deliverable mapping to SDLC stages."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    async def test_hitl_required_plans(self, client):
        """Test HITL-required plan artifacts."""
        # Implementation needed
        pass
```

#### 4.2 HITL Duplicate Prevention Tests (NEW)

**File**: `backend/tests/integration/test_hitl_duplicate_prevention.py`

```python
"""
Test suite for HITL duplicate message prevention.
Tests the single approval per task workflow.
"""

import pytest
from app.tasks.agent_tasks import process_agent_task

class TestHITLDuplicatePrevention:
    """Test HITL duplicate prevention workflow."""
    
    @pytest.mark.real_data
    async def test_single_approval_per_task(self, db_manager):
        """Test that only one approval is created per task."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    async def test_existing_approval_reuse(self, db_manager):
        """Test reuse of existing approval records."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    async def test_no_response_approval_creation(self, db_manager):
        """Test that response approvals are not created."""
        # Implementation needed
        pass
```

### 5. Performance & Load Tests

#### 5.1 Consolidated Service Performance (NEW)

**File**: `backend/tests/performance/test_consolidated_services_performance.py`

```python
"""
Performance tests for consolidated services.
Ensures consolidation didn't impact performance.
"""

import pytest
import time
from app.services.document_service import DocumentService
from app.services.llm_service import LLMService

class TestConsolidatedServicePerformance:
    """Test performance of consolidated services."""
    
    @pytest.mark.real_data
    @pytest.mark.performance
    async def test_document_service_large_assembly(self, performance_timer):
        """Test document assembly performance with large datasets."""
        # Implementation needed - should complete <2000ms
        pass
    
    @pytest.mark.real_data
    @pytest.mark.performance
    def test_llm_service_usage_tracking_bulk(self, performance_timer):
        """Test LLM usage tracking performance with bulk operations."""
        # Implementation needed - should complete <500ms
        pass
```

### 6. Security & Safety Tests

#### 6.1 HITL Safety Integration (UPDATED)

**File**: `backend/tests/security/test_hitl_safety_consolidated.py`

```python
"""
Security tests for HITL safety system post-consolidation.
"""

import pytest
from app.services.hitl_safety_service import HITLSafetyService

class TestHITLSafetyConsolidated:
    """Test HITL safety with consolidated services."""
    
    @pytest.mark.real_data
    @pytest.mark.security
    async def test_safety_with_document_service(self, db_manager):
        """Test HITL safety integration with DocumentService."""
        # Implementation needed
        pass
    
    @pytest.mark.real_data
    @pytest.mark.security
    async def test_safety_with_llm_service(self, db_manager):
        """Test HITL safety integration with LLMService."""
        # Implementation needed
        pass
```

## Test Implementation Priorities

### Priority 1 (Critical - Implement First)
1. **DocumentService Tests** - Core functionality, 0% coverage
2. **LLMService Tests** - Core functionality, 0% coverage  
3. **Configuration Tests** - Simplified settings validation
4. **HITL Duplicate Prevention** - Critical workflow fix

### Priority 2 (Important - Implement Second)
1. **Workflow Deliverables Tests** - New 17-artifact system
2. **Orchestrator Recovery Tests** - Updated integration
3. **Performance Tests** - Ensure consolidation didn't hurt performance
4. **Startup Service Tests** - Enhanced cleanup functionality

### Priority 3 (Standard - Implement Third)
1. **Security Integration Tests** - HITL safety with consolidated services
2. **Error Handling Tests** - Consolidated service error scenarios
3. **Backward Compatibility Tests** - Ensure aliases work correctly

## Test Execution Guidelines

### Running Tests by Category

```bash
# Run all real database tests
pytest -m real_data

# Run all mock data tests  
pytest -m mock_data

# Run external service tests
pytest -m external_service

# Run performance tests
pytest -m performance

# Run security tests
pytest -m security
```

### Test Development Standards

1. **Real Data First**: Prioritize `@pytest.mark.real_data` tests over mocks
2. **External Service Mocking**: Mock external APIs but use real database
3. **Performance Thresholds**: Document expected completion times
4. **Error Scenarios**: Test both success and failure paths
5. **Classification Required**: All tests must have data source markers

### Database Testing Patterns

```python
# Use DatabaseTestManager for real database tests
@pytest.mark.real_data
async def test_with_real_database(self, db_manager):
    with db_manager.get_session() as session:
        service = MyService(session)
        result = service.create_record(data)
        
        # Verify actual database state
        db_checks = [{'table': 'records', 'conditions': {'id': result.id}, 'count': 1}]
        assert db_manager.verify_database_state(db_checks)
```

## Quality Gates

### Before Merge Requirements
- **>80% test coverage** on critical paths (consolidated services, HITL workflow)
- **All new tests classified** with appropriate markers
- **Performance tests pass** within documented thresholds
- **Security tests validate** HITL safety integration
- **No inappropriate mocking** of internal services/database sessions

### Test Maintenance
- **Monthly review** of mock vs real test ratios
- **Quarterly cleanup** of outdated test patterns
- **Continuous monitoring** of test execution times
- **Regular validation** of test classification accuracy

## Implementation Checklist

### Phase 1: Core Service Tests (Week 1)
- [ ] Create `test_document_service.py` with 15+ test cases
- [ ] Create `test_llm_service.py` with 20+ test cases
- [ ] Update existing tests using old service imports
- [ ] Validate all tests use proper classification markers

### Phase 2: Integration Tests (Week 2)  
- [ ] Create `test_workflow_deliverables.py` with 10+ test cases
- [ ] Create `test_hitl_duplicate_prevention.py` with 8+ test cases
- [ ] Update `test_orchestrator_recovery.py` for new integration
- [ ] Create `test_settings_simplified.py` with 12+ test cases

### Phase 3: Performance & Security (Week 3)
- [ ] Create `test_consolidated_services_performance.py` with 6+ test cases
- [ ] Create `test_hitl_safety_consolidated.py` with 10+ test cases
- [ ] Update existing performance tests for new thresholds
- [ ] Validate security test coverage meets requirements

### Phase 4: Validation & Documentation (Week 4)
- [ ] Run full test suite and achieve >80% pass rate
- [ ] Document test count changes and coverage improvements
- [ ] Update test execution documentation
- [ ] Create test maintenance procedures

## Expected Outcomes

**Test Suite Improvements:**
- **New Test Files**: 8-10 new test files for consolidated services
- **Updated Test Files**: 15-20 existing files updated for new APIs
- **Test Count**: +100-150 new test cases for missing coverage
- **Pass Rate Target**: >85% (up from current 75%)
- **Coverage Target**: >80% on all consolidated services

**Quality Improvements:**
- **Real Database Testing**: Increased ratio of real vs mock tests
- **Performance Validation**: Documented thresholds for all critical operations
- **Security Coverage**: Complete HITL safety integration testing
- **Maintenance Reduction**: Simplified test patterns aligned with consolidated architecture

This testing guide provides the foundation for comprehensive test coverage of the consolidated BMAD backend architecture, ensuring production readiness and maintainability.