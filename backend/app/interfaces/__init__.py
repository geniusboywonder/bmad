"""Service interfaces for dependency injection and SOLID compliance."""

# Orchestrator interfaces
from .orchestrator_interface import IOrchestratorService
from .project_lifecycle_interface import IProjectLifecycleManager
from .agent_coordinator_interface import IAgentCoordinator
from .workflow_integrator_interface import IWorkflowIntegrator
from .handoff_manager_interface import IHandoffManager
from .status_tracker_interface import IStatusTracker
from .context_manager_interface import IContextManager

# HITL interfaces
from .hitl_interface import (
    IHitlCore,
    ITriggerProcessor,
    IResponseProcessor,
    IPhaseGateManager,
    IValidationEngine
)

# Workflow interfaces
from .workflow_interface import (
    IExecutionEngine,
    IStateManager,
    IEventDispatcher,
    ISdlcOrchestrator
)

# AutoGen interfaces
from .autogen_interface import (
    IAutoGenCore,
    IAgentFactory,
    IConversationManager
)

# Template interfaces
from .template_interface import (
    ITemplateCore,
    ITemplateLoader,
    ITemplateRenderer
)

__all__ = [
    # Orchestrator interfaces
    "IOrchestratorService",
    "IProjectLifecycleManager",
    "IAgentCoordinator",
    "IWorkflowIntegrator",
    "IHandoffManager",
    "IStatusTracker",
    "IContextManager",

    # HITL interfaces
    "IHitlCore",
    "ITriggerProcessor",
    "IResponseProcessor",
    "IPhaseGateManager",
    "IValidationEngine",

    # Workflow interfaces
    "IExecutionEngine",
    "IStateManager",
    "IEventDispatcher",
    "ISdlcOrchestrator",

    # AutoGen interfaces
    "IAutoGenCore",
    "IAgentFactory",
    "IConversationManager",

    # Template interfaces
    "ITemplateCore",
    "ITemplateLoader",
    "ITemplateRenderer"
]