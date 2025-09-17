"""Analyst agent for comprehensive requirements analysis and PRD generation."""

from typing import Dict, Any, List, Optional
from uuid import uuid4
import json
import structlog
from datetime import datetime, timezone

from app.agents.base_agent import BaseAgent
from app.models.task import Task, TaskStatus
from app.models.context import ContextArtifact
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.services.context_store import ContextStoreService
from app.services.template_service import TemplateService

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
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any], db_session=None):
        """Initialize Analyst agent with requirements analysis optimization."""
        super().__init__(agent_type, llm_config)

        # Configure for Anthropic Claude (optimized for requirements analysis)
        # Note: In production, this should be configurable based on provider availability
        self.llm_config.update({
            "model": llm_config.get("model", "claude-3-5-sonnet-20241022"),  # Updated to latest Claude model
            "temperature": 0.4,  # Balanced for analysis accuracy
        })

        # Initialize services
        self.db = db_session
        self.context_store = ContextStoreService(db_session) if db_session else None
        self.template_service = TemplateService() if db_session else None

        # Initialize AutoGen agent
        self._initialize_autogen_agent()

        logger.info("Analyst agent initialized with enhanced requirements analysis capabilities")
    
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
        """Execute analyst task with enhanced requirements analysis and PRD generation.

        Args:
            task: Task to execute with analysis instructions
            context: Context artifacts from previous stages or user input

        Returns:
            Analysis result with requirements, personas, PRD content, and HITL requests
        """
        logger.info("Analyst executing enhanced requirements analysis task",
                   task_id=task.task_id,
                   context_count=len(context))

        try:
            # Step 1: Validate analysis completeness and identify gaps
            completeness_check = self._validate_analysis_completeness(context)
            logger.info("Analysis completeness check completed",
                       gaps_found=len(completeness_check.get("missing_elements", [])),
                       confidence=completeness_check.get("confidence_score", 0))

            # Step 2: Generate HITL requests for clarification if needed
            hitl_requests = []
            if completeness_check.get("requires_clarification", False):
                hitl_requests = self._generate_clarification_requests(
                    task, completeness_check.get("missing_elements", [])
                )
                logger.info("Generated HITL clarification requests",
                           request_count=len(hitl_requests))

            # Step 3: Prepare enhanced analysis context
            analysis_context = self._prepare_enhanced_analysis_context(task, context, completeness_check)

            # Step 4: Execute analysis with LLM reliability features
            raw_response = await self._execute_with_reliability(analysis_context, task)

            # Step 5: Parse and structure analysis response
            analysis_result = self._parse_analysis_response(raw_response, task)

            # Step 6: Generate professional PRD using BMAD templates
            prd_document = await self._generate_prd_from_template(analysis_result, task, context)

            # Step 7: Create context artifacts for results
            result_artifacts = self._create_analysis_artifacts(analysis_result, prd_document, task)

            # Step 8: Final completeness validation
            final_validation = self._validate_final_analysis(analysis_result, prd_document)

            logger.info("Analyst task completed with enhanced features",
                       task_id=task.task_id,
                       personas_created=len(analysis_result.get("user_personas", [])),
                       requirements_count=len(analysis_result.get("functional_requirements", [])),
                       prd_generated=bool(prd_document),
                       hitl_requests=len(hitl_requests),
                       artifacts_created=len(result_artifacts))

            return {
                "success": True,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "output": analysis_result,
                "prd_document": prd_document,
                "requirements_summary": analysis_result.get("executive_summary", {}),
                "stakeholder_questions": analysis_result.get("stakeholder_questions", []),
                "hitl_requests": hitl_requests,
                "completeness_validation": final_validation,
                "artifacts_created": result_artifacts,
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

    def _validate_analysis_completeness(self, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Validate completeness of requirements analysis and identify gaps.

        Args:
            context: Context artifacts to analyze

        Returns:
            Completeness validation results
        """
        missing_elements = []
        confidence_score = 1.0
        requires_clarification = False

        # Check for user input
        user_input_found = any(
            artifact.artifact_type == "user_input" or
            (isinstance(artifact.content, dict) and artifact.content.get("user_idea"))
            for artifact in context
        )

        if not user_input_found:
            missing_elements.append("user_input")
            confidence_score -= 0.3

        # Check for existing analysis artifacts
        existing_analysis = [
            artifact for artifact in context
            if isinstance(artifact.content, dict) and
            artifact.content.get("analysis_type") == "requirements_analysis"
        ]

        if not existing_analysis:
            missing_elements.append("requirements_analysis")
            confidence_score -= 0.4
            requires_clarification = True

        # Check for specific requirement elements
        if existing_analysis:
            latest_analysis = existing_analysis[-1].content

            # Check functional requirements
            func_reqs = latest_analysis.get("functional_requirements", [])
            if len(func_reqs) < 3:
                missing_elements.append("functional_requirements")
                confidence_score -= 0.2

            # Check user personas
            personas = latest_analysis.get("user_personas", [])
            if len(personas) < 1:
                missing_elements.append("user_personas")
                confidence_score -= 0.15

            # Check non-functional requirements
            non_func_reqs = latest_analysis.get("non_functional_requirements", [])
            if len(non_func_reqs) < 2:
                missing_elements.append("non_functional_requirements")
                confidence_score -= 0.1

            # Check success criteria
            success_criteria = latest_analysis.get("success_criteria", [])
            if len(success_criteria) < 2:
                missing_elements.append("success_criteria")
                confidence_score -= 0.1

        # Determine if clarification is needed
        if confidence_score < 0.7 or len(missing_elements) > 2:
            requires_clarification = True

        return {
            "is_complete": len(missing_elements) == 0,
            "confidence_score": max(0.0, confidence_score),
            "missing_elements": missing_elements,
            "requires_clarification": requires_clarification,
            "existing_analysis_count": len(existing_analysis),
            "recommendations": self._generate_completeness_recommendations(missing_elements)
        }

    def _generate_completeness_recommendations(self, missing_elements: List[str]) -> List[str]:
        """Generate recommendations for addressing completeness gaps."""
        recommendations = []

        for element in missing_elements:
            if element == "user_input":
                recommendations.append("Gather detailed user requirements and business objectives")
            elif element == "requirements_analysis":
                recommendations.append("Conduct comprehensive requirements analysis session")
            elif element == "functional_requirements":
                recommendations.append("Define specific functional requirements with acceptance criteria")
            elif element == "user_personas":
                recommendations.append("Develop detailed user personas and use cases")
            elif element == "non_functional_requirements":
                recommendations.append("Specify performance, security, and usability requirements")
            elif element == "success_criteria":
                recommendations.append("Define measurable success criteria and KPIs")

        return recommendations

    def _generate_clarification_requests(self, task: Task, missing_elements: List[str]) -> List[Dict[str, Any]]:
        """Generate HITL requests for clarification on missing elements.

        Args:
            task: Current task
            missing_elements: List of missing requirement elements

        Returns:
            List of HITL request configurations
        """
        hitl_requests = []

        for element in missing_elements:
            if element == "user_input":
                hitl_requests.append({
                    "question": "Please provide more details about the project requirements and objectives",
                    "options": ["Provide detailed requirements", "Schedule requirements workshop", "Share existing documentation"],
                    "priority": "high",
                    "reason": "Missing user input for requirements analysis"
                })

            elif element == "functional_requirements":
                hitl_requests.append({
                    "question": "What are the key functional requirements for this system?",
                    "options": ["List core features", "Provide use cases", "Share functional specifications"],
                    "priority": "high",
                    "reason": "Insufficient functional requirements defined"
                })

            elif element == "user_personas":
                hitl_requests.append({
                    "question": "Who are the primary users of this system and what are their needs?",
                    "options": ["Describe user roles", "Provide user scenarios", "Share user research"],
                    "priority": "medium",
                    "reason": "Missing user persona definitions"
                })

            elif element == "non_functional_requirements":
                hitl_requests.append({
                    "question": "What are the non-functional requirements (performance, security, etc.)?",
                    "options": ["Specify performance needs", "Define security requirements", "List scalability needs"],
                    "priority": "medium",
                    "reason": "Missing non-functional requirements"
                })

        return hitl_requests

    def _prepare_enhanced_analysis_context(self, task: Task, context: List[ContextArtifact],
                                         completeness_check: Dict[str, Any]) -> str:
        """Prepare enhanced analysis context with completeness information."""

        base_context = self._prepare_analysis_context(task, context)

        # Add completeness information
        completeness_info = [
            "",
            "ANALYSIS COMPLETENESS STATUS:",
            f"Confidence Score: {completeness_check.get('confidence_score', 0):.2f}",
            f"Missing Elements: {', '.join(completeness_check.get('missing_elements', [])) or 'None'}",
            f"Requires Clarification: {completeness_check.get('requires_clarification', False)}",
        ]

        if completeness_check.get("recommendations"):
            completeness_info.extend([
                "",
                "RECOMMENDATIONS:",
                *[f"- {rec}" for rec in completeness_check["recommendations"][:3]]
            ])

        completeness_info.extend([
            "",
            "ENHANCED ANALYSIS REQUIREMENTS:",
            "Focus on addressing the identified gaps while maintaining analysis quality.",
            "Generate specific clarification questions for stakeholders if needed.",
            "Ensure all requirements are SMART (Specific, Measurable, Achievable, Relevant, Time-bound)."
        ])

        return base_context + "\n".join(completeness_info)

    async def _generate_prd_from_template(self, analysis_result: Dict[str, Any], task: Task,
                                        context: List[ContextArtifact]) -> Optional[Dict[str, Any]]:
        """Generate professional PRD using BMAD templates.

        Args:
            analysis_result: Structured analysis results
            task: Current task
            context: Context artifacts

        Returns:
            Generated PRD document or None if template service unavailable
        """
        if not self.template_service:
            logger.warning("Template service not available, skipping PRD generation")
            return None

        try:
            # Prepare template variables
            template_vars = {
                "project_id": str(task.project_id),
                "task_id": str(task.task_id),
                "analysis_date": datetime.now(timezone.utc).isoformat(),
                "executive_summary": analysis_result.get("executive_summary", {}),
                "user_personas": analysis_result.get("user_personas", []),
                "functional_requirements": analysis_result.get("functional_requirements", []),
                "non_functional_requirements": analysis_result.get("non_functional_requirements", []),
                "business_constraints": analysis_result.get("business_constraints", []),
                "success_criteria": analysis_result.get("success_criteria", []),
                "risk_assessment": analysis_result.get("risk_assessment", []),
                "stakeholder_questions": analysis_result.get("stakeholder_questions", []),
                "recommendations": analysis_result.get("recommendations", ""),
                "analysis_confidence": analysis_result.get("analysis_confidence", 0.8),
                "completeness_score": analysis_result.get("completeness_score", 0.75)
            }

            # Generate PRD using template
            prd_content = await self.template_service.render_template_async(
                template_name="prd-tmpl.yaml",
                variables=template_vars
            )

            logger.info("PRD generated from template",
                       template="prd-tmpl.yaml",
                       content_length=len(str(prd_content)))

            return {
                "document_type": "product_requirements_document",
                "template_used": "prd-tmpl.yaml",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "content": prd_content,
                "metadata": {
                    "analysis_confidence": template_vars["analysis_confidence"],
                    "completeness_score": template_vars["completeness_score"],
                    "requirements_count": len(template_vars["functional_requirements"]),
                    "personas_count": len(template_vars["user_personas"])
                }
            }

        except Exception as e:
            logger.error("Failed to generate PRD from template",
                        error=str(e),
                        template="prd-tmpl.yaml")
            return None

    def _create_analysis_artifacts(self, analysis_result: Dict[str, Any],
                                 prd_document: Optional[Dict[str, Any]], task: Task) -> List[str]:
        """Create context artifacts for analysis results.

        Args:
            analysis_result: Structured analysis results
            prd_document: Generated PRD document
            task: Current task

        Returns:
            List of created artifact IDs
        """
        if not self.context_store:
            logger.warning("Context store not available, skipping artifact creation")
            return []

        created_artifacts = []

        try:
            # Create requirements analysis artifact
            analysis_artifact = self.context_store.create_artifact(
                project_id=task.project_id,
                source_agent=self.agent_type.value,
                artifact_type="requirements_analysis",
                content=analysis_result
            )
            created_artifacts.append(str(analysis_artifact.context_id))

            # Create PRD artifact if available
            if prd_document:
                prd_artifact = self.context_store.create_artifact(
                    project_id=task.project_id,
                    source_agent=self.agent_type.value,
                    artifact_type="product_requirements_document",
                    content=prd_document
                )
                created_artifacts.append(str(prd_artifact.context_id))

            logger.info("Analysis artifacts created",
                       analysis_artifact=str(analysis_artifact.context_id),
                       prd_artifact=created_artifacts[1] if len(created_artifacts) > 1 else None)

        except Exception as e:
            logger.error("Failed to create analysis artifacts",
                        error=str(e),
                        task_id=str(task.task_id))

        return created_artifacts

    def _validate_final_analysis(self, analysis_result: Dict[str, Any],
                               prd_document: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform final validation of analysis completeness and quality.

        Args:
            analysis_result: Structured analysis results
            prd_document: Generated PRD document

        Returns:
            Final validation results
        """
        validation_results = {
            "overall_quality": "good",
            "issues_found": [],
            "recommendations": [],
            "ready_for_next_phase": True
        }

        # Check analysis completeness
        confidence = analysis_result.get("analysis_confidence", 0.8)
        completeness = analysis_result.get("completeness_score", 0.75)

        if confidence < 0.6:
            validation_results["issues_found"].append("Low analysis confidence")
            validation_results["recommendations"].append("Consider stakeholder review")
            validation_results["overall_quality"] = "needs_review"

        if completeness < 0.7:
            validation_results["issues_found"].append("Incomplete requirements")
            validation_results["recommendations"].append("Gather additional requirements")
            validation_results["overall_quality"] = "needs_improvement"

        # Check for critical missing elements
        critical_elements = ["functional_requirements", "user_personas", "success_criteria"]
        for element in critical_elements:
            if not analysis_result.get(element):
                validation_results["issues_found"].append(f"Missing {element}")
                validation_results["ready_for_next_phase"] = False

        # Check PRD generation
        if not prd_document:
            validation_results["issues_found"].append("PRD generation failed")
            validation_results["recommendations"].append("Manual PRD creation recommended")

        # Determine overall readiness
        if validation_results["issues_found"] and validation_results["ready_for_next_phase"]:
            validation_results["ready_for_next_phase"] = False

        logger.info("Final analysis validation completed",
                   quality=validation_results["overall_quality"],
                   issues=len(validation_results["issues_found"]),
                   ready=validation_results["ready_for_next_phase"])

        return validation_results
