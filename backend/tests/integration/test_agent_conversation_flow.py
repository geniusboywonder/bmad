"""Integration tests for agent conversation flow and context passing."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import json

from app.models.task import Task, TaskStatus
from app.models.context import ContextArtifact, ArtifactType
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.services.agent_service import AgentService
from app.agents.factory import get_agent_factory


@pytest.mark.asyncio
class TestAgentConversationFlow:
    """Test complete agent conversation flows with context passing."""
    
    @pytest.fixture
    def project_id(self):
        """Create a project ID for testing."""
        return uuid4()
    
    @pytest.fixture
    def user_input_artifact(self, project_id):
        """Create initial user input artifact."""
        return ContextArtifact(
            context_id=uuid4(),
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={
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
        )
    
    @pytest.fixture
    def mock_context_store(self):
        """Create mock context store service."""
        mock_store = AsyncMock()
        mock_store.get_artifacts_by_project.return_value = []
        mock_store.get_artifacts_by_ids.return_value = []
        mock_store.create_artifact.return_value = MagicMock(context_id=uuid4())
        return mock_store
    
    @pytest.fixture
    def mock_agent_status_service(self):
        """Create mock agent status service."""
        mock_service = AsyncMock()
        return mock_service
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    async def test_orchestrator_to_analyst_handoff(
        self, mock_status_service, mock_context_store,
        project_id, user_input_artifact
    ):
        """Test handoff from Orchestrator to Analyst with requirements analysis."""
        
        # Setup mocks
        mock_context_store_instance = AsyncMock()
        mock_context_store_instance.get_artifacts_by_project.return_value = [user_input_artifact]
        mock_context_store_instance.create_artifact.return_value = MagicMock(context_id=uuid4())
        mock_context_store.return_value = mock_context_store_instance
        
        mock_status_service_instance = AsyncMock()
        mock_status_service.return_value = mock_status_service_instance
        
        # Create agent service
        agent_service = AgentService()
        
        # Create orchestrator task
        orchestrator_task = Task(
            task_id=uuid4(),
            project_id=project_id,
            agent_type=AgentType.ORCHESTRATOR.value,
            status=TaskStatus.PENDING,
            instructions="Analyze project requirements and create handoff to Analyst"
        )
        
        # Mock orchestrator agent execution
        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            # Mock orchestrator agent
            mock_orchestrator = AsyncMock()
            mock_orchestrator.execute_task.return_value = {
                "success": True,
                "output": {
                    "orchestration_type": "workflow_coordination",
                    "current_phase": "discovery",
                    "next_agent": "analyst",
                    "instructions": "Conduct comprehensive requirements analysis",
                    "workflow_decisions": {
                        "decision": "proceed_with_analysis",
                        "reasoning": "User input provides sufficient detail for analysis"
                    }
                }
            }
            
            mock_get_agent.return_value = mock_orchestrator
            
            # Execute orchestrator task
            orchestrator_result = await agent_service.execute_task_with_agent(orchestrator_task)
            
            # Verify orchestrator execution
            assert orchestrator_result["success"] is True
            assert "output" in orchestrator_result
            
            # Verify orchestrator identified next agent as analyst
            output = orchestrator_result["output"]
            assert output["next_agent"] == "analyst"
            assert output["current_phase"] == "discovery"
        
        # Create handoff to analyst
        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            mock_orchestrator.create_handoff.return_value = HandoffSchema(
                handoff_id=uuid4(),
                from_agent=AgentType.ORCHESTRATOR.value,
                to_agent=AgentType.ANALYST.value,
                project_id=project_id,
                phase="discovery",
                context_ids=[user_input_artifact.context_id],
                instructions="Conduct comprehensive requirements analysis for task management API",
                expected_outputs=["project_requirements", "user_personas", "success_criteria"]
            )
            
            mock_get_agent.return_value = mock_orchestrator
            
            handoff = await agent_service.create_agent_handoff(
                AgentType.ORCHESTRATOR, AgentType.ANALYST, orchestrator_task
            )
            
            # Verify handoff creation
            assert handoff.from_agent == AgentType.ORCHESTRATOR.value
            assert handoff.to_agent == AgentType.ANALYST.value
            assert handoff.phase == "discovery"
            assert "requirements analysis" in handoff.instructions
        
        # Execute analyst task with handoff
        analyst_task = Task(
            task_id=uuid4(),
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            status=TaskStatus.PENDING,
            instructions=handoff.instructions
        )
        
        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            # Mock analyst agent
            mock_analyst = AsyncMock()
            mock_analyst.execute_task.return_value = {
                "success": True,
                "output": {
                    "analysis_type": "requirements_analysis",
                    "status": "completed",
                    "user_personas": [
                        {
                            "name": "Project Manager",
                            "description": "Manages team tasks and project deadlines",
                            "needs": ["Task organization", "Progress tracking", "Team collaboration"]
                        },
                        {
                            "name": "Team Member",
                            "description": "Individual contributor working on assigned tasks",
                            "needs": ["Task clarity", "Status updates", "Time management"]
                        }
                    ],
                    "functional_requirements": [
                        "Create new tasks with title, description, status, due date",
                        "Update task status (todo, in_progress, done)",
                        "Assign tasks to team members",
                        "Filter and search tasks by various criteria",
                        "Authenticate users with JWT tokens"
                    ],
                    "non_functional_requirements": [
                        "API response time < 200ms",
                        "Support 100 concurrent users",
                        "99.9% uptime",
                        "GDPR compliant data handling"
                    ],
                    "success_criteria": [
                        "Users can complete task CRUD operations in <30 seconds",
                        "System supports expected user load without degradation",
                        "All API endpoints return proper status codes and error messages"
                    ]
                }
            }
            
            mock_get_agent.return_value = mock_analyst
            
            # Execute analyst task
            analyst_result = await agent_service.execute_task_with_agent(analyst_task, handoff)
            
            # Verify analyst execution
            assert analyst_result["success"] is True
            assert "output" in analyst_result
            
            # Verify analyst produced requirements analysis
            analysis_output = analyst_result["output"]
            assert analysis_output["analysis_type"] == "requirements_analysis"
            assert len(analysis_output["user_personas"]) == 2
            assert len(analysis_output["functional_requirements"]) >= 4
            assert len(analysis_output["non_functional_requirements"]) >= 3
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    async def test_analyst_to_architect_handoff(
        self, mock_status_service, mock_context_store, project_id
    ):
        """Test handoff from Analyst to Architect with technical design."""
        
        # Setup mocks
        mock_context_store_instance = AsyncMock()
        mock_context_store.return_value = mock_context_store_instance
        
        mock_status_service_instance = AsyncMock()
        mock_status_service.return_value = mock_status_service_instance
        
        # Create requirements artifact from analyst
        requirements_artifact = ContextArtifact(
            context_id=uuid4(),
            project_id=project_id,
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.SOFTWARE_SPECIFICATION,
            content={
                "functional_requirements": [
                    "Task CRUD operations",
                    "User authentication",
                    "Task filtering and search"
                ],
                "non_functional_requirements": [
                    "Response time < 200ms",
                    "Support 100 concurrent users"
                ],
                "user_personas": [
                    {"name": "Project Manager", "needs": ["Task organization"]}
                ]
            }
        )
        
        mock_context_store_instance.get_artifacts_by_ids.return_value = [requirements_artifact]
        mock_context_store_instance.create_artifact.return_value = MagicMock(context_id=uuid4())
        
        # Create agent service
        agent_service = AgentService()
        
        # Create handoff from analyst to architect
        analyst_task = Task(
            task_id=uuid4(),
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            status=TaskStatus.COMPLETED,
            instructions="Requirements analysis completed"
        )
        
        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            # Mock analyst agent for handoff creation
            mock_analyst = AsyncMock()
            mock_analyst.create_handoff.return_value = HandoffSchema(
                handoff_id=uuid4(),
                from_agent=AgentType.ANALYST.value,
                to_agent=AgentType.ARCHITECT.value,
                project_id=project_id,
                phase="design",
                context_ids=[requirements_artifact.context_id],
                instructions="Design technical architecture for task management API based on requirements",
                expected_outputs=["system_architecture", "api_specifications", "implementation_plan"]
            )
            
            mock_get_agent.return_value = mock_analyst
            
            handoff = await agent_service.create_agent_handoff(
                AgentType.ANALYST, AgentType.ARCHITECT, analyst_task, [requirements_artifact]
            )
            
            # Verify handoff
            assert handoff.from_agent == AgentType.ANALYST.value
            assert handoff.to_agent == AgentType.ARCHITECT.value
            assert handoff.phase == "design"
        
        # Execute architect task
        architect_task = Task(
            task_id=uuid4(),
            project_id=project_id,
            agent_type=AgentType.ARCHITECT.value,
            status=TaskStatus.PENDING,
            instructions=handoff.instructions
        )
        
        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            # Mock architect agent
            mock_architect = AsyncMock()
            mock_architect.execute_task.return_value = {
                "success": True,
                "output": {
                    "architecture_type": "technical_system_design",
                    "status": "completed",
                    "system_components": [
                        {
                            "name": "API Gateway",
                            "type": "presentation_layer",
                            "technology": "FastAPI",
                            "responsibilities": ["Request routing", "Authentication", "Rate limiting"]
                        },
                        {
                            "name": "Task Service",
                            "type": "business_logic_layer",
                            "technology": "Python",
                            "responsibilities": ["Task CRUD", "Business rules", "Validation"]
                        },
                        {
                            "name": "Database",
                            "type": "data_layer",
                            "technology": "PostgreSQL",
                            "responsibilities": ["Data persistence", "Transactions", "Constraints"]
                        }
                    ],
                    "api_specifications": [
                        {
                            "endpoint": "/api/v1/tasks",
                            "method": "GET",
                            "description": "List all tasks",
                            "parameters": ["limit", "offset", "status"]
                        },
                        {
                            "endpoint": "/api/v1/tasks",
                            "method": "POST",
                            "description": "Create new task",
                            "request_schema": {"title": "string", "description": "string"}
                        }
                    ],
                    "implementation_plan": {
                        "phase_1": "Database setup and models",
                        "phase_2": "Core API endpoints",
                        "phase_3": "Authentication integration",
                        "phase_4": "Testing and validation"
                    }
                }
            }
            
            mock_get_agent.return_value = mock_architect
            
            # Execute architect task
            architect_result = await agent_service.execute_task_with_agent(architect_task, handoff)
            
            # Verify architect execution
            assert architect_result["success"] is True
            assert "output" in architect_result
            
            # Verify architect produced technical design
            design_output = architect_result["output"]
            assert design_output["architecture_type"] == "technical_system_design"
            assert len(design_output["system_components"]) == 3
            assert len(design_output["api_specifications"]) >= 2
            assert "implementation_plan" in design_output
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    async def test_multi_agent_context_preservation(
        self, mock_status_service, mock_context_store, project_id
    ):
        """Test context preservation across multiple agent handoffs."""
        
        # Setup mocks
        mock_context_store_instance = AsyncMock()
        mock_context_store.return_value = mock_context_store_instance
        
        mock_status_service_instance = AsyncMock()
        mock_status_service.return_value = mock_status_service_instance
        
        # Create agent service
        agent_service = AgentService()
        
        # Simulate context building through workflow
        artifacts = []
        
        # 1. User input artifact
        user_artifact = ContextArtifact(
            context_id=uuid4(),
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={"user_request": "Build task management API"}
        )
        artifacts.append(user_artifact)
        
        # 2. Requirements artifact from analyst
        requirements_artifact = ContextArtifact(
            context_id=uuid4(),
            project_id=project_id,
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.SOFTWARE_SPECIFICATION,
            content={
                "functional_requirements": ["Task CRUD", "Authentication"],
                "user_personas": [{"name": "Project Manager"}]
            }
        )
        artifacts.append(requirements_artifact)
        
        # 3. Architecture artifact from architect
        architecture_artifact = ContextArtifact(
            context_id=uuid4(),
            project_id=project_id,
            source_agent=AgentType.ARCHITECT,
            artifact_type=ArtifactType.SYSTEM_ARCHITECTURE,
            content={
                "system_components": ["API Gateway", "Task Service", "Database"],
                "api_specifications": ["/api/v1/tasks"],
                "technology_stack": {"backend": "FastAPI", "database": "PostgreSQL"}
            }
        )
        artifacts.append(architecture_artifact)
        
        # Mock context retrieval to return cumulative artifacts
        mock_context_store_instance.get_artifacts_by_ids.return_value = artifacts
        mock_context_store_instance.create_artifact.return_value = MagicMock(context_id=uuid4())
        
        # Test coder agent receiving complete context
        coder_task = Task(
            task_id=uuid4(),
            project_id=project_id,
            agent_type=AgentType.CODER.value,
            status=TaskStatus.PENDING,
            instructions="Implement the task management API based on requirements and architecture"
        )
        
        # Create handoff with all context
        handoff = HandoffSchema(
            handoff_id=uuid4(),
            from_agent=AgentType.ARCHITECT.value,
            to_agent=AgentType.CODER.value,
            project_id=project_id,
            phase="build",
            context_ids=[artifact.context_id for artifact in artifacts],
            instructions="Implement API based on complete project context",
            expected_outputs=["source_code", "unit_tests", "documentation"]
        )
        
        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            # Mock coder agent
            mock_coder = AsyncMock()
            mock_coder.execute_task.return_value = {
                "success": True,
                "output": {
                    "implementation_type": "full_stack_implementation",
                    "source_files": [
                        {"filename": "main.py", "content": "FastAPI application"},
                        {"filename": "models.py", "content": "SQLAlchemy models"},
                        {"filename": "api.py", "content": "API endpoints"}
                    ],
                    "context_summary": "Implemented based on user requirements, analyst specifications, and architect design"
                }
            }
            
            mock_get_agent.return_value = mock_coder
            
            # Execute coder task with complete context
            coder_result = await agent_service.execute_task_with_agent(coder_task, handoff)
            
            # Verify coder execution
            assert coder_result["success"] is True
            
            # Verify coder received and processed complete context
            mock_coder.execute_task.assert_called_once()
            call_args = mock_coder.execute_task.call_args
            
            # Check that task and context were passed
            assert call_args[0][0] == coder_task  # First arg is task
            context_artifacts_passed = call_args[0][1]  # Second arg is context
            
            # Verify all context artifacts were passed
            assert len(context_artifacts_passed) == len(artifacts)
            
            # Verify context includes original user input and all intermediate outputs
            context_sources = [artifact.source_agent for artifact in context_artifacts_passed]
            assert AgentType.ORCHESTRATOR in context_sources
            assert AgentType.ANALYST in context_sources
            assert AgentType.ARCHITECT in context_sources
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    async def test_agent_status_tracking_during_workflow(
        self, mock_status_service, mock_context_store, project_id
    ):
        """Test agent status tracking throughout workflow execution."""
        
        # Setup mocks
        mock_context_store_instance = AsyncMock()
        mock_context_store_instance.get_artifacts_by_project.return_value = []
        mock_context_store_instance.create_artifact.return_value = MagicMock(context_id=uuid4())
        mock_context_store.return_value = mock_context_store_instance
        
        mock_status_service_instance = AsyncMock()
        mock_status_service.return_value = mock_status_service_instance
        
        # Create agent service
        agent_service = AgentService()
        
        # Create test task
        task = Task(
            task_id=uuid4(),
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            status=TaskStatus.PENDING,
            instructions="Test task for status tracking"
        )
        
        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            # Mock successful agent execution
            mock_agent = AsyncMock()
            mock_agent.execute_task.return_value = {
                "success": True,
                "output": {"test": "result"}
            }
            mock_get_agent.return_value = mock_agent
            
            # Execute task
            result = await agent_service.execute_task_with_agent(task)
            
            # Verify status transitions
            # Should be called: working -> idle (on success)
            assert mock_status_service_instance.set_agent_working.call_count == 1
            assert mock_status_service_instance.set_agent_idle.call_count == 1
            assert mock_status_service_instance.set_agent_error.call_count == 0
            
            # Verify working status was set with correct parameters
            working_call = mock_status_service_instance.set_agent_working.call_args
            assert working_call[0][0] == AgentType.ANALYST  # agent_type
            assert working_call[0][1] == task.task_id       # task_id
            assert working_call[0][2] == task.project_id    # project_id
            
            # Verify idle status was set with correct parameters
            idle_call = mock_status_service_instance.set_agent_idle.call_args
            assert idle_call[0][0] == AgentType.ANALYST      # agent_type
            assert idle_call[0][1] == task.project_id        # project_id
        
        # Test error case
        with patch.object(agent_service, '_get_agent_instance') as mock_get_agent:
            # Mock failed agent execution
            mock_agent = AsyncMock()
            mock_agent.execute_task.return_value = {
                "success": False,
                "error": "Test error"
            }
            mock_get_agent.return_value = mock_agent
            
            # Reset mock counters
            mock_status_service_instance.reset_mock()
            
            # Execute task
            result = await agent_service.execute_task_with_agent(task)
            
            # Verify error status transition
            # Should be called: working -> error (on failure)
            assert mock_status_service_instance.set_agent_working.call_count == 1
            assert mock_status_service_instance.set_agent_error.call_count == 1
            assert mock_status_service_instance.set_agent_idle.call_count == 0
            
            # Verify error status was set with correct parameters
            error_call = mock_status_service_instance.set_agent_error.call_args
            assert error_call[0][0] == AgentType.ANALYST      # agent_type
            assert "Test error" in error_call[0][1]           # error_message
            assert error_call[0][2] == task.task_id           # task_id
            assert error_call[0][3] == task.project_id        # project_id


def test_agent_service_singleton():
    """Test that get_agent_service returns singleton instance."""
    service1 = get_agent_service()
    service2 = get_agent_service()
    
    assert service1 is service2
    assert isinstance(service1, AgentService)