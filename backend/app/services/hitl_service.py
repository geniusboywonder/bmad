"""
HITL Service - Backward compatibility alias module.

This module maintains backward compatibility while the HITL service has been
refactored into focused, single-responsibility services following SOLID principles.
"""

from sqlalchemy.orm import Session

# Import the refactored HITL core
from .hitl.hitl_core import HitlCore

# Import trigger manager and its classes
from .hitl_trigger_manager import HitlTriggerManager, HITLTriggerManager, OversightLevel, HitlTriggerCondition

# For backward compatibility, expose HitlService as an alias to HitlCore
HitlService = HitlCore

# Also expose individual services for direct access if needed
from .hitl import (
    TriggerProcessor,
    PhaseGateManager,
    ResponseProcessor,
    ValidationEngine
)

__all__ = [
    "HitlService",
    "HitlCore",
    "TriggerProcessor",
    "PhaseGateManager",
    "ResponseProcessor",
    "ValidationEngine",
    "HitlTriggerManager",
    "HITLTriggerManager",
    "OversightLevel",
    "HitlTriggerCondition"
]