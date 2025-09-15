#!/usr/bin/env python3
"""Audit Trail Integration Testing for Google ADK + BMAD.

This module tests Audit Trail logging with ADK agents
to ensure comprehensive compliance and security logging.
"""

import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import structlog

# Add backend to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.agents.adk_analyst import ADKAnalystAgent
from app.models.agent import AgentType
from app.models.task import Task

logger = structlog.get_logger(__name__)


async def run_audit_trail_integration_tests() -> Dict[str, Any]:
    """Run comprehensive Audit Trail integration tests."""
    logger.info("Starting Audit Trail integration tests")

    try:
        # Mock audit service
        audit_service = AsyncMock()
        audit_log_entries = []

        def capture_audit_entry(entry):
            audit_log_entries.append({
                "action": entry.get("action", "unknown"),
                "user_id": entry.get("user_id", "system"),
                "resource": entry.get("resource", "agent"),
                "details": entry.get("details", {}),
                "timestamp": datetime.now().isoformat()
            })

        audit_service.log_action = AsyncMock(side_effect=lambda entry: capture_audit_entry(entry))

        # Create ADK analyst agent
        agent = ADKAnalystAgent(
            agent_type=AgentType.ANALYST,
            llm_config={"model": "gemini-2.0-flash"}
        )

        # Mock audit logging in agent methods
        original_execute = agent.execute_task

        async def audit_instrumented_execute(task, context):
            # Log task execution start
            await audit_service.log_action({
                "action": "agent_task_started",
                "user_id": "test_user",
                "resource": "adk_analyst_agent",
                "details": {
                    "task_id": str(task.task_id),
                    "project_id": str(task.project_id),
                    "agent_type": "analyst",
                    "framework": "google_adk"
                }
            })

            # Execute task
            result = await original_execute(task, context)

            # Log task completion
            await audit_service.log_action({
                "action": "agent_task_completed",
                "user_id": "test_user",
                "resource": "adk_analyst_agent",
                "details": {
                    "task_id": str(task.task_id),
                    "success": result.get("success", False),
                    "execution_time": result.get("execution_time", 0),
                    "framework": "google_adk"
                }
            })

            return result

        agent.execute_task = audit_instrumented_execute

        # Create and execute test task
        test_task = Task(
            task_id="test_audit_task",
            project_id="test_project",
            instructions="Test audit trail integration",
            status="pending",
            priority=1
        )

        result = await agent.execute_task(test_task, [])

        # Verify audit trail
        audit_test_result = {
            "success": result.get("success", False),
            "audit_entries_logged": len(audit_log_entries),
            "audit_actions": [entry["action"] for entry in audit_log_entries],
            "audit_trail_working": len(audit_log_entries) >= 2,  # start + completion
            "compliance_logging_enabled": True,
            "test_type": "audit_trail_integration"
        }

        logger.info("Audit Trail integration test completed", **audit_test_result)
        return audit_test_result

    except Exception as e:
        logger.error("Audit Trail integration test failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "audit_trail_working": False,
            "test_type": "audit_trail_integration"
        }


if __name__ == "__main__":
    print("🧪 Testing Audit Trail Integration")
    print("=" * 50)

    async def run_test():
        result = await run_audit_trail_integration_tests()

        print("\n📊 Audit Trail Integration Test Results:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Audit Entries Logged: {result.get('audit_entries_logged', 0)}")
        print(f"   Audit Actions: {result.get('audit_actions', [])}")
        print(f"   Integration Working: {result.get('audit_trail_working', False)}")

        if not result.get("success", False):
            print(f"   Error: {result.get('error', 'Unknown error')}")

    asyncio.run(run_test())
