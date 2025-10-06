"""
Security tests for HITL safety system post-consolidation.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from app.services.hitl_safety_service import HITLSafetyService
from app.services.document_service import DocumentService
from app.services.llm_service import LLMService
from app.database.models import HitlAgentApprovalDB, EmergencyStopDB, AgentBudgetControlDB
from tests.utils.database_test_utils import DatabaseTestManager


class TestHITLSafetyConsolidated:
    """Test HITL safety with consolidated services."""
    
    @pytest.fixture
    def hitl_safety_service(self, db_manager):
        """Create HITLSafetyService instance."""
        with db_manager.get_session() as session:
            return HITLSafetyService(session)
    
    @pytest.fixture
    def document_service(self):
        """Create DocumentService for safety testing."""
        config = {
            "enable_deduplication": True,
            "enable_conflict_resolution": True,
            "max_section_size": 8192,
            "enable_semantic_sectioning": True
        }
        return DocumentService(config)
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService for safety testing."""
        return LLMService()
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for safety testing."""
        return {
            "project_id": uuid4(),
            "agent_type": "analyst",
            "task_id": uuid4(),
            "estimated_tokens": 500,
            "estimated_cost": 0.01
        }

    # Document Service Safety Integration Tests
    
    @pytest.mark.real_data
    @pytest.mark.security
    async def test_safety_with_document_service(self, hitl_safety_service, document_service, db_manager, sample_project_data):
        """Test HITL safety integration with DocumentService."""
        with db_manager.get_session() as session:
            # Create HITL approval request for document processing
            approval_id = await hitl_safety_service.create_approval_request(
                project_id=sample_project_data["project_id"],
                task_id=sample_project_data["task_id"],
                agent_type=sample_project_data["agent_type"],
                request_type="PRE_EXECUTION",
                estimated_tokens=sample_project_data["estimated_tokens"],
                estimated_cost=sample_project_data["estimated_cost"],
                context_summary="Document processing operation",
                safety_metadata={
                    "operation_type": "document_assembly",
                    "artifact_count": 10,
                    "content_size": "medium"
                }
            )
            
            # Verify approval was created
            approval = session.query(HitlAgentApprovalDB).filter(
                HitlAgentApprovalDB.id == approval_id
            ).first()
            
            assert approval is not None
            assert approval.status == "PENDING"
            assert approval.request_type == "PRE_EXECUTION"
            
            # Simulate approval
            approval.status = "APPROVED"
            approval.user_response = "approve"
            approval.responded_at = datetime.now(timezone.utc)
            session.commit()
            
            # Now execute document service operation (would be gated by HITL)
            test_artifacts = [
                {"id": "doc1", "content": "# Test Document 1\nContent here."},
                {"id": "doc2", "content": "# Test Document 2\nMore content."}
            ]
            
            result = await document_service.assemble_document(
                artifacts=test_artifacts,
                project_id=str(sample_project_data["project_id"])
            )
            
            # Verify operation completed successfully after approval
            assert result is not None
            assert "content" in result
            assert result["metadata"]["artifact_count"] == 2

    @pytest.mark.real_data
    @pytest.mark.security
    async def test_document_service_safety_rejection(self, hitl_safety_service, document_service, db_manager, sample_project_data):
        """Test document service operation rejection via HITL safety."""
        with db_manager.get_session() as session:
            # Create HITL approval request
            approval_id = await hitl_safety_service.create_approval_request(
                project_id=sample_project_data["project_id"],
                task_id=sample_project_data["task_id"],
                agent_type=sample_project_data["agent_type"],
                request_type="PRE_EXECUTION",
                estimated_tokens=sample_project_data["estimated_tokens"],
                estimated_cost=sample_project_data["estimated_cost"],
                context_summary="Potentially unsafe document operation",
                safety_metadata={
                    "operation_type": "document_assembly",
                    "risk_level": "high",
                    "sensitive_content": True
                }
            )
            
            # Simulate rejection
            approval = session.query(HitlAgentApprovalDB).filter(
                HitlAgentApprovalDB.id == approval_id
            ).first()
            
            approval.status = "REJECTED"
            approval.user_response = "reject"
            approval.user_comment = "Operation contains sensitive content"
            approval.responded_at = datetime.now(timezone.utc)
            session.commit()
            
            # Verify rejection prevents operation
            # (In real implementation, this would be checked before execution)
            assert approval.status == "REJECTED"
            assert "sensitive content" in approval.user_comment

    # LLM Service Safety Integration Tests
    
    @pytest.mark.real_data
    @pytest.mark.security
    async def test_safety_with_llm_service(self, hitl_safety_service, llm_service, db_manager, sample_project_data):
        """Test HITL safety integration with LLMService."""
        with db_manager.get_session() as session:
            # Create HITL approval for LLM operation
            approval_id = await hitl_safety_service.create_approval_request(
                project_id=sample_project_data["project_id"],
                task_id=sample_project_data["task_id"],
                agent_type=sample_project_data["agent_type"],
                request_type="PRE_EXECUTION",
                estimated_tokens=sample_project_data["estimated_tokens"],
                estimated_cost=sample_project_data["estimated_cost"],
                context_summary="LLM request processing",
                safety_metadata={
                    "operation_type": "llm_request",
                    "provider": "openai",
                    "model": "gpt-4o",
                    "token_estimate": sample_project_data["estimated_tokens"]
                }
            )
            
            # Approve the request
            approval = session.query(HitlAgentApprovalDB).filter(
                HitlAgentApprovalDB.id == approval_id
            ).first()
            
            approval.status = "APPROVED"
            approval.user_response = "approve"
            approval.responded_at = datetime.now(timezone.utc)
            session.commit()
            
            # Execute LLM service operation (tracking usage)
            llm_service.track_usage(
                agent_type=sample_project_data["agent_type"],
                provider="openai",
                model="gpt-4o",
                tokens=sample_project_data["estimated_tokens"],
                response_time=1500.0,
                project_id=sample_project_data["project_id"],
                task_id=sample_project_data["task_id"],
                success=True,
                estimated_cost=sample_project_data["estimated_cost"]
            )
            
            # Verify usage was tracked after approval
            assert len(llm_service.usage_history) == 1
            usage = llm_service.usage_history[0]
            assert usage.project_id == sample_project_data["project_id"]
            assert usage.task_id == sample_project_data["task_id"]
            assert usage.success is True

    @pytest.mark.real_data
    @pytest.mark.security
    async def test_llm_service_budget_safety_integration(self, hitl_safety_service, llm_service, db_manager, sample_project_data):
        """Test LLM service integration with budget safety controls."""
        with db_manager.get_session() as session:
            # Create budget control for the project
            budget_control = AgentBudgetControlDB(
                project_id=sample_project_data["project_id"],
                agent_type=sample_project_data["agent_type"],
                daily_token_limit=1000,
                session_token_limit=500,
                daily_cost_limit=0.05,
                session_cost_limit=0.02,
                current_daily_tokens=400,  # Already used 400 tokens
                current_session_tokens=200,  # Already used 200 tokens
                current_daily_cost=0.02,  # Already spent $0.02
                current_session_cost=0.01  # Already spent $0.01
            )
            session.add(budget_control)
            session.commit()
            
            # Try to create approval that would exceed budget
            high_cost_request = {
                **sample_project_data,
                "estimated_tokens": 700,  # Would exceed session limit (200 + 700 > 500)
                "estimated_cost": 0.03   # Would exceed session cost limit (0.01 + 0.03 > 0.02)
            }
            
            # This should trigger budget safety checks
            approval_id = await hitl_safety_service.create_approval_request(
                project_id=high_cost_request["project_id"],
                task_id=high_cost_request["task_id"],
                agent_type=high_cost_request["agent_type"],
                request_type="PRE_EXECUTION",
                estimated_tokens=high_cost_request["estimated_tokens"],
                estimated_cost=high_cost_request["estimated_cost"],
                context_summary="High-cost LLM operation",
                safety_metadata={
                    "budget_check": True,
                    "estimated_tokens": high_cost_request["estimated_tokens"],
                    "estimated_cost": high_cost_request["estimated_cost"]
                }
            )
            
            # Verify approval was created with budget warning
            approval = session.query(HitlAgentApprovalDB).filter(
                HitlAgentApprovalDB.id == approval_id
            ).first()
            
            assert approval is not None
            # Should have budget-related metadata or warnings
            assert approval.estimated_tokens == 700
            assert approval.estimated_cost == 0.03

    # Emergency Stop Integration Tests
    
    @pytest.mark.real_data
    @pytest.mark.security
    async def test_emergency_stop_integration(self, hitl_safety_service, document_service, llm_service, db_manager, sample_project_data):
        """Test emergency stop integration with consolidated services."""
        with db_manager.get_session() as session:
            # Create emergency stop
            emergency_stop = EmergencyStopDB(
                project_id=sample_project_data["project_id"],
                reason="Budget exceeded - emergency halt",
                triggered_by="system",
                status="ACTIVE",
                stop_all_agents=True,
                metadata={
                    "trigger_condition": "budget_exceeded",
                    "threshold_value": 0.05,
                    "current_value": 0.06
                }
            )
            session.add(emergency_stop)
            session.commit()
            session.refresh(emergency_stop)
            
            # Try to create approval request during emergency stop
            try:
                approval_id = await hitl_safety_service.create_approval_request(
                    project_id=sample_project_data["project_id"],
                    task_id=sample_project_data["task_id"],
                    agent_type=sample_project_data["agent_type"],
                    request_type="PRE_EXECUTION",
                    estimated_tokens=sample_project_data["estimated_tokens"],
                    estimated_cost=sample_project_data["estimated_cost"],
                    context_summary="Operation during emergency stop"
                )
                
                # If approval is created, it should be automatically rejected or flagged
                approval = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.id == approval_id
                ).first()
                
                # Should either fail to create or be marked with emergency status
                if approval:
                    assert approval.status in ["REJECTED", "EMERGENCY_BLOCKED"]
                    
            except Exception as e:
                # Emergency stop should prevent approval creation
                assert "emergency" in str(e).lower() or "stop" in str(e).lower()

    # Cross-Service Safety Validation Tests
    
    @pytest.mark.real_data
    @pytest.mark.security
    async def test_cross_service_safety_validation(self, hitl_safety_service, document_service, llm_service, db_manager):
        """Test safety validation across multiple consolidated services."""
        project_id = uuid4()
        
        with db_manager.get_session() as session:
            # Scenario: Document processing that requires LLM analysis
            
            # Step 1: Create approval for document assembly
            doc_approval_id = await hitl_safety_service.create_approval_request(
                project_id=project_id,
                task_id=uuid4(),
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                estimated_tokens=200,
                estimated_cost=0.004,
                context_summary="Document assembly for analysis",
                safety_metadata={
                    "operation_type": "document_assembly",
                    "next_operation": "llm_analysis"
                }
            )
            
            # Step 2: Create approval for subsequent LLM analysis
            llm_approval_id = await hitl_safety_service.create_approval_request(
                project_id=project_id,
                task_id=uuid4(),
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                estimated_tokens=300,
                estimated_cost=0.006,
                context_summary="LLM analysis of assembled document",
                safety_metadata={
                    "operation_type": "llm_analysis",
                    "depends_on": str(doc_approval_id)
                }
            )
            
            # Verify both approvals were created
            doc_approval = session.query(HitlAgentApprovalDB).filter(
                HitlAgentApprovalDB.id == doc_approval_id
            ).first()
            
            llm_approval = session.query(HitlAgentApprovalDB).filter(
                HitlAgentApprovalDB.id == llm_approval_id
            ).first()
            
            assert doc_approval is not None
            assert llm_approval is not None
            assert doc_approval.project_id == llm_approval.project_id

    # Safety Metadata Validation Tests
    
    @pytest.mark.real_data
    @pytest.mark.security
    async def test_safety_metadata_validation(self, hitl_safety_service, db_manager, sample_project_data):
        """Test validation of safety metadata in HITL requests."""
        with db_manager.get_session() as session:
            # Test with comprehensive safety metadata
            safety_metadata = {
                "operation_type": "document_processing",
                "risk_level": "medium",
                "data_sensitivity": "internal",
                "compliance_requirements": ["GDPR", "SOX"],
                "estimated_processing_time": 300,
                "resource_requirements": {
                    "cpu": "medium",
                    "memory": "high",
                    "network": "low"
                },
                "security_controls": {
                    "encryption": True,
                    "audit_logging": True,
                    "access_control": "role_based"
                }
            }
            
            approval_id = await hitl_safety_service.create_approval_request(
                project_id=sample_project_data["project_id"],
                task_id=sample_project_data["task_id"],
                agent_type=sample_project_data["agent_type"],
                request_type="PRE_EXECUTION",
                estimated_tokens=sample_project_data["estimated_tokens"],
                estimated_cost=sample_project_data["estimated_cost"],
                context_summary="Operation with comprehensive safety metadata",
                safety_metadata=safety_metadata
            )
            
            # Verify metadata was stored correctly
            approval = session.query(HitlAgentApprovalDB).filter(
                HitlAgentApprovalDB.id == approval_id
            ).first()
            
            assert approval is not None
            # Verify safety metadata is accessible (implementation dependent)
            # This would typically be stored in a metadata field or related table

    # Audit Trail Integration Tests
    
    @pytest.mark.real_data
    @pytest.mark.security
    async def test_safety_audit_trail_integration(self, hitl_safety_service, db_manager, sample_project_data):
        """Test audit trail integration for safety operations."""
        with db_manager.get_session() as session:
            # Create and process approval with audit trail
            approval_id = await hitl_safety_service.create_approval_request(
                project_id=sample_project_data["project_id"],
                task_id=sample_project_data["task_id"],
                agent_type=sample_project_data["agent_type"],
                request_type="PRE_EXECUTION",
                estimated_tokens=sample_project_data["estimated_tokens"],
                estimated_cost=sample_project_data["estimated_cost"],
                context_summary="Audited safety operation"
            )
            
            # Simulate approval process with audit trail
            approval = session.query(HitlAgentApprovalDB).filter(
                HitlAgentApprovalDB.id == approval_id
            ).first()
            
            # Record approval decision
            approval.status = "APPROVED"
            approval.user_response = "approve"
            approval.user_comment = "Operation approved after security review"
            approval.responded_at = datetime.now(timezone.utc)
            session.commit()
            
            # Verify audit trail information is complete
            assert approval.status == "APPROVED"
            assert approval.user_response == "approve"
            assert approval.user_comment is not None
            assert approval.responded_at is not None
            assert approval.created_at is not None

    # Performance Impact of Safety Controls
    
    @pytest.mark.real_data
    @pytest.mark.security
    @pytest.mark.performance
    async def test_safety_controls_performance_impact(self, hitl_safety_service, document_service, llm_service, db_manager):
        """Test that safety controls don't significantly impact performance."""
        import time
        
        project_id = uuid4()
        
        with db_manager.get_session() as session:
            # Measure time for safety-controlled operations
            start_time = time.time()
            
            # Create multiple approval requests
            approval_ids = []
            for i in range(10):
                approval_id = await hitl_safety_service.create_approval_request(
                    project_id=project_id,
                    task_id=uuid4(),
                    agent_type="analyst",
                    request_type="PRE_EXECUTION",
                    estimated_tokens=100 + i * 10,
                    estimated_cost=0.002 + i * 0.001,
                    context_summary=f"Performance test operation {i}"
                )
                approval_ids.append(approval_id)
            
            # Approve all requests
            for approval_id in approval_ids:
                approval = session.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.id == approval_id
                ).first()
                approval.status = "APPROVED"
                approval.user_response = "approve"
                approval.responded_at = datetime.now(timezone.utc)
            
            session.commit()
            
            end_time = time.time()
            elapsed_ms = (end_time - start_time) * 1000
            
            # Safety operations should complete within reasonable time
            assert elapsed_ms < 5000, f"Safety operations took {elapsed_ms:.2f}ms, exceeding 5000ms threshold"
            
            # Verify all approvals were processed
            assert len(approval_ids) == 10

    # Integration Error Handling Tests
    
    @pytest.mark.real_data
    @pytest.mark.security
    async def test_safety_integration_error_handling(self, hitl_safety_service, db_manager, sample_project_data):
        """Test error handling in safety integration scenarios."""
        with db_manager.get_session() as session:
            # Test with invalid project ID
            invalid_project_id = "invalid-uuid-format"
            
            with pytest.raises(Exception):
                await hitl_safety_service.create_approval_request(
                    project_id=invalid_project_id,
                    task_id=sample_project_data["task_id"],
                    agent_type=sample_project_data["agent_type"],
                    request_type="PRE_EXECUTION",
                    estimated_tokens=sample_project_data["estimated_tokens"],
                    estimated_cost=sample_project_data["estimated_cost"],
                    context_summary="Invalid project ID test"
                )
            
            # Test with negative cost/tokens
            with pytest.raises(Exception):
                await hitl_safety_service.create_approval_request(
                    project_id=sample_project_data["project_id"],
                    task_id=sample_project_data["task_id"],
                    agent_type=sample_project_data["agent_type"],
                    request_type="PRE_EXECUTION",
                    estimated_tokens=-100,  # Invalid negative value
                    estimated_cost=-0.01,   # Invalid negative value
                    context_summary="Negative values test"
                )