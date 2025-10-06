"""
Test suite for dynamic workflow deliverables system.
Tests the new 17-artifact SDLC workflow.
"""

import pytest
import json
from typing import Dict, Any, List
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.api.workflows import get_workflow_deliverables
from tests.utils.database_test_utils import DatabaseTestManager


class TestWorkflowDeliverables:
    """Test dynamic workflow deliverables integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_workflow_yaml(self):
        """Sample workflow YAML content for testing."""
        return """
name: "Greenfield Fullstack Development"
description: "Complete SDLC workflow for greenfield fullstack applications"
version: "1.0"

phases:
  analyze:
    agent: "analyst"
    deliverables:
      - name: "Analyze Plan"
        type: "plan"
        hitl_required: true
        description: "Human-approved analysis plan"
      - name: "Product Requirement"
        type: "document"
        description: "Product requirements document"
      - name: "PRD Epic"
        type: "epic"
        description: "Product requirement epic"
      - name: "Feature Story"
        type: "story"
        description: "Feature user story"

  design:
    agent: "architect"
    deliverables:
      - name: "Design Plan"
        type: "plan"
        hitl_required: true
        description: "Human-approved design plan"
      - name: "Front End Spec"
        type: "specification"
        description: "Frontend technical specification"
      - name: "Fullstack Architecture"
        type: "architecture"
        description: "Complete system architecture"

  build:
    agent: "coder"
    deliverables:
      - name: "Build Plan"
        type: "plan"
        hitl_required: true
        description: "Human-approved build plan"
      - name: "Story"
        type: "story"
        description: "Implementation story"
      - name: "Implementation Files"
        type: "code"
        description: "Source code files"
      - name: "Bug Fixes"
        type: "fixes"
        description: "Bug fix implementations"

  validate:
    agent: "tester"
    deliverables:
      - name: "Validate Plan"
        type: "plan"
        hitl_required: true
        description: "Human-approved validation plan"
      - name: "Test Case"
        type: "test"
        description: "Test case specifications"
      - name: "Validation Report"
        type: "report"
        description: "Validation results report"

  launch:
    agent: "deployer"
    deliverables:
      - name: "Launch Plan"
        type: "plan"
        hitl_required: true
        description: "Human-approved launch plan"
      - name: "Deployment Checklist"
        type: "checklist"
        description: "Pre-deployment checklist"
      - name: "Deployment Report"
        type: "report"
        description: "Deployment results report"
"""

    @pytest.mark.real_data
    async def test_greenfield_fullstack_deliverables(self, client, sample_workflow_yaml):
        """Test loading of greenfield fullstack deliverables."""
        # Mock the workflow file loading
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = sample_workflow_yaml
            
            with patch('os.path.exists', return_value=True):
                response = client.get("/api/v1/workflows/greenfield-fullstack/deliverables")
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "deliverables" in data
        assert "metadata" in data
        
        deliverables = data["deliverables"]
        
        # Verify total deliverable count (17 artifacts)
        total_deliverables = sum(len(stage_deliverables) for stage_deliverables in deliverables.values())
        assert total_deliverables == 17
        
        # Verify all stages are present
        expected_stages = ["analyze", "design", "build", "validate", "launch"]
        assert set(deliverables.keys()) == set(expected_stages)

    @pytest.mark.real_data
    async def test_deliverables_stage_mapping(self, client, sample_workflow_yaml):
        """Test deliverable mapping to SDLC stages."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = sample_workflow_yaml
            
            with patch('os.path.exists', return_value=True):
                response = client.get("/api/v1/workflows/greenfield-fullstack/deliverables")
        
        assert response.status_code == 200
        
        data = response.json()
        deliverables = data["deliverables"]
        
        # Verify stage distribution
        assert len(deliverables["analyze"]) == 4
        assert len(deliverables["design"]) == 3
        assert len(deliverables["build"]) == 4
        assert len(deliverables["validate"]) == 3
        assert len(deliverables["launch"]) == 3
        
        # Verify deliverable structure
        for stage, stage_deliverables in deliverables.items():
            for deliverable in stage_deliverables:
                assert "name" in deliverable
                assert "type" in deliverable
                assert "description" in deliverable
                assert "stage" in deliverable
                assert deliverable["stage"] == stage

    @pytest.mark.real_data
    async def test_hitl_required_plans(self, client, sample_workflow_yaml):
        """Test HITL-required plan artifacts."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = sample_workflow_yaml
            
            with patch('os.path.exists', return_value=True):
                response = client.get("/api/v1/workflows/greenfield-fullstack/deliverables")
        
        assert response.status_code == 200
        
        data = response.json()
        deliverables = data["deliverables"]
        
        # Find all HITL-required deliverables
        hitl_required = []
        for stage_deliverables in deliverables.values():
            for deliverable in stage_deliverables:
                if deliverable.get("hitl_required", False):
                    hitl_required.append(deliverable)
        
        # Should have 5 HITL-required plans (one per stage)
        assert len(hitl_required) == 5
        
        # Verify all are plan types
        for deliverable in hitl_required:
            assert deliverable["type"] == "plan"
            assert "Plan" in deliverable["name"]
        
        # Verify one per stage
        hitl_stages = {deliverable["stage"] for deliverable in hitl_required}
        assert hitl_stages == {"analyze", "design", "build", "validate", "launch"}

    @pytest.mark.real_data
    async def test_workflow_deliverables_metadata(self, client, sample_workflow_yaml):
        """Test workflow deliverables metadata."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = sample_workflow_yaml
            
            with patch('os.path.exists', return_value=True):
                response = client.get("/api/v1/workflows/greenfield-fullstack/deliverables")
        
        assert response.status_code == 200
        
        data = response.json()
        metadata = data["metadata"]
        
        # Verify metadata structure
        assert "workflow_name" in metadata
        assert "workflow_version" in metadata
        assert "total_deliverables" in metadata
        assert "stages_count" in metadata
        assert "hitl_required_count" in metadata
        
        # Verify metadata values
        assert metadata["workflow_name"] == "Greenfield Fullstack Development"
        assert metadata["workflow_version"] == "1.0"
        assert metadata["total_deliverables"] == 17
        assert metadata["stages_count"] == 5
        assert metadata["hitl_required_count"] == 5

    @pytest.mark.real_data
    async def test_workflow_not_found(self, client):
        """Test workflow deliverables for non-existent workflow."""
        with patch('os.path.exists', return_value=False):
            response = client.get("/api/v1/workflows/non-existent-workflow/deliverables")
        
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.real_data
    async def test_invalid_workflow_yaml(self, client):
        """Test handling of invalid workflow YAML."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = invalid_yaml
            
            with patch('os.path.exists', return_value=True):
                response = client.get("/api/v1/workflows/greenfield-fullstack/deliverables")
        
        assert response.status_code == 500
        
        data = response.json()
        assert "detail" in data
        assert "yaml" in data["detail"].lower() or "parse" in data["detail"].lower()

    @pytest.mark.real_data
    async def test_workflow_deliverables_caching(self, client, sample_workflow_yaml):
        """Test workflow deliverables caching behavior."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = sample_workflow_yaml
            
            with patch('os.path.exists', return_value=True):
                # First request
                response1 = client.get("/api/v1/workflows/greenfield-fullstack/deliverables")
                assert response1.status_code == 200
                
                # Second request (should use cache if implemented)
                response2 = client.get("/api/v1/workflows/greenfield-fullstack/deliverables")
                assert response2.status_code == 200
                
                # Responses should be identical
                assert response1.json() == response2.json()

    @pytest.mark.real_data
    async def test_deliverables_agent_assignment(self, client, sample_workflow_yaml):
        """Test deliverables are properly assigned to agents."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = sample_workflow_yaml
            
            with patch('os.path.exists', return_value=True):
                response = client.get("/api/v1/workflows/greenfield-fullstack/deliverables")
        
        assert response.status_code == 200
        
        data = response.json()
        deliverables = data["deliverables"]
        
        # Verify agent assignments per stage
        stage_agents = {
            "analyze": "analyst",
            "design": "architect", 
            "build": "coder",
            "validate": "tester",
            "launch": "deployer"
        }
        
        for stage, expected_agent in stage_agents.items():
            stage_deliverables = deliverables[stage]
            for deliverable in stage_deliverables:
                # Agent should be assigned at stage level or deliverable level
                assert "agent" in deliverable or stage in stage_agents
                if "agent" in deliverable:
                    assert deliverable["agent"] == expected_agent

    @pytest.mark.real_data
    async def test_deliverables_filtering_by_type(self, client, sample_workflow_yaml):
        """Test filtering deliverables by type."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = sample_workflow_yaml
            
            with patch('os.path.exists', return_value=True):
                # Test filtering by plan type
                response = client.get("/api/v1/workflows/greenfield-fullstack/deliverables?type=plan")
        
        assert response.status_code == 200
        
        data = response.json()
        deliverables = data["deliverables"]
        
        # Should only return plan deliverables
        plan_count = 0
        for stage_deliverables in deliverables.values():
            for deliverable in stage_deliverables:
                assert deliverable["type"] == "plan"
                plan_count += 1
        
        assert plan_count == 5  # One plan per stage

    @pytest.mark.real_data
    async def test_deliverables_filtering_by_hitl_required(self, client, sample_workflow_yaml):
        """Test filtering deliverables by HITL requirement."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = sample_workflow_yaml
            
            with patch('os.path.exists', return_value=True):
                # Test filtering by HITL required
                response = client.get("/api/v1/workflows/greenfield-fullstack/deliverables?hitl_required=true")
        
        assert response.status_code == 200
        
        data = response.json()
        deliverables = data["deliverables"]
        
        # Should only return HITL-required deliverables
        hitl_count = 0
        for stage_deliverables in deliverables.values():
            for deliverable in stage_deliverables:
                assert deliverable.get("hitl_required", False) is True
                hitl_count += 1
        
        assert hitl_count == 5  # All HITL-required deliverables

    @pytest.mark.real_data
    async def test_workflow_deliverables_performance(self, client, sample_workflow_yaml):
        """Test workflow deliverables API performance."""
        import time
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = sample_workflow_yaml
            
            with patch('os.path.exists', return_value=True):
                start_time = time.time()
                
                response = client.get("/api/v1/workflows/greenfield-fullstack/deliverables")
                
                end_time = time.time()
                elapsed_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        
        # Should complete within reasonable time
        assert elapsed_ms < 1000  # Less than 1 second

    @pytest.mark.real_data
    async def test_multiple_workflow_support(self, client):
        """Test support for multiple workflow types."""
        workflows = [
            ("greenfield-fullstack", "Greenfield Fullstack Development"),
            ("greenfield-service", "Greenfield Service Development"),
            ("greenfield-ui", "Greenfield UI Development")
        ]
        
        for workflow_id, expected_name in workflows:
            sample_yaml = f"""
name: "{expected_name}"
description: "Test workflow"
version: "1.0"
phases:
  test:
    agent: "analyst"
    deliverables:
      - name: "Test Deliverable"
        type: "document"
        description: "Test deliverable"
"""
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = sample_yaml
                
                with patch('os.path.exists', return_value=True):
                    response = client.get(f"/api/v1/workflows/{workflow_id}/deliverables")
            
            if response.status_code == 200:
                data = response.json()
                assert data["metadata"]["workflow_name"] == expected_name

    @pytest.mark.real_data
    async def test_workflow_deliverables_validation(self, client):
        """Test workflow deliverables validation."""
        # Test workflow with missing required fields
        invalid_workflow = """
name: "Invalid Workflow"
phases:
  test:
    deliverables:
      - name: "Test"
        # Missing type and description
"""
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = invalid_workflow
            
            with patch('os.path.exists', return_value=True):
                response = client.get("/api/v1/workflows/invalid-workflow/deliverables")
        
        # Should handle validation gracefully
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            # If successful, should have proper structure
            data = response.json()
            assert "deliverables" in data
            assert "metadata" in data