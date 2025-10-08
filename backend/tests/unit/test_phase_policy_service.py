"""
Unit tests for the PhasePolicyService.
"""

import unittest
from unittest.mock import Mock
from uuid import uuid4

from app.services.orchestrator.phase_policy_service import PhasePolicyService

class TestPhasePolicyService(unittest.TestCase):

    def setUp(self):
        self.project_manager = Mock()
        self.policy_service = PhasePolicyService(self.project_manager)

    def test_evaluate_allowed(self):
        project_id = uuid4()
        self.project_manager.get_current_phase.return_value = "discovery"

        decision = self.policy_service.evaluate(
            project_id, "analyst", "gather requirements"
        )

        self.assertEqual(decision["status"], "allowed")

    def test_evaluate_denied_agent_not_allowed(self):
        project_id = uuid4()
        self.project_manager.get_current_phase.return_value = "discovery"

        decision = self.policy_service.evaluate(
            project_id, "coder", "implement feature"
        )

        self.assertEqual(decision["status"], "denied")
        self.assertEqual(decision["reason_code"], "agent_not_allowed")

    def test_evaluate_needs_clarification_prompt_mismatch(self):
        project_id = uuid4()
        self.project_manager.get_current_phase.return_value = "discovery"

        decision = self.policy_service.evaluate(
            project_id, "analyst", "write code"
        )

        self.assertEqual(decision["status"], "needs_clarification")
        self.assertEqual(decision["reason_code"], "prompt_mismatch")

    def test_evaluate_override(self):
        project_id = uuid4()
        self.project_manager.get_current_phase.return_value = "discovery"

        decision = self.policy_service.evaluate(
            project_id, "coder", "implement feature", override=True
        )

        self.assertEqual(decision["status"], "allowed")

if __name__ == "__main__":
    unittest.main()
