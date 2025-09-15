"""ADK Workflow Templates for multi-agent collaborative scenarios."""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class WorkflowType(str, Enum):
    """Enumeration of supported ADK workflow types."""
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    SYSTEM_DESIGN = "system_design"
    CODE_REVIEW = "code_review"
    TESTING_STRATEGY = "testing_strategy"
    DEPLOYMENT_PLANNING = "deployment_planning"
    ARCHITECTURE_REVIEW = "architecture_review"
    SECURITY_ASSESSMENT = "security_assessment"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


@dataclass
class WorkflowStep:
    """Represents a single step in an ADK workflow."""
    agent_type: str
    instruction: str
    expected_output: str
    handoff_conditions: List[str]
    priority: str = "medium"
    timeout_minutes: int = 10
    required_context: List[str] = None

    def __post_init__(self):
        if self.required_context is None:
            self.required_context = []


@dataclass
class WorkflowTemplate:
    """Complete workflow template with metadata."""
    name: str
    description: str
    workflow_type: WorkflowType
    steps: List[WorkflowStep]
    max_duration_minutes: int
    required_agents: List[str]
    success_criteria: List[str]
    fallback_strategies: Dict[str, Any] = None

    def __post_init__(self):
        if self.fallback_strategies is None:
            self.fallback_strategies = {}


class ADKWorkflowTemplates:
    """Predefined multi-agent workflow templates optimized for ADK GroupChat."""

    # Comprehensive Requirements Analysis Workflow
    COMPREHENSIVE_ANALYSIS = WorkflowTemplate(
        name="Comprehensive Requirements Analysis",
        description="Multi-agent collaborative analysis of project requirements with iterative refinement",
        workflow_type=WorkflowType.REQUIREMENTS_ANALYSIS,
        max_duration_minutes=45,
        required_agents=["analyst", "architect"],
        success_criteria=[
            "Complete PRD with acceptance criteria",
            "Technical feasibility assessment",
            "Identified risks and constraints",
            "Stakeholder alignment achieved"
        ],
        steps=[
            WorkflowStep(
                agent_type="analyst",
                instruction="""Analyze the provided requirements and create a comprehensive Product Requirements Document (PRD).
                Focus on:
                - User personas and use cases
                - Functional requirements with clear acceptance criteria
                - Non-functional requirements (performance, security, scalability)
                - Business rules and constraints
                - Success metrics and KPIs

                Provide specific, measurable requirements that will guide development.""",
                expected_output="product_requirements_document",
                handoff_conditions=["prd_complete", "requirements_clear"],
                priority="high",
                timeout_minutes=15,
                required_context=["project_description", "stakeholder_input"]
            ),
            WorkflowStep(
                agent_type="architect",
                instruction="""Review the PRD from the Analyst and provide technical feasibility assessment.
                Evaluate:
                - Technical complexity and risks
                - Architecture implications and constraints
                - Technology stack recommendations
                - Integration requirements
                - Performance and scalability considerations

                Identify any gaps or clarifications needed from the Analyst.""",
                expected_output="technical_feasibility_review",
                handoff_conditions=["feasibility_assessed", "architecture_recommendations"],
                priority="high",
                timeout_minutes=15,
                required_context=["product_requirements_document"]
            ),
            WorkflowStep(
                agent_type="analyst",
                instruction="""Review the technical feasibility feedback and refine the PRD accordingly.
                Address:
                - Technical constraints identified by Architect
                - Updated acceptance criteria based on feasibility
                - Risk mitigation strategies
                - Implementation priorities and phasing

                Ensure the PRD is technically sound and ready for development.""",
                expected_output="refined_requirements",
                handoff_conditions=["requirements_refined", "ready_for_development"],
                priority="medium",
                timeout_minutes=15,
                required_context=["technical_feasibility_review", "original_prd"]
            )
        ]
    )

    # System Design Collaboration Workflow
    SYSTEM_DESIGN_COLLABORATION = WorkflowTemplate(
        name="System Design Collaboration",
        description="Collaborative system design with multiple architectural perspectives",
        workflow_type=WorkflowType.SYSTEM_DESIGN,
        max_duration_minutes=60,
        required_agents=["architect", "analyst"],
        success_criteria=[
            "Complete system architecture document",
            "API specifications defined",
            "Data model finalized",
            "Scalability and performance requirements addressed"
        ],
        steps=[
            WorkflowStep(
                agent_type="architect",
                instruction="""Design the high-level system architecture based on requirements.
                Create:
                - System context diagram
                - Component architecture overview
                - Technology stack recommendations
                - Deployment architecture
                - Security architecture considerations

                Focus on scalability, maintainability, and technical excellence.""",
                expected_output="system_architecture_design",
                handoff_conditions=["architecture_drafted", "components_identified"],
                priority="high",
                timeout_minutes=20,
                required_context=["refined_requirements", "technical_constraints"]
            ),
            WorkflowStep(
                agent_type="analyst",
                instruction="""Review the system architecture from a business and user perspective.
                Evaluate:
                - Alignment with business requirements
                - User experience implications
                - Functional completeness
                - Non-functional requirement coverage
                - Risk and dependency identification

                Provide feedback on business impact and user value.""",
                expected_output="business_architecture_review",
                handoff_conditions=["business_alignment_verified", "user_impact_assessed"],
                priority="high",
                timeout_minutes=15,
                required_context=["system_architecture_design", "business_requirements"]
            ),
            WorkflowStep(
                agent_type="architect",
                instruction="""Incorporate business feedback and finalize the system architecture.
                Update:
                - Architecture diagrams with business context
                - Component specifications with business requirements
                - API specifications with business use cases
                - Data models with business entities
                - Implementation roadmap with business priorities

                Ensure the architecture delivers maximum business value.""",
                expected_output="final_system_architecture",
                handoff_conditions=["architecture_finalized", "implementation_ready"],
                priority="high",
                timeout_minutes=25,
                required_context=["business_architecture_review", "system_architecture_design"]
            )
        ]
    )

    # Code Review and Quality Assurance Workflow
    CODE_REVIEW_COLLABORATION = WorkflowTemplate(
        name="Code Review Collaboration",
        description="Multi-agent code review with quality assessment and improvement recommendations",
        workflow_type=WorkflowType.CODE_REVIEW,
        max_duration_minutes=30,
        required_agents=["coder", "architect", "analyst"],
        success_criteria=[
            "Code quality assessment completed",
            "Security vulnerabilities identified and addressed",
            "Performance optimization recommendations provided",
            "Maintainability improvements suggested"
        ],
        steps=[
            WorkflowStep(
                agent_type="coder",
                instruction="""Perform initial code review focusing on implementation quality.
                Assess:
                - Code structure and organization
                - Algorithm efficiency and correctness
                - Error handling and edge cases
                - Code documentation and comments
                - Test coverage and quality

                Provide specific recommendations for code improvements.""",
                expected_output="code_quality_assessment",
                handoff_conditions=["code_reviewed", "issues_identified"],
                priority="medium",
                timeout_minutes=10,
                required_context=["source_code", "requirements"]
            ),
            WorkflowStep(
                agent_type="architect",
                instruction="""Review code from architectural and design perspective.
                Evaluate:
                - Adherence to architectural patterns
                - Component coupling and cohesion
                - Scalability and performance considerations
                - Security implementation
                - Design pattern usage and appropriateness

                Identify architectural improvements and refactoring opportunities.""",
                expected_output="architectural_code_review",
                handoff_conditions=["architecture_reviewed", "design_issues_identified"],
                priority="medium",
                timeout_minutes=10,
                required_context=["code_quality_assessment", "system_architecture"]
            ),
            WorkflowStep(
                agent_type="analyst",
                instruction="""Review code from business requirements and user experience perspective.
                Assess:
                - Functional requirement implementation
                - User experience and usability
                - Business rule compliance
                - Data validation and integrity
                - Error messaging and user feedback

                Ensure code meets business needs and user expectations.""",
                expected_output="business_code_review",
                handoff_conditions=["business_requirements_verified", "user_experience_validated"],
                priority="medium",
                timeout_minutes=10,
                required_context=["architectural_code_review", "business_requirements"]
            )
        ]
    )

    # Testing Strategy Development Workflow
    TESTING_STRATEGY_COLLABORATION = WorkflowTemplate(
        name="Testing Strategy Collaboration",
        description="Comprehensive testing strategy development with multiple quality perspectives",
        workflow_type=WorkflowType.TESTING_STRATEGY,
        max_duration_minutes=40,
        required_agents=["analyst", "architect", "coder"],
        success_criteria=[
            "Comprehensive test strategy document",
            "Test automation framework recommendations",
            "Quality metrics and KPIs defined",
            "Testing resource requirements identified"
        ],
        steps=[
            WorkflowStep(
                agent_type="analyst",
                instruction="""Define testing requirements based on business needs.
                Identify:
                - Business-critical test scenarios
                - User acceptance criteria testing
                - Regression testing requirements
                - Performance and load testing needs
                - User experience testing requirements

                Focus on business value and risk mitigation.""",
                expected_output="business_testing_requirements",
                handoff_conditions=["business_testing_defined", "acceptance_criteria_covered"],
                priority="medium",
                timeout_minutes=12,
                required_context=["business_requirements", "user_stories"]
            ),
            WorkflowStep(
                agent_type="architect",
                instruction="""Design technical testing architecture and frameworks.
                Define:
                - Test automation framework recommendations
                - Integration testing strategies
                - API testing approaches
                - Database testing requirements
                - Performance testing frameworks

                Ensure testing architecture supports development velocity.""",
                expected_output="technical_testing_architecture",
                handoff_conditions=["testing_architecture_defined", "automation_framework_selected"],
                priority="medium",
                timeout_minutes=15,
                required_context=["business_testing_requirements", "system_architecture"]
            ),
            WorkflowStep(
                agent_type="coder",
                instruction="""Develop practical testing implementation approach.
                Create:
                - Test case templates and examples
                - Test data management strategies
                - CI/CD integration for automated testing
                - Test reporting and metrics collection
                - Debugging and troubleshooting approaches

                Ensure testing is practical and maintainable.""",
                expected_output="testing_implementation_plan",
                handoff_conditions=["testing_plan_complete", "implementation_guidelines_provided"],
                priority="medium",
                timeout_minutes=13,
                required_context=["technical_testing_architecture", "development_standards"]
            )
        ]
    )

    # Deployment Planning Workflow
    DEPLOYMENT_PLANNING_COLLABORATION = WorkflowTemplate(
        name="Deployment Planning Collaboration",
        description="Comprehensive deployment planning with risk assessment and rollback strategies",
        workflow_type=WorkflowType.DEPLOYMENT_PLANNING,
        max_duration_minutes=35,
        required_agents=["architect", "analyst", "coder"],
        success_criteria=[
            "Complete deployment plan with phases",
            "Rollback strategies defined",
            "Risk mitigation plan developed",
            "Monitoring and alerting configured"
        ],
        steps=[
            WorkflowStep(
                agent_type="architect",
                instruction="""Design deployment architecture and infrastructure requirements.
                Define:
                - Target deployment environments
                - Infrastructure requirements and scaling
                - Containerization and orchestration strategy
                - Database migration and data seeding plans
                - Security and compliance requirements

                Ensure deployment architecture supports business continuity.""",
                expected_output="deployment_architecture",
                handoff_conditions=["deployment_architecture_defined", "infrastructure_requirements_specified"],
                priority="high",
                timeout_minutes=12,
                required_context=["system_architecture", "business_requirements"]
            ),
            WorkflowStep(
                agent_type="analyst",
                instruction="""Assess business impact and risk of deployment.
                Evaluate:
                - Business continuity during deployment
                - User impact and communication requirements
                - Rollback procedures and business recovery
                - Success metrics and KPIs for deployment
                - Stakeholder communication and training needs

                Ensure deployment minimizes business disruption.""",
                expected_output="deployment_risk_assessment",
                handoff_conditions=["business_impact_assessed", "rollback_plan_defined"],
                priority="high",
                timeout_minutes=10,
                required_context=["deployment_architecture", "business_requirements"]
            ),
            WorkflowStep(
                agent_type="coder",
                instruction="""Develop detailed deployment implementation and automation.
                Create:
                - Deployment scripts and automation
                - Configuration management approach
                - Monitoring and alerting setup
                - Post-deployment validation procedures
                - Documentation and runbooks

                Ensure deployment is automated, reliable, and well-documented.""",
                expected_output="deployment_implementation",
                handoff_conditions=["deployment_automated", "monitoring_configured"],
                priority="high",
                timeout_minutes=13,
                required_context=["deployment_risk_assessment", "deployment_architecture"]
            )
        ]
    )

    @classmethod
    def get_template(cls, workflow_type: WorkflowType) -> WorkflowTemplate:
        """Get workflow template by type.

        Args:
            workflow_type: The type of workflow template to retrieve

        Returns:
            WorkflowTemplate instance

        Raises:
            ValueError: If workflow type is not supported
        """
        template_map = {
            WorkflowType.REQUIREMENTS_ANALYSIS: cls.COMPREHENSIVE_ANALYSIS,
            WorkflowType.SYSTEM_DESIGN: cls.SYSTEM_DESIGN_COLLABORATION,
            WorkflowType.CODE_REVIEW: cls.CODE_REVIEW_COLLABORATION,
            WorkflowType.TESTING_STRATEGY: cls.TESTING_STRATEGY_COLLABORATION,
            WorkflowType.DEPLOYMENT_PLANNING: cls.DEPLOYMENT_PLANNING_COLLABORATION
        }

        if workflow_type not in template_map:
            available_types = [wt.value for wt in template_map.keys()]
            raise ValueError(f"Unsupported workflow type: {workflow_type.value}. "
                           f"Available types: {available_types}")

        return template_map[workflow_type]

    @classmethod
    def list_available_templates(cls) -> Dict[str, Dict[str, Any]]:
        """List all available workflow templates with metadata.

        Returns:
            Dictionary mapping template names to metadata
        """
        templates = [
            cls.COMPREHENSIVE_ANALYSIS,
            cls.SYSTEM_DESIGN_COLLABORATION,
            cls.CODE_REVIEW_COLLABORATION,
            cls.TESTING_STRATEGY_COLLABORATION,
            cls.DEPLOYMENT_PLANNING_COLLABORATION
        ]

        return {
            template.name: {
                "description": template.description,
                "workflow_type": template.workflow_type.value,
                "max_duration_minutes": template.max_duration_minutes,
                "required_agents": template.required_agents,
                "step_count": len(template.steps),
                "success_criteria": template.success_criteria
            }
            for template in templates
        }

    @classmethod
    def get_template_for_agents(cls, available_agents: List[str]) -> List[WorkflowTemplate]:
        """Get workflow templates that can be executed with available agents.

        Args:
            available_agents: List of available agent types

        Returns:
            List of compatible workflow templates
        """
        all_templates = [
            cls.COMPREHENSIVE_ANALYSIS,
            cls.SYSTEM_DESIGN_COLLABORATION,
            cls.CODE_REVIEW_COLLABORATION,
            cls.TESTING_STRATEGY_COLLABORATION,
            cls.DEPLOYMENT_PLANNING_COLLABORATION
        ]

        compatible_templates = []
        for template in all_templates:
            # Check if all required agents are available
            if all(agent in available_agents for agent in template.required_agents):
                compatible_templates.append(template)

        return compatible_templates

    @classmethod
    def create_custom_template(cls,
                             name: str,
                             description: str,
                             workflow_type: WorkflowType,
                             steps: List[WorkflowStep],
                             required_agents: List[str],
                             max_duration_minutes: int = 30) -> WorkflowTemplate:
        """Create a custom workflow template.

        Args:
            name: Template name
            description: Template description
            workflow_type: Type of workflow
            steps: List of workflow steps
            required_agents: List of required agent types
            max_duration_minutes: Maximum duration in minutes

        Returns:
            Custom WorkflowTemplate instance
        """
        return WorkflowTemplate(
            name=name,
            description=description,
            workflow_type=workflow_type,
            steps=steps,
            max_duration_minutes=max_duration_minutes,
            required_agents=required_agents,
            success_criteria=["Custom workflow completed successfully"],
            fallback_strategies={"default": "Continue with available agents"}
        )
