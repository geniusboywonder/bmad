#!/usr/bin/env python3
"""
Test Script to Validate All Schema Fixes

This script tests that all the enum vs boolean fixes are working correctly
and demonstrates the prevention of the original issues.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import get_session
from app.database.models import (
    ResponseApprovalDB, WebSocketNotificationDB,
    EmergencyStopDB, AgentBudgetControlDB, TaskDB, ProjectDB
)


def test_boolean_fields():
    """Test that boolean fields work correctly with the fixed schema."""
    print("🧪 Testing boolean field operations...")

    session_gen = get_session()
    session = next(session_gen)

    try:
        # Test WebSocketNotificationDB boolean fields
        print("  ✓ Testing WebSocketNotificationDB boolean fields...")
        notification = WebSocketNotificationDB(
            event_type='schema_test',
            title='Test Notification',
            message='Testing boolean fields',
            delivered=True,
            expired=False
        )
        session.add(notification)
        session.commit()

        # Verify round-trip
        retrieved = session.query(WebSocketNotificationDB).filter_by(
            event_type='schema_test'
        ).first()
        assert retrieved.delivered is True
        assert retrieved.expired is False
        assert isinstance(retrieved.delivered, bool)
        assert isinstance(retrieved.expired, bool)
        print("    ✅ WebSocketNotificationDB boolean fields work correctly")

        # Test EmergencyStopDB boolean field
        print("  ✓ Testing EmergencyStopDB boolean field...")
        stop = EmergencyStopDB(
            agent_type='test_agent',
            stop_reason='Schema test',
            triggered_by='TEST',
            active=True
        )
        session.add(stop)
        session.commit()

        retrieved_stop = session.query(EmergencyStopDB).filter_by(
            stop_reason='Schema test'
        ).first()
        assert retrieved_stop.active is True
        assert isinstance(retrieved_stop.active, bool)
        print("    ✅ EmergencyStopDB boolean field works correctly")

        # Test AgentBudgetControlDB boolean field
        print("  ✓ Testing AgentBudgetControlDB boolean field...")
        project = ProjectDB(
            name='Schema Test Project',
            description='Testing schema fixes',
            status='active'
        )
        session.add(project)
        session.commit()

        budget = AgentBudgetControlDB(
            project_id=project.id,
            agent_type='test_agent',
            emergency_stop_enabled=True
        )
        session.add(budget)
        session.commit()

        retrieved_budget = session.query(AgentBudgetControlDB).filter_by(
            project_id=project.id
        ).first()
        assert retrieved_budget.emergency_stop_enabled is True
        assert isinstance(retrieved_budget.emergency_stop_enabled, bool)
        print("    ✅ AgentBudgetControlDB boolean field works correctly")

        session.rollback()  # Clean up
        print("✅ All boolean field tests passed!")

    except Exception as e:
        session.rollback()
        print(f"❌ Boolean field test failed: {e}")
        return False
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

    return True


def test_enum_fields():
    """Test that enum fields work correctly."""
    print("🧪 Testing enum field operations...")

    session_gen = get_session()
    session = next(session_gen)

    try:
        # Test TaskDB enum field (should now be taskstatus enum)
        print("  ✓ Testing TaskDB status enum field...")
        project = ProjectDB(
            name='Enum Test Project',
            description='Testing enum fixes',
            status='active'
        )
        session.add(project)
        session.commit()

        task = TaskDB(
            project_id=project.id,
            agent_type='test_agent',
            status='PENDING',  # Should use taskstatus enum values
            instructions='Test task'
        )
        session.add(task)
        session.commit()

        retrieved_task = session.query(TaskDB).filter_by(
            project_id=project.id
        ).first()
        assert retrieved_task.status == 'PENDING'

        # Test changing enum values
        for status in ['WORKING', 'COMPLETED', 'FAILED']:
            retrieved_task.status = status
            session.commit()
            session.refresh(retrieved_task)
            assert retrieved_task.status == status

        print("    ✅ TaskDB status enum field works correctly")

        session.rollback()  # Clean up
        print("✅ All enum field tests passed!")

    except Exception as e:
        session.rollback()
        print(f"❌ Enum field test failed: {e}")
        return False
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

    return True


def test_schema_validation():
    """Test that schema validation catches issues."""
    print("🧪 Testing schema validation tool...")

    try:
        from scripts.validate_database_schema import DatabaseSchemaValidator

        validator = DatabaseSchemaValidator()
        issues = validator.validate_all()

        if not issues:
            print("✅ Schema validation passed - no issues found!")
            return True
        else:
            print(f"❌ Schema validation found {len(issues)} issues:")
            for issue in issues:
                print(f"  - {issue.table}.{issue.column}: {issue.issue_type}")
            return False

    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")
        return False


def main():
    """Run all schema fix validation tests."""
    print("🔍 Running Schema Fix Validation Tests")
    print("=" * 50)

    results = []

    # Test boolean fields
    results.append(test_boolean_fields())
    print()

    # Test enum fields
    results.append(test_enum_fields())
    print()

    # Test schema validation
    results.append(test_schema_validation())
    print()

    # Summary
    print("=" * 50)
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Schema fixes are working correctly")
        print("✅ No enum vs boolean mismatches detected")
        print("✅ Database schema is consistent with models")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please review the issues above and fix them before proceeding.")
        sys.exit(1)


if __name__ == '__main__':
    main()