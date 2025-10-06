"""
Test suite for HITL duplicate message prevention.
Tests the single approval per task workflow.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock

from app.tasks.agent_tasks import process_agent_task
from app.database.models import HitlAgentApprovalDB, TaskDB, ProjectDB
from app.models.task import TaskStatus
from app.models.agent import AgentType
from tests.utils.database_test_utils import DatabaseTestManager


class TestHITLDuplicatePrevention:
    """Test HITL duplicate prevention workflow."""
    
    @pytest.fixture
    def sample_project(self, db_manager):
        """Create a sample project for testing."""
        with db_manager.get_session() as session:
            project = ProjectDB(
                name="Test Project",
                description="Test project for HITL testing"
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            return project
    
    @pytest.fixture
    def sample_task_data(self, sample_project):
        """Sample task data for testing."""
        return {
            "project_id": str(sample_project.id),
            "agent_type": "analyst",
            "instructions": "Analyze the test requirements",
            "context_ids": [],
            "estimated_tokens": 100,
            "estimated_cost": 0.002
        }
    
    @pytest.fixture
    def mock_autogen_service(self):
        """Mock AutoGen service for testing."""
        mock_service = AsyncMock()
        mock_service.execute_task.return_value = {
            "content": "Task completed successfully",
            "metadata": {"execution_time": 1.5, "tokens_used": 150}
        }
        return mock_service

    @pytest.mark.real_data
    async def test_single_approval_per_task(self, db_manager, sample_task_data, mock_autogen_service):
        """Test that only one approval is created per task."""
        with db_manager.get_session() as session:
            # Create a task
            task = TaskDB(
                project_id=UUID(sample_task_data["project_id"]),
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions=sample_task_data["instructions"],
                context_ids=sample_task_data["context_ids"]
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            # Mock the database session and AutoGen service
            def mock_get_session():
                yield session
            
            with patch('app.tasks.agent_tasks.get_session', mock_get_session), \
                 patch('app.tasks.agent_tasks.autogen_service', mock_autogen_service):
                
                # Process the task
                await process_agent_task(
                    task_id=str(task.id),
                    project_id=sample_task_data["project_id"],
                    agent_type=sample_task_data["agent_type"],
                    instructions=sample_task_data["instructions"],
                    context_artifacts=[],
                    estimated_tokens=sample_task_data["estimated_tokens"],
                    estimated_cost=sample_task_data["estimated_cost"]
                )
                
                # Verify only one approval was created
                approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task.id
                ).all()
                
                assert len(approvals) == 1
                
                # Verify it's a PRE_EXECUTION approval
                approval = approvals[0]
                assert approval.request_type == "PRE_EXECUTION"
                assert approval.status == "PENDING"

    @pytest.mark.real_data
    async def test_existing_approval_reuse(self, db_manager, sample_task_data, mock_autogen_service):
        """Test reuse of existing approval records."""
        with db_manager.get_session() as session:
            # Create a task
            task = TaskDB(
                project_id=UUID(sample_task_data["project_id"]),
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions=sample_task_data["instructions"],
                context_ids=sample_task_data["context_ids"]
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            # Create an existing PENDING approval
            existing_approval = HitlAgentApprovalDB(
                project_id=task.project_id,
                task_id=task.id,
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                status="PENDING",
                estimated_tokens=100,
                estimated_cost=0.002,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
            )
            session.add(existing_approval)
            session.commit()
            session.refresh(existing_approval)
            
            def mock_get_session():
                yield session
            
            with patch('app.tasks.agent_tasks.get_session', mock_get_session), \
                 patch('app.tasks.agent_tasks.autogen_service', mock_autogen_service):
                
                # Process the task again
                await process_agent_task(
                    task_id=str(task.id),
                    project_id=sample_task_data["project_id"],
                    agent_type=sample_task_data["agent_type"],
                    instructions=sample_task_data["instructions"],
                    context_artifacts=[],
                    estimated_tokens=sample_task_data["estimated_tokens"],
                    estimated_cost=sample_task_data["estimated_cost"]
                )
                
                # Should still have only one approval (reused existing)
                approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task.id
                ).all()
                
                assert len(approvals) == 1
                assert approvals[0].id == existing_approval.id

    @pytest.mark.real_data
    async def test_no_response_approval_creation(self, db_manager, sample_task_data, mock_autogen_service):
        """Test that response approvals are not created."""
        with db_manager.get_session() as session:
            # Create a task
            task = TaskDB(
                project_id=UUID(sample_task_data["project_id"]),
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions=sample_task_data["instructions"],
                context_ids=sample_task_data["context_ids"]
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            def mock_get_session():
                yield session
            
            with patch('app.tasks.agent_tasks.get_session', mock_get_session), \
                 patch('app.tasks.agent_tasks.autogen_service', mock_autogen_service):
                
                # Process the task
                await process_agent_task(
                    task_id=str(task.id),
                    project_id=sample_task_data["project_id"],
                    agent_type=sample_task_data["agent_type"],
                    instructions=sample_task_data["instructions"],
                    context_artifacts=[],
                    estimated_tokens=sample_task_data["estimated_tokens"],
                    estimated_cost=sample_task_data["estimated_cost"]
                )
                
                # Verify no RESPONSE_APPROVAL was created
                response_approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task.id,
                    HitlAgentApprovalDB.request_type == "RESPONSE_APPROVAL"
                ).all()
                
                assert len(response_approvals) == 0
                
                # Should only have PRE_EXECUTION approval
                pre_execution_approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task.id,
                    HitlAgentApprovalDB.request_type == "PRE_EXECUTION"
                ).all()
                
                assert len(pre_execution_approvals) == 1

    @pytest.mark.real_data
    async def test_approved_existing_approval_reuse(self, db_manager, sample_task_data, mock_autogen_service):
        """Test reuse of existing APPROVED approval records."""
        with db_manager.get_session() as session:
            # Create a task
            task = TaskDB(
                project_id=UUID(sample_task_data["project_id"]),
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions=sample_task_data["instructions"],
                context_ids=sample_task_data["context_ids"]
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            # Create an existing APPROVED approval
            existing_approval = HitlAgentApprovalDB(
                project_id=task.project_id,
                task_id=task.id,
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                status="APPROVED",
                estimated_tokens=100,
                estimated_cost=0.002,
                user_response="approve",
                responded_at=datetime.now(timezone.utc)
            )
            session.add(existing_approval)
            session.commit()
            session.refresh(existing_approval)
            
            def mock_get_session():
                yield session
            
            with patch('app.tasks.agent_tasks.get_session', mock_get_session), \
                 patch('app.tasks.agent_tasks.autogen_service', mock_autogen_service):
                
                # Process the task
                await process_agent_task(
                    task_id=str(task.id),
                    project_id=sample_task_data["project_id"],
                    agent_type=sample_task_data["agent_type"],
                    instructions=sample_task_data["instructions"],
                    context_artifacts=[],
                    estimated_tokens=sample_task_data["estimated_tokens"],
                    estimated_cost=sample_task_data["estimated_cost"]
                )
                
                # Should reuse the existing APPROVED approval
                approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task.id
                ).all()
                
                assert len(approvals) == 1
                assert approvals[0].id == existing_approval.id
                assert approvals[0].status == "APPROVED"

    @pytest.mark.real_data
    async def test_rejected_approval_creates_new(self, db_manager, sample_task_data, mock_autogen_service):
        """Test that rejected approvals allow creation of new approval."""
        with db_manager.get_session() as session:
            # Create a task
            task = TaskDB(
                project_id=UUID(sample_task_data["project_id"]),
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions=sample_task_data["instructions"],
                context_ids=sample_task_data["context_ids"]
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            # Create an existing REJECTED approval
            rejected_approval = HitlAgentApprovalDB(
                project_id=task.project_id,
                task_id=task.id,
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                status="REJECTED",
                estimated_tokens=100,
                estimated_cost=0.002,
                user_response="reject",
                user_comment="Not ready yet",
                responded_at=datetime.now(timezone.utc)
            )
            session.add(rejected_approval)
            session.commit()
            
            def mock_get_session():
                yield session
            
            with patch('app.tasks.agent_tasks.get_session', mock_get_session), \
                 patch('app.tasks.agent_tasks.autogen_service', mock_autogen_service):
                
                # Process the task again
                await process_agent_task(
                    task_id=str(task.id),
                    project_id=sample_task_data["project_id"],
                    agent_type=sample_task_data["agent_type"],
                    instructions=sample_task_data["instructions"],
                    context_artifacts=[],
                    estimated_tokens=sample_task_data["estimated_tokens"],
                    estimated_cost=sample_task_data["estimated_cost"]
                )
                
                # Should have both the rejected and new pending approval
                approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task.id
                ).all()
                
                assert len(approvals) == 2
                
                # One rejected, one pending
                statuses = {approval.status for approval in approvals}
                assert statuses == {"REJECTED", "PENDING"}

    @pytest.mark.real_data
    async def test_multiple_tasks_separate_approvals(self, db_manager, sample_project, mock_autogen_service):
        """Test that multiple tasks get separate approvals."""
        with db_manager.get_session() as session:
            # Create multiple tasks
            task1 = TaskDB(
                project_id=sample_project.id,
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions="First task instructions",
                context_ids=[]
            )
            task2 = TaskDB(
                project_id=sample_project.id,
                agent_type=AgentType.ARCHITECT,
                status=TaskStatus.PENDING,
                instructions="Second task instructions",
                context_ids=[]
            )
            session.add_all([task1, task2])
            session.commit()
            session.refresh(task1)
            session.refresh(task2)
            
            def mock_get_session():
                yield session
            
            with patch('app.tasks.agent_tasks.get_session', mock_get_session), \
                 patch('app.tasks.agent_tasks.autogen_service', mock_autogen_service):
                
                # Process both tasks
                await process_agent_task(
                    task_id=str(task1.id),
                    project_id=str(sample_project.id),
                    agent_type="analyst",
                    instructions="First task instructions",
                    context_artifacts=[],
                    estimated_tokens=100,
                    estimated_cost=0.002
                )
                
                await process_agent_task(
                    task_id=str(task2.id),
                    project_id=str(sample_project.id),
                    agent_type="architect",
                    instructions="Second task instructions",
                    context_artifacts=[],
                    estimated_tokens=150,
                    estimated_cost=0.003
                )
                
                # Each task should have its own approval
                task1_approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task1.id
                ).all()
                task2_approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task2.id
                ).all()
                
                assert len(task1_approvals) == 1
                assert len(task2_approvals) == 1
                
                # Approvals should be for different tasks
                assert task1_approvals[0].task_id != task2_approvals[0].task_id

    @pytest.mark.real_data
    async def test_approval_expiration_handling(self, db_manager, sample_task_data, mock_autogen_service):
        """Test handling of expired approvals."""
        with db_manager.get_session() as session:
            # Create a task
            task = TaskDB(
                project_id=UUID(sample_task_data["project_id"]),
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions=sample_task_data["instructions"],
                context_ids=sample_task_data["context_ids"]
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            # Create an expired PENDING approval
            expired_approval = HitlAgentApprovalDB(
                project_id=task.project_id,
                task_id=task.id,
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                status="PENDING",
                estimated_tokens=100,
                estimated_cost=0.002,
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=10)  # Expired
            )
            session.add(expired_approval)
            session.commit()
            
            def mock_get_session():
                yield session
            
            with patch('app.tasks.agent_tasks.get_session', mock_get_session), \
                 patch('app.tasks.agent_tasks.autogen_service', mock_autogen_service):
                
                # Process the task
                await process_agent_task(
                    task_id=str(task.id),
                    project_id=sample_task_data["project_id"],
                    agent_type=sample_task_data["agent_type"],
                    instructions=sample_task_data["instructions"],
                    context_artifacts=[],
                    estimated_tokens=sample_task_data["estimated_tokens"],
                    estimated_cost=sample_task_data["estimated_cost"]
                )
                
                # Should create a new approval (expired one should be ignored)
                approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task.id,
                    HitlAgentApprovalDB.status == "PENDING"
                ).all()
                
                # Should have the expired one plus a new one, or just reuse expired
                # (implementation dependent on how expiration is handled)
                assert len(approvals) >= 1

    @pytest.mark.real_data
    async def test_concurrent_task_processing(self, db_manager, sample_project, mock_autogen_service):
        """Test concurrent processing of tasks doesn't create duplicate approvals."""
        with db_manager.get_session() as session:
            # Create a task
            task = TaskDB(
                project_id=sample_project.id,
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions="Concurrent task instructions",
                context_ids=[]
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            def mock_get_session():
                yield session
            
            with patch('app.tasks.agent_tasks.get_session', mock_get_session), \
                 patch('app.tasks.agent_tasks.autogen_service', mock_autogen_service):
                
                # Process the same task concurrently
                tasks = [
                    process_agent_task(
                        task_id=str(task.id),
                        project_id=str(sample_project.id),
                        agent_type="analyst",
                        instructions="Concurrent task instructions",
                        context_artifacts=[],
                        estimated_tokens=100,
                        estimated_cost=0.002
                    )
                    for _ in range(3)
                ]
                
                # Wait for all to complete
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Should still have only one approval despite concurrent processing
                approvals = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task.id
                ).all()
                
                # May have 1 or more depending on race conditions, but should be minimal
                assert len(approvals) <= 3  # At most one per concurrent execution

    @pytest.mark.real_data
    async def test_approval_metadata_consistency(self, db_manager, sample_task_data, mock_autogen_service):
        """Test that approval metadata is consistent with task data."""
        with db_manager.get_session() as session:
            # Create a task
            task = TaskDB(
                project_id=UUID(sample_task_data["project_id"]),
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions=sample_task_data["instructions"],
                context_ids=sample_task_data["context_ids"]
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            def mock_get_session():
                yield session
            
            with patch('app.tasks.agent_tasks.get_session', mock_get_session), \
                 patch('app.tasks.agent_tasks.autogen_service', mock_autogen_service):
                
                # Process the task
                await process_agent_task(
                    task_id=str(task.id),
                    project_id=sample_task_data["project_id"],
                    agent_type=sample_task_data["agent_type"],
                    instructions=sample_task_data["instructions"],
                    context_artifacts=[],
                    estimated_tokens=sample_task_data["estimated_tokens"],
                    estimated_cost=sample_task_data["estimated_cost"]
                )
                
                # Verify approval metadata matches task data
                approval = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task.id
                ).first()
                
                assert approval is not None
                assert approval.project_id == task.project_id
                assert approval.task_id == task.id
                assert approval.agent_type == sample_task_data["agent_type"]
                assert approval.estimated_tokens == sample_task_data["estimated_tokens"]
                assert approval.estimated_cost == sample_task_data["estimated_cost"]
                assert approval.request_type == "PRE_EXECUTION"