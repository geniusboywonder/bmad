"""
Full-Stack Integration Tests: API → Database → Celery Flow

These tests verify that API endpoints properly persist data to the database
and that Celery tasks are created and tracked correctly.
"""

import pytest
import asyncio
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from tests.utils.database_test_utils import (
    DatabaseTestManager, APITestClient, assert_no_mocks_in_call_stack,
    verify_celery_task_in_database, create_full_stack_test_scenario
)

@pytest.fixture
def db_manager():
    """Database manager for full-stack tests."""
    manager = DatabaseTestManager(use_memory_db=False)  # Use real PostgreSQL
    manager.setup_test_database()
    yield manager
    manager.cleanup_test_database()

@pytest.fixture
def api_client(db_manager):
    """API test client with database verification."""
    return APITestClient(app, db_manager)

class TestProjectManagementFlow:
    """Test complete project management API → Database flow."""

    @pytest.mark.real_data

    def test_create_project_persists_to_database(self, api_client, db_manager):
        """Test that creating a project via API persists to database."""
        # Ensure no mocks are interfering
        assert_no_mocks_in_call_stack()

        project_data = {
            'name': 'Full Stack Test Project',
            'description': 'Testing API to DB flow'
        }

        result = api_client.post_and_verify_db(
            '/api/v1/projects/',
            data=project_data,
            db_checks=[
                {
                    'table': 'projects',
                    'conditions': {'name': 'Full Stack Test Project'},
                    'count': 1
                }
            ]
        )

        assert result['status_code'] == 201
        assert result['db_state_valid']
        assert result['json']['name'] == project_data['name']

        # Verify project ID is tracked for cleanup
        project_id = result['json']['id']
        db_manager.track_test_record('projects', project_id)

    @pytest.mark.real_data

    def test_update_project_modifies_database(self, api_client, db_manager):
        """Test that updating a project modifies the database."""
        # Create initial project
        project = db_manager.create_test_project(name='Original Name')

        update_data = {
            'name': 'Updated Name',
            'description': 'Updated description'
        }

        result = api_client.client.put(
            f'/api/v1/projects/{project.id}',
            json=update_data
        )

        # Verify database was updated
        db_state_valid = db_manager.verify_database_state([
            {
                'table': 'projects',
                'conditions': {'name': 'Updated Name', 'id': project.id},
                'count': 1
            }
        ])

        assert result.status_code == 200
        assert db_state_valid

    @pytest.mark.real_data

    def test_get_projects_matches_database_state(self, api_client, db_manager):
        """Test that GET projects returns data consistent with database."""
        # Create test projects
        project1 = db_manager.create_test_project(name='Test Project 1')
        project2 = db_manager.create_test_project(name='Test Project 2')

        result = api_client.get_and_verify_consistency(
            '/api/v1/projects',
            expected_db_state=[
                {
                    'table': 'projects',
                    'count': 2  # At minimum, should include our test projects
                }
            ]
        )

        assert result['status_code'] == 200
        assert result['db_state_valid']

        # Verify API response includes our test projects
        projects = result['json']
        project_names = [p['name'] for p in projects]
        assert 'Test Project 1' in project_names
        assert 'Test Project 2' in project_names

class TestTaskManagementFlow:
    """Test complete task management API → Database → Celery flow."""

    @pytest.mark.real_data
    def test_create_task_persists_to_database(self, api_client, db_manager):
        """Test that creating a task via API persists to database."""
        # Create test scenario
        scenario = create_full_stack_test_scenario(db_manager)
        project_id = scenario['project_id']

        task_data = {
            'agent_type': 'analyst',
            'instructions': 'Full stack test task',
            'context_ids': []
        }

        result = api_client.post_and_verify_db(
            f'/api/v1/projects/{project_id}/tasks',
            data=task_data,
            db_checks=[
                {
                    'table': 'tasks',
                    'conditions': {
                        'project_id': project_id,
                        'agent_type': 'analyst'
                    },
                    'count': 2  # Original + new task
                }
            ]
        )

        assert result['status_code'] == 201
        assert result['db_state_valid']
        assert result['json']['status'] == 'submitted'
        assert 'task_id' in result['json']

        # Track for cleanup
        task_id = result['json']['task_id']
        db_manager.track_test_record('tasks', task_id)

    @pytest.mark.real_data

    def test_task_status_updates_persist_to_database(self, api_client, db_manager):
        """Test that task status updates persist correctly."""
        scenario = create_full_stack_test_scenario(db_manager)
        task = scenario['task']

        # Update task status
        update_data = {'status': 'WORKING'}
        result = api_client.client.patch(
            f'/api/v1/tasks/{task.id}',
            json=update_data
        )

        # Verify database state
        db_state_valid = db_manager.verify_database_state([
            {
                'table': 'tasks',
                'conditions': {'id': task.id, 'status': 'WORKING'},
                'count': 1
            }
        ])

        assert result.status_code == 200
        assert db_state_valid

    @pytest.mark.real_data

    def test_task_deletion_removes_from_database(self, api_client, db_manager):
        """Test that deleting a task removes it from database."""
        scenario = create_full_stack_test_scenario(db_manager)
        task = scenario['task']

        # Delete task
        result = api_client.client.delete(f'/api/v1/tasks/{task.id}')

        # Verify task is removed from database
        db_state_valid = db_manager.verify_database_state([
            {
                'table': 'tasks',
                'conditions': {'id': task.id},
                'count': 0
            }
        ])

        assert result.status_code == 204
        assert db_state_valid

class TestHITLSafetyFlow:
    """Test HITL safety system API → Database flow."""

    @pytest.mark.real_data
    def test_create_hitl_request_persists_to_database(self, api_client, db_manager):
        """Test that HITL requests are properly persisted."""
        scenario = create_full_stack_test_scenario(db_manager)

        hitl_data = {
            'project_id': str(scenario['project_id']),
            'task_id': str(scenario['task_id']),
            'agent_type': 'analyst',
            'instructions': 'Test agent execution',
            'estimated_tokens': 100
        }

        result = api_client.client.post(
            '/api/v1/hitl-safety/request-agent-execution',
            json=hitl_data
        )

        assert result.status_code == 200
        response_json = result.json()
        assert 'approval_id' in response_json

        approval_id = response_json['approval_id']

        db_state_valid = db_manager.verify_database_state([
            {
                'table': 'hitl_agent_approvals',
                'conditions': {
                    'id': approval_id,
                    'project_id': str(scenario['project_id']),
                    'agent_type': 'analyst'
                },
                'count': 1
            }
        ])
        assert db_state_valid

        # Track for cleanup
        db_manager.track_test_record('hitl_agent_approvals', approval_id)

    @pytest.mark.real_data

    def test_emergency_stop_creates_database_record(self, api_client, db_manager):
        """Test that emergency stops are properly persisted."""
        scenario = create_full_stack_test_scenario(db_manager)

        stop_data = {
            'project_id': scenario['project_id'],
            'agent_type': 'analyst',
            'stop_reason': 'Full stack test emergency stop'
        }

        result = api_client.post_and_verify_db(
            '/api/v1/hitl-safety/emergency-stop',
            data=stop_data,
            db_checks=[
                {
                    'table': 'emergency_stops',
                    'conditions': {
                        'project_id': scenario['project']['id'],
                        'agent_type': 'analyst',
                        'active': True
                    },
                    'count': 1
                }
            ]
        )

        assert result['status_code'] == 201
        assert result['db_state_valid']

        # Track for cleanup
        stop_id = result['json']['id']
        db_manager.track_test_record('emergency_stops', stop_id)

    @pytest.mark.mock_data

    def test_budget_controls_persist_correctly(self, api_client, db_manager):
        """Test that budget control updates persist to database."""
        scenario = create_full_stack_test_scenario(db_manager)

        budget_data = {
            'project_id': scenario['project_id'],
            'agent_type': 'analyst',
            'daily_token_limit': 2000,
            'session_token_limit': 1000,
            'emergency_stop_enabled': True
        }

        result = api_client.post_and_verify_db(
            '/api/v1/hitl-safety/budget-controls',
            data=budget_data,
            db_checks=[
                {
                    'table': 'agent_budget_controls',
                    'conditions': {
                        'project_id': scenario['project']['id'],
                        'daily_token_limit': 2000,
                        'emergency_stop_enabled': True
                    },
                    'count': 1
                }
            ]
        )

        assert result['status_code'] == 201
        assert result['db_state_valid']

class TestWorkflowExecutionFlow:
    """Test workflow execution API → Database → Celery flow."""

    @pytest.mark.real_data

    def test_workflow_execution_creates_database_records(self, api_client, db_manager):
        """Test that workflow execution creates proper database records."""
        scenario = create_full_stack_test_scenario(db_manager)

        workflow_data = {
            'workflow_id': 'test_workflow',
            'project_id': scenario['project_id'],
            'context_data': {'test': 'data'}
        }

        result = api_client.post_and_verify_db(
            '/api/v1/workflows/execute',
            data=workflow_data,
            db_checks=[
                {
                    'table': 'workflow_states',
                    'conditions': {
                        'project_id': scenario['project']['id'],
                        'workflow_id': 'test_workflow'
                    },
                    'count': 1
                }
            ]
        )

        # Note: This might return different status codes depending on implementation
        assert result['status_code'] in [201, 202]  # Created or Accepted
        assert result['db_state_valid']

        # Verify execution ID is returned
        if result['json']:
            execution_id = result['json'].get('execution_id')
            if execution_id:
                db_manager.track_test_record('workflow_states', execution_id)

class TestDataConsistencyAndIntegrity:
    """Test data consistency across the full stack."""

    @pytest.mark.mock_data

    def test_no_orphaned_records_after_project_deletion(self, api_client, db_manager):
        """Test that deleting a project properly cleans up related records."""
        scenario = create_full_stack_test_scenario(db_manager)
        project_id = scenario['project']['id']

        # Create additional related records
        with db_manager.get_session() as session:
            # Add context artifact
            artifact = ContextArtifactDB(
                project_id=project_id,
                artifact_type='USER_INPUT',
                name='Test Artifact',
                content={'test': 'data'}
            )
            session.add(artifact)
            session.commit()

        # Delete project
        result = api_client.client.delete(f'/api/v1/projects/{project_id}')
        assert result.status_code == 204

        # Verify related records are cleaned up
        db_state_valid = db_manager.verify_database_state([
            {
                'table': 'projects',
                'conditions': {'id': project_id},
                'count': 0
            },
            {
                'table': 'tasks',
                'conditions': {'project_id': project_id},
                'count': 0
            },
            {
                'table': 'context_artifacts',
                'conditions': {'project_id': project_id},
                'count': 0
            }
        ])

        assert db_state_valid

    @pytest.mark.mock_data

    def test_enum_fields_work_correctly_end_to_end(self, api_client, db_manager):
        """Test that enum fields work correctly through the full API → DB flow."""
        scenario = create_full_stack_test_scenario(db_manager)

        # Test all valid task status enum values
        task_id = scenario['task']['id']
        valid_statuses = ['PENDING', 'WORKING', 'COMPLETED', 'FAILED', 'CANCELLED']

        for status in valid_statuses:
            result = api_client.client.patch(
                f'/api/v1/tasks/{task_id}',
                json={'status': status}
            )

            assert result.status_code == 200

            # Verify database state
            db_state_valid = db_manager.verify_database_state([
                {
                    'table': 'tasks',
                    'conditions': {'id': task_id, 'status': status},
                    'count': 1
                }
            ])
            assert db_state_valid

    @pytest.mark.mock_data

    def test_boolean_fields_work_correctly_end_to_end(self, api_client, db_manager):
        """Test that boolean fields work correctly through the full API → DB flow."""
        scenario = create_full_stack_test_scenario(db_manager)

        # Test emergency stop boolean field
        stop_data = {
            'project_id': scenario['project_id'],
            'agent_type': 'analyst',
            'stop_reason': 'Boolean field test'
        }

        # Create emergency stop
        result = api_client.post_and_verify_db(
            '/api/v1/hitl-safety/emergency-stop',
            data=stop_data,
            db_checks=[
                {
                    'table': 'emergency_stops',
                    'conditions': {'active': True},  # Boolean field
                    'count': 1
                }
            ]
        )

        assert result['status_code'] == 201
        assert result['db_state_valid']

        stop_id = result['json']['id']
        db_manager.track_test_record('emergency_stops', stop_id)

        # Deactivate emergency stop
        deactivate_result = api_client.client.delete(
            f'/api/v1/hitl-safety/emergency-stop/{stop_id}'
        )

        assert deactivate_result.status_code == 200

        # Verify boolean field updated
        db_state_valid = db_manager.verify_database_state([
            {
                'table': 'emergency_stops',
                'conditions': {'id': stop_id, 'active': False},  # Boolean field
                'count': 1
            }
        ])
        assert db_state_valid

class TestCeleryIntegration:
    """Test Celery task integration with database persistence."""

    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_celery_tasks_are_tracked_in_database(self, api_client, db_manager):
        """Test that Celery tasks are properly tracked in the database."""
        scenario = create_full_stack_test_scenario(db_manager)

        # Create a task that should trigger Celery
        task_data = {
            'project_id': scenario['project_id'],
            'agent_type': 'analyst',
            'instructions': 'Task that should create Celery job',
            'context_ids': []
        }

        result = api_client.post_and_verify_db(
            '/api/v1/tasks',
            data=task_data,
            db_checks=[
                {
                    'table': 'tasks',
                    'conditions': {'project_id': scenario['project']['id']},
                    'count': 2  # Original + new task
                }
            ]
        )

        assert result['status_code'] == 201
        assert result['db_state_valid']

        task_id = result['json']['id']
        db_manager.track_test_record('tasks', task_id)

        # Verify the task exists in database (not just Celery queue)
        celery_task_in_db = verify_celery_task_in_database(task_id, db_manager)
        assert celery_task_in_db, "Celery task should be persisted to database"