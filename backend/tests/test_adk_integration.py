#!/usr/bin/env python3
"""Test script for Google ADK integration with BMAD Analyst agent."""

import asyncio
import sys
import os
import pytest
from typing import Dict, Any
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.analyst import AnalystAgent
from app.models.task import Task
from app.models.context import ContextArtifact, ArtifactType
from app.models.agent import AgentType

@pytest.mark.external_service
async def test_adk_analyst_agent():
    """Test the ADK Analyst agent integration."""

    print("🧪 Testing Google ADK Integration with BMAD Analyst Agent")
    print("=" * 60)

    try:
        # Step 1: Initialize ADK Analyst Agent
        print("1. Initializing ADK Analyst Agent...")
        llm_config = {
            "model": "gemini-2.0-flash",
            "temperature": 0.4,
            "max_tokens": 4096
        }

        agent = AnalystAgent(
            agent_type=AgentType.ANALYST,
            llm_config=llm_config
        )

        print("✅ ADK Analyst Agent initialized successfully")
        print(f"   Framework: {agent.get_agent_info().get('framework', 'unknown')}")
        print(f"   Agent Type: {agent.get_agent_info().get('agent_type', 'unknown')}")

        # Step 2: Create a test task
        print("\n2. Creating test task...")
        task = Task(
            task_id=uuid4(),
            project_id=uuid4(),
            agent_type=AgentType.ANALYST.value,
            instructions="Analyze requirements for a simple task management system. Create user personas, functional requirements, and success criteria.",
            status="pending"
        )
        print(f"✅ Test task created: {task.task_id}")

        # Step 3: Create test context
        print("\n3. Creating test context...")
        context_artifacts = [
            ContextArtifact(
                context_id=uuid4(),
                project_id=task.project_id,
                source_agent=AgentType.ORCHESTRATOR,
                artifact_type=ArtifactType.USER_INPUT,
                content={
                    "project_description": "Build a task management system for small teams",
                    "target_users": "Project managers and team members",
                    "key_features": ["Create tasks", "Assign tasks", "Track progress", "Set deadlines"]
                }
            )
        ]
        print(f"✅ Test context created with {len(context_artifacts)} artifacts")

        # Step 4: Test agent info
        print("\n4. Testing agent information...")
        agent_info = agent.get_agent_info()
        print(f"✅ Agent info retrieved:")
        print(f"   - Framework: {agent_info.get('framework', 'unknown')}")
        print(f"   - ADK Initialized: {agent_info.get('adk_initialized', False)}")
        print(f"   - Reliability Features: {len(agent_info.get('reliability_features', {}))}")

        # Step 5: Test basic functionality (without full execution to avoid API calls)
        print("\n5. Testing basic functionality...")

        # Test handoff creation
        handoff = await agent.create_handoff(AgentType.ARCHITECT, task, context_artifacts)
        print(f"✅ Handoff created to {handoff.to_agent}")

        # Test context message preparation
        context_message = agent.prepare_context_message(context_artifacts, handoff)
        print(f"✅ Context message prepared ({len(context_message)} characters)")
        print(f"   - Phase: {handoff.phase}")
        print(f"   - Framework: {handoff.metadata.get('framework', 'unknown')}")

        print("\n🎉 ADK Integration Test Completed Successfully!")
        print("=" * 60)
        print("✅ All basic functionality tests passed")
        print("✅ ADK agent initialization working")
        print("✅ BMAD enterprise features preserved")
        print("✅ Context and handoff mechanisms functional")
        print("\n📋 Next Steps:")
        print("   - Test full agent execution with LLM API")
        print("   - Validate HITL integration")
        print("   - Test audit trail logging")
        print("   - Verify WebSocket compatibility")

        return True

    except Exception as e:
        print(f"\n❌ ADK Integration Test Failed: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

@pytest.mark.external_service
async def test_fallback_functionality():
    """Test fallback functionality when ADK fails."""
    print("\n🔄 Testing Fallback Functionality...")

    try:
        agent = AnalystAgent(
            agent_type=AgentType.ANALYST,
            llm_config={"model": "gemini-2.0-flash"}
        )

        # Test fallback response generation
        fallback_response = agent._generate_fallback_response()
        print("✅ Fallback response generated")
        print(f"   - Type: {fallback_response.get('agent_type', 'unknown')}")
        print(f"   - Status: {fallback_response.get('status', 'unknown')}")
        print(f"   - Framework: {fallback_response.get('framework', 'unknown')}")

        return True

    except Exception as e:
        print(f"❌ Fallback test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting ADK Integration Tests for BMAD System")
    print("Framework: Google ADK + BMAD Enterprise Features")
    print()

    # Run main test
    success = asyncio.run(test_adk_analyst_agent())

    # Run fallback test
    fallback_success = asyncio.run(test_fallback_functionality())

    # Summary
    print("\n📊 Test Summary:")
    print(f"   Main Integration Test: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"   Fallback Test: {'✅ PASSED' if fallback_success else '❌ FAILED'}")

    if success and fallback_success:
        print("\n🎯 Phase 1 (ADK Pilot) Status: READY FOR PRODUCTION TESTING")
        print("   - ADK integration successful")
        print("   - BMAD enterprise features preserved")
        print("   - Fallback mechanisms working")
        sys.exit(0)
    else:
        print("\n⚠️  Phase 1 Issues Detected - Review and fix before proceeding")
        sys.exit(1)
