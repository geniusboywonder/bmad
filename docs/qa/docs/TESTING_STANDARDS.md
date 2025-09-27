# Testing Standards: Mock vs Real Data Classification

## 🎯 **MANDATORY REQUIREMENT**

**ALL tests must clearly indicate whether they use mock data or real database operations.**

This is enforced automatically by the testing framework and **tests will fail** if not properly classified.

## 📋 **Required Test Markers**

### Data Source Classification (Required)

Every test **MUST** have exactly one of these markers:

```python
@pytest.mark.mock_data
def test_example_with_mocks():
    """Test using mocked data - may hide database schema issues."""
    pass

@pytest.mark.real_data
def test_example_with_real_db():
    """Test using real database operations - catches actual issues."""
    pass
```

### Additional Markers (Optional)

```python
@pytest.mark.api_integration    # Verifies complete API → Database flow
@pytest.mark.database_schema    # Validates database schema consistency
@pytest.mark.external_service   # Mocks external services (APIs, file system)
```

## 🚨 **Enforcement Rules**

### 1. Missing Classification = Test Failure
```bash
❌ MISSING CLASSIFICATION: Test must be marked with either:
   @pytest.mark.mock_data    (for tests using mocks)
   @pytest.mark.real_data    (for tests using real database)
```

### 2. Conflicting Markers = Test Failure
```bash
❌ CONFLICTING MARKERS: Test cannot have both mock_data and real_data markers.
```

### 3. Visual Indicators During Test Runs
```bash
🎭 MOCK DATA TEST: test_example_with_mocks
   ⚠️  Warning: Using mocked data - may hide real database schema issues

💾 REAL DATA TEST: test_example_with_real_db
   ✅ Using real database operations - validates actual schema and constraints
```

## 📝 **Test Naming Conventions**

### File Naming
- **Mock-heavy files**: `test_service_name.py`
- **Real database files**: `test_service_name_real_db.py`
- **Integration files**: `test_integration_feature_name.py`

### Function Naming
- **Mock tests**: `test_function_name_mock()`
- **Real DB tests**: `test_function_name_real_db()`
- **API tests**: `test_api_endpoint_name_integration()`

## ✅ **Examples of Proper Classification**

### Mock Data Test
```python
@pytest.mark.mock_data
@pytest.mark.external_service
def test_email_service_send_mock(mock_smtp_client):
    """Test email sending with mocked SMTP client."""
    # Uses mock for external email service - APPROPRIATE
    mock_smtp_client.send.return_value = True

    result = email_service.send_notification("test@example.com")

    assert result is True
    mock_smtp_client.send.assert_called_once()
```

### Real Database Test
```python
@pytest.mark.real_data
@pytest.mark.database_schema
def test_user_creation_real_db(db_manager):
    """Test user creation with real database persistence."""
    # Uses real database - catches schema issues
    with db_manager.get_session() as session:
        user = UserDB(email="test@example.com", active=True)
        session.add(user)
        session.commit()

        # Verify boolean field works correctly
        assert user.active is True
        assert isinstance(user.active, bool)
```

### API Integration Test
```python
@pytest.mark.real_data
@pytest.mark.api_integration
def test_complete_user_signup_flow(api_client, db_manager):
    """Test complete user signup API → Database flow."""
    # Tests end-to-end API to database persistence
    signup_data = {"email": "new@example.com", "password": "secure123"}

    result = api_client.post_and_verify_db(
        '/api/v1/users/signup',
        data=signup_data,
        db_checks=[{
            'table': 'users',
            'conditions': {'email': 'new@example.com'},
            'count': 1
        }]
    )

    assert result['status_code'] == 201
    assert result['db_state_valid']
```

## 🚫 **What NOT to Mock**

### Mock Only External Dependencies
- ✅ External APIs (HTTP requests)
- ✅ File system operations
- ✅ Email services
- ✅ Third-party libraries
- ✅ Time-dependent operations (use `freezegun`)

### Never Mock Internal Systems
- ❌ Database sessions
- ❌ Database models
- ❌ Internal service calls
- ❌ API endpoints
- ❌ Business logic

## 📊 **Migration Strategy**

### Step 1: Classify Existing Tests
```python
# Add markers to existing tests
@pytest.mark.mock_data  # For tests using mocks
@pytest.mark.real_data  # For tests using real database
```

### Step 2: Create Real Database Alternatives
```python
# Create test_service_name_real_db.py
@pytest.mark.real_data
def test_service_method_real_db(db_manager):
    # Real database implementation
```

### Step 3: Phase Out Critical Mocks
- Replace high-risk database mocking
- Keep mocks only for external dependencies
- Validate with schema checking tools

## 🔍 **Validation Tools**

### Run Classification Validation
```bash
# This will fail tests without proper markers
python -m pytest tests/ -v
```

### Check Mock Usage
```bash
# Analyze remaining mock usage
python scripts/analyze_mock_usage.py
```

### Compare Test Effectiveness
```bash
# Compare mock vs real database test results
python scripts/compare_mock_vs_real_tests.py
```

## 🎯 **Benefits of This System**

### 1. **Transparency**
- Immediately visible which tests use mocks vs real data
- Clear warnings about potential schema issues

### 2. **Quality Assurance**
- Real database tests catch enum vs boolean mismatches
- API integration tests verify end-to-end flow
- Schema validation prevents production issues

### 3. **Migration Tracking**
- Easy to identify tests that need real database alternatives
- Progress tracking as mocks are replaced
- Performance monitoring of real vs mock tests

## 🚀 **Implementation Status**

### ✅ Completed
- Test framework with mandatory classification
- Real database testing utilities
- Schema validation tools
- Mock usage analysis
- Critical mock files replaced

### 📋 Next Steps
1. Update existing test files with proper markers
2. Create real database alternatives for remaining high-risk mocks
3. Monitor test performance and optimize as needed
4. Establish CI/CD integration for schema validation

---

**Remember: Every test must clearly indicate if it uses mock or real data. This prevents hidden database issues and ensures reliable test coverage.**