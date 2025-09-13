"""Pydantic data models for BotArmy backend."""

from .task import Task, TaskStatus
from .agent import AgentStatus, AgentType
from .context import ContextArtifact, ArtifactType
from .hitl import HitlRequest, HitlStatus, HitlAction
from .handoff import HandoffSchema
from .workflow import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    WorkflowExecutionStep,
    WorkflowType,
    WorkflowExecutionState
)
from .template import (
    TemplateDefinition,
    TemplateSection,
    TemplateOutput,
    TemplateWorkflow,
    TemplateSectionType,
    TemplateOutputFormat,
    TemplateWorkflowMode
)

__all__ = [
    "Task",
    "TaskStatus",
    "AgentStatus",
    "AgentType",
    "ContextArtifact",
    "ArtifactType",
    "HitlRequest",
    "HitlStatus",
    "HitlAction",
    "HandoffSchema",
    # Workflow models
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowExecution",
    "WorkflowExecutionStep",
    "WorkflowType",
    "WorkflowExecutionState",
    # Template models
    "TemplateDefinition",
    "TemplateSection",
    "TemplateOutput",
    "TemplateWorkflow",
    "TemplateSectionType",
    "TemplateOutputFormat",
    "TemplateWorkflowMode",
]
