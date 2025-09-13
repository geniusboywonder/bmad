"""Architect agent for technical architecture and system design."""

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


class ArchitectAgent(BaseAgent):
    """Architect agent specializing in technical architecture and system design with GPT-4 optimization.
    
    The Architect is responsible for:
    - Technical architecture creation from Analyst's requirements
    - API design and detailed data model definitions
    - Risk assessment and technical constraint identification
    - Implementation planning with clear deliverables and timelines
    - Integration design including database schema and system boundaries
    """
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any]):
        """Initialize Architect agent with technical design optimization."""
        super().__init__(agent_type, llm_config)
        
        # Configure for OpenAI GPT-4 (optimized for technical reasoning)
        # Using available model for now, but should be GPT-4 in production
        self.llm_config.update({
            "model": llm_config.get("model", "gpt-4o-mini"),
            "temperature": 0.2,  # Lower temperature for technical precision
        })
        
        # Initialize AutoGen agent
        self._initialize_autogen_agent()
        
        logger.info("Architect agent initialized with technical design focus")
    
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
        """Execute architect task with technical design focus.
        
        Args:
            task: Task to execute with architecture instructions
            context: Context artifacts from requirements analysis
            
        Returns:
            Architecture result with system design, APIs, and implementation plan
        """
        logger.info("Architect executing technical design task",
                   task_id=task.task_id,
                   context_count=len(context))
        
        try:
            # Prepare architecture design context
            design_context = self._prepare_design_context(task, context)
            
            # Execute with LLM reliability features
            raw_response = await self._execute_with_reliability(design_context, task)
            
            # Parse and structure architecture response
            architecture_result = self._parse_architecture_response(raw_response, task)
            
            logger.info("Architect task completed successfully",
                       task_id=task.task_id,
                       components_designed=len(architecture_result.get("system_components", [])),
                       apis_specified=len(architecture_result.get("api_specifications", [])))
            
            return {
                "success": True,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "output": architecture_result,
                "architecture_summary": architecture_result.get("architecture_overview", {}),
                "implementation_plan": architecture_result.get("implementation_plan", {}),
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