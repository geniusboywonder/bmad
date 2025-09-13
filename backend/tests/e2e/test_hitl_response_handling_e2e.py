"""
End-to-End tests for Story 2.3: HITL Response Handling

Test scenarios:
- 2.3-E2E-001: Complete HITL approve workflow (P0)
- 2.3-E2E-002: Complete HITL amend workflow (P1)
"""

import pytest
import asyncio
import unittest.mock
from uuid import UUID
from fastapi.testclient import TestClient
from fastapi import status

from app.models.agent import AgentType
from app.models.context import ArtifactType
from app.models.task import TaskStatus
from app.models.hitl import HitlStatus, HitlAction
from app.schemas.handoff import HandoffSchema
from tests.conftest import assert_performance_threshold


class TestCompleteHitlApproveWorkflow:
    """Test scenario 2.3-E2E-001: Complete HITL approve workflow (P0)"""
    
    @pytest.mark.e2e
    @pytest.mark.p0
    @pytest.mark.hitl
    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_complete_hitl_approval_workflow(
        self, client: TestClient, db_session, orchestrator_service, 
        context_store_service, mock_autogen_service, performance_timer
    ):
        """Test complete workflow from task creation through HITL approval to continuation."""
        performance_timer.start()
        
        # Step 1: Create project
        project_data = {
            "name": "HITL Approval Workflow Test",
            "description": "Testing complete HITL approval process"
        }
        
        response = client.post("/api/v1/projects/", json=project_data)
        assert response.status_code == status.HTTP_201_CREATED
        project_id = UUID(response.json()["id"])
        
        # Step 2: Create initial context (user requirements)
        user_requirements = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={
                "project_goal": "Develop a customer relationship management system",
                "key_features": [
                    "Customer contact management",
                    "Sales pipeline tracking",
                    "Reporting and analytics",
                    "Email integration",
                    "Mobile accessibility"
                ],
                "performance_requirements": {
                    "response_time": "< 300ms",
                    "concurrent_users": 500,
                    "uptime": "99.5%"
                },
                "compliance_requirements": ["GDPR", "SOC2"],
                "timeline": "4 months development"
            }
        )
        
        # Step 3: Analysis Phase - Create and execute task
        analysis_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analyze CRM requirements and create detailed specification",
            context_ids=[user_requirements.context_id]
        )
        
        # Execute analysis with mock AutoGen
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            dummy_analysis_handoff = HandoffSchema(
                handoff_id=analysis_task.task_id,
                from_agent=AgentType.ORCHESTRATOR.value,
                to_agent=analysis_task.agent_type,
                project_id=analysis_task.project_id,
                phase="analysis",
                context_summary="Initial analysis of CRM requirements.",
                context_ids=[str(c) for c in analysis_task.context_ids],
                instructions=analysis_task.instructions,
                expected_outputs=["Detailed specification"],
                priority='high',
            )
            analysis_result = await orchestrator_service.process_task_with_autogen(analysis_task, dummy_analysis_handoff)
            
            # Complete analysis task
            orchestrator_service.update_task_status(
                analysis_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "requirements_analysis": "Comprehensive CRM analysis completed",
                    "feature_breakdown": {
                        "core_modules": ["contacts", "deals", "activities", "reports"],
                        "integrations": ["email", "calendar", "phone"],
                        "user_roles": ["admin", "sales_rep", "manager"]
                    },
                    "technical_recommendations": {
                        "architecture": "microservices",
                        "database": "PostgreSQL with Redis cache",
                        "frontend": "React SPA",
                        "api": "REST with GraphQL for complex queries"
                    }
                }
            )
        
        # Step 4: Create analysis output artifact
        analysis_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={
                "project_specification": {
                    "scope": "Full-featured CRM system",
                    "complexity": "Medium-High",
                    "estimated_effort": "4 months, 4 developers"
                },
                "functional_requirements": [
                    {
                        "module": "contact_management",
                        "features": ["CRUD operations", "search", "categorization", "import/export"],
                        "priority": "critical"
                    },
                    {
                        "module": "sales_pipeline",
                        "features": ["deal_tracking", "stage_management", "forecasting"],
                        "priority": "critical"
                    },
                    {
                        "module": "reporting",
                        "features": ["sales_reports", "activity_reports", "custom_dashboards"],
                        "priority": "high"
                    },
                    {
                        "module": "integrations",
                        "features": ["email_sync", "calendar_integration", "phone_system"],
                        "priority": "medium"
                    }
                ],
                "technical_architecture": {
                    "services": ["user-service", "contact-service", "deal-service", "report-service"],
                    "data_model": "normalized with audit trails",
                    "security": "JWT authentication, RBAC authorization",
                    "deployment": "containerized microservices on Kubernetes"
                },
                "quality_attributes": {
                    "performance": "sub-300ms response time",
                    "scalability": "horizontal scaling capable",
                    "reliability": "99.5% uptime with graceful degradation",
                    "security": "GDPR compliant, encrypted data"
                }
            },
            artifact_metadata={
                "review_required": True,
                "stakeholder_approval": "pending",
                "complexity_score": 7.5,
                "risk_assessment": "medium"
            }
        )
        
        # Step 5: Create HITL request for analysis review
        hitl_request = orchestrator_service.create_hitl_request(
            project_id=project_id,
            task_id=analysis_task.task_id,
            question="""
            Please review the CRM system analysis and specification:

            **Project Scope**: Full-featured Customer Relationship Management system
            **Timeline**: 4 months development with 4 developers
            **Architecture**: Microservices with PostgreSQL and Redis
            **Key Features**: Contact management, Sales pipeline, Reporting, Email integration

            **Technical Approach**:
            - REST API with GraphQL for complex queries
            - React frontend with responsive design
            - JWT authentication with role-based access control
            - Containerized deployment on Kubernetes

            **Quality Requirements**:
            - Response time: < 300ms
            - Concurrent users: 500
            - Uptime: 99.5%
            - GDPR and SOC2 compliance

            Please review and decide whether to:
            - APPROVE: Proceed with architecture design phase
            - REJECT: Requirements need significant revision
            - AMEND: Request specific improvements or clarifications
            """,
            options=["approve", "reject", "amend"],
            ttl_hours=48  # 48-hour review window
        )
        
        # Step 6: Verify HITL request creation
        hitl_get_response = client.get(f"/api/v1/hitl/{hitl_request.id}")
        assert hitl_get_response.status_code == status.HTTP_200_OK
        
        hitl_data = hitl_get_response.json()
        assert hitl_data["status"] == HitlStatus.PENDING.value
        assert hitl_data["project_id"] == str(project_id)
        assert hitl_data["task_id"] == str(analysis_task.task_id)
        assert "CRM system analysis" in hitl_data["question"]
        assert len(hitl_data["options"]) == 3
        
        # Step 7: Submit approval response (simulating stakeholder review)
        approval_response_data = {
            "action": "approve",
            "comment": """
            Excellent analysis! The requirements are well-structured and the technical approach is sound.

            **Strengths**:
            ✓ Comprehensive feature breakdown with clear priorities
            ✓ Appropriate technology stack for scalability requirements
            ✓ Good consideration of compliance and security needs
            ✓ Realistic timeline and resource estimates

            **Approval Decision**: 
            The analysis meets all requirements and provides a solid foundation for the architecture phase. 
            Approved to proceed with detailed system design.

            **Next Steps Guidance**:
            - Focus on API design and service boundaries
            - Plan data migration strategy for existing customer data
            - Design user experience workflows for key user journeys
            - Prepare detailed security implementation plan

            Approved for continuation to architecture phase.
            """,
            "metadata": {
                "reviewer_role": "product_owner",
                "review_duration_minutes": 45,
                "confidence_level": "high"
            }
        }
        
        approval_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json=approval_response_data
        )
        
        assert approval_response.status_code == status.HTTP_200_OK
        
        response_data = approval_response.json()
        assert response_data["action"] == "approve"
        assert response_data["workflow_resumed"] is True
        assert "hitl_request_id" in response_data
        assert response_data["hitl_request_id"] == str(hitl_request.id)
        
        # Step 8: Verify HITL request status updated
        updated_hitl_response = client.get(f"/api/v1/hitl/{hitl_request.id}")
        updated_hitl_data = updated_hitl_response.json()
        
        assert updated_hitl_data["status"] == HitlStatus.APPROVED.value
        assert updated_hitl_data["user_response"] == "approved"
        assert "Excellent analysis" in updated_hitl_data["response_comment"]
        assert updated_hitl_data["responded_at"] is not None
        
        # Step 9: Workflow continuation - Create architecture task
        architecture_handoff = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": """
            Create detailed system architecture for the approved CRM system specification.
            
            **Approved Requirements Context**:
            - Microservices architecture with 4 core services
            - PostgreSQL primary database with Redis caching
            - React frontend with JWT authentication
            - 500 concurrent users, <300ms response time
            - GDPR and SOC2 compliance required
            
            **Architecture Deliverables**:
            1. Service boundary design and API specifications
            2. Database schema design with audit trails
            3. Security architecture with RBAC implementation
            4. Deployment architecture for Kubernetes
            5. Integration patterns for email and calendar systems
            
            **Quality Focus**:
            - Performance optimization strategies
            - Scalability patterns and auto-scaling configuration
            - Security implementation details
            - Data privacy and compliance measures
            """,
            "context_ids": [user_requirements.context_id, analysis_artifact.context_id],
            "expected_output": "Comprehensive technical architecture specification ready for development"
        }
        
        architecture_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=architecture_handoff
        )
        
        # Step 10: Execute architecture task
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            dummy_architecture_handoff = HandoffSchema(
                handoff_id=architecture_task.task_id,
                from_agent=architecture_handoff["from_agent"],
                to_agent=architecture_handoff["to_agent"],
                project_id=architecture_task.project_id,
                phase="architecture",
                context_summary="Creation of detailed system architecture.",
                context_ids=[str(c) for c in architecture_task.context_ids],
                instructions=architecture_handoff["task_instructions"],
                expected_outputs=[architecture_handoff["expected_output"]],
                priority='high',
            )
            arch_result = await orchestrator_service.process_task_with_autogen(architecture_task, dummy_architecture_handoff)
            
            orchestrator_service.update_task_status(
                architecture_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "architecture_completed": True,
                    "services_designed": 4,
                    "api_endpoints": 32,
                    "security_layers": ["authentication", "authorization", "encryption", "audit"]
                }
            )
        
        # Step 11: Create architecture output
        architecture_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ARCHITECT.value,
            artifact_type=ArtifactType.SYSTEM_ARCHITECTURE,
            content={
                "architecture_overview": "Microservices-based CRM system approved after HITL review",
                "services_architecture": {
                    "user_service": {"responsibilities": ["authentication", "user_profiles", "permissions"]},
                    "contact_service": {"responsibilities": ["contact_crud", "search", "categorization"]},
                    "deal_service": {"responsibilities": ["pipeline_management", "forecasting", "reporting"]},
                    "integration_service": {"responsibilities": ["email_sync", "calendar", "external_apis"]}
                },
                "approval_context": {
                    "hitl_approved": True,
                    "approved_by": "product_owner",
                    "approval_comment": "Analysis meets requirements, proceeding with confidence",
                    "stakeholder_confidence": "high"
                }
            },
            artifact_metadata={
                "based_on_approved_analysis": str(analysis_artifact.context_id),
                "hitl_request_id": str(hitl_request.id),
                "approval_workflow_complete": True
            }
        )
        
        performance_timer.stop()
        
        # Step 12: Final verification of complete workflow
        
        # Verify project status reflects workflow progression
        final_status_response = client.get(f"/api/v1/projects/{project_id}/status")
        assert final_status_response.status_code == status.HTTP_200_OK
        
        final_status_data = final_status_response.json()
        tasks = final_status_data["tasks"]
        
        # Should have 2 completed tasks: Analysis and Architecture
        assert len(tasks) == 2
        completed_tasks = [task for task in tasks if task["status"] == TaskStatus.COMPLETED.value]
        assert len(completed_tasks) == 2
        
        # Verify agent progression
        agent_sequence = [task["agent_type"] for task in tasks]
        expected_sequence = [AgentType.ANALYST.value, AgentType.ARCHITECT.value]
        assert agent_sequence == expected_sequence
        
        # Verify context artifacts created
        all_artifacts = context_store_service.get_artifacts_by_project(project_id)
        assert len(all_artifacts) == 3  # User requirements + Analysis + Architecture
        
        artifact_types = [artifact.artifact_type for artifact in all_artifacts]
        expected_types = [ArtifactType.USER_INPUT, ArtifactType.PROJECT_PLAN, ArtifactType.SYSTEM_ARCHITECTURE]
        for expected_type in expected_types:
            assert expected_type in artifact_types
        
        # Verify HITL workflow completion
        hitl_history_response = client.get(f"/api/v1/hitl/{hitl_request.id}/history")
        if hitl_history_response.status_code == status.HTTP_200_OK:
            history_data = hitl_history_response.json()
            assert len(history_data["history"]) >= 1
            assert history_data["history"][0]["action"] == "approve"
        
        # Verify architecture includes HITL approval context
        final_arch_artifact = next(
            artifact for artifact in all_artifacts
            if artifact.artifact_type == ArtifactType.SYSTEM_ARCHITECTURE
        )
        assert final_arch_artifact.content["approval_context"]["hitl_approved"] is True
        assert final_arch_artifact.artifact_metadata["approval_workflow_complete"] is True
        
        # Verify performance
        assert_performance_threshold(
            performance_timer.elapsed_ms,
            10000,  # 10 seconds for complete HITL approval workflow
            "Complete HITL approval workflow"
        )
    
    @pytest.mark.e2e
    @pytest.mark.p1
    @pytest.mark.hitl
    @pytest.mark.workflow
    def test_hitl_approval_with_conditions(
        self, client: TestClient, db_session, orchestrator_service, context_store_service
    ):
        """Test HITL approval workflow with conditional approval and guidance."""
        # Create project and initial setup
        project_data = {"name": "Conditional HITL Approval Test"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = UUID(response.json()["id"])
        
        # Create simple task and HITL request
        task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Create project proposal"
        )
        
        orchestrator_service.update_task_status(
            task.task_id,
            TaskStatus.COMPLETED,
            output={"proposal": "Initial project proposal completed"}
        )
        
        hitl_request = orchestrator_service.create_hitl_request(
            project_id=project_id,
            task_id=task.task_id,
            question="Please review project proposal for approval",
            options=["approve", "reject", "amend"]
        )
        
        # Submit conditional approval
        conditional_approval = {
            "action": "approve",
            "comment": """
            CONDITIONAL APPROVAL with the following requirements:

            **Approved Elements**:
            ✓ Overall project approach is sound
            ✓ Timeline appears realistic
            ✓ Resource allocation is appropriate

            **Required Conditions for Final Approval**:
            1. Add detailed risk mitigation strategies
            2. Include specific performance metrics and KPIs
            3. Provide backup plan for critical dependencies
            4. Add stakeholder communication plan

            **Guidance for Next Phase**:
            - Architecture phase should address scalability concerns upfront
            - Consider security requirements from the beginning
            - Plan for incremental delivery milestones

            Approved to proceed with architecture phase contingent on addressing the above conditions.
            """,
            "metadata": {
                "approval_type": "conditional",
                "conditions_count": 4,
                "follow_up_required": True
            }
        }
        
        approval_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json=conditional_approval
        )
        
        assert approval_response.status_code == status.HTTP_200_OK
        
        # Verify conditional approval processed correctly
        response_data = approval_response.json()
        assert response_data["action"] == "approve"
        assert response_data["workflow_resumed"] is True
        
        # Verify approval comment contains conditions
        updated_hitl = client.get(f"/api/v1/hitl/{hitl_request.id}")
        hitl_data = updated_hitl.json()
        
        assert "CONDITIONAL APPROVAL" in hitl_data["response_comment"]
        assert "risk mitigation" in hitl_data["response_comment"]
        assert "performance metrics" in hitl_data["response_comment"]
        
        # Verify workflow can continue with conditional guidance
        assert hitl_data["status"] == HitlStatus.APPROVED.value
        assert hitl_data["responded_at"] is not None


class TestCompleteHitlAmendWorkflow:
    """Test scenario 2.3-E2E-002: Complete HITL amend workflow (P1)"""
    
    @pytest.mark.e2e
    @pytest.mark.p1
    @pytest.mark.hitl
    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_complete_hitl_amendment_workflow(
        self, client: TestClient, db_session, orchestrator_service, 
        context_store_service, mock_autogen_service, performance_timer
    ):
        """Test complete workflow with HITL amendments and iterative improvement."""
        performance_timer.start()
        
        # Step 1: Create project
        project_data = {
            "name": "HITL Amendment Workflow Test",
            "description": "Testing complete HITL amendment and iteration process"
        }
        
        response = client.post("/api/v1/projects/", json=project_data)
        assert response.status_code == status.HTTP_201_CREATED
        project_id = UUID(response.json()["id"])
        
        # Step 2: Create initial requirements
        user_requirements = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={
                "project_type": "Enterprise Data Analytics Platform",
                "business_objectives": [
                    "Real-time data processing and visualization",
                    "Predictive analytics and machine learning",
                    "Multi-tenant data isolation and security",
                    "Self-service analytics for business users"
                ],
                "technical_constraints": [
                    "Must handle 100TB+ data volumes",
                    "Sub-second query response times",
                    "99.9% availability requirement",
                    "SOX and HIPAA compliance"
                ]
            }
        )
        
        # Step 3: Initial analysis phase
        analysis_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analyze enterprise analytics platform requirements",
            context_ids=[user_requirements.context_id]
        )
        
        # Execute initial analysis
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            dummy_analysis_handoff = HandoffSchema(
                handoff_id=analysis_task.task_id,
                from_agent=AgentType.ORCHESTRATOR.value,
                to_agent=analysis_task.agent_type,
                project_id=analysis_task.project_id,
                phase="analysis",
                context_summary="Initial analysis of enterprise analytics platform requirements.",
                context_ids=[str(c) for c in analysis_task.context_ids],
                instructions=analysis_task.instructions,
                expected_outputs=["Initial analysis"],
                priority='high',
            )
            await orchestrator_service.process_task_with_autogen(analysis_task, dummy_analysis_handoff)
            
            orchestrator_service.update_task_status(
                analysis_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "analysis_status": "Initial analysis completed",
                    "identified_components": ["data_ingestion", "processing_engine", "analytics_ui"],
                    "technology_recommendation": "Apache Spark with Elasticsearch"
                }
            )
        
        # Step 4: Create initial analysis artifact (deliberately incomplete for amendment)
        initial_analysis = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={
                "project_overview": "Enterprise Data Analytics Platform",
                "high_level_components": [
                    "Data ingestion layer",
                    "Stream processing engine", 
                    "Analytics dashboard"
                ],
                "technology_stack": {
                    "processing": "Apache Spark",
                    "storage": "Elasticsearch",
                    "frontend": "React dashboard"
                },
                "basic_requirements": {
                    "data_volume": "Large scale",
                    "performance": "Fast queries",
                    "security": "Enterprise grade"
                }
                # Deliberately missing: detailed architecture, compliance specifics, 
                # performance metrics, security implementation, etc.
            },
            artifact_metadata={
                "completeness_score": 0.4,  # Intentionally incomplete
                "review_stage": "initial_draft"
            }
        )
        
        # Step 5: Create HITL request for review
        hitl_request = orchestrator_service.create_hitl_request(
            project_id=project_id,
            task_id=analysis_task.task_id,
            question="""
            Please review the Enterprise Data Analytics Platform analysis:

            **Current Analysis**:
            - High-level components identified (ingestion, processing, dashboard)
            - Basic technology stack proposed (Spark, Elasticsearch, React)
            - General requirements outlined

            **Business Context**:
            - 100TB+ data volumes with real-time processing
            - Sub-second query response requirements  
            - Multi-tenant with SOX and HIPAA compliance
            - Self-service analytics for business users

            Please evaluate whether this analysis is sufficient to proceed with architecture design, 
            or if amendments are needed to address missing details.
            """,
            options=["approve", "reject", "amend"],
            ttl_hours=24
        )
        
        # Step 6: Submit amendment request (identifying gaps)
        amendment_response_data = {
            "action": "amend",
            "content": """
            The current analysis is a good starting point but lacks critical details needed for enterprise implementation. Please address the following gaps:

            **CRITICAL MISSING ELEMENTS**:

            1. **Detailed Architecture Specification**:
               - Service-oriented architecture design
               - Data flow diagrams and processing pipelines
               - API specifications and integration patterns
               - Microservices vs monolithic architecture decision

            2. **Performance and Scalability Details**:
               - Specific performance benchmarks and SLAs
               - Auto-scaling strategies and resource management
               - Load balancing and failover mechanisms
               - Caching strategies for sub-second query times

            3. **Security and Compliance Implementation**:
               - Detailed HIPAA and SOX compliance measures
               - Multi-tenant data isolation architecture
               - Authentication, authorization, and audit logging
               - Data encryption at rest and in transit
               - Role-based access control (RBAC) design

            4. **Data Management Strategy**:
               - Data governance and quality frameworks
               - ETL/ELT pipeline design for 100TB+ volumes
               - Data lifecycle management and archiving
               - Backup and disaster recovery procedures

            5. **Technology Deep-dive**:
               - Justification for Spark vs alternatives (Flink, Storm)
               - Elasticsearch cluster design and optimization
               - Database selection for metadata and configuration
               - Monitoring and observability stack

            6. **Operational Considerations**:
               - Deployment and DevOps strategy
               - Monitoring, alerting, and troubleshooting
               - Capacity planning and cost optimization
               - Development and testing environments

            **DELIVERABLE REQUIREMENTS**:
            - Technical architecture document with diagrams
            - Security implementation specification
            - Performance testing strategy
            - Compliance validation checklist
            - Risk assessment and mitigation plan

            Please revise the analysis to include these elements before proceeding to detailed design.
            """,
            "comment": "Analysis needs significant enhancement to meet enterprise requirements. Focus on architecture, security, and compliance details.",
            "priority": "high",
            "estimated_effort": "3-5 additional days for comprehensive analysis"
        }
        
        amendment_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json=amendment_response_data
        )
        
        assert amendment_response.status_code == status.HTTP_200_OK
        
        response_data = amendment_response.json()
        assert response_data["action"] == "amend"
        assert response_data["workflow_resumed"] is True
        
        # Step 7: Verify amendment processing
        amended_hitl = client.get(f"/api/v1/hitl/{hitl_request.id}")
        hitl_data = amended_hitl.json()
        
        assert hitl_data["status"] == HitlStatus.AMENDED.value
        assert hitl_data["user_response"] == "amended"
        assert "CRITICAL MISSING ELEMENTS" in hitl_data["amended_content"]["amended_content"]
        assert "enterprise requirements" in hitl_data["response_comment"]
        
        # Step 8: Create enhanced analysis task based on amendments
        enhanced_analysis_handoff = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ANALYST.value,  # Same agent, enhanced task
            "task_instructions": f"""
            Revise and enhance the enterprise analytics platform analysis based on stakeholder amendments.

            **Amendment Requirements** (from HITL feedback):
            {amendment_response_data['content']}

            **Enhanced Analysis Deliverables**:
            1. Comprehensive technical architecture with service boundaries
            2. Detailed security and compliance implementation plan
            3. Performance benchmarking and scalability strategy
            4. Data governance and lifecycle management framework
            5. Technology selection justification with alternatives analysis
            6. Operational readiness and DevOps implementation plan

            **Quality Standards**:
            - Enterprise-grade security and compliance focus
            - Quantitative performance specifications
            - Risk assessment with mitigation strategies
            - Cost-benefit analysis for technology choices
            """,
            "context_ids": [user_requirements.context_id, initial_analysis.context_id],
            "expected_output": "Enhanced enterprise analytics platform specification ready for architecture phase",
            "amendment_context": {
                "hitl_request_id": str(hitl_request.id),
                "amendment_areas": ["architecture", "security", "performance", "compliance"]
            }
        }
        
        enhanced_analysis_task = orchestrator_service.create_task_from_handoff(
            project_id=project_id,
            handoff_schema=enhanced_analysis_handoff
        )
        
        # Step 9: Execute enhanced analysis
        with unittest.mock.patch.object(orchestrator_service, 'autogen_service', mock_autogen_service):
            dummy_enhanced_analysis_handoff = HandoffSchema(
                handoff_id=enhanced_analysis_task.task_id,
                from_agent=enhanced_analysis_handoff["from_agent"],
                to_agent=enhanced_analysis_handoff["to_agent"],
                project_id=enhanced_analysis_task.project_id,
                phase="analysis",
                context_summary="Enhanced analysis based on stakeholder feedback.",
                context_ids=[str(c) for c in enhanced_analysis_task.context_ids],
                instructions=enhanced_analysis_handoff["task_instructions"],
                expected_outputs=[enhanced_analysis_handoff["expected_output"]],
                priority='high',
            )
            enhanced_result = await orchestrator_service.process_task_with_autogen(enhanced_analysis_task, dummy_enhanced_analysis_handoff)
            
            orchestrator_service.update_task_status(
                enhanced_analysis_task.task_id,
                TaskStatus.COMPLETED,
                output={
                    "enhanced_analysis": "Comprehensive analysis addressing all amendment requirements",
                    "architecture_components": 12,
                    "security_controls": 25,
                    "compliance_measures": 18,
                    "performance_specifications": "detailed with quantitative targets"
                }
            )
        
        # Step 10: Create enhanced analysis artifact
        enhanced_analysis_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={
                "project_specification": {
                    "name": "Enterprise Data Analytics Platform",
                    "complexity": "High - Enterprise Scale",
                    "architecture_type": "Microservices with Event-Driven Architecture"
                },
                "detailed_architecture": {
                    "services": [
                        "data-ingestion-service", "stream-processing-service", "batch-processing-service",
                        "query-engine-service", "analytics-ui-service", "user-management-service",
                        "audit-logging-service", "notification-service", "metadata-service"
                    ],
                    "data_flow": "Event-driven with Apache Kafka message bus",
                    "api_gateway": "Kong with rate limiting and authentication",
                    "service_mesh": "Istio for inter-service communication"
                },
                "security_implementation": {
                    "authentication": "OAuth 2.0 with SAML integration",
                    "authorization": "Attribute-Based Access Control (ABAC)",
                    "data_encryption": "AES-256 at rest, TLS 1.3 in transit",
                    "audit_logging": "Comprehensive with tamper-proof trails",
                    "compliance_controls": {
                        "hipaa": ["data_minimization", "access_controls", "audit_trails", "encryption"],
                        "sox": ["data_integrity", "access_logging", "change_management", "reporting"]
                    }
                },
                "performance_specifications": {
                    "query_response": "< 500ms for 95th percentile",
                    "data_ingestion": "1M+ events/second sustained",
                    "concurrent_users": "10,000 with auto-scaling",
                    "storage_capacity": "100TB+ with automated tiering",
                    "availability": "99.9% with <5min RTO/RPO"
                },
                "technology_justification": {
                    "apache_spark": "Chosen for unified batch/stream processing over Flink due to ecosystem maturity",
                    "elasticsearch": "Selected for analytical queries, considered ClickHouse but chose for operational simplicity",
                    "kafka": "Event streaming backbone for decoupled architecture",
                    "kubernetes": "Container orchestration with auto-scaling and service mesh support"
                },
                "amendment_addressed": {
                    "hitl_request_id": str(hitl_request.id),
                    "amendment_items_covered": 6,
                    "completeness_improvement": "from 40% to 95%",
                    "stakeholder_feedback_incorporated": True
                }
            },
            artifact_metadata={
                "version": "2.0_post_amendment",
                "based_on_hitl_feedback": str(hitl_request.id),
                "completeness_score": 0.95,
                "review_stage": "comprehensive_specification",
                "amendment_cycle_complete": True
            }
        )
        
        # Step 11: Create second HITL request for enhanced analysis review
        second_hitl_request = orchestrator_service.create_hitl_request(
            project_id=project_id,
            task_id=enhanced_analysis_task.task_id,
            question="""
            Please review the ENHANCED Enterprise Data Analytics Platform analysis:

            **Improvements Made** (based on previous amendments):
            ✓ Detailed microservices architecture with 9 core services
            ✓ Comprehensive security implementation with HIPAA/SOX compliance
            ✓ Quantified performance specifications with SLA targets
            ✓ Technology selection with justification and alternatives analysis
            ✓ Operational readiness and DevOps considerations
            ✓ Risk assessment and mitigation strategies

            **Key Enhancements**:
            - Event-driven architecture with Kafka message bus
            - Service mesh (Istio) for inter-service communication
            - ABAC authorization with comprehensive audit logging
            - Auto-scaling for 10K+ concurrent users
            - Data tiering for 100TB+ storage optimization

            The analysis now addresses all previous amendment requirements. 
            Please review for approval to proceed with detailed architecture design.
            """,
            options=["approve", "reject", "amend"]
        )
        
        # Step 12: Submit approval for enhanced analysis
        final_approval = {
            "action": "approve",
            "comment": """
            EXCELLENT ENHANCEMENT - All amendment requirements addressed comprehensively!

            **Outstanding Improvements**:
            ✓ Architecture is now enterprise-ready with clear service boundaries
            ✓ Security and compliance implementation is thoroughly detailed
            ✓ Performance specifications are quantified and realistic
            ✓ Technology choices are well-justified with alternatives considered
            ✓ Operational considerations demonstrate production readiness

            **Particular Strengths**:
            - Event-driven architecture will provide excellent scalability
            - ABAC authorization model is perfect for multi-tenant requirements
            - Service mesh approach will simplify inter-service communication
            - Performance targets are aggressive but achievable with proposed stack

            **Quality Assessment**:
            - Completeness: 95% (excellent improvement from 40%)
            - Technical depth: Enterprise-grade specification
            - Risk mitigation: Comprehensive coverage
            - Implementation readiness: Ready for architecture phase

            APPROVED for detailed architecture design phase. This specification provides 
            an excellent foundation for the development team.
            """,
            "metadata": {
                "improvement_rating": "excellent",
                "amendment_success": True,
                "confidence_level": "very_high"
            }
        }
        
        final_approval_response = client.post(
            f"/api/v1/hitl/{second_hitl_request.id}/respond",
            json=final_approval
        )
        
        assert final_approval_response.status_code == status.HTTP_200_OK
        
        performance_timer.stop()
        
        # Step 13: Verify complete amendment workflow
        
        # Verify final project status
        final_status = client.get(f"/api/v1/projects/{project_id}/status")
        status_data = final_status.json()
        tasks = status_data["tasks"]
        
        # Should have 2 completed analysis tasks (initial + enhanced)
        assert len(tasks) == 2
        completed_tasks = [task for task in tasks if task["status"] == TaskStatus.COMPLETED.value]
        assert len(completed_tasks) == 2
        
        # Both tasks should be analyst tasks
        for task in tasks:
            assert task["agent_type"] == AgentType.ANALYST.value
        
        # Verify artifacts created
        all_artifacts = context_store_service.get_artifacts_by_project(project_id)
        assert len(all_artifacts) == 3  # Requirements + Initial Analysis + Enhanced Analysis
        
        # Verify enhanced analysis quality
        enhanced_artifact = next(
            artifact for artifact in all_artifacts
            if artifact.artifact_metadata.get("version") == "2.0_post_amendment"
        )
        
        assert enhanced_artifact.artifact_metadata["completeness_score"] == 0.95
        assert enhanced_artifact.content["amendment_addressed"]["stakeholder_feedback_incorporated"] is True
        assert len(enhanced_artifact.content["detailed_architecture"]["services"]) == 9
        
        # Verify HITL requests history
        first_hitl_history = client.get(f"/api/v1/hitl/{hitl_request.id}/history")
        if first_hitl_history.status_code == status.HTTP_200_OK:
            first_history_data = first_hitl_history.json()
            assert len(first_history_data["history"]) >= 1
            assert first_history_data["history"][0]["action"] == "amend"
        
        second_hitl_history = client.get(f"/api/v1/hitl/{second_hitl_request.id}/history")
        if second_hitl_history.status_code == status.HTTP_200_OK:
            second_history_data = second_hitl_history.json()
            assert len(second_history_data["history"]) >= 1
            assert second_history_data["history"][0]["action"] == "approve"
        
        # Verify both HITL requests final status
        final_first_hitl = client.get(f"/api/v1/hitl/{hitl_request.id}")
        final_second_hitl = client.get(f"/api/v1/hitl/{second_hitl_request.id}")
        
        assert final_first_hitl.json()["status"] == HitlStatus.AMENDED.value
        assert final_second_hitl.json()["status"] == HitlStatus.APPROVED.value
        
        # Verify performance
        assert_performance_threshold(
            performance_timer.elapsed_ms,
            15000,  # 15 seconds for complete amendment workflow
            "Complete HITL amendment workflow with iteration"
        )
    
    @pytest.mark.e2e
    @pytest.mark.p2
    @pytest.mark.hitl
    @pytest.mark.workflow
    def test_multi_round_amendment_workflow(
        self, client: TestClient, db_session, orchestrator_service, context_store_service
    ):
        """Test workflow with multiple rounds of amendments and refinements."""
        # Create project
        project_data = {"name": "Multi-Round Amendment Test"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = UUID(response.json()["id"])
        
        # Create initial task
        task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Create initial proposal"
        )
        
        orchestrator_service.update_task_status(
            task.task_id,
            TaskStatus.COMPLETED,
            output={"proposal": "basic proposal"}
        )
        
        # First HITL request
        hitl_1 = orchestrator_service.create_hitl_request(
            project_id=project_id,
            task_id=task.task_id,
            question="Review initial proposal",
            options=["approve", "reject", "amend"]
        )
        
        # First amendment
        client.post(
            f"/api/v1/hitl/{hitl_1.id}/respond",
            json={
                "action": "amend",
                "content": "Add technical details and risk assessment",
                "comment": "Proposal too high-level"
            }
        )
        
        # Second task (addressing first amendment)
        task_2 = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Enhanced proposal with technical details"
        )
        
        orchestrator_service.update_task_status(
            task_2.task_id,
            TaskStatus.COMPLETED,
            output={"proposal": "enhanced with technical details"}
        )
        
        # Second HITL request
        hitl_2 = orchestrator_service.create_hitl_request(
            project_id=project_id,
            task_id=task_2.task_id,
            question="Review enhanced proposal",
            options=["approve", "reject", "amend"]
        )
        
        # Second amendment (more specific)
        client.post(
            f"/api/v1/hitl/{hitl_2.id}/respond",
            json={
                "action": "amend",
                "content": "Add specific performance metrics and cost analysis",
                "comment": "Need quantitative details"
            }
        )
        
        # Third task (addressing second amendment)
        task_3 = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Final proposal with metrics and cost analysis"
        )
        
        orchestrator_service.update_task_status(
            task_3.task_id,
            TaskStatus.COMPLETED,
            output={"proposal": "comprehensive with metrics and costs"}
        )
        
        # Third HITL request
        hitl_3 = orchestrator_service.create_hitl_request(
            project_id=project_id,
            task_id=task_3.task_id,
            question="Final review of comprehensive proposal",
            options=["approve", "reject", "amend"]
        )
        
        # Final approval
        final_response = client.post(
            f"/api/v1/hitl/{hitl_3.id}/respond",
            json={
                "action": "approve",
                "comment": "Excellent - all requirements addressed"
            }
        )
        
        assert final_response.status_code == status.HTTP_200_OK
        
        # Verify multi-round workflow completion
        final_status = client.get(f"/api/v1/projects/{project_id}/status")
        tasks = final_status.json()["tasks"]
        
        # Should have 3 tasks (initial + 2 amendments)
        assert len(tasks) == 3
        completed_tasks = [t for t in tasks if t["status"] == TaskStatus.COMPLETED.value]
        assert len(completed_tasks) == 3
        
        # Verify HITL progression: amend -> amend -> approve
        hitl_1_final = client.get(f"/api/v1/hitl/{hitl_1.id}")
        hitl_2_final = client.get(f"/api/v1/hitl/{hitl_2.id}")
        hitl_3_final = client.get(f"/api/v1/hitl/{hitl_3.id}")
        
        assert hitl_1_final.json()["status"] == HitlStatus.AMENDED.value
        assert hitl_2_final.json()["status"] == HitlStatus.AMENDED.value
        assert hitl_3_final.json()["status"] == HitlStatus.APPROVED.value
        
        # Verify iterative improvement in comments
        assert "high-level" in hitl_1_final.json()["response_comment"]
        assert "quantitative" in hitl_2_final.json()["response_comment"]
        assert "Excellent" in hitl_3_final.json()["response_comment"]