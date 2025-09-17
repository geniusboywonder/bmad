"""HITL service package - refactored into focused, single-responsibility services."""

from .hitl_core import HitlCore
from .trigger_processor import TriggerProcessor
from .phase_gate_manager import PhaseGateManager
from .response_processor import ResponseProcessor
from .validation_engine import ValidationEngine

# For backward compatibility, expose HitlService as an alias to HitlCore
HitlService = HitlCore

__all__ = [
    "HitlService",  # Backward compatibility
    "HitlCore",
    "TriggerProcessor",
    "PhaseGateManager",
    "ResponseProcessor",
    "ValidationEngine"
]