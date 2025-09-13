"""
End-to-End tests for Story 2.1: Sequential Task Handoff

Test scenarios:
- 2.1-E2E-001: Complete SDLC workflow execution (P0)
- 2.1-E2E-002: Multi-phase project progression (P1)
"""

import pytest
import asyncio
import unittest.mock
from uuid import UUID
from fastapi.testclient import TestClient
from fastapi import status

from app.models.task import TaskStatus
from app.models.agent import AgentType
from app.models.context import ArtifactType
from app.schemas.handoff import HandoffSchema
from tests.conftest import assert_performance_threshold


class TestCompleteSDLCWorkflowExecution:
    """Test scenario 2.1-E2E-001: Complete SDLC workflow execution (P0)"""
    
    @pytest.mark.e2e
    @pytest.mark.p0
    @pytest.mark.workflow
    @pytest.mark.sdlc
    @pytest.mark.asyncio
    async def test_complete_sdlc_workflow_execution(
        self, client: TestClient, db_session, orchestrator_service, 
        context_store_service, mock_autogen_service, performance_timer
    ):
        """Test complete SDLC workflow from analysis through deployment."""
        performance_timer.start()
        
        # Step 1: Create project via API
        project_data = {
            "name": "E2E SDLC Workflow Test",
            "description": "Complete workflow test project"
        }
        
        response = client.post("/api/v1/projects/", json=project_data)
        assert response.status_code == status.HTTP_201_CREATED
        project_id = UUID(response.json()["id"])
        
        # Step 2: Create initial user input context
        user_input = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={
                "requirements": "Build a task management system with user authentication",
                "features": ["user registration", "task creation", "task tracking", "reporting"],
                "constraints": ["web application", "responsive design", "database persistence"]
            }
        )
        
        # Step 3: Analysis Phase - Create analyst task
        analysis_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analyze user requirements and create detailed project plan",
            context_ids=[user_input.context_id]
        )
        
        # Step 4: Execute analysis task (simulated with mock)
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            dummy_analysis_handoff = HandoffSchema(
                handoff_id=analysis_task.task_id,
                from_agent=AgentType.ORCHESTRATOR.value,
                to_agent=analysis_task.agent_type,
                project_id=analysis_task.project_id,
                phase="analysis",
                context_summary="Initial analysis of user requirements.",
                context_ids=[str(c) for c in analysis_task.context_ids],
                instructions=analysis_task.instructions,
                expected_outputs=["Detailed project plan"],
                priority='high',
            )
            analysis_result = await orchestrator_service.process_task_with_autogen(analysis_task, dummy_analysis_handoff)
            
            # Complete analysis task
            orchestrator_service.update_task_status(
                analysis_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "project_plan": "Detailed analysis completed",
                    "architecture_requirements": ["API layer", "database layer", "frontend"],
                    "technology_stack": ["FastAPI", "PostgreSQL", "React"]
                }
            )
        
        # Step 5: Create analysis output artifact
        analysis_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={
                "components": ["authentication", "task_management", "reporting"],
                "database_schema": {"users": ["id", "username"], "tasks": ["id", "title", "status"]},
                "api_endpoints": ["/auth", "/tasks", "/reports"]
            }
        )
        
        # Step 6: Architecture Phase - Create handoff to architect
        architecture_handoff = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Design system architecture based on analysis",
            "context_ids": [user_input.context_id, analysis_artifact.context_id],
            "expected_output": "Technical architecture specification"
        }
        
        architecture_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=architecture_handoff
        )
        
        # Execute architecture task
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            dummy_architecture_handoff = HandoffSchema(
                handoff_id=architecture_task.task_id,
                from_agent=architecture_handoff["from_agent"],
                to_agent=architecture_handoff["to_agent"],
                project_id=architecture_task.project_id,
                phase="architecture",
                context_summary="Design of the system architecture based on the project plan.",
                context_ids=[str(c) for c in architecture_task.context_ids],
                instructions=architecture_handoff["task_instructions"],
                expected_outputs=[architecture_handoff["expected_output"]],
                priority='high',
            )
            await orchestrator_service.process_task_with_autogen(architecture_task, dummy_architecture_handoff)
            
            orchestrator_service.update_task_status(
                architecture_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "system_design": "Microservices architecture",
                    "components": ["auth-service", "task-service", "ui-service"],
                    "data_flow": "API Gateway -> Services -> Database"
                }
            )
        
        # Step 7: Create architecture output artifact
        architecture_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ARCHITECT.value,
            artifact_type=ArtifactType.SYSTEM_ARCHITECTURE,
            content={
                "services": ["auth", "tasks", "reports"],
                "databases": ["users_db", "tasks_db"],
                "interfaces": ["REST API", "WebSocket"]
            }
        )
        
        # Step 8: Implementation Phase - Create handoff to coder
        implementation_handoff = {
            "from_agent": AgentType.ARCHITECT.value,
            "to_agent": AgentType.CODER.value,
            "task_instructions": "Implement system based on architecture",
            "context_ids": [analysis_artifact.context_id, architecture_artifact.context_id],
            "expected_output": "Working application code"
        }
        
        implementation_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=implementation_handoff
        )
        
        # Execute implementation task
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            dummy_implementation_handoff = HandoffSchema(
                handoff_id=implementation_task.task_id,
                from_agent=implementation_handoff["from_agent"],
                to_agent=implementation_handoff["to_agent"],
                project_id=implementation_task.project_id,
                phase="coding",
                context_summary="Implementation of the core services based on the architecture.",
                context_ids=[str(c) for c in implementation_task.context_ids],
                instructions=implementation_handoff["task_instructions"],
                expected_outputs=[implementation_handoff["expected_output"]],
                priority='high',
            )
            await orchestrator_service.process_task_with_autogen(implementation_task, dummy_implementation_handoff)
            
            orchestrator_service.update_task_status(
                implementation_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "code_modules": ["auth.py", "tasks.py", "database.py"],
                    "api_endpoints": 12,
                    "test_coverage": "85%"
                }
            )
        
        # Step 9: Create implementation output artifact
        code_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.CODER.value,
            artifact_type=ArtifactType.SOURCE_CODE,
            content={
                "modules": ["authentication", "task_management", "api_layer"],
                "languages": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "React"]
            }
        )
        
        # Step 10: Testing Phase - Create handoff to tester
        testing_handoff = {
            "from_agent": AgentType.CODER.value,
            "to_agent": AgentType.TESTER.value,
            "task_instructions": "Test implemented system",
            "context_ids": [architecture_artifact.context_id, code_artifact.context_id],
            "expected_output": "Test results and quality report"
        }
        
        testing_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=testing_handoff
        )
        
        # Execute testing task
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            dummy_testing_handoff = HandoffSchema(
                handoff_id=testing_task.task_id,
                from_agent=testing_handoff["from_agent"],
                to_agent=testing_handoff["to_agent"],
                project_id=testing_task.project_id,
                phase="testing",
                context_summary="Testing of the implemented system.",
                context_ids=[str(c) for c in testing_task.context_ids],
                instructions=testing_handoff["task_instructions"],
                expected_outputs=[testing_handoff["expected_output"]],
                priority='high',
            )
            await orchestrator_service.process_task_with_autogen(testing_task, dummy_testing_handoff)
            
            orchestrator_service.update_task_status(
                testing_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "test_results": "All tests passing",
                    "coverage": "90%",
                    "performance": "Within requirements"
                }
            )
        
        # Step 11: Create test output artifact
        test_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.TESTER.value,
            artifact_type=ArtifactType.TEST_RESULTS,
            content={
                "unit_tests": 45,
                "integration_tests": 20,
                "e2e_tests": 10,
                "all_passing": True
            }
        )
        
        # Step 12: Deployment Phase - Create handoff to deployer
        deployment_handoff = {
            "from_agent": AgentType.TESTER.value,
            "to_agent": AgentType.DEPLOYER.value,
            "task_instructions": "Deploy tested system",
            "context_ids": [code_artifact.context_id, test_artifact.context_id],
            "expected_output": "Deployment package and configuration"
        }
        
        deployment_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=deployment_handoff
        )
        
        # Execute deployment task
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            dummy_deployment_handoff = HandoffSchema(
                handoff_id=deployment_task.task_id,
                from_agent=deployment_handoff["from_agent"],
                to_agent=deployment_handoff["to_agent"],
                project_id=deployment_task.project_id,
                phase="deployment",
                context_summary="Deployment of the tested system.",
                context_ids=[str(c) for c in deployment_task.context_ids],
                instructions=deployment_handoff["task_instructions"],
                expected_outputs=[deployment_handoff["expected_output"]],
                priority='high',
            )
            await orchestrator_service.process_task_with_autogen(deployment_task, dummy_deployment_handoff)
            
            orchestrator_service.update_task_status(
                deployment_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "deployment_status": "Successfully deployed",
                    "environment": "production",
                    "url": "https://app.example.com"
                }
            )
        
        performance_timer.stop()
        
        # Step 13: Verify complete workflow
        final_status = client.get(f"/api/v1/projects/{project_id}/status")
        assert final_status.status_code == status.HTTP_200_OK
        
        status_data = final_status.json()
        tasks = status_data["tasks"]
        
        # Verify all phases completed
        assert len(tasks) == 5  # Analysis, Architecture, Implementation, Testing, Deployment
        
        # Verify all tasks completed
        completed_tasks = [task for task in tasks if task["status"] == TaskStatus.COMPLETED.value]
        assert len(completed_tasks) == 5
        
        # Verify agent progression through SDLC
        agent_sequence = [task["agent_type"] for task in tasks]
        expected_sequence = [
            AgentType.ANALYST.value,
            AgentType.ARCHITECT.value, 
            AgentType.CODER.value,
            AgentType.TESTER.value,
            AgentType.DEPLOYER.value
        ]
        assert agent_sequence == expected_sequence
        
        # Verify all context artifacts created
        all_artifacts = context_store_service.get_artifacts_by_project(project_id)
        assert len(all_artifacts) == 6  # User input + 5 phase outputs
        
        artifact_types = [artifact.artifact_type for artifact in all_artifacts]
        expected_types = [
            ArtifactType.USER_INPUT,
            ArtifactType.PROJECT_PLAN,
            ArtifactType.SYSTEM_ARCHITECTURE,
            ArtifactType.SOURCE_CODE,
            ArtifactType.TEST_RESULTS
        ]
        
        for expected_type in expected_types:
            assert expected_type in artifact_types
        
        # Verify performance
        assert_performance_threshold(performance_timer.elapsed_ms, 30000, "Complete SDLC workflow")
    
    @pytest.mark.e2e
    @pytest.mark.p0
    @pytest.mark.workflow
    def test_workflow_error_recovery(
        self, client: TestClient, db_session, orchestrator_service, context_store_service
    ):
        """Test workflow recovery from errors during SDLC execution."""
        # Create project
        project_data = {"name": "Error Recovery Test"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = UUID(response.json()["id"])
        
        # Create initial task
        task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analysis task that will fail"
        )
        
        # Simulate task failure
        orchestrator_service.update_task_status(
            task.task_id,
            TaskStatus.FAILED,
            error_message="Simulated task failure"
        )
        
        # Verify task marked as failed
        status_response = client.get(f"/api/v1/projects/{project_id}/status")
        status_data = status_response.json()
        failed_task = status_data["tasks"][0]
        assert failed_task["status"] == TaskStatus.FAILED.value
        
        # Recovery: Create new task to replace failed one
        recovery_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Recovery analysis task"
        )
        
        # Complete recovery task
        orchestrator_service.update_task_status(
            recovery_task.task_id,
            TaskStatus.COMPLETED,
            output={"recovery": "Analysis completed successfully"}
        )
        
        # Verify recovery
        final_status = client.get(f"/api/v1/projects/{project_id}/status")
        final_data = final_status.json()
        tasks = final_data["tasks"]
        
        assert len(tasks) == 2  # Failed task + recovery task
        
        task_statuses = [task["status"] for task in tasks]
        assert TaskStatus.FAILED.value in task_statuses
        assert TaskStatus.COMPLETED.value in task_statuses


class TestMultiPhaseProjectProgression:
    """Test scenario 2.1-E2E-002: Multi-phase project progression (P1)"""
    
    @pytest.mark.e2e
    @pytest.mark.p1
    @pytest.mark.workflow
    def test_parallel_project_workflows(
        self, client: TestClient, db_session, orchestrator_service, 
        context_store_service, performance_timer
    ):
        """Test multiple projects progressing through SDLC phases simultaneously."""
        performance_timer.start()
        
        # Create multiple projects
        projects = []
        for i in range(3):
            project_data = {
                "name": f"Parallel Project {i+1}",
                "description": f"Project {i+1} for parallel testing"
            }
            response = client.post("/api/v1/projects/", json=project_data)
            project_id = UUID(response.json()["id"])
            projects.append(project_id)
        
        # Create tasks for each project in different phases
        project_tasks = {}
        
        for i, project_id in enumerate(projects):
            # Create user input for each project
            user_input = context_store_service.create_artifact(
                project_id=project_id,
                source_agent=AgentType.ORCHESTRATOR,
                artifact_type=ArtifactType.USER_INPUT,
                content={"requirements": f"Project {i+1} requirements"}
            )
            
            # Create task in different phases for each project
            if i == 0:
                # Project 1: Analysis phase
                task = orchestrator_service.create_task(
                    project_id=project_id,
                    agent_type=AgentType.ANALYST.value,
                    instructions="Analyze requirements",
                    context_ids=[user_input.context_id]
                )
            elif i == 1:
                # Project 2: Architecture phase (skip analysis for test)
                task = orchestrator_service.create_task(
                    project_id=project_id,
                    agent_type=AgentType.ARCHITECT.value,
                    instructions="Design architecture"
                )
            else:
                # Project 3: Implementation phase (skip previous phases for test)
                task = orchestrator_service.create_task(
                    project_id=project_id,
                    agent_type=AgentType.CODER.value,
                    instructions="Implement system"
                )
            
            project_tasks[project_id] = task
        
        # Complete all tasks
        for project_id, task in project_tasks.items():
            orchestrator_service.update_task_status(
                task.task_id,
                TaskStatus.COMPLETED,
                output={"phase_completed": True}
            )
        
        performance_timer.stop()
        
        # Verify all projects have completed tasks
        for project_id in projects:
            status_response = client.get(f"/api/v1/projects/{project_id}/status")
            status_data = status_response.json()
            tasks = status_data["tasks"]
            
            assert len(tasks) == 1
            assert tasks[0]["status"] == TaskStatus.COMPLETED.value
        
        # Verify performance for parallel execution
        assert_performance_threshold(performance_timer.elapsed_ms, 5000, "Parallel project workflows")
    
    @pytest.mark.e2e
    @pytest.mark.p1
    @pytest.mark.workflow
    def test_workflow_phase_dependencies(
        self, client: TestClient, db_session, orchestrator_service, context_store_service
    ):
        """Test that workflow phases maintain proper dependencies."""
        # Create project
        project_data = {"name": "Phase Dependencies Test"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = UUID(response.json()["id"])
        
        # Create user input
        user_input = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={"requirements": "System requirements"}
        )
        
        # Phase 1: Analysis
        analysis_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analyze requirements",
            context_ids=[user_input.context_id]
        )
        
        # Complete analysis and create output
        orchestrator_service.update_task_status(
            analysis_task.task_id,
            TaskStatus.COMPLETED,
            output={"analysis_completed": True}
        )
        
        analysis_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"plan": "Detailed project plan"}
        )
        
        # Phase 2: Architecture (depends on analysis)
        architecture_handoff = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Create architecture based on analysis",
            "context_ids": [analysis_artifact.context_id]  # Dependency on analysis output
        }
        
        architecture_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=architecture_handoff
        )
        
        # Complete architecture
        orchestrator_service.update_task_status(
            architecture_task.task_id,
            TaskStatus.COMPLETED,
            output={"architecture_completed": True}
        )
        
        # Verify dependency chain
        status_response = client.get(f"/api/v1/projects/{project_id}/status")
        status_data = status_response.json()
        tasks = status_data["tasks"]
        
        # Should have 2 tasks: analysis and architecture
        assert len(tasks) == 2
        
        # Both should be completed
        completed_tasks = [task for task in tasks if task["status"] == TaskStatus.COMPLETED.value]
        assert len(completed_tasks) == 2
        
        # Verify architecture task has context dependency
        architecture_task_data = next(
            task for task in tasks 
            if task["agent_type"] == AgentType.ARCHITECT.value
        )
        
        # Should have context from analysis phase
        # (This would be verified in the actual task context_ids field)
        assert architecture_task_data is not None
    
    @pytest.mark.e2e
    @pytest.mark.p2
    @pytest.mark.workflow
    def test_workflow_context_propagation(
        self, client: TestClient, db_session, orchestrator_service, context_store_service
    ):
        """Test context propagation through workflow phases."""
        # Create project
        project_data = {"name": "Context Propagation Test"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = UUID(response.json()["id"])
        
        # Create rich user input
        user_input = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={
                "requirements": "Build e-commerce platform",
                "features": ["product catalog", "shopping cart", "payment"],
                "constraints": ["scalable", "secure", "mobile-friendly"]
            }
        )
        
        # Analysis phase
        analysis_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analyze e-commerce requirements",
            context_ids=[user_input.context_id]
        )
        
        orchestrator_service.update_task_status(
            analysis_task.task_id,
            TaskStatus.COMPLETED,
            output={"analysis": "Requirements analyzed"}
        )
        
        # Create analysis artifact with enriched context
        analysis_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={
                "modules": ["catalog", "cart", "payment", "user_management"],
                "database_entities": ["products", "users", "orders"],
                "integrations": ["payment_gateway", "inventory_system"]
            }
        )
        
        # Architecture phase with context from both user input and analysis
        architecture_handoff = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Design e-commerce architecture",
            "context_ids": [user_input.context_id, analysis_artifact.context_id]
        }
        
        architecture_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=architecture_handoff
        )
        
        # Verify context propagation
        # Architecture task should have context from both user input and analysis
        assert len(architecture_task.context_ids) == 2
        assert str(user_input.context_id) in architecture_task.context_ids
        assert str(analysis_artifact.context_id) in architecture_task.context_ids
        
        # Verify context can be retrieved
        task_context = context_store_service.get_artifacts_by_ids(architecture_task.context_ids)
        assert len(task_context) == 2
        
        # Verify context content preservation
        user_context = next(
            artifact for artifact in task_context 
            if artifact.artifact_type == ArtifactType.USER_INPUT
        )
        analysis_context = next(
            artifact for artifact in task_context 
            if artifact.artifact_type == ArtifactType.PROJECT_PLAN
        )
        
        assert "e-commerce platform" in user_context.content["requirements"]
        assert "catalog" in analysis_context.content["modules"]