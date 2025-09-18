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

**MANDATORY**: All tests must use classification markers:

```python
@pytest.mark.real_data        # Uses real database/services
@pytest.mark.external_service # Mocks external dependencies only  
@pytest.mark.mock_data        # Uses mocks (legacy/comparison)
```

### Database Testing Standards

Use `DatabaseTestManager` for real database operations:

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
- **All tests have proper classification markers**
- **No inappropriate database/service mocking**
- **Database state verification for data operations**

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
- **Missing test classification markers**

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
```