"""Analyst agent for requirements analysis and PRD generation."""

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


class AnalystAgent(BaseAgent):
    """Analyst agent specializing in requirements analysis with Claude LLM optimization.
    
    The Analyst is responsible for:
    - Requirements analysis and PRD generation from user input
    - Completeness validation and identification of missing requirements
    - Stakeholder interaction through chat interface for comprehensive gathering
    - User persona creation and business requirement mapping
    - Success criteria definition with measurable acceptance conditions
    """
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any]):
        """Initialize Analyst agent with requirements analysis optimization."""
        super().__init__(agent_type, llm_config)
        
        # Configure for Anthropic Claude (optimized for requirements analysis)
        # Note: In production, this should be configurable based on provider availability
        self.llm_config.update({
            "model": llm_config.get("model", "gpt-4o-mini"),  # Using available model
            "temperature": 0.4,  # Balanced for analysis accuracy
        })
        
        # Initialize AutoGen agent
        self._initialize_autogen_agent()
        
        logger.info("Analyst agent initialized with requirements analysis focus")
    
    def _create_system_message(self) -> str:
        """Create Analyst-specific system message for AutoGen."""
        return """You are the Analyst specializing in requirements analysis and PRD generation.

Your core expertise includes:
- Business requirements analysis and stakeholder needs assessment
- User persona development and user story creation
- Functional and non-functional requirements specification
- Success criteria definition with measurable metrics
- Risk identification and constraint analysis
- Comprehensive documentation and PRD generation

Requirements Analysis Process:
1. Understand the business context and user needs
2. Identify all stakeholders and their requirements
3. Create detailed user personas and journey maps
4. Define functional requirements with clear acceptance criteria
5. Specify non-functional requirements (performance, security, usability)
6. Identify constraints, risks, and dependencies
7. Generate comprehensive Product Requirements Document

Analysis Principles:
- Ask clarifying questions when requirements are unclear
- Focus on the "what" and "why" rather than "how"
- Ensure requirements are SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- Consider edge cases and error scenarios
- Balance user needs with business constraints
- Prioritize requirements based on business value and risk

Communication Style:
- Use clear, business-friendly language
- Structure information logically with proper sections
- Include rationale for decisions and recommendations
- Provide examples and use cases to illustrate requirements
- Flag areas that need stakeholder input or clarification

Always respond with structured JSON containing:
- Executive summary of findings
- User personas and target audience
- Detailed functional requirements
- Non-functional requirements and constraints
- Success criteria and acceptance conditions
- Risk assessment and recommendations
- Questions for stakeholder clarification (if any)"""
    
    async def execute_task(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute analyst task with requirements analysis focus.
        
        Args:
            task: Task to execute with analysis instructions
            context: Context artifacts from previous stages or user input
            
        Returns:
            Analysis result with requirements, personas, and PRD content
        """
        logger.info("Analyst executing requirements analysis task",
                   task_id=task.task_id,
                   context_count=len(context))
        
        try:
            # Prepare requirements analysis context
            analysis_context = self._prepare_analysis_context(task, context)
            
            # Execute with LLM reliability features
            raw_response = await self._execute_with_reliability(analysis_context, task)
            
            # Parse and structure analysis response
            analysis_result = self._parse_analysis_response(raw_response, task)
            
            logger.info("Analyst task completed successfully",
                       task_id=task.task_id,
                       personas_created=len(analysis_result.get("user_personas", [])),
                       requirements_count=len(analysis_result.get("functional_requirements", [])))
            
            return {
                "success": True,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "output": analysis_result,
                "requirements_summary": analysis_result.get("executive_summary", {}),
                "stakeholder_questions": analysis_result.get("stakeholder_questions", []),
                "context_used": [str(artifact.context_id) for artifact in context]
            }
            
        except Exception as e:
            logger.error("Analyst task execution failed",
                        task_id=task.task_id,
                        error=str(e))
            
            return {
                "success": False,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "error": str(e),
                "fallback_analysis": self._create_fallback_analysis(),
                "context_used": [str(artifact.context_id) for artifact in context]
            }
    
    async def create_handoff(self, to_agent: AgentType, task: Task, 
                           context: List[ContextArtifact]) -> HandoffSchema:
        """Create structured handoff to another agent with requirements context.
        
        Args:
            to_agent: Target agent type for the handoff
            task: Current task being handed off
            context: Context artifacts to pass along
            
        Returns:
            HandoffSchema with requirements-aware handoff information
        """
        # Create handoff instructions based on target agent
        if to_agent == AgentType.ARCHITECT:
            instructions = self._create_architect_handoff_instructions(context)
            expected_outputs = ["system_architecture", "technical_specifications", "implementation_plan"]
            phase = "design"
        else:
            # Generic handoff for other agents
            instructions = f"Proceed with {to_agent.value} tasks based on completed requirements analysis"
            expected_outputs = [f"{to_agent.value}_deliverable"]
            phase = "next_phase"
        
        handoff = HandoffSchema(
            handoff_id=uuid4(),
            from_agent=self.agent_type.value,
            to_agent=to_agent.value,
            project_id=task.project_id,
            phase=phase,
            context_ids=[artifact.context_id for artifact in context],
            instructions=instructions,
            expected_outputs=expected_outputs,
            priority=2,  # Normal priority for analyst handoffs
            metadata={
                "analysis_phase": "requirements_complete",
                "analyst_task_id": str(task.task_id),
                "handoff_reason": "requirements_analysis_complete",
                "requirements_summary": self._create_requirements_summary(context),
                "stakeholder_input_needed": self._check_stakeholder_input_needed(context)
            }
        )
        
        logger.info("Analyst handoff created",
                   to_agent=to_agent.value,
                   phase=phase,
                   requirements_context=len(context))
        
        return handoff
    
    def _prepare_analysis_context(self, task: Task, context: List[ContextArtifact]) -> str:
        """Prepare context message for requirements analysis."""
        
        context_parts = [
            "REQUIREMENTS ANALYSIS TASK:",
            f"Task: {task.instructions}",
            "",
            "PROJECT CONTEXT:",
            f"Project ID: {task.project_id}",
            f"Task ID: {task.task_id}",
            "",
            "ANALYSIS INPUTS:",
        ]
        
        if not context:
            context_parts.append("- No previous context available (this appears to be initial project analysis)")
        else:
            for i, artifact in enumerate(context):
                context_parts.extend([
                    f"",
                    f"Input {i+1} from {artifact.source_agent} ({artifact.artifact_type}):",
                    f"Content: {str(artifact.content)[:800]}..." if len(str(artifact.content)) > 800 else f"Content: {artifact.content}",
                ])
        
        context_parts.extend([
            "",
            "ANALYSIS REQUIREMENTS:",
            "Conduct comprehensive requirements analysis including:",
            "1. User personas and target audience identification",
            "2. Functional requirements with acceptance criteria",
            "3. Non-functional requirements (performance, security, usability)",
            "4. Business constraints and technical limitations",
            "5. Success criteria and measurable outcomes",
            "6. Risk assessment and mitigation strategies",
            "7. Stakeholder questions for clarification",
            "",
            "OUTPUT FORMAT:",
            "Provide structured JSON with comprehensive analysis results.",
            "",
            "Focus on completeness and clarity to minimize rework in later phases."
        ])
        
        return "\n".join(context_parts)
    
    def _parse_analysis_response(self, raw_response: str, task: Task) -> Dict[str, Any]:
        """Parse and structure the requirements analysis response."""
        
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
                    # Create structured response from text
                    response_data = self._extract_analysis_from_text(raw_response)
            
            # Structure the analysis result
            structured_analysis = {
                "analysis_type": "requirements_analysis",
                "status": "completed",
                "executive_summary": response_data.get("executive_summary", {
                    "project_overview": "Requirements analysis completed",
                    "key_findings": "User needs and system requirements identified",
                    "next_steps": "Proceed to architectural design phase"
                }),
                "user_personas": response_data.get("user_personas", []),
                "functional_requirements": response_data.get("functional_requirements", []),
                "non_functional_requirements": response_data.get("non_functional_requirements", []),
                "business_constraints": response_data.get("business_constraints", []),
                "success_criteria": response_data.get("success_criteria", []),
                "risk_assessment": response_data.get("risk_assessment", []),
                "stakeholder_questions": response_data.get("stakeholder_questions", []),
                "recommendations": response_data.get("recommendations", "Proceed with architectural design"),
                "analysis_confidence": response_data.get("analysis_confidence", 0.8),
                "completeness_score": response_data.get("completeness_score", 0.75)
            }
            
            return structured_analysis
            
        except Exception as e:
            logger.warning("Failed to parse analysis response, using fallback",
                          error=str(e))
            return self._create_fallback_analysis(raw_response)
    
    def _extract_analysis_from_text(self, text_response: str) -> Dict[str, Any]:
        """Extract analysis information from text response when JSON parsing fails."""
        
        # Basic extraction patterns
        sections = {}
        
        # Look for common section headers
        import re
        
        # Executive summary
        summary_match = re.search(r'(?i)(executive summary|overview|summary)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if summary_match:
            sections["executive_summary"] = {"overview": summary_match.group(2).strip()}
        
        # User personas
        personas_match = re.search(r'(?i)(user personas?|personas?|users?)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if personas_match:
            sections["user_personas"] = [{"name": "Primary User", "description": personas_match.group(2).strip()}]
        
        # Requirements
        req_match = re.search(r'(?i)(requirements?|functional requirements?)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if req_match:
            sections["functional_requirements"] = [req_match.group(2).strip()]
        
        return sections
    
    def _create_fallback_analysis(self, raw_response: str = None) -> Dict[str, Any]:
        """Create fallback analysis response when parsing fails."""
        
        return {
            "analysis_type": "fallback_requirements_analysis",
            "status": "completed_with_fallback",
            "executive_summary": {
                "project_overview": "Requirements analysis completed using fallback approach",
                "key_findings": "Basic user needs and system requirements identified",
                "next_steps": "Proceed with caution to architectural design - review recommended"
            },
            "user_personas": [
                {
                    "name": "Primary User",
                    "description": "End user who needs the system functionality",
                    "needs": ["System access", "Core functionality", "Reliable performance"],
                    "goals": ["Complete tasks efficiently", "Access information easily"]
                }
            ],
            "functional_requirements": [
                "System must provide core functionality as specified",
                "Users must be able to authenticate and access features", 
                "System must handle user inputs and provide appropriate responses",
                "Data must be stored and retrieved accurately"
            ],
            "non_functional_requirements": [
                "System should respond within acceptable time limits",
                "System should be available during business hours",
                "System should handle expected user load",
                "System should maintain data security and privacy"
            ],
            "business_constraints": [
                "Budget and timeline constraints may apply",
                "Existing system integration may be required",
                "Compliance with relevant standards may be needed"
            ],
            "success_criteria": [
                "Core functionality works as specified",
                "Users can complete primary tasks successfully",
                "System meets performance expectations"
            ],
            "risk_assessment": [
                "Analysis parsing failed - may need human review",
                "Requirements may be incomplete",
                "Stakeholder validation strongly recommended"
            ],
            "stakeholder_questions": [
                "Please validate the functional requirements",
                "Are there additional user personas to consider?",
                "What are the specific performance requirements?",
                "Are there compliance or security requirements?"
            ],
            "recommendations": "Requires stakeholder review due to analysis parsing issues",
            "analysis_confidence": 0.4,
            "completeness_score": 0.5,
            "fallback_reason": "Response parsing failed",
            "original_response": raw_response[:300] + "..." if raw_response and len(raw_response) > 300 else raw_response
        }
    
    def _create_architect_handoff_instructions(self, context: List[ContextArtifact]) -> str:
        """Create specific instructions for handoff to Architect agent."""
        
        instructions = """Based on the completed requirements analysis, design the technical architecture for this system.

Your architectural design should include:

1. **System Architecture Overview**
   - High-level system components and their relationships
   - Technology stack recommendations with rationale
   - Architecture patterns and design principles to follow

2. **API Design and Specifications**
   - RESTful API endpoints and data contracts
   - Request/response schemas and validation rules
   - Authentication and authorization mechanisms

3. **Data Model Design**
   - Database schema with relationships and constraints
   - Data flow diagrams and storage strategies
   - Caching and performance optimization considerations

4. **Integration Points**
   - External service integrations and dependencies
   - Third-party API requirements and limitations
   - System boundaries and interface definitions

5. **Technical Risk Assessment**
   - Scalability considerations and bottlenecks
   - Security vulnerabilities and mitigation strategies
   - Performance requirements and optimization plans

6. **Implementation Planning**
   - Development phases and milestone definitions
   - Task breakdown with effort estimates
   - Dependencies and critical path identification

Please ensure your architecture aligns with the identified requirements and constraints."""
        
        if context:
            requirements_summary = self._extract_key_requirements(context)
            instructions += f"\n\nKEY REQUIREMENTS TO ADDRESS:\n{requirements_summary}"
        
        return instructions
    
    def _extract_key_requirements(self, context: List[ContextArtifact]) -> str:
        """Extract key requirements from context for handoff instructions."""
        
        key_requirements = []
        
        for artifact in context:
            if isinstance(artifact.content, dict):
                # Extract functional requirements
                func_reqs = artifact.content.get("functional_requirements", [])
                if func_reqs:
                    key_requirements.extend(func_reqs[:3])  # Top 3 requirements
                
                # Extract non-functional requirements
                nonfunc_reqs = artifact.content.get("non_functional_requirements", [])
                if nonfunc_reqs:
                    key_requirements.extend(nonfunc_reqs[:2])  # Top 2 non-functional
        
        if not key_requirements:
            return "- Review all requirements artifacts for comprehensive understanding"
        
        return "\n".join([f"- {req}" for req in key_requirements[:5]])  # Limit to 5 items
    
    def _create_requirements_summary(self, context: List[ContextArtifact]) -> str:
        """Create summary of requirements for handoff metadata."""
        
        if not context:
            return "No requirements context available"
        
        summary_parts = []
        for artifact in context:
            if isinstance(artifact.content, dict):
                req_count = len(artifact.content.get("functional_requirements", []))
                persona_count = len(artifact.content.get("user_personas", []))
                summary_parts.append(f"{req_count} requirements, {persona_count} personas")
            else:
                summary_parts.append("requirements document")
        
        return ", ".join(summary_parts) if summary_parts else "basic requirements analysis"
    
    def _check_stakeholder_input_needed(self, context: List[ContextArtifact]) -> bool:
        """Check if stakeholder input is needed based on analysis."""
        
        for artifact in context:
            if isinstance(artifact.content, dict):
                questions = artifact.content.get("stakeholder_questions", [])
                if questions:
                    return True
                
                confidence = artifact.content.get("analysis_confidence", 1.0)
                if confidence < 0.7:
                    return True
        
        return False