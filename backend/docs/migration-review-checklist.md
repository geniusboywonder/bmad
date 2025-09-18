# Database Migration Review Checklist

This checklist ensures database migrations are safe, correct, and maintain schema consistency.

## Pre-Migration Development

### ✅ Schema Design Review

- [ ] **Model Definitions Match Intent**
  - Boolean fields use `Column(Boolean)`, not enum types
  - Enum fields use appropriate enum types, not varchar
  - Foreign key relationships are correctly defined
  - Column types match business logic requirements

- [ ] **Type Consistency Check**
  - Run `python scripts/validate_database_schema.py` before creating migration
  - Verify no enum vs boolean mismatches exist
  - Check that all required tables and columns exist

### ✅ Migration File Review

- [ ] **Migration Content Verification**
  - Migration has descriptive, meaningful name
  - Both `upgrade()` and `downgrade()` functions are implemented
  - Raw SQL statements are used for complex type changes
  - Data cleanup is performed before type changes (if needed)

- [ ] **Enum vs Boolean Pattern Check**
  ```python
  # ❌ WRONG - Using enum for boolean concept
  sa.Column('active', sa.Enum('IDLE', 'BUSY', 'ERROR', name='agentstatus'))

  # ✅ CORRECT - Using boolean for boolean concept
  sa.Column('active', sa.Boolean(), default=True)

  # ✅ CORRECT - Using enum for state concept
  sa.Column('status', sa.Enum('PENDING', 'WORKING', 'COMPLETED', name='taskstatus'))
  ```

- [ ] **Data Preservation**
  - Migration preserves existing data where possible
  - Data transformation logic is correct and tested
  - Backup strategy for data-destructive operations

## Migration Testing

### ✅ Local Testing

- [ ] **Clean Database Test**
  ```bash
  # Test full migration from scratch
  dropdb bmad_test
  createdb bmad_test
  alembic upgrade head
  python scripts/validate_database_schema.py --fail-on-errors
  ```

- [ ] **Rollback Testing**
  ```bash
  # Test that downgrade works
  alembic downgrade -1
  alembic upgrade head
  ```

- [ ] **Model Operations Test**
  ```python
  # Test that models work with new schema
  python -c "
  from app.database.models import *
  from app.database.connection import get_session
  # Test model creation/save operations
  "
  ```

### ✅ Integration Testing

- [ ] **Schema Validation Tests Pass**
  ```bash
  python -m pytest tests/integration/test_database_schema_validation.py -v
  ```

- [ ] **All Tests Pass**
  ```bash
  python -m pytest tests/ -v --tb=short
  ```

## Deployment Safety

### ✅ Production Readiness

- [ ] **Migration Safety Assessment**
  - Migration is non-blocking (doesn't lock tables for extended periods)
  - No breaking changes to existing application code
  - Compatible with current application version during deployment

- [ ] **Rollback Plan**
  - Downgrade migration tested and verified
  - Data backup strategy in place
  - Application compatibility during rollback verified

### ✅ Post-Deployment Verification

- [ ] **Schema Validation in CI/CD**
  - GitHub Actions schema validation workflow passes
  - No schema drift detected in production

- [ ] **Application Health Check**
  - All model operations work correctly
  - No enum vs boolean type errors in logs
  - API endpoints function properly

## Common Anti-Patterns to Avoid

### 🚫 Type Mismatches

```python
# ❌ WRONG - Boolean concept using enum
emergency_stop_enabled = sa.Enum('IDLE', 'BUSY', 'ERROR', name='agentstatus')

# ❌ WRONG - Copy-pasting enum definitions without understanding
auto_approved = sa.Enum('IDLE', 'BUSY', 'ERROR', name='agentstatus')  # Should be Boolean!

# ❌ WRONG - Using varchar for enum concepts
status = sa.String(16)  # Should use proper enum type
```

### 🚫 Poor Migration Practices

```python
# ❌ WRONG - No downgrade implementation
def downgrade() -> None:
    pass

# ❌ WRONG - Ignoring data during type changes
op.alter_column('table', 'column', type_=new_type)  # May fail with existing data

# ❌ WRONG - Not testing migration on clean database
```

## Schema Validation Automation

### Continuous Integration

The schema validation workflow automatically:

1. **Validates on every migration change**
   - Triggered by changes to `alembic/versions/**` or model files
   - Runs full migration on clean PostgreSQL database
   - Validates schema consistency with `validate_database_schema.py`

2. **Prevents deployment of broken schemas**
   - Uses `--fail-on-errors` flag to block CI/CD pipeline
   - Runs integration tests to verify model operations
   - Ensures no enum vs boolean mismatches

### Local Development

```bash
# Run before creating migration
python scripts/validate_database_schema.py

# Run after creating migration
alembic upgrade head
python scripts/validate_database_schema.py --fail-on-errors

# Run integration tests
python -m pytest tests/integration/test_database_schema_validation.py -v
```

## Emergency Response

### If Schema Issues Found in Production

1. **Immediate Assessment**
   ```bash
   # Check current schema state
   python scripts/validate_database_schema.py

   # Identify specific issues
   python scripts/validate_database_schema.py --suggest-migrations
   ```

2. **Hotfix Process**
   - Create emergency migration to fix type mismatches
   - Test migration on production-like data
   - Deploy with careful monitoring
   - Verify schema validation passes post-deployment

This checklist should be used for every database migration to prevent the enum vs boolean issues and other schema inconsistencies that can cause production failures.