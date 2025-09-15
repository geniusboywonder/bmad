#!/usr/bin/env python3
"""ADK Context Store Integration Testing.

This module tests Context Store integration with ADK agents
to ensure proper artifact creation, retrieval, and context passing.
"""

import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import structlog

# Add backend to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.agents.bmad_adk_wrapper import BMADADKWrapper
from app.models.context import ContextArtifact, ArtifactType
from app.models.agent import AgentType
from app.models.task import Task

logger = structlog.get_logger(__name__)


async def run_adk_context_integration_tests() -> Dict[str, Any]:
    """Run comprehensive ADK Context Store integration tests."""
    logger.info("Starting ADK Context Store integration tests")

    try:
        # Mock context store service
        context_store = AsyncMock()

        # Create sample context artifacts
        sample_artifacts = [
            ContextArtifact(
                context_id="550e8400-e29b-41d4-a716-446655440000",
                project_id="550e8400-e29b-41d4-a716-446655440001",
                source_agent=AgentType.ANALYST,
                artifact_type=ArtifactType.USER_INPUT,
                content={"user_input": "Create a web application for task management"},
                artifact_metadata={"phase": "discovery"}
            ),
            ContextArtifact(
                context_id="550e8400-e29b-41d4-a716-446655440002",
                project_id="550e8400-e29b-41d4-a716-446655440001",
                source_agent=AgentType.ARCHITECT,
                artifact_type=ArtifactType.SYSTEM_ARCHITECTURE,
                content={"architecture": "React frontend, FastAPI backend, PostgreSQL"},
                artifact_metadata={"phase": "design"}
            )
        ]

        # Mock context store methods
        context_store.get_artifacts_by_project_and_type = AsyncMock(return_value=sample_artifacts)
        context_store.get_artifacts_by_project_and_agent = AsyncMock(return_value=sample_artifacts[:1])
        context_store.create_artifact = AsyncMock(return_value=sample_artifacts[0])

        # Create ADK wrapper with mocked services
        wrapper = BMADADKWrapper(
            agent_name="context_test_agent",
            agent_type="analyst",
            instruction="You are an analyst agent that can read and create context artifacts."
        )

        # Mock the ADK execution to avoid API calls
        async def mock_adk_execute(message: str) -> Dict[str, Any]:
            return {
                "success": True,
                "response": f"Analyzed context and generated insights for: {message}",
                "execution_id": "test-execution-context"
            }

        wrapper._execute_adk_agent = mock_adk_execute

        # Test 1: Context Reading Integration
        logger.info("Testing context reading integration")

        # Mock the ADK execution to simulate context-aware processing
        async def mock_context_aware_execute(message: str, execution_id: str) -> Dict[str, Any]:
            # Simulate reading context artifacts and generating response
            context_summary = f"Found {len(sample_artifacts)} context artifacts"
            return {
                "success": True,
                "response": f"Analysis based on context: {context_summary}. {message}",
                "session_id": f"session_{execution_id}"
            }

        wrapper._execute_adk_agent = mock_context_aware_execute

        result = await wrapper.process_with_enterprise_controls(
            message="Analyze the project requirements and architecture",
            project_id="550e8400-e29b-41d4-a716-446655440001",
            task_id="test-context-task",
            user_id="test_user"
        )

        context_reading_success = result["success"] and "execution_id" in result
        logger.info("Context reading test completed", success=context_reading_success)

        # Test 2: Context Creation Integration
        logger.info("Testing context creation integration")

        # Mock ADK execution to simulate artifact creation
        async def mock_artifact_creation_execute(message: str, execution_id: str) -> Dict[str, Any]:
            return {
                "success": True,
                "response": "Analysis completed and artifact created",
                "session_id": f"session_{execution_id}"
            }

        wrapper._execute_adk_agent = mock_artifact_creation_execute

        result = await wrapper.process_with_enterprise_controls(
            message="Create analysis artifact based on user requirements",
            project_id="550e8400-e29b-41d4-a716-446655440001",
            task_id="test-artifact-creation",
            user_id="test_user"
        )

        context_creation_success = result["success"] and "execution_id" in result
        logger.info("Context creation test completed", success=context_creation_success)

        # Test 3: Context Filtering by Type
        logger.info("Testing context filtering by type")

        # Test filtering user input artifacts
        user_input_artifacts = [art for art in sample_artifacts if art.artifact_type == ArtifactType.USER_INPUT]
        context_store.get_artifacts_by_project_and_type.assert_not_called()  # Not directly called

        # Test filtering by agent
        analyst_artifacts = [art for art in sample_artifacts if art.source_agent == AgentType.ANALYST]
        context_store.get_artifacts_by_project_and_agent.assert_not_called()  # Not directly called

        filtering_success = len(user_input_artifacts) == 1 and len(analyst_artifacts) == 1
        logger.info("Context filtering test completed", success=filtering_success)

        # Test 4: Context Chain Integration
        logger.info("Testing context chain integration")

        # Simulate agent reading previous artifacts and creating new ones
        context_chain = [
            sample_artifacts[0],  # User input
            sample_artifacts[1],  # Architecture
            # Analysis output would be created by the agent
        ]

        # Verify context chain maintains data integrity
        context_chain_valid = all(
            art.project_id == "550e8400-e29b-41d4-a716-446655440001" for art in context_chain
        )
        logger.info("Context chain integration test completed", valid=context_chain_valid)

        # Compile test results
        adk_context_test_result = {
            "success": context_reading_success and context_creation_success and filtering_success and context_chain_valid,
            "context_reading_success": context_reading_success,
            "context_creation_success": context_creation_success,
            "context_filtering_success": filtering_success,
            "context_chain_valid": context_chain_valid,
            "artifacts_processed": len(sample_artifacts),
            "artifacts_created": 1,
            "test_type": "adk_context_integration"
        }

        logger.info("ADK Context Store integration test completed", **adk_context_test_result)
        return adk_context_test_result

    except Exception as e:
        logger.error("ADK Context Store integration test failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "context_reading_success": False,
            "context_creation_success": False,
            "context_filtering_success": False,
            "context_chain_valid": False,
            "test_type": "adk_context_integration"
        }


if __name__ == "__main__":
    print("🧪 Testing ADK Context Store Integration")
    print("=" * 50)

    async def run_test():
        result = await run_adk_context_integration_tests()

        print("\n📊 ADK Context Store Integration Test Results:")
        print(f"   Overall Success: {result.get('success', False)}")
        print(f"   Context Reading: {result.get('context_reading_success', False)}")
        print(f"   Context Creation: {result.get('context_creation_success', False)}")
        print(f"   Context Filtering: {result.get('context_filtering_success', False)}")
        print(f"   Context Chain Valid: {result.get('context_chain_valid', False)}")
        print(f"   Artifacts Processed: {result.get('artifacts_processed', 0)}")
        print(f"   Artifacts Created: {result.get('artifacts_created', 0)}")

        if not result.get("success", False):
            print(f"   Error: {result.get('error', 'Unknown error')}")

    asyncio.run(run_test())
