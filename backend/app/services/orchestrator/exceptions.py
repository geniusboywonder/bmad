from app.services.orchestrator.phase_policy_service import PolicyDecision

class PolicyViolationException(Exception):
    """Custom exception for policy violations."""
    def __init__(self, decision: PolicyDecision):
        self.decision = decision
        super().__init__(decision.message)