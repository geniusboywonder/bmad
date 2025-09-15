#!/usr/bin/env python3
"""Custom BMAD Tools for ADK Integration.

This module creates custom tools specifically designed for BMAD workflows,
integrating seamlessly with ADK's tool ecosystem while leveraging BMAD's
business logic and domain expertise.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
import json

logger = structlog.get_logger(__name__)


@dataclass
class BMADToolResult:
    """Result structure for BMAD custom tools."""
    success: bool
    data: Any
    metadata: Dict[str, Any]
    execution_time: float
    tool_name: str
    timestamp: datetime


class BMADRequirementsAnalyzer:
    """Custom tool for analyzing project requirements using BMAD methodology."""

    def __init__(self):
        self.analysis_templates = {
            "functional": self._analyze_functional_requirements,
            "non_functional": self._analyze_non_functional_requirements,
            "user_stories": self._generate_user_stories,
            "acceptance_criteria": self._generate_acceptance_criteria
        }

    async def analyze_requirements(self, requirements_text: str,
                                 analysis_type: str = "comprehensive") -> BMADToolResult:
        """Analyze requirements using BMAD methodology."""
        start_time = asyncio.get_event_loop().time()

        try:
            if analysis_type == "comprehensive":
                results = await self._comprehensive_analysis(requirements_text)
            else:
                analysis_func = self.analysis_templates.get(analysis_type)
                if analysis_func:
                    results = await analysis_func(requirements_text)
                else:
                    results = {"error": f"Unknown analysis type: {analysis_type}"}

            execution_time = asyncio.get_event_loop().time() - start_time

            return BMADToolResult(
                success=True,
                data=results,
                metadata={
                    "analysis_type": analysis_type,
                    "input_length": len(requirements_text),
                    "processing_method": "bmad_methodology"
                },
                execution_time=execution_time,
                tool_name="requirements_analyzer",
                timestamp=datetime.now()
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Requirements analysis failed: {e}")

            return BMADToolResult(
                success=False,
                data={"error": str(e)},
                metadata={"analysis_type": analysis_type},
                execution_time=execution_time,
                tool_name="requirements_analyzer",
                timestamp=datetime.now()
            )

    async def _comprehensive_analysis(self, requirements_text: str) -> Dict[str, Any]:
        """Perform comprehensive requirements analysis."""
        # Functional requirements analysis
        functional = await self._analyze_functional_requirements(requirements_text)

        # Non-functional requirements analysis
        non_functional = await self._analyze_non_functional_requirements(requirements_text)

        # User stories generation
        user_stories = await self._generate_user_stories(requirements_text)

        # Acceptance criteria
        acceptance_criteria = await self._generate_acceptance_criteria(requirements_text)

        return {
            "functional_requirements": functional,
            "non_functional_requirements": non_functional,
            "user_stories": user_stories,
            "acceptance_criteria": acceptance_criteria,
            "analysis_summary": {
                "total_user_stories": len(user_stories),
                "functional_requirements_count": len(functional),
                "non_functional_requirements_count": len(non_functional),
                "acceptance_criteria_count": len(acceptance_criteria)
            }
        }

    async def _analyze_functional_requirements(self, text: str) -> List[str]:
        """Extract functional requirements."""
        # In a real implementation, this would use NLP/ML to extract requirements
        # For demo purposes, we'll use pattern matching
        functional_keywords = ["shall", "should", "must", "will", "can", "user can", "system shall"]
        sentences = text.split('.')

        functional_reqs = []
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in functional_keywords):
                functional_reqs.append(sentence)

        return functional_reqs[:10]  # Limit to top 10

    async def _analyze_non_functional_requirements(self, text: str) -> List[str]:
        """Extract non-functional requirements."""
        non_functional_keywords = ["performance", "security", "usability", "reliability",
                                 "scalability", "availability", "response time", "throughput"]
        sentences = text.split('.')

        non_functional_reqs = []
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in non_functional_keywords):
                non_functional_reqs.append(sentence)

        return non_functional_reqs[:5]  # Limit to top 5

    async def _generate_user_stories(self, text: str) -> List[str]:
        """Generate user stories from requirements."""
        # Extract potential user roles and actions
        user_roles = ["user", "customer", "administrator", "manager", "developer"]
        actions = ["view", "create", "edit", "delete", "manage", "access", "login"]

        user_stories = []
        for role in user_roles:
            for action in actions:
                if role in text.lower() and action in text.lower():
                    story = f"As a {role}, I want to {action} so that I can accomplish my goals."
                    user_stories.append(story)

        return user_stories[:8]  # Limit to top 8

    async def _generate_acceptance_criteria(self, text: str) -> List[str]:
        """Generate acceptance criteria for requirements."""
        criteria_templates = [
            "Given the user is logged in, when they perform the action, then the system should respond within 2 seconds",
            "Given valid input data, when the operation is executed, then it should complete successfully",
            "Given invalid input data, when the operation is attempted, then the system should display an appropriate error message",
            "Given the user has appropriate permissions, when they access the feature, then they should see all expected elements",
            "Given the system is under load, when multiple users access simultaneously, then performance should remain acceptable"
        ]

        return criteria_templates[:6]  # Return first 6 criteria


class BMADArchitectureGenerator:
    """Custom tool for generating system architecture using BMAD patterns."""

    def __init__(self):
        self.architecture_patterns = {
            "microservices": self._generate_microservices_architecture,
            "monolithic": self._generate_monolithic_architecture,
            "serverless": self._generate_serverless_architecture,
            "hybrid": self._generate_hybrid_architecture
        }

    async def generate_architecture(self, requirements: Dict[str, Any],
                                  architecture_type: str = "microservices") -> BMADToolResult:
        """Generate system architecture based on requirements."""
        start_time = asyncio.get_event_loop().time()

        try:
            generator_func = self.architecture_patterns.get(architecture_type,
                                                          self._generate_microservices_architecture)
            architecture = await generator_func(requirements)

            execution_time = asyncio.get_event_loop().time() - start_time

            return BMADToolResult(
                success=True,
                data=architecture,
                metadata={
                    "architecture_type": architecture_type,
                    "requirements_processed": len(requirements),
                    "generation_method": "bmad_patterns"
                },
                execution_time=execution_time,
                tool_name="architecture_generator",
                timestamp=datetime.now()
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Architecture generation failed: {e}")

            return BMADToolResult(
                success=False,
                data={"error": str(e)},
                metadata={"architecture_type": architecture_type},
                execution_time=execution_time,
                tool_name="architecture_generator",
                timestamp=datetime.now()
            )

    async def _generate_microservices_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate microservices architecture."""
        services = []

        # Analyze requirements to determine services
        if "authentication" in str(requirements).lower():
            services.append({
                "name": "auth-service",
                "responsibility": "User authentication and authorization",
                "technology": "Node.js + JWT",
                "database": "Redis for sessions"
            })

        if "data" in str(requirements).lower():
            services.append({
                "name": "data-service",
                "responsibility": "Data processing and storage",
                "technology": "Python + FastAPI",
                "database": "PostgreSQL"
            })

        if "notification" in str(requirements).lower():
            services.append({
                "name": "notification-service",
                "responsibility": "Email and push notifications",
                "technology": "Go + RabbitMQ",
                "database": "MongoDB"
            })

        return {
            "architecture_type": "microservices",
            "services": services,
            "communication": "REST APIs + gRPC",
            "deployment": "Kubernetes",
            "monitoring": "Prometheus + Grafana",
            "scalability": "Auto-scaling based on load"
        }

    async def _generate_monolithic_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate monolithic architecture."""
        return {
            "architecture_type": "monolithic",
            "components": ["Web Layer", "Business Logic", "Data Access"],
            "technology": "Django/Python",
            "database": "PostgreSQL",
            "deployment": "Single server with load balancer",
            "scalability": "Vertical scaling"
        }

    async def _generate_serverless_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate serverless architecture."""
        return {
            "architecture_type": "serverless",
            "components": ["API Gateway", "Lambda Functions", "DynamoDB"],
            "technology": "AWS Lambda + API Gateway",
            "database": "DynamoDB",
            "deployment": "Serverless framework",
            "scalability": "Automatic scaling"
        }

    async def _generate_hybrid_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hybrid architecture."""
        return {
            "architecture_type": "hybrid",
            "components": {
                "frontend": "React SPA",
                "backend": "Microservices",
                "data": "Hybrid (SQL + NoSQL)",
                "deployment": "Kubernetes + Serverless"
            },
            "technology": "Mixed stack",
            "scalability": "Mixed scaling strategies"
        }


class BMADCodeGenerator:
    """Custom tool for generating code using BMAD patterns and best practices."""

    def __init__(self):
        self.code_templates = {
            "api_endpoint": self._generate_api_endpoint,
            "database_model": self._generate_database_model,
            "service_class": self._generate_service_class,
            "test_case": self._generate_test_case
        }

    async def generate_code(self, specification: Dict[str, Any],
                          code_type: str = "api_endpoint") -> BMADToolResult:
        """Generate code based on specification."""
        start_time = asyncio.get_event_loop().time()

        try:
            generator_func = self.code_templates.get(code_type, self._generate_api_endpoint)
            code = await generator_func(specification)

            execution_time = asyncio.get_event_loop().time() - start_time

            return BMADToolResult(
                success=True,
                data=code,
                metadata={
                    "code_type": code_type,
                    "specification_processed": len(specification),
                    "generation_method": "bmad_patterns"
                },
                execution_time=execution_time,
                tool_name="code_generator",
                timestamp=datetime.now()
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Code generation failed: {e}")

            return BMADToolResult(
                success=False,
                data={"error": str(e)},
                metadata={"code_type": code_type},
                execution_time=execution_time,
                tool_name="code_generator",
                timestamp=datetime.now()
            )

    async def _generate_api_endpoint(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API endpoint code."""
        endpoint_name = spec.get("endpoint", "/api/users")
        method = spec.get("method", "GET")
        description = spec.get("description", "User management endpoint")

        code = f'''
@app.{method.lower()}("{endpoint_name}")
async def {endpoint_name.replace("/", "_").replace("-", "_").strip("_")}(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    {description}

    This endpoint follows BMAD API patterns:
    - Input validation using Pydantic models
    - Proper error handling with HTTP status codes
    - Database transaction management
    - Audit logging for compliance
    """
    try:
        # Input validation
        # Business logic
        # Database operations
        # Response formatting

        return {{"success": True, "message": "{description} completed"}}

    except Exception as e:
        logger.error(f"API endpoint error: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
'''

        return {
            "language": "python",
            "framework": "FastAPI",
            "code": code.strip(),
            "dependencies": ["fastapi", "sqlalchemy", "pydantic"],
            "patterns_used": ["input_validation", "error_handling", "audit_logging"]
        }

    async def _generate_database_model(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate database model code."""
        model_name = spec.get("model", "User")
        fields = spec.get("fields", ["id", "name", "email"])

        code = f'''
class {model_name}(Base):
    """{model_name} database model following BMAD patterns."""

    __tablename__ = "{model_name.lower()}s"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Custom fields
'''

        for field in fields:
            if field != "id":
                code += f'    {field} = Column(String, index=True)\n'

        code += '''
    # Relationships
    # Add relationships as needed

    def __repr__(self):
        return f"<{model_name}(id={{self.id}}, name={{getattr(self, 'name', 'N/A')}})>"
'''

        return {
            "language": "python",
            "orm": "SQLAlchemy",
            "code": code.strip(),
            "patterns_used": ["base_model", "timestamps", "relationships"]
        }

    async def _generate_service_class(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate service class code."""
        service_name = spec.get("service", "UserService")

        code = f'''
class {service_name}:
    """{service_name} following BMAD service patterns."""

    def __init__(self, db: Session):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity with validation and audit logging."""
        try:
            # Input validation
            # Business logic validation
            # Database transaction
            # Audit logging

            return {{"success": True, "id": "generated_id"}}

        except Exception as e:
            logger.error(f"Create operation failed: {{e}}")
            raise

    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve entity by ID with caching."""
        try:
            # Cache check
            # Database query
            # Response formatting

            return {{"id": entity_id, "data": "entity_data"}}

        except Exception as e:
            logger.error(f"Get operation failed: {{e}}")
            return None

    async def update(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity with optimistic locking."""
        try:
            # Existence check
            # Business logic validation
            # Database update with versioning
            # Audit logging

            return {{"success": True, "updated": True}}

        except Exception as e:
            logger.error(f"Update operation failed: {{e}}")
            raise

    async def delete(self, entity_id: str) -> Dict[str, Any]:
        """Soft delete entity with audit trail."""
        try:
            # Existence check
            # Soft delete (update deleted_at)
            # Audit logging

            return {{"success": True, "deleted": True}}

        except Exception as e:
            logger.error(f"Delete operation failed: {{e}}")
            raise
'''

        return {
            "language": "python",
            "pattern": "service_layer",
            "code": code.strip(),
            "patterns_used": ["transaction_management", "audit_logging", "error_handling"]
        }

    async def _generate_test_case(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test case code."""
        test_name = spec.get("test", "test_user_operations")

        code = f'''
def {test_name}():
    """Test case following BMAD testing patterns."""

    # Arrange
    # Set up test data and mocks

    # Act
    # Execute the operation being tested

    # Assert
    # Verify expected behavior

    # Cleanup
    # Clean up test data

    pass
'''

        return {
            "language": "python",
            "framework": "pytest",
            "code": code.strip(),
            "patterns_used": ["arrange_act_assert", "test_isolation", "cleanup"]
        }


# Global tool instances
requirements_analyzer = BMADRequirementsAnalyzer()
architecture_generator = BMADArchitectureGenerator()
code_generator = BMADCodeGenerator()


async def analyze_requirements(requirements_text: str, analysis_type: str = "comprehensive") -> BMADToolResult:
    """Convenience function for requirements analysis."""
    return await requirements_analyzer.analyze_requirements(requirements_text, analysis_type)


async def generate_architecture(requirements: Dict[str, Any], architecture_type: str = "microservices") -> BMADToolResult:
    """Convenience function for architecture generation."""
    return await architecture_generator.generate_architecture(requirements, architecture_type)


async def generate_code(specification: Dict[str, Any], code_type: str = "api_endpoint") -> BMADToolResult:
    """Convenience function for code generation."""
    return await code_generator.generate_code(specification, code_type)


if __name__ == "__main__":
    print("🚀 BMAD Custom Tools Demo")
    print("=" * 50)

    async def run_demo():
        # Test requirements analysis
        sample_requirements = """
        The system shall allow users to login with email and password.
        Users must be able to view their dashboard after login.
        The system should respond within 2 seconds for all operations.
        User data must be encrypted and secure.
        """

        print("📋 Analyzing Requirements...")
        analysis_result = await analyze_requirements(sample_requirements)
        print(f"Analysis completed in {analysis_result.execution_time:.2f}s")
        print(f"Found {len(analysis_result.data.get('functional_requirements', []))} functional requirements")

        # Test architecture generation
        print("\n🏗️  Generating Architecture...")
        arch_result = await generate_architecture({"authentication": True, "data": True})
        print(f"Architecture generated: {arch_result.data.get('architecture_type')}")
        print(f"Services: {len(arch_result.data.get('services', []))}")

        # Test code generation
        print("\n💻 Generating Code...")
        code_result = await generate_code({"endpoint": "/api/users", "method": "GET"})
        print(f"Code generated for: {code_result.data.get('language')} {code_result.data.get('framework')}")

        print("\n✅ BMAD custom tools demo completed")

    asyncio.run(run_demo())
