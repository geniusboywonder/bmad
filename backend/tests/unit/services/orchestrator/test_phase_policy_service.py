import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.orchestrator.phase_policy_service import PhasePolicyService, PolicyDecision

class TestPhasePolicyService(unittest.TestCase):

    def setUp(self):
        self.db_session = MagicMock(spec=Session)
        self.policy_service = PhasePolicyService(self.db_session)
        self.project_id = uuid4()

    @patch('app.services.orchestrator.phase_policy_service.ProjectManager')
    def test_evaluate_allowed(self, MockProjectManager):
        """Test that an agent is allowed when in the correct phase."""
        # Arrange
        mock_project_manager = MockProjectManager.return_value
        mock_project_manager.get_current_phase.return_value = "analyze"
        self.policy_service.project_manager = mock_project_manager

        # Act
        decision = self.policy_service.evaluate(self.project_id, "analyst")

        # Assert
        self.assertEqual(decision.status, "allowed")
        self.assertEqual(decision.current_phase, "analyze")
        self.assertIn("analyst", decision.allowed_agents)

    @patch('app.services.orchestrator.phase_policy_service.ProjectManager')
    def test_evaluate_denied(self, MockProjectManager):
        """Test that an agent is denied when in the wrong phase."""
        # Arrange
        mock_project_manager = MockProjectManager.return_value
        mock_project_manager.get_current_phase.return_value = "analyze"
        self.policy_service.project_manager = mock_project_manager

        # Act
        decision = self.policy_service.evaluate(self.project_id, "coder")

        # Assert
        self.assertEqual(decision.status, "denied")
        self.assertEqual(decision.reason_code, "agent_not_allowed")
        self.assertEqual(decision.current_phase, "analyze")
        self.assertNotIn("coder", decision.allowed_agents)

    @patch('app.services.orchestrator.phase_policy_service.ProjectManager')
    def test_evaluate_no_active_phase(self, MockProjectManager):
        """Test behavior when the project has no active phase."""
        # Arrange
        mock_project_manager = MockProjectManager.return_value
        mock_project_manager.get_current_phase.return_value = None
        self.policy_service.project_manager = mock_project_manager

        # Act
        decision = self.policy_service.evaluate(self.project_id, "analyst")

        # Assert
        self.assertEqual(decision.status, "denied")
        self.assertEqual(decision.reason_code, "no_active_phase")

    @patch('app.services.orchestrator.phase_policy_service.ProjectManager')
    def test_evaluate_no_policy_for_phase(self, MockProjectManager):
        """Test behavior when there is no policy for the current phase."""
        # Arrange
        mock_project_manager = MockProjectManager.return_value
        mock_project_manager.get_current_phase.return_value = "unknown_phase"
        self.policy_service.project_manager = mock_project_manager

        # Act
        decision = self.policy_service.evaluate(self.project_id, "analyst")

        # Assert
        self.assertEqual(decision.status, "denied")
        self.assertEqual(decision.reason_code, "no_policy_for_phase")

    def test_load_policies(self):
        """Test that the policy configuration is loaded correctly."""
        self.assertIsNotNone(self.policy_service.policies)
        self.assertIn("analyze", self.policy_service.policies)
        self.assertIn("allowed_agents", self.policy_service.policies["analyze"])

if __name__ == "__main__":
    unittest.main()