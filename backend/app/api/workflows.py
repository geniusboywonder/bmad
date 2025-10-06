"""
Workflow API Endpoints for BMAD Core Template System

✅ BMAD RADICAL SIMPLIFICATION (October 2025):
- Consolidated 11 workflow services → 3 unified services (73% reduction)
- Unified execution engine, state management, and event dispatching
- Preserved all functionality through intelligent consolidation

This module provides REST API endpoints for workflow and template management,
enabling frontend applications to interact with the simplified BMAD Core system.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from ..services.template_service import TemplateService
from ..services.workflow_service_consolidated import ConsolidatedWorkflowService
from ..services.agent_team_service import AgentTeamService
from ..utils.yaml_parser import YAMLParser
from ..database.connection import get_session

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

# Initialize services that don't require database session
template_service = TemplateService()
agent_team_service = AgentTeamService()

# Workflow service will be created per request with database session
yaml_parser = YAMLParser()


# Pydantic models for API requests/responses
class TemplateRenderRequest(BaseModel):
    """Request model for template rendering."""
    template_id: str = Field(..., description="ID of the template to render")
    variables: Dict[str, Any] = Field(..., description="Variable values for substitution")
    output_format: Optional[str] = Field(None, description="Desired output format")

    model_config = ConfigDict(
        json_encoders={
            dict: lambda v: v
        }
    )


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution."""
    workflow_id: str = Field(..., description="ID of the workflow to execute")
    project_id: str = Field(..., description="ID of the project")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data")

    model_config = ConfigDict(
        json_encoders={
            dict: lambda v: v
        }
    )


class WorkflowAdvanceRequest(BaseModel):
    """Request model for advancing workflow execution."""
    execution_id: str = Field(..., description="ID of the workflow execution")
    current_agent: str = Field(..., description="Name of the agent that completed")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data from agent")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(
        json_encoders={
            dict: lambda v: v
        }
    )


class HandoffGenerationRequest(BaseModel):
    """Request model for handoff generation."""
    execution_id: str = Field(..., description="ID of the workflow execution")
    from_agent: str = Field(..., description="Agent handing off")
    to_agent: str = Field(..., description="Agent receiving handoff")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context")

    model_config = ConfigDict(
        json_encoders={
            dict: lambda v: v
        }
    )


# API Endpoints

@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_templates():
    """
    List all available templates.

    Returns:
        List of template metadata
    """
    try:
        templates = template_service.list_available_templates()
        return templates
    except Exception as e:
        logger.error(f"Failed to list templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.get("/templates/{template_id}")
async def get_template_metadata(template_id: str):
    """
    Get metadata for a specific template.

    Args:
        template_id: ID of the template

    Returns:
        Template metadata
    """
    try:
        metadata = template_service.get_template_metadata(template_id)
        if metadata is None:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template metadata for '{template_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get template metadata: {str(e)}")


@router.post("/templates/render")
async def render_template(request: TemplateRenderRequest):
    """
    Render a template with provided variables.

    Args:
        request: Template render request

    Returns:
        Rendered template content
    """
    try:
        # Validate template variables first
        validation = template_service.validate_template_variables(
            request.template_id,
            request.variables
        )

        if not validation["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Template validation failed",
                    "validation": validation
                }
            )

        # Render template
        rendered_content = template_service.render_template(
            request.template_id,
            request.variables,
            request.output_format
        )

        return {
            "template_id": request.template_id,
            "rendered_content": rendered_content,
            "variables_used": request.variables,
            "output_format": request.output_format or "markdown"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to render template '{request.template_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to render template: {str(e)}")


@router.post("/templates/validate")
async def validate_template_variables(request: TemplateRenderRequest):
    """
    Validate variables for a template without rendering.

    Args:
        request: Template validation request

    Returns:
        Validation results
    """
    try:
        validation = template_service.validate_template_variables(
            request.template_id,
            request.variables
        )
        return validation
    except Exception as e:
        logger.error(f"Failed to validate template '{request.template_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate template: {str(e)}")


@router.get("/workflows", response_model=List[Dict[str, Any]])
async def list_workflows(db: Session = Depends(get_session)):
    """
    List all available workflows.

    Returns:
        List of workflow metadata
    """
    try:
        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        workflows = workflow_service.list_available_workflows()
        return workflows
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


@router.get("/workflows/{workflow_id}")
async def get_workflow_metadata(workflow_id: str, db: Session = Depends(get_session)):
    """
    Get metadata for a specific workflow.

    Args:
        workflow_id: ID of the workflow

    Returns:
        Workflow metadata
    """
    try:
        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        metadata = workflow_service.get_workflow_metadata(workflow_id)
        if metadata is None:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow metadata for '{workflow_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow metadata: {str(e)}")


@router.post("/workflows/execute")
async def start_workflow_execution(request: WorkflowExecutionRequest, db: Session = Depends(get_session)):
    """
    Start execution of a workflow.

    Args:
        request: Workflow execution request

    Returns:
        Workflow execution details
    """
    try:
        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        execution = await workflow_service.start_workflow_execution(
            request.workflow_id,
            request.project_id,
            request.context_data
        )

        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": execution.project_id,
            "status": execution.status.value,
            "started_at": execution.started_at,
            "next_agent": workflow_service.get_next_agent(execution.execution_id),
            "total_steps": len(execution.steps)
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start workflow execution for '{request.workflow_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow execution: {str(e)}")


@router.post("/workflows/advance")
async def advance_workflow_execution(request: WorkflowAdvanceRequest, db: Session = Depends(get_session)):
    """
    Advance workflow execution to the next step.

    Args:
        request: Workflow advance request

    Returns:
        Updated execution status
    """
    try:
        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        execution = workflow_service.advance_workflow_execution(
            request.execution_id,
            request.current_agent,
            request.result,
            request.error_message
        )

        return {
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "completed_at": execution.completed_at,
            "next_agent": workflow_service.get_next_agent(request.execution_id),
            "error_message": execution.error_message
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to advance workflow execution '{request.execution_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to advance workflow execution: {str(e)}")


@router.get("/executions/{execution_id}")
async def get_workflow_execution_status(execution_id: str, db: Session = Depends(get_session)):
    """
    Get the current status of a workflow execution.

    Args:
        execution_id: ID of the workflow execution

    Returns:
        Execution status information
    """
    try:
        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        status = workflow_service.get_workflow_execution_status(execution_id)
        if status is None:
            raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status for '{execution_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")


@router.post("/executions/{execution_id}/handoff")
async def generate_handoff(execution_id: str, request: HandoffGenerationRequest, db: Session = Depends(get_session)):
    """
    Generate a handoff for agent transition.

    Args:
        execution_id: ID of the workflow execution
        request: Handoff generation request

    Returns:
        Generated handoff information
    """
    try:
        # Override execution_id from URL if not provided in request
        request.execution_id = execution_id

        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        handoff = workflow_service.generate_handoff(
            request.execution_id,
            request.from_agent,
            request.to_agent,
            request.context_data
        )

        if handoff is None:
            raise HTTPException(
                status_code=400,
                detail=f"Could not generate handoff from '{request.from_agent}' to '{request.to_agent}'"
            )

        return {
            "handoff_id": handoff.handoff_id,
            "from_agent": handoff.from_agent,
            "to_agent": handoff.to_agent,
            "phase": handoff.phase,
            "instructions": handoff.instructions,
            "expected_outputs": handoff.expected_outputs,
            "priority": handoff.priority.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate handoff for execution '{execution_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate handoff: {str(e)}")


@router.get("/executions/{execution_id}/validate")
async def validate_workflow_execution(execution_id: str, db: Session = Depends(get_session)):
    """
    Validate the current state of a workflow execution.

    Args:
        execution_id: ID of the workflow execution

    Returns:
        Validation results
    """
    try:
        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        validation = workflow_service.validate_workflow_execution(execution_id)
        return validation
    except Exception as e:
        logger.error(f"Failed to validate execution '{execution_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate execution: {str(e)}")


@router.get("/teams", response_model=List[Dict[str, Any]])
async def list_agent_teams():
    """
    List all available agent teams.

    Returns:
        List of team metadata
    """
    try:
        teams = agent_team_service.list_available_teams()
        return teams
    except Exception as e:
        logger.error(f"Failed to list agent teams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list agent teams: {str(e)}")


@router.get("/teams/{team_id}")
async def get_team_metadata(team_id: str):
    """
    Get metadata for a specific agent team.

    Args:
        team_id: ID of the team

    Returns:
        Team metadata
    """
    try:
        metadata = agent_team_service.get_team_metadata(team_id)
        if metadata is None:
            raise HTTPException(status_code=404, detail=f"Team '{team_id}' not found")
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team metadata for '{team_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get team metadata: {str(e)}")


@router.get("/teams/compatible/{workflow_id}")
async def get_compatible_teams(workflow_id: str):
    """
    Get agent teams compatible with a specific workflow.

    Args:
        workflow_id: ID of the workflow

    Returns:
        List of compatible teams
    """
    try:
        teams = agent_team_service.get_compatible_teams(workflow_id)
        return [
            {
                "team_id": team.team_id,
                "name": team.name,
                "description": team.description,
                "agent_types": team.get_agent_types(),
                "agent_count": len(team.agents)
            }
            for team in teams
        ]
    except Exception as e:
        logger.error(f"Failed to get compatible teams for workflow '{workflow_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compatible teams: {str(e)}")


@router.get("/teams/{team_id}/validate")
async def validate_team_composition(team_id: str):
    """
    Validate the composition of an agent team.

    Args:
        team_id: ID of the team

    Returns:
        Validation results
    """
    try:
        validation = agent_team_service.validate_team_composition(team_id)
        return validation
    except Exception as e:
        logger.error(f"Failed to validate team '{team_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate team: {str(e)}")


@router.post("/cache/clear")
async def clear_all_caches(db: Session = Depends(get_session)):
    """
    Clear all service caches.

    Returns:
        Cache clearing status
    """
    try:
        template_service.clear_cache()
        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        workflow_service.clear_cache()
        agent_team_service.clear_cache()

        return {
            "message": "All caches cleared successfully",
            "services": ["template_service", "workflow_service", "agent_team_service"]
        }
    except Exception as e:
        logger.error(f"Failed to clear caches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear caches: {str(e)}")


@router.get("/health")
async def get_bmad_core_health(db: Session = Depends(get_session)):
    """
    Get health status of BMAD Core services.

    Returns:
        Health status information
    """
    try:
        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        health_status = {
            "status": "healthy",
            "services": {
                "template_service": "healthy",
                "workflow_service": "healthy",
                "agent_team_service": "healthy"
            },
            "cache_status": {
                "template_cache_enabled": template_service._cache_enabled,
                "workflow_cache_enabled": workflow_service._cache_enabled,
                "team_cache_enabled": agent_team_service._cache_enabled
            }
        }

        # Check if base directories exist
        if not template_service.template_base_path.exists():
            health_status["services"]["template_service"] = "degraded"
            health_status["status"] = "degraded"

        if not workflow_service.workflow_base_path.exists():
            health_status["services"]["workflow_service"] = "degraded"
            health_status["status"] = "degraded"

        if not agent_team_service.team_base_path.exists():
            health_status["services"]["agent_team_service"] = "degraded"
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Failed to get BMAD Core health: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "services": {
                "template_service": "unknown",
                "workflow_service": "unknown",
                "agent_team_service": "unknown"
            }
        }


@router.get("/{workflow_id}/deliverables")
async def get_workflow_deliverables(workflow_id: str, db: Session = Depends(get_session)):
    """
    Get expected deliverables/artifacts from workflow YAML definition.

    This endpoint parses the workflow YAML file and extracts all artifacts
    that agents are expected to create, organized by SDLC stage.

    Args:
        workflow_id: ID of the workflow (e.g., 'greenfield-fullstack')

    Returns:
        Dictionary mapping SDLC stages to expected deliverables
    """
    try:
        # Load workflow definition
        workflow_service = ConsolidatedWorkflowService(db, workflow_base_path="app/workflows")
        workflow = workflow_service.load_workflow(workflow_id)

        # Map of SDLC stages to agents
        stage_agents = {
            "analyze": ["analyst", "pm"],
            "design": ["architect", "ux-expert", "ux"],
            "build": ["developer", "dev", "sm", "scrum"],
            "validate": ["tester", "qa"],
            "launch": ["deployer"]
        }

        # Extract deliverables from workflow sequence
        deliverables_by_stage = {
            "analyze": [],
            "design": [],
            "build": [],
            "validate": [],
            "launch": []
        }

        for step in workflow.sequence:
            # Get deliverable name from 'creates' field
            deliverable_name = None
            if hasattr(step, 'creates') and step.creates:
                # Remove file extension and clean up name
                deliverable_name = step.creates.replace('.md', '').replace('_', ' ').replace('-', ' ').title()
            elif hasattr(step, 'action') and step.action:
                # Use action as deliverable for non-creation steps
                deliverable_name = step.action.replace('_', ' ').title()

            if not deliverable_name:
                continue

            # Determine which stage this deliverable belongs to
            agent = getattr(step, 'agent', None)
            if agent is None:
                # Skip non-agent steps (like project_setup_guidance)
                continue

            agent_lower = agent.lower()
            assigned_stage = None

            for stage, agents in stage_agents.items():
                if any(agent_name in agent_lower for agent_name in agents):
                    assigned_stage = stage
                    break

            if not assigned_stage:
                # Default to analyze if agent not recognized
                assigned_stage = "analyze"

            # Add deliverable to stage
            notes = getattr(step, 'notes', '')
            deliverable = {
                "name": deliverable_name,
                "agent": agent.title(),
                "description": notes.split('.')[0] if notes else f"Create {deliverable_name}",
                "optional": getattr(step, 'optional', False) or ('optional' in notes.lower() if notes else False)
            }

            deliverables_by_stage[assigned_stage].append(deliverable)

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "deliverables": deliverables_by_stage
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    except Exception as e:
        logger.error(f"Failed to get deliverables for workflow '{workflow_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow deliverables: {str(e)}")
