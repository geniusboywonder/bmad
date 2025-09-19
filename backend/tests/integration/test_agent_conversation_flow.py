import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.models.task import Task, TaskStatus
from app.models.context import ContextArtifact, ArtifactType, ContextArtifactCreate
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.services.agent_service import AgentService
from app.services.context_store import ContextStoreService
from app.services.agent_status_service import AgentStatusService
from tests.utils.database_test_utils import DatabaseTestManager

@pytest.mark.asyncio
class TestAgentConversationFlow:
    @pytest.fixture
    def db_manager(self):
        """Real database manager for conversation flow tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.fixture
    def context_store(self, db_manager):
        """Real context store service with database session."""
        with db_manager.get_session() as session:
            yield ContextStoreService(session)

    @pytest.fixture
    def agent_status_service(self):
        """Real agent status service."""
        return AgentStatusService()

    @pytest.fixture
    def agent_service(self, db_manager, context_store, agent_status_service):
        """Real agent service with real dependencies."""
        with db_manager.get_session() as session:
            service = AgentService(session)
            service.context_store = context_store
            service.agent_status_service = agent_status_service
            yield service

    @pytest.mark.mock_data

    async def test_orchestrator_to_analyst_handoff(self, db_manager, agent_service, context_store):
        """Test handoff from Orchestrator to Analyst with requirements analysis."""
        # 1. Create a project and an initial artifact
        project = db_manager.create_test_project(name="Conversation Flow Test Project")
        user_input_content = {
            "user_request": "Create a simple task management API",
            "requirements": [
                "Users can create, read, update, delete tasks",
                "Tasks have title, description, status, due date",
                "REST API with authentication",
                "Database persistence"
            ],
            "constraints": [
                "Use FastAPI framework",
                "PostgreSQL database",
                "JWT authentication"
            ]
        }
        user_input_artifact_data = ContextArtifactCreate(
            project_id=project.id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content=user_input_content
        )
        user_input_artifact = await context_store.create_artifact(user_input_artifact_data)

        # 2. Create and execute orchestrator task
        orchestrator_task = Task(
            task_id=uuid4(),
            project_id=project.id,
            agent_type=AgentType.ORCHESTRATOR.value,
            status=TaskStatus.PENDING,
            instructions="Analyze project requirements and create handoff to Analyst"
        )

        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.execute_task.return_value = {
                "success": True,
                "output": {
                    "next_agent": "analyst",
                    "instructions": "Conduct comprehensive requirements analysis",
                }
            }
            mock_orchestrator.create_handoff.return_value = HandoffSchema(
                from_agent=AgentType.ORCHESTRATOR.value,
                to_agent=AgentType.ANALYST.value,
                project_id=project.id,
                phase="discovery",
                context_ids=[user_input_artifact.id],
                instructions="Conduct comprehensive requirements analysis for task management API",
                expected_outputs=["project_requirements", "user_personas", "success_criteria"]
            )
            mock_get_agent.return_value = mock_orchestrator

            orchestrator_result = await agent_service.execute_task_with_agent(orchestrator_task)
            assert orchestrator_result["success"] is True

            handoff = await agent_service.create_agent_handoff(
                AgentType.ORCHESTRATOR, AgentType.ANALYST, orchestrator_task
            )

        # 3. Create and execute analyst task
        analyst_task = Task(
            task_id=uuid4(),
            project_id=project.id,
            agent_type=AgentType.ANALYST.value,
            status=TaskStatus.PENDING,
            instructions=handoff.instructions
        )

        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            mock_analyst = AsyncMock()
            mock_analyst.execute_task.return_value = {
                "success": True,
                "output": {
                    "analysis_type": "requirements_analysis",
                    "status": "completed",
                }
            }
            mock_get_agent.return_value = mock_analyst

            analyst_result = await agent_service.execute_task_with_agent(analyst_task, handoff)
            assert analyst_result["success"] is True
            assert analyst_result["output"]["analysis_type"] == "requirements_analysis"