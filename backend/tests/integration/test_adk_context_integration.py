import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.agents.bmad_adk_wrapper import BMADADKWrapper
from app.models.context import ContextArtifact, ArtifactType, ContextArtifactCreate
from app.models.agent import AgentType
from app.services.context_store import ContextStoreService
from tests.utils.database_test_utils import DatabaseTestManager


@pytest.mark.asyncio
class TestADKContextIntegration:
    @pytest.fixture
    def db_manager(self):
        """Real database manager for context integration tests."""
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
    def adk_wrapper(self, context_store):
        """BMAD ADK Wrapper with real context store."""
        wrapper = BMADADKWrapper(
            agent_name="context_test_agent",
            agent_type="analyst",
            instruction="You are an analyst agent that can read and create context artifacts.",
            context_store=context_store
        )
        return wrapper

    async def test_context_reading_and_creation(self, db_manager, context_store, adk_wrapper):
        """Test context reading and creation with real database."""
        # 1. Create a project and an initial artifact
        project = db_manager.create_test_project(name="ADK Context Test Project")
        initial_artifact_content = {"user_input": "Create a web application for task management"}
        
        initial_artifact_data = ContextArtifactCreate(
            project_id=project.id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content=initial_artifact_content,
        )
        initial_artifact = await context_store.create_artifact(initial_artifact_data)

        # 2. Execute the ADK agent
        with patch.object(adk_wrapper, '_execute_adk_agent', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "response": "Analysis complete, new artifact created.",
                "execution_id": "test-execution-context"
            }

            result = await adk_wrapper.process_with_enterprise_controls(
                message="Analyze the project requirements and create a new artifact.",
                project_id=str(project.id),
                task_id=str(uuid4()),
                user_id="test_user"
            )

        # 3. Verify the result and the database state
        assert result["success"] is True
        
        # The wrapper should have fetched the context and passed it to the agent.
        # The mock_execute should have been called with the context.
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args[0]
        passed_context = call_args[2]
        assert len(passed_context) == 1
        assert passed_context[0].id == initial_artifact.id