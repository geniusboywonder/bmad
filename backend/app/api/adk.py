"""ADK (Agent Development Kit) API endpoints."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from datetime import datetime
import structlog

from app.database.connection import get_session
from adk_agent_factory import ADKAgentFactory
from app.services.adk_orchestration_service import ADKOrchestrationService
from app.tools.adk_tool_registry import ADKToolRegistry
from app.services.adk_handoff_service import ADKHandoffService
from app.settings import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/adk")

# Pydantic models for ADK endpoints
class ADKAgentCreateRequest(BaseModel):
    """Request model for creating ADK agents."""
    agent_type: str = Field(..., description="Type of agent to create")
    name: str = Field(..., description="Human-readable name for the agent")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific configuration parameters")
    tool_assignments: List[str] = Field(default_factory=list, description="List of tools to assign to this agent")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Percentage of requests to route to this ADK agent")

class ADKAgentResponse(BaseModel):
    """Response model for ADK agent information."""
    agent_id: str
    agent_type: str
    name: str
    status: str  # "initializing", "active", "inactive", "error"
    configuration: Dict[str, Any]
    tool_assignments: List[str]
    rollout_percentage: int
    created_at: datetime
    last_activity: Optional[datetime] = None

class ADKAgentDeleteResponse(BaseModel):
    """Response model for ADK agent deletion."""
    agent_id: str
    status: str
    message: str
    cleanup_completed: bool

class ADKRolloutConfigResponse(BaseModel):
    """Response model for ADK rollout configuration."""
    analyst_percentage: int
    architect_percentage: int
    coder_percentage: int
    tester_percentage: int
    deployer_percentage: int
    orchestrator_percentage: int
    last_updated: datetime
    consistency_hashing_enabled: bool

class ADKRolloutConfigUpdateRequest(BaseModel):
    """Request model for updating ADK rollout configuration."""
    analyst_percentage: int = Field(ge=0, le=100)
    architect_percentage: int = Field(ge=0, le=100)
    coder_percentage: int = Field(ge=0, le=100)
    tester_percentage: int = Field(ge=0, le=100)
    deployer_percentage: int = Field(ge=0, le=100)
    orchestrator_percentage: int = Field(ge=0, le=100)

class MultiAgentWorkflowRequest(BaseModel):
    """Request model for creating multi-agent workflows."""
    agents: List[str] = Field(..., description="List of agent IDs to include in the workflow")
    workflow_type: str = Field(..., description="Type of workflow to create")
    project_id: UUID
    initial_prompt: str = Field(..., description="Initial prompt to start the collaborative workflow")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional context data for the workflow")
    max_rounds: int = Field(default=10, ge=1, le=50, description="Maximum number of conversation rounds")

class MultiAgentWorkflowResponse(BaseModel):
    """Response model for multi-agent workflow information."""
    workflow_id: str
    status: str  # "created", "running", "completed", "failed", "terminated"
    agents: List[str]
    workflow_type: str
    project_id: UUID
    created_at: datetime
    current_round: int
    max_rounds: int

class MultiAgentWorkflowStatusResponse(BaseModel):
    """Response model for detailed multi-agent workflow status."""
    workflow_id: str
    status: str
    current_round: int
    max_rounds: int
    participants: List[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]
    artifacts_generated: List[Dict[str, Any]]
    estimated_completion_time: Optional[datetime] = None

class WorkflowTerminationResponse(BaseModel):
    """Response model for workflow termination."""
    workflow_id: str
    status: str
    message: str
    resources_cleaned: bool
    final_artifacts: Optional[Dict[str, Any]] = None

class CollaborativeAnalysisRequest(BaseModel):
    """Request model for collaborative analysis."""
    agents: List[str] = Field(..., description="List of agent IDs for collaborative analysis")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    project_id: UUID
    target_content: str = Field(..., description="Content to be analyzed")
    context_documents: List[str] = Field(default_factory=list, description="Additional context documents")

class CollaborativeAnalysisResponse(BaseModel):
    """Response model for collaborative analysis results."""
    analysis_id: str
    status: str
    analysis_type: str
    agents_contributed: List[str]
    consolidated_findings: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    confidence_score: float = Field(ge=0.0, le=1.0)
    completed_at: datetime

class AgentHandoffRequest(BaseModel):
    """Request model for creating agent handoffs."""
    from_agent: str = Field(..., description="Agent initiating the handoff")
    to_agent: str = Field(..., description="Agent receiving the handoff")
    phase: str = Field(..., description="Current workflow phase")
    instructions: str = Field(..., description="Detailed instructions for the receiving agent")
    expected_outputs: List[str] = Field(..., description="Expected deliverables from the handoff")
    priority: str = Field(default="medium", description="Priority level")
    context_ids: List[str] = Field(default_factory=list, description="IDs of context artifacts")
    project_id: UUID

class AgentHandoffResponse(BaseModel):
    """Response model for agent handoff information."""
    handoff_id: str
    status: str  # "pending", "accepted", "in_progress", "completed", "failed", "cancelled"
    from_agent: str
    to_agent: str
    phase: str
    priority: str
    created_at: datetime
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AgentHandoffStatusResponse(BaseModel):
    """Response model for detailed handoff status."""
    handoff_id: str
    status: str
    progress_percentage: int = Field(ge=0, le=100)
    current_step: str
    estimated_completion: Optional[datetime] = None
    artifacts_generated: List[Dict[str, Any]]
    issues_encountered: List[str]

class HandoffCancellationResponse(BaseModel):
    """Response model for handoff cancellation."""
    handoff_id: str
    status: str
    message: str
    resources_cleaned: bool

class HandoffExecutionResponse(BaseModel):
    """Response model for handoff execution results."""
    handoff_id: str
    execution_id: str
    status: str
    results: Dict[str, Any]
    artifacts_created: List[Dict[str, Any]]
    execution_time_seconds: float

class ADKWorkflowTemplateResponse(BaseModel):
    """Response model for ADK workflow templates."""
    template_id: str
    name: str
    description: str
    workflow_type: str
    required_agents: List[str]
    max_duration_minutes: int
    step_count: int
    success_criteria: List[str]

class ADKWorkflowTemplateDetailResponse(BaseModel):
    """Response model for detailed ADK workflow template information."""
    template_id: str
    name: str
    description: str
    workflow_type: str
    steps: List[Dict[str, Any]]
    required_agents: List[str]
    max_duration_minutes: int
    success_criteria: List[str]
    fallback_strategies: Dict[str, Any]

class AgentCompatibilityResponse(BaseModel):
    """Response model for agent compatibility assessment."""
    agent_type: str
    compatible: bool
    reason: str
    required_tools: List[str]
    available_tools: List[str]

class ADKToolResponse(BaseModel):
    """Response model for ADK tool information."""
    tool_name: str
    tool_type: str  # "function", "openapi", "specialized"
    description: str
    status: str  # "active", "inactive", "error"
    compatible_agents: List[str]
    last_used: Optional[datetime] = None
    usage_count: int

class ADKToolDetailResponse(BaseModel):
    """Response model for detailed ADK tool information."""
    tool_name: str
    tool_type: str
    description: str
    status: str
    parameters: Dict[str, Any]
    output_schema: Dict[str, Any]
    capabilities: List[str]
    risk_level: str  # "low", "medium", "high"
    requires_approval: bool
    usage_statistics: Dict[str, Any]

class ADKToolExecutionRequest(BaseModel):
    """Request model for ADK tool execution."""
    parameters: Dict[str, Any] = Field(..., description="Tool execution parameters")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for execution")
    project_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    bypass_approval: bool = Field(default=False, description="Bypass HITL approval for high-risk operations")

class ADKToolExecutionResponse(BaseModel):
    """Response model for ADK tool execution results."""
    execution_id: str
    status: str  # "success", "pending_approval", "failed", "error"
    result: Optional[Dict[str, Any]] = None
    execution_time_ms: int
    risk_level: str
    approval_required: bool
    approval_request_id: Optional[str] = None
    error_message: Optional[str] = None

class OpenAPIToolRegistrationRequest(BaseModel):
    """Request model for registering OpenAPI tools."""
    openapi_spec: Dict[str, Any] = Field(..., description="Complete OpenAPI specification")
    tool_name: str = Field(..., description="Unique name for the tool")
    description: str = Field(..., description="Human-readable description")
    base_url_override: Optional[str] = Field(default=None, description="Override the base URL from the spec")
    authentication_config: Optional[Dict[str, Any]] = Field(default=None, description="Authentication configuration")
    risk_assessment_overrides: Optional[Dict[str, Any]] = Field(default=None, description="Custom risk assessment rules")

class OpenAPIToolRegistrationResponse(BaseModel):
    """Response model for OpenAPI tool registration."""
    tool_name: str
    status: str
    endpoints_registered: int
    validation_errors: List[str]
    warnings: List[str]
    risk_assessment: Dict[str, Any]

class ADKToolSearchResult(BaseModel):
    """Response model for ADK tool search results."""
    tool_name: str
    tool_type: str
    description: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    compatible_agents: List[str]
    capabilities: List[str]

class ADKHealthResponse(BaseModel):
    """Response model for ADK system health status."""
    overall_status: str  # "healthy", "degraded", "unhealthy"
    components: Dict[str, Dict[str, Any]]
    system_metrics: Dict[str, Any]
    last_updated: datetime

class ADKMetricsResponse(BaseModel):
    """Response model for comprehensive ADK metrics."""
    time_range: str
    agent_metrics: Dict[str, Any]
    workflow_metrics: Dict[str, Any]
    tool_metrics: Dict[str, Any]
    handoff_metrics: Dict[str, Any]
    system_performance: Dict[str, Any]
    generated_at: datetime

# Dependency injection
def get_adk_agent_factory() -> ADKAgentFactory:
    """Get ADK agent factory instance."""
    return ADKAgentFactory()

def get_adk_orchestration_service() -> ADKOrchestrationService:
    """Get ADK orchestration service instance."""
    return ADKOrchestrationService()

def get_adk_tool_registry() -> ADKToolRegistry:
    """Get ADK tool registry instance."""
    return ADKToolRegistry()

def get_adk_handoff_service() -> ADKHandoffService:
    """Get ADK handoff service instance."""
    return ADKHandoffService()

# ADK Agent Management Endpoints
@router.post("/agents/create", response_model=ADKAgentResponse, tags=["adk"])
async def create_adk_agent(
    request: ADKAgentCreateRequest,
    agent_factory: ADKAgentFactory = Depends(get_adk_agent_factory)
):
    """Create a new ADK-powered agent instance with specified configuration."""
    try:
        agent = await agent_factory.create_agent(
            agent_type=request.agent_type,
            name=request.name,
            configuration=request.configuration,
            tool_assignments=request.tool_assignments,
            rollout_percentage=request.rollout_percentage
        )
        return ADKAgentResponse(**agent.dict())
    except Exception as e:
        logger.error("Failed to create ADK agent", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@router.get("/agents/{agent_id}", response_model=ADKAgentResponse, tags=["adk"])
async def get_adk_agent(
    agent_id: str = Path(..., description="Agent ID"),
    agent_factory: ADKAgentFactory = Depends(get_adk_agent_factory)
):
    """Get details of a specific ADK agent instance."""
    try:
        agent = await agent_factory.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return ADKAgentResponse(**agent.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get ADK agent", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")

@router.delete("/agents/{agent_id}", response_model=ADKAgentDeleteResponse, tags=["adk"])
async def delete_adk_agent(
    agent_id: str = Path(..., description="Agent ID"),
    agent_factory: ADKAgentFactory = Depends(get_adk_agent_factory)
):
    """Delete an ADK agent instance and clean up resources."""
    try:
        result = await agent_factory.delete_agent(agent_id)
        return ADKAgentDeleteResponse(**result)
    except Exception as e:
        logger.error("Failed to delete ADK agent", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

@router.get("/agents", response_model=List[ADKAgentResponse], tags=["adk"])
async def list_adk_agents(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    agent_factory: ADKAgentFactory = Depends(get_adk_agent_factory)
):
    """List all active ADK agent instances with their status and configuration."""
    try:
        agents = await agent_factory.list_agents(
            agent_type=agent_type,
            status=status
        )
        return [ADKAgentResponse(**agent.dict()) for agent in agents]
    except Exception as e:
        logger.error("Failed to list ADK agents", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

# ADK Rollout Configuration Endpoints
@router.get("/rollout/config", response_model=ADKRolloutConfigResponse, tags=["adk"])
async def get_adk_rollout_config(
    agent_factory: ADKAgentFactory = Depends(get_adk_agent_factory)
):
    """Get current ADK rollout configuration and percentages for each agent type."""
    try:
        config = await agent_factory.get_rollout_config()
        return ADKRolloutConfigResponse(**config)
    except Exception as e:
        logger.error("Failed to get ADK rollout config", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get rollout config: {str(e)}")

@router.post("/rollout/config", response_model=ADKRolloutConfigResponse, tags=["adk"])
async def update_adk_rollout_config(
    request: ADKRolloutConfigUpdateRequest,
    agent_factory: ADKAgentFactory = Depends(get_adk_agent_factory)
):
    """Update ADK rollout percentages for different agent types."""
    try:
        config = await agent_factory.update_rollout_config(
            analyst_percentage=request.analyst_percentage,
            architect_percentage=request.architect_percentage,
            coder_percentage=request.coder_percentage,
            tester_percentage=request.tester_percentage,
            deployer_percentage=request.deployer_percentage,
            orchestrator_percentage=request.orchestrator_percentage
        )
        return ADKRolloutConfigResponse(**config)
    except Exception as e:
        logger.error("Failed to update ADK rollout config", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update rollout config: {str(e)}")

# Multi-Agent Orchestration Endpoints
@router.post("/orchestration/workflows", response_model=MultiAgentWorkflowResponse, tags=["adk-orchestration"])
async def create_multi_agent_workflow(
    request: MultiAgentWorkflowRequest,
    orchestration_service: ADKOrchestrationService = Depends(get_adk_orchestration_service)
):
    """Create a collaborative workflow with multiple ADK agents."""
    try:
        workflow = await orchestration_service.create_workflow(
            agents=request.agents,
            workflow_type=request.workflow_type,
            project_id=str(request.project_id),
            initial_prompt=request.initial_prompt,
            context_data=request.context_data,
            max_rounds=request.max_rounds
        )
        return MultiAgentWorkflowResponse(**workflow)
    except Exception as e:
        logger.error("Failed to create multi-agent workflow", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@router.get("/orchestration/workflows", response_model=List[MultiAgentWorkflowResponse], tags=["adk-orchestration"])
async def list_active_workflows(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    orchestration_service: ADKOrchestrationService = Depends(get_adk_orchestration_service)
):
    """List all active multi-agent workflows with their current status."""
    try:
        workflows = await orchestration_service.list_workflows(project_id=str(project_id) if project_id else None)
        return [MultiAgentWorkflowResponse(**wf) for wf in workflows]
    except Exception as e:
        logger.error("Failed to list workflows", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

@router.get("/orchestration/workflows/{workflow_id}", response_model=MultiAgentWorkflowStatusResponse, tags=["adk-orchestration"])
async def get_workflow_status(
    workflow_id: str = Path(..., description="Workflow ID"),
    orchestration_service: ADKOrchestrationService = Depends(get_adk_orchestration_service)
):
    """Get detailed status and progress of a specific multi-agent workflow."""
    try:
        status = await orchestration_service.get_workflow_status(workflow_id)
        if not status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return MultiAgentWorkflowStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow status", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@router.delete("/orchestration/workflows/{workflow_id}", response_model=WorkflowTerminationResponse, tags=["adk-orchestration"])
async def terminate_workflow(
    workflow_id: str = Path(..., description="Workflow ID"),
    orchestration_service: ADKOrchestrationService = Depends(get_adk_orchestration_service)
):
    """Terminate an active multi-agent workflow and clean up resources."""
    try:
        result = await orchestration_service.terminate_workflow(workflow_id)
        return WorkflowTerminationResponse(**result)
    except Exception as e:
        logger.error("Failed to terminate workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to terminate workflow: {str(e)}")

@router.post("/orchestration/analysis", response_model=CollaborativeAnalysisResponse, tags=["adk-orchestration"])
async def execute_collaborative_analysis(
    request: CollaborativeAnalysisRequest,
    orchestration_service: ADKOrchestrationService = Depends(get_adk_orchestration_service)
):
    """Execute a collaborative analysis using multiple ADK agents."""
    try:
        analysis = await orchestration_service.execute_analysis(
            agents=request.agents,
            analysis_type=request.analysis_type,
            project_id=str(request.project_id),
            target_content=request.target_content,
            context_documents=request.context_documents
        )
        return CollaborativeAnalysisResponse(**analysis)
    except Exception as e:
        logger.error("Failed to execute collaborative analysis", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute analysis: {str(e)}")

# Agent Handoff Endpoints
@router.post("/handoffs", response_model=AgentHandoffResponse, tags=["adk-handoff"])
async def create_agent_handoff(
    request: AgentHandoffRequest,
    handoff_service: ADKHandoffService = Depends(get_adk_handoff_service)
):
    """Create a structured handoff between two ADK agents."""
    try:
        handoff = await handoff_service.create_handoff(
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            phase=request.phase,
            instructions=request.instructions,
            expected_outputs=request.expected_outputs,
            priority=request.priority,
            context_ids=request.context_ids,
            project_id=str(request.project_id)
        )
        return AgentHandoffResponse(**handoff)
    except Exception as e:
        logger.error("Failed to create agent handoff", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create handoff: {str(e)}")

@router.get("/handoffs", response_model=List[AgentHandoffResponse], tags=["adk-handoff"])
async def list_active_handoffs(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    handoff_service: ADKHandoffService = Depends(get_adk_handoff_service)
):
    """List all active agent handoffs with their current status."""
    try:
        handoffs = await handoff_service.list_handoffs(project_id=str(project_id) if project_id else None)
        return [AgentHandoffResponse(**hf) for hf in handoffs]
    except Exception as e:
        logger.error("Failed to list handoffs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list handoffs: {str(e)}")

@router.get("/handoffs/{handoff_id}", response_model=AgentHandoffStatusResponse, tags=["adk-handoff"])
async def get_handoff_status(
    handoff_id: str = Path(..., description="Handoff ID"),
    handoff_service: ADKHandoffService = Depends(get_adk_handoff_service)
):
    """Get detailed status and progress of a specific agent handoff."""
    try:
        status = await handoff_service.get_handoff_status(handoff_id)
        if not status:
            raise HTTPException(status_code=404, detail="Handoff not found")
        return AgentHandoffStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get handoff status", handoff_id=handoff_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get handoff status: {str(e)}")

@router.delete("/handoffs/{handoff_id}", response_model=HandoffCancellationResponse, tags=["adk-handoff"])
async def cancel_handoff(
    handoff_id: str = Path(..., description="Handoff ID"),
    handoff_service: ADKHandoffService = Depends(get_adk_handoff_service)
):
    """Cancel an active agent handoff and notify involved agents."""
    try:
        result = await handoff_service.cancel_handoff(handoff_id)
        return HandoffCancellationResponse(**result)
    except Exception as e:
        logger.error("Failed to cancel handoff", handoff_id=handoff_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cancel handoff: {str(e)}")

@router.post("/handoffs/{handoff_id}/execute", response_model=HandoffExecutionResponse, tags=["adk-handoff"])
async def execute_handoff(
    handoff_id: str = Path(..., description="Handoff ID"),
    handoff_service: ADKHandoffService = Depends(get_adk_handoff_service)
):
    """Execute an agent handoff by transferring context and initiating the receiving agent's work."""
    try:
        result = await handoff_service.execute_handoff(handoff_id)
        return HandoffExecutionResponse(**result)
    except Exception as e:
        logger.error("Failed to execute handoff", handoff_id=handoff_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute handoff: {str(e)}")

# ADK Workflow Templates Endpoints
@router.get("/templates", response_model=List[ADKWorkflowTemplateResponse], tags=["adk-templates"])
async def list_adk_workflow_templates():
    """List all available ADK workflow templates with their metadata."""
    try:
        # This would typically come from a template registry service
        templates = [
            {
                "template_id": "requirements-analysis",
                "name": "Requirements Analysis",
                "description": "Collaborative requirements gathering and analysis",
                "workflow_type": "analysis",
                "required_agents": ["analyst", "architect"],
                "max_duration_minutes": 60,
                "step_count": 5,
                "success_criteria": ["Requirements documented", "Stakeholder alignment achieved"]
            },
            {
                "template_id": "system-design",
                "name": "System Design",
                "description": "Collaborative system architecture and design",
                "workflow_type": "design",
                "required_agents": ["architect", "coder"],
                "max_duration_minutes": 90,
                "step_count": 7,
                "success_criteria": ["Architecture documented", "Design validated"]
            }
        ]
        return [ADKWorkflowTemplateResponse(**template) for template in templates]
    except Exception as e:
        logger.error("Failed to list workflow templates", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

@router.get("/templates/{template_id}", response_model=ADKWorkflowTemplateDetailResponse, tags=["adk-templates"])
async def get_adk_workflow_template(
    template_id: str = Path(..., description="Template ID")
):
    """Get detailed information about a specific ADK workflow template."""
    try:
        # Mock template data - in real implementation this would come from a service
        templates = {
            "requirements-analysis": {
                "template_id": "requirements-analysis",
                "name": "Requirements Analysis",
                "description": "Collaborative requirements gathering and analysis",
                "workflow_type": "analysis",
                "steps": [
                    {"step": 1, "description": "Gather initial requirements", "agent": "analyst"},
                    {"step": 2, "description": "Analyze requirements", "agent": "analyst"},
                    {"step": 3, "description": "Design system architecture", "agent": "architect"},
                    {"step": 4, "description": "Validate design", "agent": "architect"},
                    {"step": 5, "description": "Document final requirements", "agent": "analyst"}
                ],
                "required_agents": ["analyst", "architect"],
                "max_duration_minutes": 60,
                "success_criteria": ["Requirements documented", "Stakeholder alignment achieved"],
                "fallback_strategies": {"timeout": "escalate", "failure": "retry"}
            }
        }

        if template_id not in templates:
            raise HTTPException(status_code=404, detail="Template not found")

        return ADKWorkflowTemplateDetailResponse(**templates[template_id])
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

@router.get("/templates/{template_id}/agents", response_model=List[AgentCompatibilityResponse], tags=["adk-templates"])
async def get_template_compatible_agents(
    template_id: str = Path(..., description="Template ID")
):
    """Get list of agents compatible with a specific ADK workflow template."""
    try:
        # Mock compatibility data
        compatibility_data = {
            "analyst": {"compatible": True, "reason": "Primary requirements analysis agent", "required_tools": ["analysis"], "available_tools": ["analysis", "documentation"]},
            "architect": {"compatible": True, "reason": "System design and architecture agent", "required_tools": ["design"], "available_tools": ["design", "modeling"]},
            "coder": {"compatible": False, "reason": "Not required for requirements analysis", "required_tools": [], "available_tools": ["coding", "testing"]}
        }

        return [AgentCompatibilityResponse(agent_type=agent_type, **data) for agent_type, data in compatibility_data.items()]
    except Exception as e:
        logger.error("Failed to get compatible agents", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get compatible agents: {str(e)}")

# ADK Tool Management Endpoints
@router.get("/tools", response_model=List[ADKToolResponse], tags=["adk-tools"])
async def list_available_adk_tools(
    tool_type: Optional[str] = Query(None, description="Filter by tool type"),
    agent_type: Optional[str] = Query(None, description="Filter by compatible agent type"),
    tool_registry: ADKToolRegistry = Depends(get_adk_tool_registry)
):
    """List all available ADK tools with their capabilities and status."""
    try:
        tools = await tool_registry.list_tools(
            tool_type=tool_type,
            agent_type=agent_type
        )
        return [ADKToolResponse(**tool) for tool in tools]
    except Exception as e:
        logger.error("Failed to list ADK tools", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@router.get("/tools/{tool_name}", response_model=ADKToolDetailResponse, tags=["adk-tools"])
async def get_adk_tool_details(
    tool_name: str = Path(..., description="Tool name"),
    tool_registry: ADKToolRegistry = Depends(get_adk_tool_registry)
):
    """Get detailed information about a specific ADK tool including capabilities and usage."""
    try:
        tool = await tool_registry.get_tool_details(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return ADKToolDetailResponse(**tool)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get tool details", tool_name=tool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get tool details: {str(e)}")

@router.post("/tools/{tool_name}/execute", response_model=ADKToolExecutionResponse, tags=["adk-tools"])
async def execute_adk_tool(
    request: ADKToolExecutionRequest,
    tool_name: str = Path(..., description="Tool name"),
    tool_registry: ADKToolRegistry = Depends(get_adk_tool_registry)
):
    """Execute an ADK tool with enterprise controls and HITL oversight."""
    try:
        result = await tool_registry.execute_tool(
            tool_name=tool_name,
            parameters=request.parameters,
            context_data=request.context_data,
            project_id=str(request.project_id) if request.project_id else None,
            task_id=str(request.task_id) if request.task_id else None,
            bypass_approval=request.bypass_approval
        )
        return ADKToolExecutionResponse(**result)
    except Exception as e:
        logger.error("Failed to execute ADK tool", tool_name=tool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute tool: {str(e)}")

@router.post("/tools/openapi/register", response_model=OpenAPIToolRegistrationResponse, tags=["adk-tools"])
async def register_openapi_tool(
    request: OpenAPIToolRegistrationRequest,
    tool_registry: ADKToolRegistry = Depends(get_adk_tool_registry)
):
    """Register a new OpenAPI specification as an ADK tool."""
    try:
        result = await tool_registry.register_openapi_tool(
            openapi_spec=request.openapi_spec,
            tool_name=request.tool_name,
            description=request.description,
            base_url_override=request.base_url_override,
            authentication_config=request.authentication_config,
            risk_assessment_overrides=request.risk_assessment_overrides
        )
        return OpenAPIToolRegistrationResponse(**result)
    except Exception as e:
        logger.error("Failed to register OpenAPI tool", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to register tool: {str(e)}")

@router.get("/tools/search", response_model=List[ADKToolSearchResult], tags=["adk-tools"])
async def search_adk_tools(
    query: str = Query(..., description="Search query"),
    tool_type: Optional[str] = Query(None, description="Filter by tool type"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    tool_registry: ADKToolRegistry = Depends(get_adk_tool_registry)
):
    """Search for ADK tools by name, description, or capabilities."""
    try:
        results = await tool_registry.search_tools(
            query=query,
            tool_type=tool_type,
            limit=limit
        )
        return [ADKToolSearchResult(**result) for result in results]
    except Exception as e:
        logger.error("Failed to search ADK tools", query=query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to search tools: {str(e)}")

# ADK System Monitoring Endpoints
@router.get("/health", response_model=ADKHealthResponse, tags=["adk"])
async def get_adk_system_health():
    """Get comprehensive health status of the ADK system including agents, tools, and orchestration services."""
    try:
        # Mock health data - in real implementation this would aggregate from all services
        health_data = {
            "overall_status": "healthy",
            "components": {
                "agent_factory": {
                    "status": "healthy",
                    "active_agents": 5,
                    "error_count": 0
                },
                "orchestration_service": {
                    "status": "healthy",
                    "active_workflows": 2,
                    "completed_workflows": 15
                },
                "tool_registry": {
                    "status": "healthy",
                    "total_tools": 25,
                    "active_tools": 20
                },
                "handoff_service": {
                    "status": "healthy",
                    "active_handoffs": 3,
                    "completed_handoffs": 12
                }
            },
            "system_metrics": {
                "uptime_seconds": 3600,
                "memory_usage_mb": 512,
                "cpu_usage_percent": 45.2,
                "active_connections": 8
            },
            "last_updated": datetime.utcnow()
        }
        return ADKHealthResponse(**health_data)
    except Exception as e:
        logger.error("Failed to get ADK system health", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")

@router.get("/metrics", response_model=ADKMetricsResponse, tags=["adk"])
async def get_adk_metrics(
    time_range: str = Query("24h", description="Time range for metrics")
):
    """Get usage metrics and performance statistics for ADK components."""
    try:
        # Mock metrics data - in real implementation this would come from monitoring services
        metrics_data = {
            "time_range": time_range,
            "agent_metrics": {
                "total_agents": 8,
                "active_agents": 5,
                "agent_utilization": 0.75,
                "average_response_time": 2.3
            },
            "workflow_metrics": {
                "total_workflows": 25,
                "completed_workflows": 20,
                "average_completion_time": 45.5,
                "success_rate": 0.92
            },
            "tool_metrics": {
                "total_tools": 25,
                "active_tools": 20,
                "total_executions": 150,
                "average_execution_time": 1.8
            },
            "handoff_metrics": {
                "total_handoffs": 18,
                "completed_handoffs": 15,
                "average_handoff_time": 5.2,
                "success_rate": 0.88
            },
            "system_performance": {
                "cpu_usage": 45.2,
                "memory_usage": 512,
                "disk_usage": 2.1,
                "network_io": 150
            },
            "generated_at": datetime.utcnow()
        }
        return ADKMetricsResponse(**metrics_data)
    except Exception as e:
        logger.error("Failed to get ADK metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
