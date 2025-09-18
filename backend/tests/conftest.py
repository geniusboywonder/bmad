import os # New
from dotenv import load_dotenv # New

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env')) # New

"""
Test configuration and fixtures for BotArmy backend testing.

This module provides comprehensive test setup including:
- Database test isolation with transaction rollbacks
- Mock service configurations  
- Test data factories
- FastAPI test client setup
- WebSocket test client setup
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import redis
from uuid import uuid4, UUID

from app.main import app
from app.database.connection import Base, get_session
from app.database.models import ProjectDB, TaskDB, ContextArtifactDB, HitlRequestDB, AgentStatusDB
from app.models.task import TaskStatus
from app.models.agent import AgentType, AgentStatus
from app.models.context import ArtifactType
from app.models.hitl import HitlStatus
from app.services.orchestrator import OrchestratorService
from app.services.context_store import ContextStoreService
from app.services.autogen_service import AutoGenService


# Test Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test with transaction rollback.
    
    This ensures test isolation by rolling back all changes after each test.
    """
    # Create all tables for each test
    Base.metadata.create_all(bind=engine)
    
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    
    # Drop all tables to ensure clean state
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """
    Create FastAPI test client with database session override.
    """
    def get_test_db():
        return db_session
    
    app.dependency_overrides[get_session] = get_test_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def orchestrator_service(db_session: Session) -> OrchestratorService:
    """Create OrchestratorService instance with test database."""
    return OrchestratorService(db_session)


@pytest.fixture
def context_store_service(db_session: Session) -> ContextStoreService:
    """Create ContextStoreService instance with test database."""
    return ContextStoreService(db_session)


@pytest.fixture
def mock_autogen_service():
    """Mock AutoGenService for testing agent execution."""
    mock_service = Mock(spec=AutoGenService)
    
    # Mock agent creation
    mock_agent = Mock()
    mock_agent.name = "test_agent"
    mock_agent.system_message = "Test system message"
    mock_service.create_agent.return_value = mock_agent
    
    # Mock task execution
    mock_result = {
        "content": "Task completed successfully",
        "metadata": {"execution_time": 1.5, "tokens_used": 150}
    }
    mock_service.execute_task = AsyncMock(return_value=mock_result)
    
    # Mock context preparation
    mock_service.prepare_context_message.return_value = "Test context message"
    
    return mock_service


# Mock Services and External Dependencies

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing cache operations."""
    mock_redis = Mock(spec=redis.Redis)
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = False
    return mock_redis


@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing async task submission."""
    mock_task = Mock()
    mock_task.id = str(uuid4())
    mock_task.status = "PENDING"
    mock_task.delay.return_value = mock_task
    return mock_task


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager for testing real-time events."""
    mock_manager = AsyncMock()
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()
    mock_manager.broadcast = AsyncMock()
    mock_manager.send_personal_message = AsyncMock()
    return mock_manager


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for AutoGen testing."""
    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.completions = Mock()
    
    # Mock response structure
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Mock LLM response"
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 100
    
    mock_client.chat.completions.create.return_value = mock_response
    
    return mock_client


# Mock Services and External Dependencies

@pytest.fixture
def mock_handoff_validator():
    """Mock handoff validator for testing schema validation."""
    mock_validator = Mock()
    mock_validator.validate_handoff.return_value = True
    mock_validator.get_next_agent.return_value = AgentType.ARCHITECT
    mock_validator.extract_context_requirements.return_value = ["project_plan"]
    return mock_validator


# Test Data Factories

@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for validation"
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "agent_type": AgentType.ANALYST,
        "instructions": "Analyze the test requirements",
        "context_ids": []
    }


@pytest.fixture
def sample_context_artifact_data():
    """Sample context artifact data for testing."""
    return {
        "source_agent": AgentType.ANALYST,
        "artifact_type": ArtifactType.PROJECT_PLAN,
        "content": {
            "plan_version": "1.0",
            "objectives": ["Complete analysis", "Generate report"],
            "timeline": "2 weeks"
        },
        "artifact_metadata": {
            "created_by": "test_agent",
            "confidence_score": 0.95
        }
    }


@pytest.fixture
def sample_hitl_request_data():
    """Sample HITL request data for testing."""
    return {
        "question": "Please approve the generated project plan",
        "options": ["approve", "reject", "amend"],
        "status": HitlStatus.PENDING
    }


@pytest.fixture
def sample_handoff_schema_data():
    """Sample HandoffSchema data for testing according to new schema format."""
    return {
        "from_agent": AgentType.ANALYST,
        "to_agent": AgentType.ARCHITECT,
        "phase": "architecture",
        "instructions": "Create technical architecture based on analysis",
        "context_summary": "Analysis phase completed with requirements gathered and documented",
        "expected_outputs": ["System architecture document", "Component specifications", "Data flow diagrams"],
        "priority": "high",
        "metadata": {"urgency": "standard", "complexity": "medium"},
        "dependencies": ["requirements_analysis"],
        "acceptance_criteria": ["Architecture covers all requirements", "Scalability considerations addressed"]
    }


@pytest.fixture
def sample_autogen_task_data():
    """Sample AutoGen task data for testing."""
    return {
        "agent_type": AgentType.CODER,
        "instructions": "Implement the user authentication module",
        "context": ["Requirements document", "Architecture specification"],
        "expected_output": "Python code with authentication logic"
    }


# Database Entity Factories

class ProjectFactory:
    """Factory for creating test Project entities."""
    
    @staticmethod
    def create(db: Session, **kwargs) -> ProjectDB:
        """Create a project with default or overridden values."""
        defaults = {
            "name": f"Test Project {uuid4().hex[:8]}",
            "description": "Test project description",
            "status": "active"
        }
        defaults.update(kwargs)
        
        project = ProjectDB(**defaults)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project


class TaskFactory:
    """Factory for creating test Task entities."""

    @staticmethod
    def create(db: Session, project_id: UUID, **kwargs) -> TaskDB:
        """Create a task with default or overridden values."""
        defaults = {
            "project_id": project_id,
            "agent_type": AgentType.ANALYST,
            "status": TaskStatus.PENDING,
            "instructions": "Test task instructions",
            "context_ids": []
        }
        defaults.update(kwargs)

        task = TaskDB(**defaults)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task


class ContextArtifactFactory:
    """Factory for creating test ContextArtifact entities."""

    @staticmethod
    def create(db: Session, project_id: UUID, **kwargs) -> ContextArtifactDB:
        """Create a context artifact with default or overridden values."""
        defaults = {
            "project_id": project_id,
            "source_agent": AgentType.ANALYST,
            "artifact_type": ArtifactType.PROJECT_PLAN,
            "content": {"test": "content"},
            "artifact_metadata": {"test": "metadata"}
        }
        defaults.update(kwargs)

        artifact = ContextArtifactDB(**defaults)
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact


class HitlRequestFactory:
    """Factory for creating test HITL request entities."""
    
    @staticmethod
    def create(db: Session, project_id: UUID, task_id: UUID, **kwargs) -> HitlRequestDB:
        """Create a HITL request with default or overridden values."""
        defaults = {
            "project_id": project_id,
            "task_id": task_id,
            "question": "Test HITL question",
            "options": ["approve", "reject"],
            "status": HitlStatus.PENDING
        }
        defaults.update(kwargs)
        
        hitl_request = HitlRequestDB(**defaults)
        db.add(hitl_request)
        db.commit()
        db.refresh(hitl_request)
        return hitl_request


class AgentStatusFactory:
    """Factory for creating test AgentStatus entities."""
    
    @staticmethod
    def create(db: Session, **kwargs) -> AgentStatusDB:
        """Create an agent status with default or overridden values."""
        defaults = {
            "agent_type": AgentType.ANALYST,
            "status": AgentStatus.IDLE
        }
        defaults.update(kwargs)
        
        agent_status = AgentStatusDB(**defaults)
        db.add(agent_status)
        db.commit()
        db.refresh(agent_status)
        return agent_status


# Test Factories as Fixtures

@pytest.fixture
def project_factory():
    """Provide ProjectFactory for tests."""
    return ProjectFactory


@pytest.fixture
def task_factory():
    """Provide TaskFactory for tests."""
    return TaskFactory


@pytest.fixture
def context_artifact_factory():
    """Provide ContextArtifactFactory for tests."""
    return ContextArtifactFactory


@pytest.fixture
def hitl_request_factory():
    """Provide HitlRequestFactory for tests."""
    return HitlRequestFactory


@pytest.fixture
def agent_status_factory():
    """Provide AgentStatusFactory for tests."""
    return AgentStatusFactory


# Sprint 2 Specific Fixtures

@pytest.fixture
def mock_sdlc_process_flow():
    """Mock SDLC process flow configuration for testing."""
    return {
        "phases": [
            {
                "name": "analysis",
                "agent_type": AgentType.ANALYST,
                "inputs": ["user_requirements"],
                "outputs": ["project_plan"]
            },
            {
                "name": "architecture",
                "agent_type": AgentType.ARCHITECT,
                "inputs": ["project_plan"],
                "outputs": ["system_architecture"]
            },
            {
                "name": "implementation",
                "agent_type": AgentType.CODER,
                "inputs": ["system_architecture"],
                "outputs": ["source_code"]
            },
            {
                "name": "testing",
                "agent_type": AgentType.TESTER,
                "inputs": ["source_code"],
                "outputs": ["test_results"]
            },
            {
                "name": "deployment",
                "agent_type": AgentType.DEPLOYER,
                "inputs": ["source_code", "test_results"],
                "outputs": ["deployment_package"]
            }
        ]
    }


# Convenience Fixtures for Common Scenarios

@pytest.fixture
def project_with_task(db_session: Session, project_factory, task_factory):
    """Create a project with an associated task."""
    project = project_factory.create(db_session)
    task = task_factory.create(db_session, project_id=project.id)
    return {"project": project, "task": task}


@pytest.fixture
def project_with_context(db_session: Session, project_factory, context_artifact_factory):
    """Create a project with context artifacts."""
    project = project_factory.create(db_session)
    artifact1 = context_artifact_factory.create(
        db_session, 
        project_id=project.id,
        artifact_type=ArtifactType.PROJECT_PLAN
    )
    artifact2 = context_artifact_factory.create(
        db_session,
        project_id=project.id,
        artifact_type=ArtifactType.SOFTWARE_SPECIFICATION
    )
    return {"project": project, "artifacts": [artifact1, artifact2]}


@pytest.fixture
def project_with_hitl(db_session: Session, project_factory, task_factory, hitl_request_factory):
    """Create a project with task and HITL request."""
    project = project_factory.create(db_session)
    task = task_factory.create(db_session, project_id=project.id)
    hitl_request = hitl_request_factory.create(
        db_session, 
        project_id=project.id, 
        task_id=task.id
    )
    return {"project": project, "task": task, "hitl_request": hitl_request}


@pytest.fixture
def project_with_workflow(db_session: Session, project_factory, task_factory, context_artifact_factory):
    """Create a project with multi-phase workflow setup."""
    project = project_factory.create(db_session)

    # Analysis phase task
    analysis_task = task_factory.create(
        db_session,
        project_id=project.id,
        agent_type=AgentType.ANALYST,
        status=TaskStatus.COMPLETED,
        output={"analysis": "Requirements analyzed"}
    )

    # Analysis output artifact
    analysis_artifact = context_artifact_factory.create(
        db_session,
        project_id=project.id,
        source_agent=AgentType.ANALYST,
        artifact_type=ArtifactType.PROJECT_PLAN
    )

    # Architecture phase task
    architecture_task = task_factory.create(
        db_session,
        project_id=project.id,
        agent_type=AgentType.ARCHITECT,
        status=TaskStatus.PENDING,
        context_ids=[analysis_artifact.id]
    )

    return {
        "project": project,
        "analysis_task": analysis_task,
        "architecture_task": architecture_task,
        "analysis_artifact": analysis_artifact
    }


# Test Utility Functions

def assert_project_matches_data(project: ProjectDB, expected_data: dict):
    """Assert that project entity matches expected data."""
    assert project.name == expected_data["name"]
    if "description" in expected_data:
        assert project.description == expected_data["description"]
    assert project.status == expected_data.get("status", "active")
    assert project.id is not None
    assert project.created_at is not None


def assert_task_matches_data(task: TaskDB, expected_data: dict):
    """Assert that task entity matches expected data."""
    assert task.agent_type == expected_data["agent_type"]
    assert task.instructions == expected_data["instructions"]
    assert task.context_ids == expected_data.get("context_ids", [])
    assert task.status == expected_data.get("status", TaskStatus.PENDING)
    assert task.id is not None
    assert task.created_at is not None


def assert_context_artifact_matches_data(artifact: ContextArtifactDB, expected_data: dict):
    """Assert that context artifact entity matches expected data."""
    assert artifact.source_agent == expected_data["source_agent"]
    assert artifact.artifact_type == expected_data["artifact_type"]
    assert artifact.content == expected_data["content"]
    if "artifact_metadata" in expected_data:
        assert artifact.artifact_metadata == expected_data["artifact_metadata"]
    assert artifact.id is not None
    assert artifact.created_at is not None


def assert_hitl_request_matches_data(hitl_request: HitlRequestDB, expected_data: dict):
    """Assert that HITL request entity matches expected data."""
    assert hitl_request.question == expected_data["question"]
    assert hitl_request.options == expected_data.get("options", [])
    assert hitl_request.status == expected_data.get("status", HitlStatus.PENDING)
    assert hitl_request.id is not None
    assert hitl_request.created_at is not None


def assert_handoff_schema_valid(handoff_data: dict):
    """Assert that handoff schema contains required fields according to new HandoffSchema model."""
    # Import the schema here to avoid circular imports
    from app.schemas.handoff import HandoffSchema, HandoffPhase, HandoffPriority
    
    # Required fields according to the new schema
    required_fields = ["from_agent", "to_agent", "phase", "instructions", "context_summary", "expected_outputs"]
    for field in required_fields:
        assert field in handoff_data, f"Missing required field: {field}"
    
    # Validate agent types are valid
    valid_agents = [agent.value for agent in AgentType]
    assert handoff_data["from_agent"] in valid_agents
    assert handoff_data["to_agent"] in valid_agents
    
    # Validate phase is a valid enum value
    valid_phases = [phase.value for phase in HandoffPhase]
    assert handoff_data["phase"] in valid_phases, f"Invalid phase: {handoff_data['phase']}"
    
    # Validate priority is a string enum (if provided)
    if "priority" in handoff_data:
        valid_priorities = [priority.value for priority in HandoffPriority]
        assert handoff_data["priority"] in valid_priorities, f"Invalid priority: {handoff_data['priority']}"
    
    # Validate expected_outputs is a list
    assert isinstance(handoff_data["expected_outputs"], list), "expected_outputs must be a list"
    
    # Validate all expected_outputs are strings
    for output in handoff_data["expected_outputs"]:
        assert isinstance(output, str), "All expected_outputs must be strings"
    
    # Validate context_summary is a string
    assert isinstance(handoff_data["context_summary"], str), "context_summary must be a string"
    assert len(handoff_data["context_summary"]) > 0, "context_summary cannot be empty"


def assert_performance_threshold(elapsed_ms: float, threshold_ms: float, operation: str):
    """Assert that operation completed within performance threshold."""
    assert elapsed_ms <= threshold_ms, (
        f"{operation} took {elapsed_ms:.2f}ms, exceeding threshold of {threshold_ms}ms"
    )


# Performance Testing Utilities

@pytest.fixture
def performance_timer():
    """Utility for measuring test execution time."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return None
    
    return Timer()


@pytest.fixture
def load_test_data():
    """Generate large datasets for performance testing."""
    def generate_artifacts(count: int, project_id: UUID):
        """Generate test artifacts for load testing."""
        return [
            {
                "project_id": project_id,
                "source_agent": AgentType.ANALYST,
                "artifact_type": ArtifactType.PROJECT_PLAN,
                "content": {"test_data": f"artifact_{i}", "size": "large"},
                "artifact_metadata": {"test_id": i, "batch": "load_test"}
            }
            for i in range(count)
        ]

    def generate_tasks(count: int, project_id: UUID):
        """Generate test tasks for load testing."""
        agent_types = list(AgentType)
        return [
            {
                "project_id": project_id,
                "agent_type": agent_types[i % len(agent_types)],
                "instructions": f"Load test task {i}",
                "status": TaskStatus.PENDING,
                "context_ids": []
            }
            for i in range(count)
        ]

    return {
        "artifacts": generate_artifacts,
        "tasks": generate_tasks
    }


# Test Markers

pytest_plugins = ["pytest_asyncio"]

# Markers for test categorization
pytestmark = [
    pytest.mark.asyncio,
]

def pytest_configure(config):
    """Configure custom pytest markers."""
    # Original markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "p0: Priority 0 - Critical tests")
    config.addinivalue_line("markers", "p1: Priority 1 - Important tests")
    config.addinivalue_line("markers", "p2: Priority 2 - Standard tests")
    config.addinivalue_line("markers", "p3: Priority 3 - Nice to have tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "handoff: Sequential task handoff tests")
    config.addinivalue_line("markers", "autogen: AutoGen framework integration tests")
    config.addinivalue_line("markers", "context: Context persistence tests")
    config.addinivalue_line("markers", "hitl: Human-in-the-loop tests")
    config.addinivalue_line("markers", "workflow: Full workflow tests")
    config.addinivalue_line("markers", "sdlc: SDLC process flow tests")

    # NEW: Data source classification markers (REQUIRED for all tests)
    config.addinivalue_line("markers", "mock_data: Test uses mock data and may hide database/schema issues")
    config.addinivalue_line("markers", "real_data: Test uses real database operations and catches actual issues")
    config.addinivalue_line("markers", "api_integration: Test verifies complete API → Database flow")
    config.addinivalue_line("markers", "database_schema: Test validates database schema consistency")
    config.addinivalue_line("markers", "external_service: Test mocks external services (APIs, file system, etc.)")


def pytest_runtest_setup(item):
    """
    Validate test classification before running.

    ALL TESTS MUST indicate if they use mock or real data.
    """
    # Get all markers for this test
    markers = [marker.name for marker in item.iter_markers()]

    # Check if test has proper data source classification
    has_mock_marker = "mock_data" in markers
    has_real_marker = "real_data" in markers

    # REQUIREMENT: Tests must have exactly one data classification marker
    if not (has_mock_marker or has_real_marker):
        pytest.fail(
            f"\n❌ MISSING CLASSIFICATION: Test {item.nodeid} must be marked with either:\n"
            f"   @pytest.mark.mock_data    (for tests using mocks)\n"
            f"   @pytest.mark.real_data    (for tests using real database)\n"
            f"\n📋 This is REQUIRED to track which tests may hide database issues."
        )

    if has_mock_marker and has_real_marker:
        pytest.fail(
            f"\n❌ CONFLICTING MARKERS: Test {item.nodeid} cannot have both mock_data and real_data markers.\n"
            f"   Choose the marker that matches the primary data source."
        )


def pytest_runtest_call(item):
    """Display test classification during execution."""
    markers = [marker.name for marker in item.iter_markers()]

    # Print clear classification info during test execution
    if "mock_data" in markers:
        print(f"\n🎭 MOCK DATA TEST: {item.name}")
        print("   ⚠️  Warning: Using mocked data - may hide real database schema issues")
        if "database_schema" in markers:
            print("   🚨 CRITICAL: Mock test claiming to validate database schema!")
    elif "real_data" in markers:
        print(f"\n💾 REAL DATA TEST: {item.name}")
        print("   ✅ Using real database operations - validates actual schema and constraints")
        if "api_integration" in markers:
            print("   🔄 Verifying complete API → Database flow")


def pytest_runtest_teardown(item, nextitem):
    """Log test results with data classification."""
    markers = [marker.name for marker in item.iter_markers()]

    # Log completion status
    if "mock_data" in markers:
        print("   🎭 Mock test completed")
    elif "real_data" in markers:
        print("   💾 Real database test completed")
