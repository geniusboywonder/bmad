"""Coder agent for comprehensive code generation and implementation."""

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


class CoderAgent(BaseAgent):
    """Coder agent specializing in code generation and implementation with AutoGen execution.
    
    The Coder is responsible for:
    - Production-ready code generation from Architect specifications
    - Quality assurance following established coding standards
    - Test creation including comprehensive unit tests
    - Edge case handling with proper validation logic
    - Documentation creation with clear code comments and API docs
    """
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any], db_session=None):
        """Initialize Coder agent with code generation optimization."""
        super().__init__(agent_type, llm_config)

        # Configure for code generation (balanced temperature for creativity and precision)
        self.llm_config.update({
            "model": llm_config.get("model", "gpt-4o"),  # Updated to use GPT-4o
            "temperature": 0.3,  # Balanced for code generation
        })

        # Initialize services
        self.db = db_session
        self.context_store = ContextStoreService(db_session) if db_session else None
        self.template_service = TemplateService() if db_session else None

        # Initialize AutoGen agent
        self._initialize_autogen_agent()

        logger.info("Coder agent initialized with enhanced code generation capabilities")
    
    def _create_system_message(self) -> str:
        """Create Coder-specific system message for AutoGen."""
        return """You are the Coder specializing in software development and implementation.

Your core expertise includes:
- Production-ready code generation following best practices
- Full-stack development across frontend and backend technologies
- Database implementation with proper ORM usage
- API development with comprehensive validation and error handling
- Test-driven development with unit and integration tests
- Code documentation and technical writing
- Performance optimization and security implementation

Development Principles:
- Write clean, readable, and maintainable code
- Follow SOLID principles and design patterns
- Implement comprehensive error handling and logging
- Include proper input validation and sanitization
- Write unit tests with high coverage (>80%)
- Add integration tests for critical workflows
- Document code with clear comments and docstrings
- Ensure type safety and proper typing

Code Quality Standards:
- Use consistent naming conventions and code style
- Implement proper separation of concerns
- Follow language-specific best practices
- Include appropriate logging and monitoring
- Handle edge cases and error conditions gracefully
- Optimize for performance without sacrificing readability
- Ensure security best practices are followed
- Make code modular and reusable

Testing Strategy:
- Write unit tests for all business logic
- Create integration tests for API endpoints
- Include end-to-end tests for user workflows
- Test error conditions and edge cases
- Validate input/output schemas and contracts
- Performance test critical components
- Security test authentication and authorization

Documentation Requirements:
- Add clear docstrings for all functions and classes
- Include inline comments for complex logic
- Create API documentation (OpenAPI/Swagger)
- Write README files for setup and usage
- Document configuration and environment requirements
- Provide examples and usage patterns

Technology Integration:
- Follow project architecture and technology choices
- Use established libraries and frameworks properly
- Implement database migrations and schema changes
- Integrate with external services and APIs
- Handle configuration management appropriately
- Ensure proper dependency management

Always respond with structured JSON containing:
- Complete source code implementations
- Unit test files with comprehensive coverage
- Configuration files and database migrations
- Documentation and setup instructions
- Performance and security considerations
- Code review checklist and quality metrics"""
    
    async def execute_task(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute coder task with enhanced implementation and code generation.

        Args:
            task: Task to execute with coding instructions
            context: Context artifacts from architecture and requirements

        Returns:
            Implementation result with source code, tests, documentation, and HITL requests
        """
        logger.info("Coder executing enhanced implementation task",
                   task_id=task.task_id,
                   context_count=len(context))

        try:
            # Step 1: Validate implementation completeness and identify gaps
            completeness_check = self._validate_implementation_completeness(context)
            logger.info("Implementation completeness check completed",
                       gaps_found=len(completeness_check.get("missing_elements", [])),
                       confidence=completeness_check.get("confidence_score", 0))

            # Step 2: Generate HITL requests for clarification if needed
            hitl_requests = []
            if completeness_check.get("requires_clarification", False):
                hitl_requests = self._generate_implementation_clarification_requests(
                    task, completeness_check.get("missing_elements", [])
                )
                logger.info("Generated HITL clarification requests",
                           request_count=len(hitl_requests))

            # Step 3: Prepare enhanced implementation context
            implementation_context = self._prepare_enhanced_implementation_context(task, context, completeness_check)

            # Step 4: Execute analysis with LLM reliability features
            raw_response = await self._execute_with_reliability(implementation_context, task)

            # Step 5: Parse and structure implementation response
            implementation_result = self._parse_implementation_response(raw_response, task)

            # Step 6: Generate professional implementation using BMAD templates
            implementation_document = await self._generate_implementation_from_template(implementation_result, task, context)

            # Step 7: Create context artifacts for results
            result_artifacts = self._create_implementation_artifacts(implementation_result, implementation_document, task)

            # Step 8: Final implementation validation
            final_validation = self._validate_final_implementation(implementation_result, implementation_document)

            logger.info("Coder task completed with enhanced features",
                       task_id=task.task_id,
                       files_created=len(implementation_result.get("source_files", [])),
                       tests_created=len(implementation_result.get("test_files", [])),
                       implementation_generated=bool(implementation_document),
                       hitl_requests=len(hitl_requests),
                       artifacts_created=len(result_artifacts))

            return {
                "success": True,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "output": implementation_result,
                "implementation_document": implementation_document,
                "implementation_summary": implementation_result.get("implementation_overview", {}),
                "code_metrics": implementation_result.get("code_metrics", {}),
                "hitl_requests": hitl_requests,
                "completeness_validation": final_validation,
                "artifacts_created": result_artifacts,
                "context_used": [str(artifact.context_id) for artifact in context]
            }

        except Exception as e:
            logger.error("Coder task execution failed",
                        task_id=task.task_id,
                        error=str(e))

            return {
                "success": False,
                "agent_type": self.agent_type.value,
                "task_id": str(task.task_id),
                "error": str(e),
                "fallback_implementation": self._create_fallback_implementation(),
                "context_used": [str(artifact.context_id) for artifact in context]
            }
    
    async def create_handoff(self, to_agent: AgentType, task: Task, 
                           context: List[ContextArtifact]) -> HandoffSchema:
        """Create structured handoff to another agent with implementation context.
        
        Args:
            to_agent: Target agent type for the handoff
            task: Current task being handed off
            context: Context artifacts to pass along
            
        Returns:
            HandoffSchema with implementation-aware handoff information
        """
        # Create handoff instructions based on target agent
        if to_agent == AgentType.TESTER:
            instructions = self._create_tester_handoff_instructions(context)
            expected_outputs = ["test_results", "quality_report", "bug_reports"]
            phase = "validate"
        elif to_agent == AgentType.DEPLOYER:
            instructions = self._create_deployer_handoff_instructions(context)
            expected_outputs = ["deployment_package", "deployment_logs", "monitoring_setup"]
            phase = "launch"
        else:
            # Generic handoff for other agents
            instructions = f"Proceed with {to_agent.value} tasks based on completed implementation"
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
            priority=2,  # Normal priority for coder handoffs
            metadata={
                "implementation_phase": "code_complete",
                "coder_task_id": str(task.task_id),
                "handoff_reason": "implementation_complete",
                "code_summary": self._create_code_summary(context),
                "testing_requirements": self._extract_testing_requirements(context),
                "deployment_readiness": self._assess_deployment_readiness(context)
            }
        )
        
        logger.info("Coder handoff created",
                   to_agent=to_agent.value,
                   phase=phase,
                   implementation_context=len(context))
        
        return handoff
    
    def _prepare_implementation_context(self, task: Task, context: List[ContextArtifact]) -> str:
        """Prepare context message for code implementation."""
        
        context_parts = [
            "CODE IMPLEMENTATION TASK:",
            f"Task: {task.instructions}",
            "",
            "PROJECT CONTEXT:",
            f"Project ID: {task.project_id}",
            f"Task ID: {task.task_id}",
            "",
            "IMPLEMENTATION SPECIFICATIONS:",
        ]
        
        if not context:
            context_parts.append("- No specifications context available (this may require clarification)")
        else:
            for i, artifact in enumerate(context):
                context_parts.extend([
                    f"",
                    f"Specification {i+1} from {artifact.source_agent} ({artifact.artifact_type}):",
                    f"Content: {str(artifact.content)[:1200]}..." if len(str(artifact.content)) > 1200 else f"Content: {artifact.content}",
                ])
        
        context_parts.extend([
            "",
            "IMPLEMENTATION REQUIREMENTS:",
            "Generate production-ready code including:",
            "",
            "1. **Backend Implementation**",
            "   - API endpoints with proper HTTP methods and status codes",
            "   - Database models with relationships and constraints",
            "   - Business logic with proper error handling",
            "   - Authentication and authorization implementation",
            "   - Input validation and sanitization",
            "",
            "2. **Database Implementation**",
            "   - SQLAlchemy models following schema specifications",
            "   - Database migrations for schema changes",
            "   - Proper indexing for performance optimization",
            "   - Data validation and integrity constraints",
            "",
            "3. **API Implementation**",
            "   - FastAPI router implementations",
            "   - Pydantic models for request/response validation",
            "   - OpenAPI documentation generation",
            "   - Comprehensive error handling with proper status codes",
            "",
            "4. **Testing Implementation**",
            "   - Unit tests with >80% code coverage",
            "   - Integration tests for API endpoints",
            "   - Test fixtures and mock configurations",
            "   - Performance tests for critical components",
            "",
            "5. **Code Quality**",
            "   - Type hints and proper typing throughout",
            "   - Docstrings for all functions and classes",
            "   - Consistent code style and naming conventions",
            "   - Logging and monitoring integration",
            "",
            "6. **Configuration and Setup**",
            "   - Environment configuration management",
            "   - Dependency management (requirements.txt/pyproject.toml)",
            "   - Docker configuration if specified",
            "   - Database connection and migration setup",
            "",
            "OUTPUT FORMAT:",
            "Provide structured JSON with complete implementation files.",
            "",
            "Ensure all code is production-ready and follows best practices."
        ])
        
        return "\n".join(context_parts)
    
    def _parse_implementation_response(self, raw_response: str, task: Task) -> Dict[str, Any]:
        """Parse and structure the code implementation response."""
        
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
                    response_data = self._extract_implementation_from_text(raw_response)
            
            # Structure the implementation result
            structured_implementation = {
                "implementation_type": "full_stack_implementation",
                "status": "completed",
                "implementation_overview": response_data.get("implementation_overview", {
                    "project_type": "web_application",
                    "technology_stack": "FastAPI + PostgreSQL",
                    "description": "Complete backend implementation with API endpoints and database"
                }),
                "source_files": response_data.get("source_files", []),
                "test_files": response_data.get("test_files", []),
                "configuration_files": response_data.get("configuration_files", []),
                "database_migrations": response_data.get("database_migrations", []),
                "api_documentation": response_data.get("api_documentation", {}),
                "setup_instructions": response_data.get("setup_instructions", []),
                "dependencies": response_data.get("dependencies", []),
                "environment_variables": response_data.get("environment_variables", []),
                "code_metrics": response_data.get("code_metrics", {}),
                "security_features": response_data.get("security_features", []),
                "performance_optimizations": response_data.get("performance_optimizations", []),
                "testing_strategy": response_data.get("testing_strategy", {}),
                "deployment_notes": response_data.get("deployment_notes", []),
                "known_limitations": response_data.get("known_limitations", []),
                "next_steps": response_data.get("next_steps", []),
                "code_quality_score": response_data.get("code_quality_score", 0.8),
                "test_coverage_estimate": response_data.get("test_coverage_estimate", 0.85)
            }
            
            return structured_implementation
            
        except Exception as e:
            logger.warning("Failed to parse implementation response, using fallback",
                          error=str(e))
            return self._create_fallback_implementation(raw_response)
    
    def _extract_implementation_from_text(self, text_response: str) -> Dict[str, Any]:
        """Extract implementation information from text response when JSON parsing fails."""
        
        sections = {}
        
        # Look for code blocks or implementation sections
        import re
        
        # Source code
        code_matches = re.findall(r'```(?:python|py)?\n(.*?)\n```', text_response, re.DOTALL)
        if code_matches:
            sections["source_files"] = [{"filename": f"implementation_{i+1}.py", "content": code} 
                                       for i, code in enumerate(code_matches)]
        
        # Test code
        test_matches = re.findall(r'(?i)test.*?```(?:python|py)?\n(.*?)\n```', text_response, re.DOTALL)
        if test_matches:
            sections["test_files"] = [{"filename": f"test_{i+1}.py", "content": test} 
                                     for i, test in enumerate(test_matches)]
        
        # Setup instructions
        setup_match = re.search(r'(?i)(setup|installation|getting started)[:.]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)', text_response)
        if setup_match:
            sections["setup_instructions"] = [setup_match.group(2).strip()]
        
        return sections
    
    def _create_fallback_implementation(self, raw_response: str = None) -> Dict[str, Any]:
        """Create fallback implementation response when parsing fails."""
        
        return {
            "implementation_type": "fallback_implementation",
            "status": "completed_with_fallback",
            "implementation_overview": {
                "project_type": "web_application",
                "technology_stack": "FastAPI + PostgreSQL + React",
                "description": "Basic implementation structure with core components",
                "architecture_pattern": "MVC with service layer"
            },
            "source_files": [
                {
                    "filename": "main.py",
                    "content": '''"""Main FastAPI application entry point."""
from fastapi import FastAPI
from app.api import projects, tasks
from app.database.connection import init_db

app = FastAPI(title="Project API", version="1.0.0")

# Include routers
app.include_router(projects.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "API is running"}
''',
                    "type": "main_application",
                    "description": "FastAPI application entry point with router setup"
                },
                {
                    "filename": "models.py",
                    "content": '''"""Database models using SQLAlchemy."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="project")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="tasks")
''',
                    "type": "database_models",
                    "description": "SQLAlchemy models for core entities"
                }
            ],
            "test_files": [
                {
                    "filename": "test_main.py",
                    "content": '''"""Tests for main application."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}

def test_api_health():
    response = client.get("/api/v1/projects")
    assert response.status_code in [200, 404]  # May not have data
''',
                    "type": "api_tests",
                    "description": "Basic API endpoint tests"
                }
            ],
            "configuration_files": [
                {
                    "filename": "requirements.txt",
                    "content": '''fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.7
pydantic==2.4.2
pytest==7.4.3
httpx==0.25.2
''',
                    "type": "dependencies",
                    "description": "Python package dependencies"
                }
            ],
            "database_migrations": [
                {
                    "filename": "001_initial_schema.sql",
                    "content": '''-- Initial database schema
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    title VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
''',
                    "type": "schema_migration",
                    "description": "Initial database schema setup"
                }
            ],
            "api_documentation": {
                "openapi_enabled": True,
                "docs_url": "/docs",
                "redoc_url": "/redoc",
                "title": "Project Management API",
                "version": "1.0.0"
            },
            "setup_instructions": [
                "Install Python 3.11+",
                "Install dependencies: pip install -r requirements.txt",
                "Set up PostgreSQL database",
                "Set environment variables for database connection",
                "Run migrations: python -m alembic upgrade head",
                "Start server: uvicorn app.main:app --reload"
            ],
            "dependencies": [
                "fastapi>=0.104.1",
                "uvicorn>=0.24.0",
                "sqlalchemy>=2.0.23",
                "psycopg2-binary>=2.9.7"
            ],
            "environment_variables": [
                "DATABASE_URL=postgresql://user:pass@localhost/dbname",
                "SECRET_KEY=your-secret-key-here",
                "DEBUG=false"
            ],
            "code_metrics": {
                "estimated_lines_of_code": 500,
                "estimated_test_coverage": 0.75,
                "complexity_score": "medium",
                "maintainability_score": 0.8
            },
            "security_features": [
                "Input validation using Pydantic models",
                "SQL injection protection via SQLAlchemy ORM",
                "Environment variable configuration for secrets"
            ],
            "performance_optimizations": [
                "Database indexing on commonly queried fields",
                "Async/await patterns for non-blocking I/O",
                "Connection pooling for database efficiency"
            ],
            "testing_strategy": {
                "unit_tests": "Business logic and utility functions",
                "integration_tests": "API endpoints with database",
                "test_coverage_target": 0.8,
                "testing_framework": "pytest"
            },
            "deployment_notes": [
                "Use Docker for containerization",
                "Set up reverse proxy (nginx) for production",
                "Configure environment-specific settings",
                "Set up database backups and monitoring"
            ],
            "known_limitations": [
                "Implementation parsing failed - may need human review",
                "Basic error handling may need enhancement",
                "Authentication system not fully implemented"
            ],
            "next_steps": [
                "Review and enhance generated code",
                "Implement comprehensive error handling",
                "Add authentication and authorization",
                "Expand test coverage to target levels"
            ],
            "code_quality_score": 0.6,
            "test_coverage_estimate": 0.7,
            "fallback_reason": "Implementation response parsing failed",
            "original_response": raw_response[:300] + "..." if raw_response and len(raw_response) > 300 else raw_response
        }
    
    def _create_tester_handoff_instructions(self, context: List[ContextArtifact]) -> str:
        """Create specific instructions for handoff to Tester agent."""
        
        instructions = """Based on the completed implementation, perform comprehensive testing and quality validation.

Your testing approach should include:

1. **Code Quality Validation**
   - Verify code follows best practices and coding standards
   - Check for proper error handling and edge case coverage
   - Validate type safety and proper documentation
   - Assess code maintainability and readability

2. **Functional Testing**
   - Test all implemented API endpoints with various inputs
   - Validate database operations and data integrity
   - Check business logic against original requirements
   - Test authentication and authorization mechanisms

3. **Integration Testing**
   - Verify component interactions and data flow
   - Test database connections and migrations
   - Validate external service integrations
   - Check system behavior under various load conditions

4. **Security Testing**
   - Validate input sanitization and validation
   - Test authentication and session management
   - Check for common security vulnerabilities
   - Verify proper error handling without information leakage

5. **Performance Testing**
   - Measure API response times and throughput
   - Test database query performance
   - Validate system behavior under expected load
   - Identify potential bottlenecks and optimizations

Please provide comprehensive test results with specific recommendations for improvements."""
        
        if context:
            code_details = self._extract_code_details(context)
            instructions += f"\n\nIMPLEMENTATION DETAILS TO TEST:\n{code_details}"
        
        return instructions
    
    def _create_deployer_handoff_instructions(self, context: List[ContextArtifact]) -> str:
        """Create specific instructions for handoff to Deployer agent."""
        
        instructions = """Based on the completed and tested implementation, prepare for deployment.

Your deployment approach should include:

1. **Deployment Package Preparation**
   - Create deployment-ready application package
   - Set up containerization (Docker) if specified
   - Prepare configuration files for target environment
   - Include all necessary dependencies and requirements

2. **Infrastructure Setup**
   - Configure target deployment environment
   - Set up database and required services
   - Configure load balancing and scaling if needed
   - Prepare monitoring and logging infrastructure

3. **Deployment Process**
   - Execute deployment to target environment
   - Run database migrations and setup scripts
   - Verify all services are running correctly
   - Perform post-deployment validation and health checks

4. **Monitoring and Maintenance**
   - Set up application monitoring and alerting
   - Configure log collection and analysis
   - Establish backup and recovery procedures
   - Create operational runbooks and documentation

Please ensure the deployment is production-ready with proper monitoring and maintenance procedures."""
        
        return instructions
    
    def _extract_code_details(self, context: List[ContextArtifact]) -> str:
        """Extract key code details from context for handoff instructions."""
        
        code_details = []
        
        for artifact in context:
            if isinstance(artifact.content, dict):
                # Extract source files count
                source_files = artifact.content.get("source_files", [])
                if source_files:
                    code_details.append(f"- Test {len(source_files)} source files for functionality")
                
                # Extract API endpoints
                api_docs = artifact.content.get("api_documentation", {})
                if api_docs:
                    code_details.append("- Validate API endpoints and documentation")
                
                # Extract testing strategy
                test_strategy = artifact.content.get("testing_strategy", {})
                if test_strategy:
                    coverage = test_strategy.get("test_coverage_target", 0.8)
                    code_details.append(f"- Validate test coverage meets target of {coverage*100}%")
        
        if not code_details:
            return "- Review all implementation artifacts for comprehensive testing"
        
        return "\n".join(code_details[:5])  # Limit to 5 items
    
    def _create_code_summary(self, context: List[ContextArtifact]) -> str:
        """Create summary of code implementation for handoff metadata."""
        
        if not context:
            return "No implementation context available"
        
        summary_parts = []
        for artifact in context:
            if isinstance(artifact.content, dict):
                source_count = len(artifact.content.get("source_files", []))
                test_count = len(artifact.content.get("test_files", []))
                summary_parts.append(f"{source_count} source files, {test_count} test files")
            else:
                summary_parts.append("implementation files")
        
        return ", ".join(summary_parts) if summary_parts else "basic code implementation"
    
    def _extract_testing_requirements(self, context: List[ContextArtifact]) -> str:
        """Extract testing requirements from context."""
        
        for artifact in context:
            if isinstance(artifact.content, dict):
                test_strategy = artifact.content.get("testing_strategy", {})
                if test_strategy:
                    coverage = test_strategy.get("test_coverage_target", 0.8)
                    framework = test_strategy.get("testing_framework", "pytest")
                    return f"coverage:{coverage},framework:{framework}"
        
        return "coverage:0.8,framework:pytest"
    
    def _assess_deployment_readiness(self, context: List[ContextArtifact]) -> str:
        """Assess deployment readiness based on implementation."""

        for artifact in context:
            if isinstance(artifact.content, dict):
                # Check if deployment notes exist
                deploy_notes = artifact.content.get("deployment_notes", [])
                config_files = artifact.content.get("configuration_files", [])

                if deploy_notes and config_files:
                    return "ready"
                elif deploy_notes or config_files:
                    return "partial"

        return "needs_preparation"

    def _validate_implementation_completeness(self, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Validate completeness of code implementation and identify gaps.

        Args:
            context: Context artifacts to analyze

        Returns:
            Completeness validation results
        """
        missing_elements = []
        confidence_score = 1.0
        requires_clarification = False

        # Check for architecture context
        architecture_found = any(
            artifact.artifact_type in ["technical_architecture", "architecture_design"] or
            (isinstance(artifact.content, dict) and artifact.content.get("architecture_type") == "technical_system_design")
            for artifact in context
        )

        if not architecture_found:
            missing_elements.append("architecture_context")
            confidence_score -= 0.4
            requires_clarification = True

        # Check for existing implementation artifacts
        existing_implementation = [
            artifact for artifact in context
            if isinstance(artifact.content, dict) and
            artifact.content.get("implementation_type") == "full_stack_implementation"
        ]

        if not existing_implementation:
            missing_elements.append("implementation_design")
            confidence_score -= 0.5
            requires_clarification = True

        # Check for specific implementation elements
        if existing_implementation:
            latest_implementation = existing_implementation[-1].content

            # Check source files
            source_files = latest_implementation.get("source_files", [])
            if len(source_files) < 2:
                missing_elements.append("source_files")
                confidence_score -= 0.2

            # Check test files
            test_files = latest_implementation.get("test_files", [])
            if len(test_files) < 1:
                missing_elements.append("test_files")
                confidence_score -= 0.15

            # Check configuration files
            config_files = latest_implementation.get("configuration_files", [])
            if len(config_files) < 1:
                missing_elements.append("configuration_files")
                confidence_score -= 0.1

            # Check API documentation
            api_docs = latest_implementation.get("api_documentation", {})
            if not api_docs:
                missing_elements.append("api_documentation")
                confidence_score -= 0.1

        # Determine if clarification is needed
        if confidence_score < 0.6 or len(missing_elements) > 3:
            requires_clarification = True

        return {
            "is_complete": len(missing_elements) == 0,
            "confidence_score": max(0.0, confidence_score),
            "missing_elements": missing_elements,
            "requires_clarification": requires_clarification,
            "existing_implementation_count": len(existing_implementation),
            "recommendations": self._generate_implementation_recommendations(missing_elements)
        }

    def _generate_implementation_recommendations(self, missing_elements: List[str]) -> List[str]:
        """Generate recommendations for addressing implementation gaps."""
        recommendations = []

        for element in missing_elements:
            if element == "architecture_context":
                recommendations.append("Gather detailed technical architecture before proceeding with implementation")
            elif element == "implementation_design":
                recommendations.append("Conduct comprehensive implementation design session")
            elif element == "source_files":
                recommendations.append("Implement core source files with proper structure")
            elif element == "test_files":
                recommendations.append("Create comprehensive test suite with high coverage")
            elif element == "configuration_files":
                recommendations.append("Set up proper configuration and environment management")
            elif element == "api_documentation":
                recommendations.append("Generate complete API documentation and specifications")

        return recommendations

    def _generate_implementation_clarification_requests(self, task: Task, missing_elements: List[str]) -> List[Dict[str, Any]]:
        """Generate HITL requests for implementation clarification.

        Args:
            task: Current task
            missing_elements: List of missing implementation elements

        Returns:
            List of HITL request configurations
        """
        hitl_requests = []

        for element in missing_elements:
            if element == "architecture_context":
                hitl_requests.append({
                    "question": "Please provide the technical architecture or detailed specifications for implementation",
                    "options": ["Share architecture document", "Schedule implementation workshop", "Provide technical specifications"],
                    "priority": "high",
                    "reason": "Missing architecture context for implementation"
                })

            elif element == "source_files":
                hitl_requests.append({
                    "question": "What are the core source files and their structure?",
                    "options": ["Define file structure", "Specify implementation approach", "Provide code examples"],
                    "priority": "high",
                    "reason": "Source file implementation required"
                })

            elif element == "test_files":
                hitl_requests.append({
                    "question": "What testing approach and coverage requirements should be implemented?",
                    "options": ["Specify test coverage target", "Define testing framework", "List critical test scenarios"],
                    "priority": "medium",
                    "reason": "Test implementation details needed"
                })

            elif element == "configuration_files":
                hitl_requests.append({
                    "question": "What configuration and environment setup is required?",
                    "options": ["Define environment variables", "Specify configuration files", "List deployment requirements"],
                    "priority": "medium",
                    "reason": "Configuration setup clarification needed"
                })

        return hitl_requests

    def _prepare_enhanced_implementation_context(self, task: Task, context: List[ContextArtifact],
                                               completeness_check: Dict[str, Any]) -> str:
        """Prepare enhanced implementation context with completeness information."""

        base_context = self._prepare_implementation_context(task, context)

        # Add completeness information
        completeness_info = [
            "",
            "IMPLEMENTATION COMPLETENESS STATUS:",
            f"Confidence Score: {completeness_check.get('confidence_score', 0):.2f}",
            f"Missing Elements: {', '.join(completeness_check.get('missing_elements', [])) or 'None'}",
            f"Requires Clarification: {completeness_check.get('requires_clarification', False)}",
        ]

        if completeness_check.get("recommendations"):
            completeness_info.extend([
                "",
                "IMPLEMENTATION RECOMMENDATIONS:",
                *[f"- {rec}" for rec in completeness_check["recommendations"][:3]]
            ])

        completeness_info.extend([
            "",
            "ENHANCED IMPLEMENTATION REQUIREMENTS:",
            "Focus on addressing the identified gaps while maintaining code quality.",
            "Generate specific clarification questions for technical stakeholders if needed.",
            "Ensure all code follows SOLID principles and best practices.",
            "Include comprehensive testing and documentation."
        ])

        return base_context + "\n".join(completeness_info)

    async def _generate_implementation_from_template(self, implementation_result: Dict[str, Any], task: Task,
                                                   context: List[ContextArtifact]) -> Optional[Dict[str, Any]]:
        """Generate professional implementation using BMAD templates.

        Args:
            implementation_result: Structured implementation results
            task: Current task
            context: Context artifacts

        Returns:
            Generated implementation document or None if template service unavailable
        """
        if not self.template_service:
            logger.warning("Template service not available, skipping implementation document generation")
            return None

        try:
            # Prepare template variables
            template_vars = {
                "project_id": str(task.project_id),
                "task_id": str(task.task_id),
                "implementation_date": datetime.now(timezone.utc).isoformat(),
                "implementation_overview": implementation_result.get("implementation_overview", {}),
                "source_files": implementation_result.get("source_files", []),
                "test_files": implementation_result.get("test_files", []),
                "configuration_files": implementation_result.get("configuration_files", []),
                "database_migrations": implementation_result.get("database_migrations", []),
                "api_documentation": implementation_result.get("api_documentation", {}),
                "setup_instructions": implementation_result.get("setup_instructions", []),
                "dependencies": implementation_result.get("dependencies", []),
                "environment_variables": implementation_result.get("environment_variables", []),
                "code_metrics": implementation_result.get("code_metrics", {}),
                "security_features": implementation_result.get("security_features", []),
                "performance_optimizations": implementation_result.get("performance_optimizations", []),
                "testing_strategy": implementation_result.get("testing_strategy", {}),
                "deployment_notes": implementation_result.get("deployment_notes", []),
                "known_limitations": implementation_result.get("known_limitations", []),
                "next_steps": implementation_result.get("next_steps", []),
                "code_quality_score": implementation_result.get("code_quality_score", 0.8),
                "test_coverage_estimate": implementation_result.get("test_coverage_estimate", 0.85)
            }

            # Generate implementation document using template
            implementation_content = await self.template_service.render_template_async(
                template_name="implementation-tmpl.yaml",
                variables=template_vars
            )

            logger.info("Implementation document generated from template",
                       template="implementation-tmpl.yaml",
                       content_length=len(str(implementation_content)))

            return {
                "document_type": "code_implementation_document",
                "template_used": "implementation-tmpl.yaml",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "content": implementation_content,
                "metadata": {
                    "code_quality_score": template_vars["code_quality_score"],
                    "test_coverage_estimate": template_vars["test_coverage_estimate"],
                    "source_files_count": len(template_vars["source_files"]),
                    "test_files_count": len(template_vars["test_files"])
                }
            }

        except Exception as e:
            logger.error("Failed to generate implementation document from template",
                        error=str(e),
                        template="implementation-tmpl.yaml")
            return None

    def _create_implementation_artifacts(self, implementation_result: Dict[str, Any],
                                       implementation_document: Optional[Dict[str, Any]], task: Task) -> List[str]:
        """Create context artifacts for implementation results.

        Args:
            implementation_result: Structured implementation results
            implementation_document: Generated implementation document
            task: Current task

        Returns:
            List of created artifact IDs
        """
        if not self.context_store:
            logger.warning("Context store not available, skipping artifact creation")
            return []

        created_artifacts = []

        try:
            # Create implementation artifact
            implementation_artifact = self.context_store.create_artifact(
                project_id=task.project_id,
                source_agent=self.agent_type.value,
                artifact_type="code_implementation",
                content=implementation_result
            )
            created_artifacts.append(str(implementation_artifact.context_id))

            # Create implementation document artifact if available
            if implementation_document:
                document_artifact = self.context_store.create_artifact(
                    project_id=task.project_id,
                    source_agent=self.agent_type.value,
                    artifact_type="implementation_document",
                    content=implementation_document
                )
                created_artifacts.append(str(document_artifact.context_id))

            logger.info("Implementation artifacts created",
                       implementation_artifact=str(implementation_artifact.context_id),
                       document_artifact=created_artifacts[1] if len(created_artifacts) > 1 else None)

        except Exception as e:
            logger.error("Failed to create implementation artifacts",
                        error=str(e),
                        task_id=str(task.task_id))

        return created_artifacts

    def _validate_final_implementation(self, implementation_result: Dict[str, Any],
                                     implementation_document: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform final validation of implementation completeness and quality.

        Args:
            implementation_result: Structured implementation results
            implementation_document: Generated implementation document

        Returns:
            Final validation results
        """
        validation_results = {
            "overall_quality": "good",
            "issues_found": [],
            "recommendations": [],
            "ready_for_next_phase": True
        }

        # Check implementation completeness
        confidence = implementation_result.get("code_quality_score", 0.8)
        source_files = len(implementation_result.get("source_files", []))
        test_files = len(implementation_result.get("test_files", []))
        test_coverage = implementation_result.get("test_coverage_estimate", 0.85)

        if confidence < 0.6:
            validation_results["issues_found"].append("Low code quality score")
            validation_results["recommendations"].append("Consider code review and refactoring")
            validation_results["overall_quality"] = "needs_review"

        if source_files < 2:
            validation_results["issues_found"].append("Insufficient source files")
            validation_results["recommendations"].append("Implement core functionality")
            validation_results["overall_quality"] = "needs_improvement"

        if test_files < 1:
            validation_results["issues_found"].append("Missing test files")
            validation_results["recommendations"].append("Implement comprehensive test suite")
            validation_results["ready_for_next_phase"] = False

        if test_coverage < 0.7:
            validation_results["issues_found"].append("Low test coverage")
            validation_results["recommendations"].append("Increase test coverage to target levels")
            validation_results["overall_quality"] = "needs_improvement"

        # Check for critical missing elements
        critical_elements = ["source_files", "test_files", "configuration_files"]
        for element in critical_elements:
            if not implementation_result.get(element):
                validation_results["issues_found"].append(f"Missing {element}")
                validation_results["ready_for_next_phase"] = False

        # Check implementation document generation
        if not implementation_document:
            validation_results["issues_found"].append("Implementation document generation failed")
            validation_results["recommendations"].append("Manual implementation documentation recommended")

        # Determine overall readiness
        if validation_results["issues_found"] and validation_results["ready_for_next_phase"]:
            validation_results["ready_for_next_phase"] = False

        logger.info("Final implementation validation completed",
                   quality=validation_results["overall_quality"],
                   issues=len(validation_results["issues_found"]),
                   ready=validation_results["ready_for_next_phase"])

        return validation_results
