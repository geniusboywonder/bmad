"""
End-to-End tests for Story 2.2: Context Persistence (Sprint 2)

Test scenarios:
- 2.2-E2E-001: Agent workflow with context persistence (P1)
"""

import pytest
import unittest.mock
from uuid import UUID
from fastapi.testclient import TestClient
from fastapi import status

from app.models.agent import AgentType
from app.models.context import ArtifactType
from app.models.task import TaskStatus
from app.schemas.handoff import HandoffSchema
from tests.conftest import assert_performance_threshold


class TestAgentWorkflowWithContextPersistence:
    """Test scenario 2.2-E2E-001: Agent workflow with context persistence (P1)"""
    
    @pytest.mark.e2e
    @pytest.mark.p1
    @pytest.mark.context
    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_complete_agent_workflow_with_persistent_context(
        self, client: TestClient, db_session, orchestrator_service, 
        context_store_service, mock_autogen_service, performance_timer
    ):
        """Test complete agent workflow with context artifacts persisted between phases."""
        performance_timer.start()
        
        # Step 1: Create project
        project_data = {
            "name": "Context Persistence E2E Test",
            "description": "Testing context flow through complete workflow"
        }
        
        response = client.post("/api/v1/projects/", json=project_data)
        assert response.status_code == status.HTTP_201_CREATED
        project_id = UUID(response.json()["id"])
        
        # Step 2: Create initial user requirements artifact
        user_requirements = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={
                "project_type": "E-commerce Platform",
                "key_features": [
                    "User authentication and profiles",
                    "Product catalog with search",
                    "Shopping cart functionality",
                    "Payment processing",
                    "Order history and tracking",
                    "Admin dashboard"
                ],
                "technical_constraints": [
                    "Must be scalable to 10,000 concurrent users",
                    "Response time under 200ms",
                    "99.9% uptime requirement",
                    "GDPR compliance required",
                    "Mobile-first responsive design"
                ],
                "business_requirements": {
                    "launch_timeline": "6 months",
                    "budget_constraints": "medium",
                    "integration_requirements": ["payment gateways", "analytics", "email service"]
                }
            },
            artifact_metadata={
                "source": "stakeholder_interviews",
                "priority": "critical",
                "approval_status": "approved"
            }
        )
        
        # Step 3: Analysis Phase - Process requirements
        analysis_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analyze user requirements and create comprehensive project plan",
            context_ids=[user_requirements.context_id]
        )
        
        # Execute analysis with context
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            # Simulate context retrieval and processing
            context_artifacts = context_store_service.get_artifacts_by_ids(analysis_task.context_ids)
            assert len(context_artifacts) == 1
            user_context = context_artifacts[0]
            
            # Verify context content is accessible
            assert "E-commerce Platform" in user_context.content["project_type"]
            assert len(user_context.content["key_features"]) == 6
            assert "scalable" in user_context.content["technical_constraints"][0]
            
            # Execute analysis task
            dummy_analysis_handoff = HandoffSchema(
                handoff_id=analysis_task.task_id,
                from_agent=AgentType.ORCHESTRATOR.value,
                to_agent=analysis_task.agent_type,
                project_id=analysis_task.project_id,
                phase="analysis",
                context_summary="Initial analysis of user requirements for the e-commerce platform.",
                context_ids=[str(c) for c in analysis_task.context_ids],
                instructions=analysis_task.instructions,
                expected_outputs=["Comprehensive project plan"],
                priority='high',
            )
            analysis_result = await orchestrator_service.process_task_with_autogen(analysis_task, dummy_analysis_handoff)
            
            # Complete analysis
            orchestrator_service.update_task_status(
                analysis_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "requirements_analysis": "comprehensive analysis completed",
                    "identified_modules": ["auth", "catalog", "cart", "payment", "orders", "admin"],
                    "complexity_assessment": "high",
                    "estimated_effort": "6 months with 5 developers"
                }
            )
        
        # Step 4: Create analysis output artifact
        analysis_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={
                "project_overview": {
                    "name": "E-commerce Platform",
                    "type": "Web Application",
                    "complexity": "High"
                },
                "functional_requirements": [
                    {
                        "module": "authentication",
                        "features": ["registration", "login", "profile_management", "password_reset"],
                        "priority": "critical"
                    },
                    {
                        "module": "product_catalog", 
                        "features": ["product_listing", "search", "filtering", "categories"],
                        "priority": "critical"
                    },
                    {
                        "module": "shopping_cart",
                        "features": ["add_items", "remove_items", "quantity_update", "persist_cart"],
                        "priority": "high"
                    },
                    {
                        "module": "payment_processing",
                        "features": ["payment_gateway", "order_creation", "payment_confirmation"],
                        "priority": "critical"
                    }
                ],
                "non_functional_requirements": {
                    "performance": {"max_response_time": "200ms", "concurrent_users": 10000},
                    "availability": {"uptime": "99.9%", "maintenance_windows": "planned"},
                    "security": ["HTTPS", "data_encryption", "GDPR_compliance"],
                    "scalability": ["horizontal_scaling", "load_balancing", "caching"]
                },
                "technology_recommendations": {
                    "backend": "FastAPI with Python",
                    "frontend": "React with TypeScript", 
                    "database": "PostgreSQL with Redis cache",
                    "deployment": "Docker containers on AWS"
                },
                "project_timeline": {
                    "total_duration": "6 months",
                    "phases": [
                        {"name": "Foundation", "duration": "1 month"},
                        {"name": "Core Features", "duration": "3 months"},
                        {"name": "Integration", "duration": "1 month"},
                        {"name": "Testing & Deployment", "duration": "1 month"}
                    ]
                }
            },
            artifact_metadata={
                "created_by": AgentType.ANALYST.value,
                "analysis_depth": "comprehensive",
                "stakeholder_reviewed": True,
                "context_sources": [str(user_requirements.context_id)]
            }
        )
        
        # Step 5: Architecture Phase - Design system using analysis
        architecture_handoff = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Design comprehensive system architecture for e-commerce platform",
            "context_ids": [user_requirements.context_id, analysis_artifact.context_id],
            "expected_output": "Detailed technical architecture with component diagrams"
        }
        
        architecture_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=architecture_handoff
        )
        
        # Execute architecture phase with accumulated context
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            # Verify architect has access to both user requirements and analysis
            arch_context_artifacts = context_store_service.get_artifacts_by_ids(architecture_task.context_ids)
            assert len(arch_context_artifacts) == 2
            
            # Verify context types
            context_types = [artifact.artifact_type for artifact in arch_context_artifacts]
            assert ArtifactType.USER_INPUT in context_types
            assert ArtifactType.PROJECT_PLAN in context_types
            
            # Access specific context data for architecture decisions
            user_input_artifact = next(
                artifact for artifact in arch_context_artifacts 
                if artifact.artifact_type == ArtifactType.USER_INPUT
            )
            plan_artifact = next(
                artifact for artifact in arch_context_artifacts
                if artifact.artifact_type == ArtifactType.PROJECT_PLAN
            )
            
            # Verify rich context is available
            assert "10,000 concurrent users" in str(user_input_artifact.content["technical_constraints"][0])
            assert "FastAPI" in plan_artifact.content["technology_recommendations"]["backend"]
            
            # Create a dummy HandoffSchema object for the call
            dummy_architecture_handoff = HandoffSchema(
                handoff_id=architecture_task.task_id,
                from_agent=architecture_handoff["from_agent"],
                to_agent=architecture_handoff["to_agent"],
                project_id=architecture_task.project_id,
                phase="architecture",
                context_summary="Design of the system architecture based on the project plan.",
                context_ids=[str(c) for c in architecture_task.context_ids],
                instructions=architecture_handoff["task_instructions"],
                expected_outputs=[architecture_handoff["expected_output"]],
                priority='high'
            )
            await orchestrator_service.process_task_with_autogen(architecture_task, dummy_architecture_handoff)
            
            orchestrator_service.update_task_status(
                architecture_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "architecture_type": "Microservices with API Gateway",
                    "services_designed": 8,
                    "integration_points": 12,
                    "scalability_features": ["auto-scaling", "load balancing", "caching layers"]
                }
            )
        
        # Step 6: Create detailed architecture artifact
        architecture_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ARCHITECT.value,
            artifact_type=ArtifactType.SYSTEM_ARCHITECTURE,
            content={
                "architecture_style": "Microservices",
                "services": [
                    {
                        "name": "user-service",
                        "responsibilities": ["authentication", "user_profiles", "authorization"],
                        "data_stores": ["user_db", "session_cache"],
                        "apis": ["/auth", "/users", "/profiles"]
                    },
                    {
                        "name": "catalog-service",
                        "responsibilities": ["product_management", "search", "categories"],
                        "data_stores": ["product_db", "search_index"],
                        "apis": ["/products", "/categories", "/search"]
                    },
                    {
                        "name": "cart-service", 
                        "responsibilities": ["cart_management", "session_persistence"],
                        "data_stores": ["cart_cache", "cart_db"],
                        "apis": ["/cart", "/cart/items"]
                    },
                    {
                        "name": "order-service",
                        "responsibilities": ["order_processing", "payment_coordination", "fulfillment"],
                        "data_stores": ["order_db", "payment_logs"],
                        "apis": ["/orders", "/payments", "/fulfillment"]
                    }
                ],
                "infrastructure": {
                    "api_gateway": "Kong with rate limiting and auth",
                    "load_balancer": "AWS ALB with health checks",
                    "databases": {
                        "primary": "PostgreSQL cluster",
                        "cache": "Redis cluster", 
                        "search": "Elasticsearch cluster"
                    },
                    "monitoring": "Prometheus + Grafana",
                    "logging": "ELK stack"
                },
                "security_architecture": {
                    "authentication": "JWT with refresh tokens",
                    "authorization": "RBAC with service-to-service auth",
                    "encryption": "TLS 1.3 in transit, AES-256 at rest",
                    "compliance": "GDPR data handling patterns"
                },
                "scalability_design": {
                    "horizontal_scaling": "Kubernetes with HPA",
                    "caching_strategy": "Multi-layer caching (CDN, API, Database)",
                    "data_partitioning": "Sharding by user_id and product_category",
                    "performance_targets": "200ms p95 response time at 10k concurrent users"
                }
            },
            artifact_metadata={
                "created_by": AgentType.ARCHITECT.value,
                "architecture_review_status": "pending_review",
                "context_sources": [str(user_requirements.context_id), str(analysis_artifact.context_id)],
                "design_decisions_documented": True
            }
        )
        
        # Step 7: Implementation Phase - Code generation using architecture
        implementation_handoff = {
            "from_agent": AgentType.ARCHITECT.value,
            "to_agent": AgentType.CODER.value,
            "task_instructions": "Implement core services based on architecture design",
            "context_ids": [
                user_requirements.context_id,
                analysis_artifact.context_id, 
                architecture_artifact.context_id
            ],
            "expected_output": "Production-ready code for core microservices"
        }
        
        implementation_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=implementation_handoff
        )
        
        # Execute implementation with full context history
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            # Verify coder has access to complete context chain
            impl_context_artifacts = context_store_service.get_artifacts_by_ids(implementation_task.context_ids)
            assert len(impl_context_artifacts) == 3
            
            # Verify context progression through workflow
            context_timeline = sorted(impl_context_artifacts, key=lambda x: x.created_at)
            assert context_timeline[0].artifact_type == ArtifactType.USER_INPUT
            assert context_timeline[1].artifact_type == ArtifactType.PROJECT_PLAN
            assert context_timeline[2].artifact_type == ArtifactType.SYSTEM_ARCHITECTURE
            
            # Access architecture details for implementation
            arch_context = next(
                artifact for artifact in impl_context_artifacts
                if artifact.artifact_type == ArtifactType.SYSTEM_ARCHITECTURE
            )
            
            services = arch_context.content["services"]
            assert len(services) == 4
            assert any(service["name"] == "user-service" for service in services)
            assert any(service["name"] == "catalog-service" for service in services)
            
            # Execute implementation
            # Create a dummy HandoffSchema object for the call
            dummy_implementation_handoff = HandoffSchema(
                handoff_id=implementation_task.task_id,
                from_agent=implementation_handoff["from_agent"],
                to_agent=implementation_handoff["to_agent"],
                project_id=implementation_task.project_id,
                phase="coding",
                context_summary="Implementation of the core services based on the architecture.",
                context_ids=[str(c) for c in implementation_task.context_ids],
                instructions=implementation_handoff["task_instructions"],
                expected_outputs=[implementation_handoff["expected_output"]],
                priority='high'
            )
            await orchestrator_service.process_task_with_autogen(implementation_task, dummy_implementation_handoff)
            
            orchestrator_service.update_task_status(
                implementation_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "services_implemented": 4,
                    "total_endpoints": 15,
                    "code_coverage": "92%",
                    "performance_metrics": "meets architecture targets"
                }
            )
        
        # Step 8: Create implementation artifact with context traceability
        implementation_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.CODER.value,
            artifact_type=ArtifactType.SOURCE_CODE,
            content={
                "implementation_summary": "Core microservices implemented according to architecture",
                "services": [
                    {
                        "name": "user-service",
                        "files": ["auth.py", "users.py", "profiles.py"],
                        "endpoints": 5,
                        "tests": "unit + integration tests included"
                    },
                    {
                        "name": "catalog-service", 
                        "files": ["products.py", "categories.py", "search.py"],
                        "endpoints": 4,
                        "tests": "comprehensive test suite"
                    },
                    {
                        "name": "cart-service",
                        "files": ["cart.py", "session.py"],
                        "endpoints": 3, 
                        "tests": "cart logic fully tested"
                    },
                    {
                        "name": "order-service",
                        "files": ["orders.py", "payments.py", "fulfillment.py"],
                        "endpoints": 3,
                        "tests": "payment flow tested"
                    }
                ],
                "code_quality": {
                    "linting": "flake8 compliant",
                    "type_checking": "mypy validated",
                    "test_coverage": "92% line coverage",
                    "documentation": "docstrings for all public APIs"
                },
                "implementation_notes": {
                    "architecture_compliance": "follows microservices patterns",
                    "performance_optimizations": ["database connection pooling", "response caching", "async processing"],
                    "security_implementations": ["JWT authentication", "input validation", "SQL injection prevention"]
                }
            },
            artifact_metadata={
                "created_by": AgentType.CODER.value,
                "implementation_status": "core_complete",
                "context_sources": [
                    str(user_requirements.context_id),
                    str(analysis_artifact.context_id),
                    str(architecture_artifact.context_id)
                ],
                "traceability": {
                    "requirements_covered": "85%",
                    "architecture_implemented": "100%"
                }
            }
        )
        
        performance_timer.stop()
        
        # Step 9: Verify complete context persistence and traceability
        
        # Get final project status
        final_status = client.get(f"/api/v1/projects/{project_id}/status")
        assert final_status.status_code == status.HTTP_200_OK
        
        status_data = final_status.json()
        tasks = status_data["tasks"]
        
        # Verify workflow progression
        assert len(tasks) == 3  # Analysis, Architecture, Implementation
        completed_tasks = [task for task in tasks if task["status"] == TaskStatus.COMPLETED.value]
        assert len(completed_tasks) == 3
        
        # Verify agent progression
        agent_sequence = [task["agent_type"] for task in tasks]
        expected_agents = [AgentType.ANALYST.value, AgentType.ARCHITECT.value, AgentType.CODER.value]
        assert agent_sequence == expected_agents
        
        # Verify context artifact chain
        all_project_artifacts = context_store_service.get_artifacts_by_project(project_id)
        assert len(all_project_artifacts) == 4  # User input + Analysis + Architecture + Implementation
        
        # Verify context types progression
        artifact_types = [artifact.artifact_type for artifact in all_project_artifacts]
        expected_types = [
            ArtifactType.USER_INPUT,
            ArtifactType.PROJECT_PLAN, 
            ArtifactType.SYSTEM_ARCHITECTURE,
            ArtifactType.SOURCE_CODE
        ]
        for expected_type in expected_types:
            assert expected_type in artifact_types
        
        # Verify context traceability - each artifact should reference previous ones
        final_artifact = next(
            artifact for artifact in all_project_artifacts
            if artifact.artifact_type == ArtifactType.SOURCE_CODE
        )
        
        context_sources = final_artifact.artifact_metadata.get("context_sources", [])
        assert len(context_sources) == 3  # References all previous artifacts
        
        # Verify context data integrity through workflow
        user_artifact = next(
            artifact for artifact in all_project_artifacts
            if artifact.artifact_type == ArtifactType.USER_INPUT
        )
        
        # Original requirements should be preserved
        assert "E-commerce Platform" in user_artifact.content["project_type"]
        assert len(user_artifact.content["key_features"]) == 6
        
        # Analysis artifact should reflect requirements
        analysis_final = next(
            artifact for artifact in all_project_artifacts
            if artifact.artifact_type == ArtifactType.PROJECT_PLAN
        )
        assert "e-commerce" in analysis_final.content["project_overview"]["name"].lower()
        
        # Architecture should be based on analysis
        arch_final = next(
            artifact for artifact in all_project_artifacts
            if artifact.artifact_type == ArtifactType.SYSTEM_ARCHITECTURE
        )
        assert len(arch_final.content["services"]) == 4
        
        # Implementation should follow architecture
        impl_final = next(
            artifact for artifact in all_project_artifacts
            if artifact.artifact_type == ArtifactType.SOURCE_CODE
        )
        assert len(impl_final.content["services"]) == 4
        
        # Verify performance
        assert_performance_threshold(
            performance_timer.elapsed_ms,
            15000,  # 15 seconds for complete workflow
            "Complete agent workflow with context persistence"
        )
        
        # Verify context relationships and dependencies
        for artifact in all_project_artifacts[1:]:  # Skip user input
            if artifact.artifact_metadata and "context_sources" in artifact.artifact_metadata:
                # Each artifact should have context sources
                sources = artifact.artifact_metadata["context_sources"]
                assert len(sources) > 0
                
                # Context sources should be retrievable
                source_artifacts = context_store_service.get_artifacts_by_ids(sources)
                assert len(source_artifacts) == len(sources)
    
    @pytest.mark.e2e
    @pytest.mark.p2
    @pytest.mark.context
    @pytest.mark.workflow
    def test_context_artifact_versioning_in_workflow(
        self, client: TestClient, db_session, orchestrator_service, context_store_service
    ):
        """Test context artifact versioning and updates during workflow execution."""
        # Create project
        project_data = {"name": "Context Versioning Test"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = UUID(response.json()["id"])
        
        # Create initial requirements
        initial_requirements = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={
                "features": ["user_auth", "product_catalog"],
                "version": "1.0"
            },
            artifact_metadata={"version": "1.0", "is_latest": True}
        )
        
        # Analysis phase creates plan based on v1.0 requirements
        analysis_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analyze requirements v1.0",
            context_ids=[initial_requirements.context_id]
        )
        
        orchestrator_service.update_task_status(
            analysis_task.task_id,
            TaskStatus.COMPLETED,
            output={"analysis": "based on v1.0 requirements"}
        )
        
        initial_plan = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={
                "plan": "Initial plan for auth and catalog",
                "based_on_requirements_version": "1.0"
            },
            artifact_metadata={
                "version": "1.0",
                "requirements_source": str(initial_requirements.context_id)
            }
        )
        
        # User updates requirements
        updated_requirements = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={
                "features": ["user_auth", "product_catalog", "shopping_cart", "payments"],
                "version": "2.0", 
                "changes": "Added shopping cart and payment features"
            },
            artifact_metadata={
                "version": "2.0",
                "is_latest": True,
                "previous_version": str(initial_requirements.context_id)
            }
        )
        
        # Update initial requirements to not be latest
        context_store_service.update_artifact(
            initial_requirements.context_id,
            artifact_metadata={
                "version": "1.0",
                "is_latest": False,
                "next_version": str(updated_requirements.context_id)
            }
        )
        
        # New analysis task using updated requirements
        updated_analysis_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Re-analyze with updated requirements v2.0",
            context_ids=[updated_requirements.context_id]
        )
        
        orchestrator_service.update_task_status(
            updated_analysis_task.task_id,
            TaskStatus.COMPLETED,
            output={"analysis": "updated based on v2.0 requirements"}
        )
        
        updated_plan = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={
                "plan": "Updated plan including cart and payments",
                "based_on_requirements_version": "2.0"
            },
            artifact_metadata={
                "version": "2.0",
                "requirements_source": str(updated_requirements.context_id),
                "supersedes": str(initial_plan.context_id)
            }
        )
        
        # Verify version chain
        all_artifacts = context_store_service.get_artifacts_by_project(project_id)
        requirements_artifacts = [
            artifact for artifact in all_artifacts
            if artifact.artifact_type == ArtifactType.USER_INPUT
        ]
        plan_artifacts = [
            artifact for artifact in all_artifacts
            if artifact.artifact_type == ArtifactType.PROJECT_PLAN
        ]
        
        assert len(requirements_artifacts) == 2  # v1.0 and v2.0
        assert len(plan_artifacts) == 2  # Based on v1.0 and v2.0
        
        # Verify latest versions
        latest_requirements = next(
            artifact for artifact in requirements_artifacts
            if artifact.artifact_metadata.get("is_latest", False)
        )
        assert latest_requirements.content["version"] == "2.0"
        assert len(latest_requirements.content["features"]) == 4  # Added features
        
        # Verify version references
        latest_plan = next(
            artifact for artifact in plan_artifacts
            if artifact.content["based_on_requirements_version"] == "2.0"
        )
        assert str(updated_requirements.context_id) in latest_plan.artifact_metadata["requirements_source"]