"""Architect agent for comprehensive technical architecture and system design."""

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


class ArchitectAgent(BaseAgent):
    """Architect agent specializing in technical architecture and system design with GPT-4 optimization.
    
    The Architect is responsible for:
    - Technical architecture creation from Analyst's requirements
    - API design and detailed data model definitions
    - Risk assessment and technical constraint identification
    - Implementation planning with clear deliverables and timelines
    - Integration design including database schema and system boundaries
    """
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any], db_session=None):
        """Initialize Architect agent with technical design optimization."""
        super().__init__(agent_type, llm_config)

        # Configure for OpenAI GPT-4 (optimized for technical reasoning)
        # Using available model for now, but should be GPT-4 in production
        self.llm_config.update({
            "model": llm_config.get("model", "gpt-4o"),  # Updated to use GPT-4o
            "temperature": 0.2,  # Lower temperature for technical precision
        })

        # Initialize services
        self.db = db_session
        self.context_store = ContextStoreService(db_session) if db_session else None
        self.template_service = TemplateService() if db_session else None

        # Initialize AutoGen agent
        self._initialize_autogen_agent()

        logger.info("Architect agent initialized with enhanced technical design capabilities")
    
    def _create_system_message(self) -> str:
        """Create Architect-specific system message for AutoGen."""
        return """You are the Architect specializing in technical architecture and system design.

Your core expertise includes:
- System architecture design and component specification
- API design with RESTful principles and data contracts
- Database schema design and data modeling
- Technology stack selection and architectural decisions
- Performance optimization and scalability planning
- Security architecture and risk mitigation
- Integration patterns and system boundaries

Architecture Design Process:
1. Analyze requirements and constraints from business analysis
2. Design high-level system architecture with component breakdown
3. Specify API endpoints, request/response schemas, and validation rules
4. Create comprehensive data models and database schema
5. Define integration points and external service dependencies
6. Assess technical risks and create mitigation strategies
7. Generate detailed implementation plan with task breakdown

Architecture Principles:
- Follow SOLID principles and clean architecture patterns
- Design for scalability, maintainability, and performance
- Ensure security by design with proper authentication/authorization
- Minimize complexity while meeting functional requirements
- Document architectural decisions and their rationale
- Consider operational requirements (monitoring, logging, deployment)
- Plan for testing and quality assurance workflows

Technology Selection Criteria:
- Align with project requirements and constraints
- Consider team expertise and learning curve
- Evaluate long-term maintenance and support
- Assess performance characteristics and scalability
- Factor in security implications and compliance needs
- Balance innovation with proven stability

Communication Style:
- Use precise technical language with clear explanations
- Provide detailed specifications with examples
- Include rationale for architectural decisions
- Structure information with logical flow and dependencies
- Highlight critical risks and mitigation strategies

Always respond with structured JSON containing:
- System architecture overview with component diagrams
- Detailed API specifications and data contracts
- Database schema with relationships and constraints
- Technology stack with justification
- Implementation plan with phases and dependencies
- Risk assessment with mitigation strategies
- Performance and scalability considerations"""
    
    async def execute_task(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute architect task with enhanced technical design and architecture generation.

        Args:
            task: Task to execute with architecture instructions
            context: Context artifacts from requirements analysis

        Returns:
            Architecture result with system design, APIs, implementation plan, and HITL requests
        """
        logger.info("Architect executing enhanced technical design task",
                   task_id=task.task_id,
                   context_count=len(context))

        try:
            # Step 1: Validate architecture completeness and identify gaps
            completeness_check = self._validate_architecture_completeness(context)
            logger.info("Architecture completeness check completed",
                       gaps_found=len(completeness_check.get("missing_elements", [])),
                       confidence=completeness_check.get("confidence_score", 0))

            # Step 2: Generate HITL requests for clarification if needed
            hitl_requests = []
            if completeness_check.get("requires_clarification", False):
                hitl_requests = self._generate_architecture_clarification_requests(
                    task, completeness_check.get("missing_elements", [])
                )
                logger.info("Generated HITL clarification requests",
                           request_count=len(hitl_requests))

            # Step 3: Prepare enhanced architecture design context
            design_context = self._prepare_enhanced_design_context(task, context, completeness_check)

            # Step 4: Execute analysis with LLM reliability features
            raw_response = await self._execute_with_reliability(design_context, task)

            # Step 5: Parse and structure architecture response
            architecture_result = self._parse_architecture_response(raw_response, task)

            # Step 6: Generate professional architecture document using BMAD templates
            architecture_document = await self._generate_architecture_from_template(architecture_result, task, context)

            # Step 7: Create context artifacts for results
            result_artifacts = self._create_architecture_artifacts(architecture_result, architecture_document, task)

            # Step 8: Final architecture validation
            final_validation = self._validate_final_architecture(architecture_result, architecture_document)

            logger.info("Architect task completed with enhanced features",
                       task_id=task.task_id,
                       components_designed=len(architecture_result.get("system_components", [])),
                       apis_specified=len(architecture_result.get("api_specifications", [])),
                       architecture_generated=bool(architecture_document),
                       hitl_requests=len(hitl_requests),
                       artifacts_created=len(result_artifacts))

            return {
                "success": True,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "output": architecture_result,
                "architecture_document": architecture_document,
                "architecture_summary": architecture_result.get("architecture_overview", {}),
                "implementation_plan": architecture_result.get("implementation_plan", {}),
                "hitl_requests": hitl_requests,
                "completeness_validation": final_validation,
                "artifacts_created": result_artifacts,
                "context_used": [str(artifact.context_id) for artifact in context]
            }

        except Exception as e:
            logger.error("Architect task execution failed",
                        task_id=task.task_id,
                        error=str(e))

            return {
                "success": False,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "error": str(e),
                "fallback_architecture": self._create_fallback_architecture(),
                "context_used": [str(artifact.context_id) for artifact in context]
            }
    
    async def create_handoff(self, to_agent: AgentType, task: Task, 
                           context: List[ContextArtifact]) -> HandoffSchema:
        """Create structured handoff to another agent with architecture context.
        
        Args:
            to_agent: Target agent type for the handoff
            task: Current task being handed off
            context: Context artifacts to pass along
            
        Returns:
            HandoffSchema with architecture-aware handoff information
        """
        # Create handoff instructions based on target agent
        if to_agent == AgentType.CODER:
            instructions = self._create_coder_handoff_instructions(context)
            expected_outputs = ["source_code", "unit_tests", "code_documentation"]
            phase = "build"
        elif to_agent == AgentType.TESTER:
            instructions = self._create_tester_handoff_instructions(context)
            expected_outputs = ["test_plan", "test_cases", "quality_validation"]
            phase = "validate"
        else:
            # Generic handoff for other agents
            instructions = f"Proceed with {to_agent.value} tasks based on completed technical architecture"
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
            priority=2,  # Normal priority for architect handoffs
            metadata={
                "architecture_phase": "design_complete",
                "architect_task_id": str(task.task_id),
                "handoff_reason": "technical_design_complete",
                "architecture_summary": self._create_architecture_summary(context),
                "technical_stack": self._extract_tech_stack(context),
                "complexity_assessment": self._assess_implementation_complexity(context)
            }
        )
        
        logger.info("Architect handoff created",
                   to_agent=to_agent.value,
                   phase=phase,
                   architecture_context=len(context))
        
        return handoff
    
    def _prepare_design_context(self, task: Task, context: List[ContextArtifact]) -> str:
        """Prepare context message for technical architecture design."""
        
        context_parts = [
            "TECHNICAL ARCHITECTURE DESIGN TASK:",
            f"Task: {task.instructions}",
            "",
            "PROJECT CONTEXT:",
            f"Project ID: {task.project_id}",
            f"Task ID: {task.task_id}",
            "",
            "REQUIREMENTS AND CONSTRAINTS:",
        ]
        
        if not context:
            context_parts.append("- No requirements context available (this may require stakeholder clarification)")
        else:
            for i, artifact in enumerate(context):
                context_parts.extend([
                    f"",
                    f"Requirements {i+1} from {artifact.source_agent} ({artifact.artifact_type}):",
                    f"Content: {str(artifact.content)[:1000]}..." if len(str(artifact.content)) > 1000 else f"Content: {artifact.content}",
                ])
        
        context_parts.extend([
            "",
            "ARCHITECTURE DESIGN REQUIREMENTS:",
            "Create comprehensive technical architecture including:",
            "",
            "1. **System Architecture**",
            "   - High-level component architecture and relationships",
            "   - Technology stack selection with rationale",
            "   - Deployment architecture and infrastructure requirements",
            "",
            "2. **API Design**",
            "   - RESTful endpoint specifications with HTTP methods",
            "   - Request/response schemas and validation rules",
            "   - Authentication and authorization mechanisms",
            "",
            "3. **Data Architecture**",
            "   - Database schema with tables, relationships, and constraints",
            "   - Data flow patterns and storage strategies",
            "   - Caching strategy and performance optimization",
            "",
            "4. **Integration Architecture**",
            "   - External service dependencies and integration patterns",
            "   - Message queuing and event-driven architecture",
            "   - System boundaries and interface definitions",
            "",
            "5. **Risk Assessment**",
            "   - Technical risks and mitigation strategies",
            "   - Scalability bottlenecks and solutions",
            "   - Security considerations and protection mechanisms",
            "",
            "6. **Implementation Plan**",
            "   - Development phases with clear milestones",
            "   - Task breakdown with effort estimates and dependencies",
            "   - Quality gates and testing strategies",
            "",
            "OUTPUT FORMAT:",
            "Provide structured JSON with comprehensive architecture specifications.",
            "",
            "Focus on creating implementable designs that developers can follow directly."
        ])
        
        return "\n".join(context_parts)
    
    def _parse_architecture_response(self, raw_response: str, task: Task) -> Dict[str, Any]:
        """Parse and structure the technical architecture response."""
        
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
                    response_data = self._extract_architecture_from_text(raw_response)
            
            # Structure the architecture result
            structured_architecture = {
                "architecture_type": "technical_system_design",
                "status": "completed",
                "architecture_overview": response_data.get("architecture_overview", {
                    "system_type": "web_application",
                    "architecture_pattern": "microservices",
                    "description": "Scalable web application architecture"
                }),
                "system_components": response_data.get("system_components", []),
                "technology_stack": response_data.get("technology_stack", {}),
                "api_specifications": response_data.get("api_specifications", []),
                "data_architecture": response_data.get("data_architecture", {}),
                "integration_points": response_data.get("integration_points", []),
                "security_architecture": response_data.get("security_architecture", {}),
                "performance_considerations": response_data.get("performance_considerations", []),
                "scalability_plan": response_data.get("scalability_plan", {}),
                "risk_assessment": response_data.get("risk_assessment", []),
                "implementation_plan": response_data.get("implementation_plan", {}),
                "quality_requirements": response_data.get("quality_requirements", []),
                "operational_requirements": response_data.get("operational_requirements", {}),
                "architectural_decisions": response_data.get("architectural_decisions", []),
                "design_confidence": response_data.get("design_confidence", 0.8),
                "implementation_complexity": response_data.get("implementation_complexity", "medium")
            }
            
            return structured_architecture
            
        except Exception as e:
            logger.warning("Failed to parse architecture response, using fallback",
                          error=str(e))
            return self._create_fallback_architecture(raw_response)
    
    def _extract_architecture_from_text(self, text_response: str) -> Dict[str, Any]:
        """Extract architecture information from text response when JSON parsing fails."""
        
        sections = {}
        
        # Look for common architecture sections
        import re
        
        # System overview
        overview_match = re.search(r'(?i)(system|architecture|overview)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if overview_match:
            sections["architecture_overview"] = {"description": overview_match.group(2).strip()}
        
        # Technology stack
        tech_match = re.search(r'(?i)(technology|tech stack|stack)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if tech_match:
            sections["technology_stack"] = {"description": tech_match.group(2).strip()}
        
        # API information
        api_match = re.search(r'(?i)(api|endpoints?)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if api_match:
            sections["api_specifications"] = [{"description": api_match.group(2).strip()}]
        
        return sections
    
    def _create_fallback_architecture(self, raw_response: str = None) -> Dict[str, Any]:
        """Create fallback architecture response when parsing fails."""
        
        return {
            "architecture_type": "fallback_technical_design",
            "status": "completed_with_fallback",
            "architecture_overview": {
                "system_type": "web_application",
                "architecture_pattern": "layered_architecture",
                "description": "Standard web application with presentation, business, and data layers",
                "scalability": "horizontal_scaling_capable"
            },
            "system_components": [
                {
                    "name": "Frontend Application",
                    "type": "presentation_layer",
                    "technology": "React/Next.js",
                    "responsibilities": ["User interface", "Client-side logic", "API consumption"]
                },
                {
                    "name": "Backend API",
                    "type": "business_logic_layer",
                    "technology": "FastAPI",
                    "responsibilities": ["Business logic", "API endpoints", "Authentication"]
                },
                {
                    "name": "Database",
                    "type": "data_layer",
                    "technology": "PostgreSQL",
                    "responsibilities": ["Data persistence", "Transaction management", "Data integrity"]
                }
            ],
            "technology_stack": {
                "frontend": "React with TypeScript",
                "backend": "FastAPI with Python",
                "database": "PostgreSQL",
                "caching": "Redis",
                "deployment": "Docker containers"
            },
            "api_specifications": [
                {
                    "endpoint": "/api/v1/projects",
                    "method": "GET",
                    "description": "List all projects",
                    "response_schema": {"projects": "array"}
                },
                {
                    "endpoint": "/api/v1/projects",
                    "method": "POST", 
                    "description": "Create new project",
                    "request_schema": {"name": "string", "description": "string"}
                }
            ],
            "data_architecture": {
                "database_type": "relational",
                "key_tables": ["projects", "tasks", "users"],
                "relationships": "foreign_key_constraints",
                "indexing_strategy": "performance_optimized"
            },
            "integration_points": [
                {
                    "service": "Authentication Provider",
                    "type": "OAuth2",
                    "purpose": "User authentication and authorization"
                }
            ],
            "security_architecture": {
                "authentication": "JWT tokens",
                "authorization": "role_based_access_control",
                "data_protection": "encryption_at_rest_and_transit"
            },
            "performance_considerations": [
                "Database query optimization with proper indexing",
                "API response caching for frequently accessed data",
                "Frontend code splitting for faster load times"
            ],
            "scalability_plan": {
                "horizontal_scaling": "Load balancer with multiple API instances",
                "database_scaling": "Read replicas for query performance",
                "caching_strategy": "Redis for session and application data"
            },
            "risk_assessment": [
                {
                    "risk": "Architecture parsing failed - may need human review",
                    "impact": "medium",
                    "mitigation": "Stakeholder validation required"
                },
                {
                    "risk": "Database performance bottlenecks",
                    "impact": "medium",
                    "mitigation": "Implement caching and query optimization"
                }
            ],
            "implementation_plan": {
                "phase_1": "Core backend API and database setup",
                "phase_2": "Frontend application development",
                "phase_3": "Integration and testing",
                "phase_4": "Deployment and monitoring setup"
            },
            "quality_requirements": [
                "Unit test coverage > 80%",
                "API response time < 200ms",
                "System uptime > 99%"
            ],
            "operational_requirements": {
                "monitoring": "Application performance monitoring",
                "logging": "Structured logging with correlation IDs",
                "backup": "Daily database backups with point-in-time recovery"
            },
            "architectural_decisions": [
                {
                    "decision": "Use FastAPI for backend",
                    "rationale": "High performance, automatic API documentation, async support"
                },
                {
                    "decision": "PostgreSQL for database",
                    "rationale": "ACID compliance, JSON support, mature ecosystem"
                }
            ],
            "design_confidence": 0.5,
            "implementation_complexity": "medium",
            "fallback_reason": "Architecture response parsing failed",
            "original_response": raw_response[:300] + "..." if raw_response and len(raw_response) > 300 else raw_response
        }
    
    def _create_coder_handoff_instructions(self, context: List[ContextArtifact]) -> str:
        """Create specific instructions for handoff to Coder agent."""
        
        instructions = """Based on the completed technical architecture, implement the system according to the specifications.

Your implementation should include:

1. **Backend Development**
   - Implement all API endpoints according to specifications
   - Create database models and relationships as designed
   - Implement authentication and authorization mechanisms
   - Add proper error handling and validation
   - Include comprehensive logging and monitoring

2. **Code Quality Standards**
   - Follow SOLID principles and clean code practices
   - Write unit tests for all business logic
   - Include integration tests for API endpoints
   - Add proper documentation and code comments
   - Ensure type safety and proper error handling

3. **Database Implementation**
   - Create database schema according to design
   - Implement proper indexes for performance
   - Add data validation and constraints
   - Include migration scripts for schema changes

4. **API Implementation**
   - Implement RESTful endpoints with proper HTTP methods
   - Add request/response validation according to schemas
   - Include API documentation (OpenAPI/Swagger)
   - Implement proper status codes and error responses

5. **Security Implementation**
   - Implement authentication mechanisms as specified
   - Add authorization checks for protected endpoints
   - Include input validation and sanitization
   - Implement proper session management

6. **Testing and Validation**
   - Write comprehensive unit tests (>80% coverage)
   - Create integration tests for critical workflows
   - Include performance tests for key endpoints
   - Add end-to-end tests for user journeys

Please ensure all code follows the architectural patterns and technology choices specified."""
        
        if context:
            tech_details = self._extract_technical_details(context)
            instructions += f"\n\nTECHNICAL SPECIFICATIONS TO IMPLEMENT:\n{tech_details}"
        
        return instructions
    
    def _create_tester_handoff_instructions(self, context: List[ContextArtifact]) -> str:
        """Create specific instructions for handoff to Tester agent."""
        
        instructions = """Based on the technical architecture and any available implementation, create comprehensive test plans and validation strategies.

Your testing approach should include:

1. **Test Plan Development**
   - Create comprehensive test strategy covering all system components
   - Define test scenarios for each API endpoint and functionality
   - Include edge cases and error condition testing
   - Plan integration tests for system component interactions

2. **Quality Validation**
   - Verify implementation matches architectural specifications
   - Validate API contracts and data schemas
   - Check security implementations and access controls
   - Assess performance against specified requirements

3. **Test Case Creation**
   - Write detailed test cases for functional requirements
   - Create automated tests for regression testing
   - Include load testing for performance validation
   - Design user acceptance tests for business scenarios

4. **Bug Detection and Reporting**
   - Identify deviations from architectural specifications
   - Document bugs with clear reproduction steps
   - Assess impact and priority of identified issues
   - Provide recommendations for fixes and improvements

Please ensure comprehensive coverage of all architectural components and requirements."""
        
        return instructions
    
    def _extract_technical_details(self, context: List[ContextArtifact]) -> str:
        """Extract key technical details from context for handoff instructions."""
        
        tech_details = []
        
        for artifact in context:
            if isinstance(artifact.content, dict):
                # Extract API specifications
                apis = artifact.content.get("api_specifications", [])
                if apis:
                    tech_details.append(f"- Implement {len(apis)} API endpoints as specified")
                
                # Extract technology stack
                tech_stack = artifact.content.get("technology_stack", {})
                if tech_stack:
                    stack_items = [f"{k}: {v}" for k, v in tech_stack.items() if isinstance(v, str)]
                    if stack_items:
                        tech_details.append(f"- Use technology stack: {', '.join(stack_items)}")
                
                # Extract database requirements
                data_arch = artifact.content.get("data_architecture", {})
                if data_arch:
                    tech_details.append("- Implement database schema according to data architecture specifications")
        
        if not tech_details:
            return "- Follow all technical specifications provided in the architecture context"
        
        return "\n".join(tech_details[:5])  # Limit to 5 items
    
    def _create_architecture_summary(self, context: List[ContextArtifact]) -> str:
        """Create summary of architecture for handoff metadata."""
        
        if not context:
            return "No architecture context available"
        
        summary_parts = []
        for artifact in context:
            if isinstance(artifact.content, dict):
                components = len(artifact.content.get("system_components", []))
                apis = len(artifact.content.get("api_specifications", []))
                summary_parts.append(f"{components} components, {apis} APIs")
            else:
                summary_parts.append("architecture document")
        
        return ", ".join(summary_parts) if summary_parts else "basic technical architecture"
    
    def _extract_tech_stack(self, context: List[ContextArtifact]) -> str:
        """Extract technology stack from context."""
        
        for artifact in context:
            if isinstance(artifact.content, dict):
                tech_stack = artifact.content.get("technology_stack", {})
                if tech_stack:
                    stack_items = [f"{k}:{v}" for k, v in tech_stack.items() if isinstance(v, str)]
                    return ",".join(stack_items[:3])  # Top 3 technologies
        
        return "standard_web_stack"
    
    def _assess_implementation_complexity(self, context: List[ContextArtifact]) -> str:
        """Assess implementation complexity based on architecture."""

        for artifact in context:
            if isinstance(artifact.content, dict):
                complexity = artifact.content.get("implementation_complexity", "medium")
                if complexity in ["low", "medium", "high", "very_high"]:
                    return complexity

                # Assess based on component count
                components = len(artifact.content.get("system_components", []))
                if components > 10:
                    return "high"
                elif components > 5:
                    return "medium"
                else:
                    return "low"

        return "medium"

    def _validate_architecture_completeness(self, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Validate completeness of technical architecture and identify gaps.

        Args:
            context: Context artifacts to analyze

        Returns:
            Completeness validation results
        """
        missing_elements = []
        confidence_score = 1.0
        requires_clarification = False

        # Check for requirements context
        requirements_found = any(
            artifact.artifact_type in ["requirements_analysis", "user_input"] or
            (isinstance(artifact.content, dict) and artifact.content.get("analysis_type") == "requirements_analysis")
            for artifact in context
        )

        if not requirements_found:
            missing_elements.append("requirements_context")
            confidence_score -= 0.4
            requires_clarification = True

        # Check for existing architecture artifacts
        existing_architecture = [
            artifact for artifact in context
            if isinstance(artifact.content, dict) and
            artifact.content.get("architecture_type") == "technical_system_design"
        ]

        if not existing_architecture:
            missing_elements.append("architecture_design")
            confidence_score -= 0.5
            requires_clarification = True

        # Check for specific architectural elements
        if existing_architecture:
            latest_architecture = existing_architecture[-1].content

            # Check system components
            components = latest_architecture.get("system_components", [])
            if len(components) < 2:
                missing_elements.append("system_components")
                confidence_score -= 0.2

            # Check API specifications
            apis = latest_architecture.get("api_specifications", [])
            if len(apis) < 1:
                missing_elements.append("api_specifications")
                confidence_score -= 0.15

            # Check technology stack
            tech_stack = latest_architecture.get("technology_stack", {})
            if len(tech_stack) < 2:
                missing_elements.append("technology_stack")
                confidence_score -= 0.1

            # Check data architecture
            data_arch = latest_architecture.get("data_architecture", {})
            if not data_arch:
                missing_elements.append("data_architecture")
                confidence_score -= 0.1

            # Check security architecture
            security = latest_architecture.get("security_architecture", {})
            if not security:
                missing_elements.append("security_architecture")
                confidence_score -= 0.1

        # Determine if clarification is needed
        if confidence_score < 0.6 or len(missing_elements) > 3:
            requires_clarification = True

        return {
            "is_complete": len(missing_elements) == 0,
            "confidence_score": max(0.0, confidence_score),
            "missing_elements": missing_elements,
            "requires_clarification": requires_clarification,
            "existing_architecture_count": len(existing_architecture),
            "recommendations": self._generate_architecture_recommendations(missing_elements)
        }

    def _generate_architecture_recommendations(self, missing_elements: List[str]) -> List[str]:
        """Generate recommendations for addressing architecture gaps."""
        recommendations = []

        for element in missing_elements:
            if element == "requirements_context":
                recommendations.append("Gather detailed requirements analysis before proceeding with architecture design")
            elif element == "architecture_design":
                recommendations.append("Conduct comprehensive technical architecture design session")
            elif element == "system_components":
                recommendations.append("Define clear system components and their responsibilities")
            elif element == "api_specifications":
                recommendations.append("Specify detailed API endpoints with request/response schemas")
            elif element == "technology_stack":
                recommendations.append("Select appropriate technology stack with justification")
            elif element == "data_architecture":
                recommendations.append("Design comprehensive data architecture and storage strategy")
            elif element == "security_architecture":
                recommendations.append("Define security architecture and protection mechanisms")

        return recommendations

    def _generate_architecture_clarification_requests(self, task: Task, missing_elements: List[str]) -> List[Dict[str, Any]]:
        """Generate HITL requests for architecture clarification.

        Args:
            task: Current task
            missing_elements: List of missing architectural elements

        Returns:
            List of HITL request configurations
        """
        hitl_requests = []

        for element in missing_elements:
            if element == "requirements_context":
                hitl_requests.append({
                    "question": "Please provide the requirements analysis or detailed project requirements for architecture design",
                    "options": ["Share requirements document", "Schedule architecture workshop", "Provide use cases"],
                    "priority": "high",
                    "reason": "Missing requirements context for architecture design"
                })

            elif element == "system_components":
                hitl_requests.append({
                    "question": "What are the key system components and their responsibilities?",
                    "options": ["Define component boundaries", "Specify component interactions", "Provide component diagram"],
                    "priority": "high",
                    "reason": "System component definition required"
                })

            elif element == "api_specifications":
                hitl_requests.append({
                    "question": "What are the required API endpoints and their specifications?",
                    "options": ["List API endpoints", "Provide API specifications", "Define data contracts"],
                    "priority": "medium",
                    "reason": "API specification details needed"
                })

            elif element == "technology_stack":
                hitl_requests.append({
                    "question": "What technology stack preferences or constraints should be considered?",
                    "options": ["Specify preferred technologies", "List technology constraints", "Define technology requirements"],
                    "priority": "medium",
                    "reason": "Technology stack clarification needed"
                })

        return hitl_requests

    def _prepare_enhanced_design_context(self, task: Task, context: List[ContextArtifact],
                                       completeness_check: Dict[str, Any]) -> str:
        """Prepare enhanced architecture design context with completeness information."""

        base_context = self._prepare_design_context(task, context)

        # Add completeness information
        completeness_info = [
            "",
            "ARCHITECTURE COMPLETENESS STATUS:",
            f"Confidence Score: {completeness_check.get('confidence_score', 0):.2f}",
            f"Missing Elements: {', '.join(completeness_check.get('missing_elements', [])) or 'None'}",
            f"Requires Clarification: {completeness_check.get('requires_clarification', False)}",
        ]

        if completeness_check.get("recommendations"):
            completeness_info.extend([
                "",
                "ARCHITECTURE RECOMMENDATIONS:",
                *[f"- {rec}" for rec in completeness_check["recommendations"][:3]]
            ])

        completeness_info.extend([
            "",
            "ENHANCED ARCHITECTURE REQUIREMENTS:",
            "Focus on addressing the identified gaps while maintaining architectural quality.",
            "Generate specific clarification questions for technical stakeholders if needed.",
            "Ensure all architectural decisions are documented with rationale.",
            "Consider scalability, security, and maintainability in all design decisions."
        ])

        return base_context + "\n".join(completeness_info)

    async def _generate_architecture_from_template(self, architecture_result: Dict[str, Any], task: Task,
                                                 context: List[ContextArtifact]) -> Optional[Dict[str, Any]]:
        """Generate professional architecture document using BMAD templates.

        Args:
            architecture_result: Structured architecture results
            task: Current task
            context: Context artifacts

        Returns:
            Generated architecture document or None if template service unavailable
        """
        if not self.template_service:
            logger.warning("Template service not available, skipping architecture document generation")
            return None

        try:
            # Prepare template variables
            template_vars = {
                "project_id": str(task.project_id),
                "task_id": str(task.task_id),
                "architecture_date": datetime.now(timezone.utc).isoformat(),
                "architecture_overview": architecture_result.get("architecture_overview", {}),
                "system_components": architecture_result.get("system_components", []),
                "technology_stack": architecture_result.get("technology_stack", {}),
                "api_specifications": architecture_result.get("api_specifications", []),
                "data_architecture": architecture_result.get("data_architecture", {}),
                "integration_points": architecture_result.get("integration_points", []),
                "security_architecture": architecture_result.get("security_architecture", {}),
                "performance_considerations": architecture_result.get("performance_considerations", []),
                "scalability_plan": architecture_result.get("scalability_plan", {}),
                "risk_assessment": architecture_result.get("risk_assessment", []),
                "implementation_plan": architecture_result.get("implementation_plan", {}),
                "quality_requirements": architecture_result.get("quality_requirements", []),
                "operational_requirements": architecture_result.get("operational_requirements", {}),
                "architectural_decisions": architecture_result.get("architectural_decisions", []),
                "design_confidence": architecture_result.get("design_confidence", 0.8),
                "implementation_complexity": architecture_result.get("implementation_complexity", "medium")
            }

            # Generate architecture document using template
            architecture_content = await self.template_service.render_template_async(
                template_name="architecture-tmpl.yaml",
                variables=template_vars
            )

            logger.info("Architecture document generated from template",
                       template="architecture-tmpl.yaml",
                       content_length=len(str(architecture_content)))

            return {
                "document_type": "technical_architecture_document",
                "template_used": "architecture-tmpl.yaml",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "content": architecture_content,
                "metadata": {
                    "design_confidence": template_vars["design_confidence"],
                    "implementation_complexity": template_vars["implementation_complexity"],
                    "components_count": len(template_vars["system_components"]),
                    "apis_count": len(template_vars["api_specifications"])
                }
            }

        except Exception as e:
            logger.error("Failed to generate architecture document from template",
                        error=str(e),
                        template="architecture-tmpl.yaml")
            return None

    def _create_architecture_artifacts(self, architecture_result: Dict[str, Any],
                                      architecture_document: Optional[Dict[str, Any]], task: Task) -> List[str]:
        """Create context artifacts for architecture results.

        Args:
            architecture_result: Structured architecture results
            architecture_document: Generated architecture document
            task: Current task

        Returns:
            List of created artifact IDs
        """
        if not self.context_store:
            logger.warning("Context store not available, skipping artifact creation")
            return []

        created_artifacts = []

        try:
            # Create technical architecture artifact
            architecture_artifact = self.context_store.create_artifact(
                project_id=task.project_id,
                source_agent=self.agent_type.value,
                artifact_type="technical_architecture",
                content=architecture_result
            )
            created_artifacts.append(str(architecture_artifact.context_id))

            # Create architecture document artifact if available
            if architecture_document:
                document_artifact = self.context_store.create_artifact(
                    project_id=task.project_id,
                    source_agent=self.agent_type.value,
                    artifact_type="architecture_document",
                    content=architecture_document
                )
                created_artifacts.append(str(document_artifact.context_id))

            logger.info("Architecture artifacts created",
                       architecture_artifact=str(architecture_artifact.context_id),
                       document_artifact=created_artifacts[1] if len(created_artifacts) > 1 else None)

        except Exception as e:
            logger.error("Failed to create architecture artifacts",
                        error=str(e),
                        task_id=str(task.task_id))

        return created_artifacts

    def _validate_final_architecture(self, architecture_result: Dict[str, Any],
                                   architecture_document: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform final validation of architecture completeness and quality.

        Args:
            architecture_result: Structured architecture results
            architecture_document: Generated architecture document

        Returns:
            Final validation results
        """
        validation_results = {
            "overall_quality": "good",
            "issues_found": [],
            "recommendations": [],
            "ready_for_next_phase": True
        }

        # Check architecture completeness
        confidence = architecture_result.get("design_confidence", 0.8)
        components = len(architecture_result.get("system_components", []))
        apis = len(architecture_result.get("api_specifications", []))
        tech_stack = len(architecture_result.get("technology_stack", {}))

        if confidence < 0.6:
            validation_results["issues_found"].append("Low architecture confidence")
            validation_results["recommendations"].append("Consider technical review")
            validation_results["overall_quality"] = "needs_review"

        if components < 2:
            validation_results["issues_found"].append("Insufficient system components")
            validation_results["recommendations"].append("Define more system components")
            validation_results["overall_quality"] = "needs_improvement"

        if apis < 1:
            validation_results["issues_found"].append("Missing API specifications")
            validation_results["recommendations"].append("Define API endpoints")
            validation_results["ready_for_next_phase"] = False

        if tech_stack < 2:
            validation_results["issues_found"].append("Incomplete technology stack")
            validation_results["recommendations"].append("Specify complete technology stack")
            validation_results["overall_quality"] = "needs_improvement"

        # Check for critical missing elements
        critical_elements = ["system_components", "api_specifications", "technology_stack"]
        for element in critical_elements:
            if not architecture_result.get(element):
                validation_results["issues_found"].append(f"Missing {element}")
                validation_results["ready_for_next_phase"] = False

        # Check architecture document generation
        if not architecture_document:
            validation_results["issues_found"].append("Architecture document generation failed")
            validation_results["recommendations"].append("Manual architecture documentation recommended")

        # Determine overall readiness
        if validation_results["issues_found"] and validation_results["ready_for_next_phase"]:
            validation_results["ready_for_next_phase"] = False

        logger.info("Final architecture validation completed",
                   quality=validation_results["overall_quality"],
                   issues=len(validation_results["issues_found"]),
                   ready=validation_results["ready_for_next_phase"])

        return validation_results
