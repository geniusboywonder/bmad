"""Orchestrator agent for managing SDLC workflow coordination."""

from typing import Dict, Any, List
from uuid import uuid4
import json
import structlog

from app.agents.base_agent import BaseAgent
from app.models.task import Task
from app.models.context import ContextArtifact
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType

logger = structlog.get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """Orchestrator agent managing 6-phase SDLC workflow with AutoGen integration.
    
    The Orchestrator serves as the central coordinator managing the workflow:
    - Discovery → Plan → Design → Build → Validate → Launch
    - Context passing management via HandoffSchema
    - Conflict resolution between agent outputs
    - State management and progress tracking
    - Time-conscious orchestration with front-loaded detail gathering
    """
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any]):
        """Initialize Orchestrator agent with workflow phases."""
        super().__init__(agent_type, llm_config)
        
        self.workflow_phases = [
            "discovery", "plan", "design", "build", "validate", "launch"
        ]
        
        # Enhanced LLM config for workflow coordination
        self.llm_config.update({
            "model": llm_config.get("model", "gpt-4o-mini"),
            "temperature": 0.3,  # Lower temperature for consistent coordination
        })
        
        # Initialize AutoGen agent
        self._initialize_autogen_agent()
        
        logger.info("Orchestrator agent initialized with SDLC workflow phases",
                   phases=self.workflow_phases)
    
    def _create_system_message(self) -> str:
        """Create Orchestrator-specific system message for AutoGen."""
        return """You are the Orchestrator managing multi-agent SDLC workflows.

Your primary responsibilities:
- Coordinate 6-phase workflow: Discovery → Plan → Design → Build → Validate → Launch
- Manage structured handoffs between agents using clear instructions
- Resolve conflicts between agent outputs after automated attempts
- Maintain project state and progress tracking throughout execution
- Create HITL requests for critical decisions and conflicts
- Front-load detail gathering to minimize iterative refinements

Workflow Management Principles:
- Each phase must be completed before moving to the next
- Gather comprehensive requirements early to avoid rework
- Ensure proper context passing between agents
- Monitor progress and identify blockers quickly
- Escalate to humans when automated resolution fails

Communication Style:
- Provide clear, structured instructions for handoffs
- Include specific deliverables and success criteria
- Reference previous context appropriately
- Maintain consistent project vocabulary and standards

Always respond with structured JSON containing:
- Current phase information
- Next steps and agent assignments
- Context requirements and handoff details
- Progress status and any issues identified"""
    
    async def execute_task(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute orchestrator task with workflow coordination.
        
        Args:
            task: Task to execute with orchestration instructions
            context: Context artifacts from previous workflow stages
            
        Returns:
            Orchestration result with workflow decisions and next steps
        """
        logger.info("Orchestrator executing workflow coordination task",
                   task_id=task.task_id,
                   context_count=len(context))
        
        try:
            # Prepare workflow context message
            context_message = self._prepare_orchestration_context(task, context)
            
            # Execute with LLM reliability features
            raw_response = await self._execute_with_reliability(context_message, task)
            
            # Parse and structure orchestration response
            orchestration_result = self._parse_orchestration_response(raw_response, task)
            
            logger.info("Orchestrator task completed successfully",
                       task_id=task.task_id,
                       current_phase=orchestration_result.get("current_phase"),
                       next_agent=orchestration_result.get("next_agent"))
            
            return {
                "success": True,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "output": orchestration_result,
                "workflow_decisions": orchestration_result.get("workflow_decisions", {}),
                "next_steps": orchestration_result.get("next_steps", []),
                "context_used": [str(artifact.context_id) for artifact in context]
            }
            
        except Exception as e:
            logger.error("Orchestrator task execution failed",
                        task_id=task.task_id,
                        error=str(e))
            
            return {
                "success": False,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "error": str(e),
                "fallback_phase": "recovery",
                "context_used": [str(artifact.context_id) for artifact in context]
            }
    
    async def create_handoff(self, to_agent: AgentType, task: Task, 
                           context: List[ContextArtifact]) -> HandoffSchema:
        """Create structured handoff to another agent with workflow context.
        
        Args:
            to_agent: Target agent type for the handoff
            task: Current task being handed off
            context: Context artifacts to pass along
            
        Returns:
            HandoffSchema with workflow-aware handoff information
        """
        # Determine current phase based on target agent
        phase_mapping = {
            AgentType.ANALYST: "discovery",
            AgentType.ARCHITECT: "design", 
            AgentType.CODER: "build",
            AgentType.TESTER: "validate",
            AgentType.DEPLOYER: "launch"
        }
        
        current_phase = phase_mapping.get(to_agent, "unknown")
        
        # Create phase-specific instructions
        instructions = self._create_phase_instructions(to_agent, current_phase, context)
        
        # Define expected outputs based on agent and phase
        expected_outputs = self._get_expected_outputs(to_agent, current_phase)
        
        handoff = HandoffSchema(
            handoff_id=uuid4(),
            from_agent=self.agent_type.value,
            to_agent=to_agent.value,
            project_id=task.project_id,
            phase=current_phase,
            context_ids=[artifact.context_id for artifact in context],
            instructions=instructions,
            expected_outputs=expected_outputs,
            priority=1,  # High priority for orchestrator handoffs
            metadata={
                "workflow_phase": current_phase,
                "orchestrator_task_id": str(task.task_id),
                "handoff_reason": "workflow_progression",
                "context_summary": self._summarize_context(context)
            }
        )
        
        logger.info("Orchestrator handoff created",
                   to_agent=to_agent.value,
                   phase=current_phase,
                   context_count=len(context))
        
        return handoff
    
    def _prepare_orchestration_context(self, task: Task, context: List[ContextArtifact]) -> str:
        """Prepare context message for orchestration decisions."""
        
        context_parts = [
            "ORCHESTRATION TASK:",
            f"Task: {task.instructions}",
            "",
            "CURRENT PROJECT STATE:",
            f"Project ID: {task.project_id}",
            f"Task ID: {task.task_id}",
            "",
            "AVAILABLE CONTEXT ARTIFACTS:",
        ]
        
        if not context:
            context_parts.append("- No context artifacts available (this may be project initiation)")
        else:
            for i, artifact in enumerate(context):
                context_parts.extend([
                    f"",
                    f"Artifact {i+1} from {artifact.source_agent} ({artifact.artifact_type}):",
                    f"Content: {str(artifact.content)[:500]}..." if len(str(artifact.content)) > 500 else f"Content: {artifact.content}",
                ])
        
        context_parts.extend([
            "",
            "ORCHESTRATION REQUIREMENTS:",
            "- Analyze current project state and context",
            "- Determine next workflow phase and agent assignment",
            "- Create specific instructions for the next agent",
            "- Identify any blockers or issues requiring HITL intervention",
            "- Provide clear success criteria and deliverables",
            "",
            "Respond with JSON containing your orchestration decisions."
        ])
        
        return "\n".join(context_parts)
    
    def _parse_orchestration_response(self, raw_response: str, task: Task) -> Dict[str, Any]:
        """Parse and structure the orchestration response."""
        
        try:
            # Try to parse as JSON
            if raw_response.strip().startswith('{'):
                response_data = json.loads(raw_response)
            else:
                # Extract JSON from text response
                import re
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    response_data = json.loads(json_match.group())
                else:
                    # Fallback: create structured response
                    response_data = self._create_fallback_orchestration(raw_response)
            
            # Ensure required fields are present
            structured_response = {
                "orchestration_type": "workflow_coordination",
                "current_phase": response_data.get("current_phase", "unknown"),
                "next_agent": response_data.get("next_agent", "analyst"),
                "workflow_decisions": response_data.get("workflow_decisions", {}),
                "next_steps": response_data.get("next_steps", []),
                "instructions": response_data.get("instructions", "Proceed with next phase"),
                "success_criteria": response_data.get("success_criteria", []),
                "issues_identified": response_data.get("issues_identified", []),
                "hitl_required": response_data.get("hitl_required", False),
                "context_summary": response_data.get("context_summary", ""),
                "project_status": response_data.get("project_status", "in_progress")
            }
            
            return structured_response
            
        except Exception as e:
            logger.warning("Failed to parse orchestration response, using fallback",
                          error=str(e))
            return self._create_fallback_orchestration(raw_response)
    
    def _create_fallback_orchestration(self, raw_response: str) -> Dict[str, Any]:
        """Create fallback orchestration response when parsing fails."""
        
        return {
            "orchestration_type": "fallback_coordination",
            "current_phase": "discovery",
            "next_agent": "analyst",
            "workflow_decisions": {
                "decision": "proceed_with_analysis",
                "reasoning": "Using fallback orchestration due to response parsing issues"
            },
            "next_steps": [
                "Initiate requirements analysis",
                "Gather project specifications", 
                "Define success criteria"
            ],
            "instructions": "Begin with comprehensive requirements analysis based on available context",
            "success_criteria": ["Complete requirements document", "Stakeholder approval"],
            "issues_identified": ["Response parsing failed - may need human review"],
            "hitl_required": True,
            "context_summary": f"Fallback response generated. Original: {raw_response[:200]}...",
            "project_status": "needs_review"
        }
    
    def _create_phase_instructions(self, to_agent: AgentType, phase: str, 
                                 context: List[ContextArtifact]) -> str:
        """Create phase-specific instructions for target agent."""
        
        instruction_templates = {
            AgentType.ANALYST: f"""As the Analyst, your task is to conduct comprehensive requirements analysis for the {phase} phase.

CRITICAL: Your FIRST task MUST be to create an Implementation Plan using the analyst-implementation-plan template. This is mandatory before any requirements analysis begins.

Based on the provided context, please:
1. **FIRST**: Create comprehensive Implementation Plan for requirements analysis phase
2. Analyze user requirements and business objectives
3. Create detailed user personas and use cases
4. Define functional and non-functional requirements
5. Identify stakeholder needs and constraints
6. Generate a comprehensive Product Requirements Document (PRD)

Focus on gathering complete information to minimize rework in later phases.""",
            
            AgentType.ARCHITECT: f"""As the Architect, your task is to design the technical solution for the {phase} phase.

CRITICAL: Your FIRST task MUST be to create an Implementation Plan using the architect-implementation-plan template. This is mandatory before any architecture work begins.

Based on the requirements analysis, please:
1. **FIRST**: Create comprehensive Implementation Plan for architecture and design phase
2. Design system architecture and technical specifications
3. Create detailed API specifications and data models
4. Define technology stack and architectural decisions
5. Identify technical risks and mitigation strategies
6. Generate detailed technical specifications with clear deliverables

Ensure your design supports scalability and maintainability.""",
            
            AgentType.CODER: f"""As the Developer, your task is to implement the solution for the {phase} phase.

CRITICAL: Your FIRST task MUST be to create an Implementation Plan using the coder-implementation-plan template. This is mandatory before any code development begins.

Based on the architectural specifications, please:
1. **FIRST**: Create comprehensive Implementation Plan for development and coding phase
2. Generate production-ready code following best practices
3. Implement all features according to specifications
4. Include comprehensive error handling and validation
5. Write unit tests for all generated code
6. Ensure code follows project standards and conventions

Focus on clean, maintainable, and well-documented code.""",
            
            AgentType.TESTER: f"""As the Tester, your task is to validate the implementation for the {phase} phase.

CRITICAL: Your FIRST task MUST be to create an Implementation Plan using the tester-implementation-plan template. This is mandatory before any testing begins.

Based on the code and requirements, please:
1. **FIRST**: Create comprehensive Implementation Plan for testing and quality assurance phase
2. Create comprehensive test plans covering all scenarios
3. Execute functional and integration testing
4. Validate against original requirements and specifications
5. Identify and document any bugs or issues
6. Verify code quality and performance characteristics

Ensure thorough testing coverage and quality validation.""",
            
            AgentType.DEPLOYER: f"""As the Deployer, your task is to handle deployment for the {phase} phase.

CRITICAL: Your FIRST task MUST be to create an Implementation Plan using the deployer-implementation-plan template. This is mandatory before any deployment work begins.

Based on the tested code, please:
1. **FIRST**: Create comprehensive Implementation Plan for deployment and launch phase
2. Create deployment strategy and configurations
3. Set up CI/CD pipelines and infrastructure
4. Deploy application to target environment
5. Perform post-deployment validation and health checks
6. Create monitoring and maintenance procedures

Ensure secure, reliable deployment with proper monitoring."""
        }
        
        base_instruction = instruction_templates.get(to_agent, 
            f"Complete your specialized tasks for the {phase} phase based on the provided context.")
        
        context_note = ""
        if context:
            context_note = f"\n\nContext Summary: You have {len(context)} context artifacts from previous agents to guide your work."
        
        return base_instruction + context_note
    
    def _get_expected_outputs(self, agent: AgentType, phase: str) -> List[str]:
        """Get expected outputs for agent and phase combination."""
        
        output_mapping = {
            AgentType.ANALYST: ["project_requirements", "user_personas", "success_criteria"],
            AgentType.ARCHITECT: ["system_architecture", "api_specifications", "implementation_plan"],
            AgentType.CODER: ["source_code", "unit_tests", "documentation"],
            AgentType.TESTER: ["test_results", "quality_report", "bug_reports"],
            AgentType.DEPLOYER: ["deployment_package", "deployment_logs", "monitoring_setup"]
        }
        
        return output_mapping.get(agent, ["deliverable"])
    
    def _summarize_context(self, context: List[ContextArtifact]) -> str:
        """Create summary of context artifacts for handoff metadata."""
        
        if not context:
            return "No context artifacts available"
        
        summary_parts = []
        for artifact in context:
            summary_parts.append(f"{artifact.source_agent}:{artifact.artifact_type}")
        
        return f"{len(context)} artifacts: {', '.join(summary_parts)}"