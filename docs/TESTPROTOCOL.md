---
inclusion: always
---

# Testing Protocol

Testing standards. Prioritize real data over mocks, automate test maintenance, ensure comprehensive coverage.

## Core Principles

- **Real Data First**: Use staging/production data over mocks. Only mock for isolated unit tests
- **Auto-Sync Tests**: Generate tests from schemas, flag outdated tests on code changes
- **Mandatory Coverage**: Security, accessibility, and critical paths require >80% coverage
- **Production-Like**: Tests must replicate real-world behavior and edge cases
- **IF THERE IS A DISCREPRENCY BETWEEN THE TEST AND THE CODE, VERIFY THE CORRECT CODE STRUCTURE IN THE REST OF THE CODEBASE**.

## Frontend Testing

**Framework**: Vitest + React Testing Library (`frontend/vitest.setup.ts`)

**Requirements**:
- Test user interactions with real DOM events
- Use `@testing-library/react` for component testing
- Run `axe-core` accessibility checks on all components
- Generate TypeScript-compliant test data with factories
- Avoid mocking hooks except for isolated unit tests
- Use staging API responses over MSW mocks when possible

## Backend Testing

**Framework**: pytest + pytest-asyncio (`backend/conftest.py`)

**Requirements**:
- Test async endpoints with real HTTP requests via `pytest-httpx`
- Use `factory_boy` for dynamic test data tied to Pydantic models
- Generate API tests from OpenAPI schema using `schemathesis`
- Test error handling: rate limits, invalid inputs, security headers
- Use staging DB or in-memory SQLite for integration tests
- Test agent orchestration with sandbox LLM APIs (not mocks)

### Mock Usage Guidelines (Critical)

**✅ APPROPRIATE MOCKING**:
- External APIs (OpenAI, Anthropic, third-party services)
- File system operations (when testing business logic)
- Time-dependent functions (`datetime.now()`)
- Network requests to external services
- Hardware-dependent operations

**❌ INAPPROPRIATE MOCKING**:
- Database sessions (`@patch('get_session')` - hides schema issues)
- Internal service instances (hides business logic bugs)
- Pydantic model validation (bypasses actual validation)
- SQLAlchemy queries (misses constraint violations)
- Internal API endpoints (bypasses request handling)

### Test Classification System

**MANDATORY**: All tests must use classification markers. Multiple markers are allowed and encouraged for complex scenarios:

```python
@pytest.mark.real_data        # Uses real database/services
@pytest.mark.external_service # Mocks external dependencies only
@pytest.mark.mock_data        # Uses mocks (legacy/comparison)

# RECOMMENDED COMBINATIONS:
@pytest.mark.real_data @pytest.mark.external_service  # Integration tests (preferred)
@pytest.mark.mock_data @pytest.mark.external_service  # Legacy compatibility
```

**Classification Rules**:
- Every test MUST have at least one classification marker
- Tests can combine `real_data` + `external_service` (recommended pattern)
- Tests can combine `mock_data` + `external_service` (legacy compatibility)
- Tests CANNOT combine `mock_data` + `real_data` (conflicting approaches)

**Best Practice**: Use `@pytest.mark.real_data @pytest.mark.external_service` for integration tests that use real database operations but mock external APIs.

### Running Tests by Classification

The multi-marker system enables powerful test filtering:

```bash
# Run only tests that use real database operations
pytest -m "real_data"

# Run tests that mock external services only (no real database)
pytest -m "external_service and not real_data"

# Run integration tests (real database + external service mocking)
pytest -m "real_data and external_service"

# Run legacy mock tests
pytest -m "mock_data"

# Run all tests except legacy mocks
pytest -m "not mock_data"

# Run fast tests (no external service calls)
pytest -m "not external_service"
```

### Database Testing Standards

**Real Database Integration Requirements**
- **Mandatory Real DB**: All integration tests must use real database connections
- **Database Test Manager**: Use proper database testing utilities for session management
- **No Mock Databases**: Mocking database calls is prohibited for integration tests
- **Session Cleanup**: All tests must properly clean up database sessions and test data
- **Schema Validation**: Database schema changes must be tested with real migrations

Use database testing utilities for real database operations:

```python
@pytest.fixture
def db_manager():
    manager = DatabaseTestManager(use_memory_db=True)
    manager.setup_test_database()
    yield manager
    manager.cleanup_test_database()

@pytest.mark.real_data
def test_with_real_database(db_manager):
    with db_manager.get_session() as session:
        service = RealService(session)
        result = service.create_record(data)

        # Verify actual database state
        db_checks = [{'table': 'records', 'conditions': {'id': result.id}, 'count': 1}]
        assert db_manager.verify_database_state(db_checks)
```

## WebSocket Testing

**Framework**: `websocket-client` (backend), Vitest (frontend)

**Requirements**:
- Test connection retries, reconnect logic, error recovery
- Use staging WebSocket server over mocks for E2E tests
- Validate message formats against schemas before transmission
- Test serialization-safe wrappers to prevent circular references
- Simulate network failures (high-latency, dropped connections)

## Visual Testing

**Framework**: Puppeteer + pixelmatch (`tests/visual/`)

**Requirements**:
- Capture at 1440px (desktop), 768px (tablet), 375px (mobile)
- Use staging environment for realistic UI rendering
- Check JavaScript console errors during tests
- Run `axe-core` accessibility validation (color contrast, font sizes)
- Compare against baseline images, approve diffs before merge

## Test Automation

**Auto-Generation**:
- Use `schemathesis` for API tests from OpenAPI schemas
- Use `hygen` for component test scaffolding
- Flag outdated tests via Git hooks on model/schema changes

**CI/CD Requirements**:
- Run tests in parallel (`vitest --maxConcurrency`, `pytest --numprocesses`)
- Fail builds on: outdated tests, <80% coverage, security/accessibility failures
- All test types must pass: unit, integration, E2E, visual

## File Structure

```
frontend/tests/     # Component unit/integration tests
backend/tests/      # API and business logic tests
tests/visual/       # Visual regression baselines
tests/e2e/         # Critical user flow tests
```

## Quality Gates

**Before any merge**:
- >80% coverage on critical paths (APIs, UI flows, WebSocket)
- All accessibility (`axe-core`) and security tests pass
- Visual diffs approved or resolved
- No hardcoded test data (use factories/staging data)
- **All tests have proper classification markers** (at least one of: real_data, external_service, mock_data)
- **No inappropriate database/service mocking** (no mocking of internal services/database sessions)
- **Database state verification for data operations** (real_data tests must verify actual DB state)
- **Prefer `real_data + external_service` pattern** for integration tests

### Production Readiness Testing Standards
- **Test Suite Health**: Minimum 95% test success rate required across all environments
- **Performance Testing**: API response times <200ms, real-time features <100ms
- **Integration Coverage**: Minimum 40% real database integration test coverage
- **Service Constructor Testing**: All services tested with proper dependency injection
- **Schema Validation**: All data models tested with proper validation patterns
- **Error Recovery Testing**: Comprehensive error handling and recovery validation

### Service Testing Patterns
- **Constructor Validation**: Service constructors tested with proper parameter patterns
- **Interface Compliance**: Services tested against declared interfaces
- **Configuration Testing**: All configuration objects tested with required fields
- **Import Path Validation**: Module imports validated during test setup
- **Framework Integration**: Framework-specific patterns (team configs, handoffs) properly tested

**Mock Analysis Tools**:
```bash
# Identify inappropriate mocking
python scripts/analyze_mock_usage.py

# Full test suite analysis
python scripts/comprehensive_mock_analysis.py

# Compare mock vs real test approaches
python scripts/compare_mock_vs_real_tests.py
```

**Avoid**:
- Overusing mocks (prefer staging data)
- Brittle tests coupled to DOM structure
- Skipping security/accessibility validation
- Hardcoded JSON fixtures
- **Mocking internal services/database sessions**
- **Tests that only validate mock interactions**
- **Missing test classification markers** (every test needs at least one)
- **Conflicting marker combinations** (cannot use mock_data + real_data)
- **Single-marker integration tests** (prefer real_data + external_service)
- **CHANGING CODE IF THERE IS A DISCREPANCY BETWEEN THE TEST AND THE CODE.**

### Test Infrastructure Anti-Patterns
- **Service Constructor Mocking**: Never mock service constructors or initialization
- **Configuration Object Mocking**: Avoid mocking configuration validation
- **Framework Integration Mocking**: Don't mock framework-specific integration patterns
- **Schema Validation Bypass**: Never skip data validation in tests
- **Import Path Errors**: Validate module import paths during test development

## Service Testing Patterns

### ✅ Real Service Testing
```python
@pytest.mark.real_data
def test_service_behavior():
    service = RealService()  # Real implementation
    result = service.execute_business_logic(input_data)
    assert isinstance(result, ExpectedType)
```

### ✅ External Dependency Mocking
```python
@pytest.mark.external_service
def test_external_integration():
    with patch('external_api.Client') as mock_client:
        mock_client.return_value.call.return_value = {"status": "success"}
        service = RealService()  # Real internal service
        result = service.call_external_api()
        assert result["status"] == "success"
```

### ✅ RECOMMENDED: Integration Testing Pattern
```python
@pytest.mark.real_data
@pytest.mark.external_service
def test_full_integration_flow(db_manager):
    """Test complete flow: real database + mocked external APIs."""
    with patch('external_api.LLMClient') as mock_llm:
        mock_llm.return_value.generate.return_value = {"text": "response"}

        with db_manager.get_session() as session:
            service = RealService(session)  # Real database operations
            result = service.process_with_llm_call(user_input)

            # Verify real database state
            assert result.id is not None
            db_checks = [{'table': 'results', 'conditions': {'id': result.id}, 'count': 1}]
            assert db_manager.verify_database_state(db_checks)
```

### ❌ Anti-Patterns
```python
# DON'T: Mock internal services
@patch('app.services.my_service.MyService')
def test_with_service_mock(mock_service):
    # This hides business logic issues

# DON'T: Mock database sessions
@patch('app.database.get_session')
def test_with_db_mock(mock_session):
    # This hides schema and constraint issues

# DON'T: Pass dict configs to string-path services
def test_service_with_wrong_config():
    service = MyService({"path": "config"})  # Should be string path

# DON'T: Skip required fields in test configurations
def test_incomplete_config():
    config = {"workflows": "single_item"}  # Should be array
    # Missing required fields like 'id', 'project_id', etc.
```

### Configuration Testing Patterns

**✅ Proper Configuration Testing**
```python
def test_service_constructor_patterns():
    # CORRECT: String path constructors
    service = TemplateService("templates/path")
    assert service.template_path == "templates/path"

def test_configuration_validation():
    # CORRECT: Array configurations with proper naming
    config = {
        "workflows": ["workflow1", "workflow2"],  # Plural array
        "id": "12345678-1234-5678-9abc-123456789abc",  # Proper UUID
        "project_id": "87654321-4321-8765-4321-987654321098",
        "required_field": "value"  # All required fields present
    }
    validator = ConfigValidator(config)
    assert validator.is_valid()

def test_framework_integration():
    # CORRECT: Test with all required agent types
    team_config = {
        "agents": [
            {"type": "orchestrator"},  # Don't miss required types
            {"type": "analyst"},
            {"type": "architect"},
            {"type": "coder"}
        ],
        "workflows": ["sdlc_workflow"]  # Plural array format
    }
    team = AgentTeam(team_config)
    assert len(team.agents) == 4
```
