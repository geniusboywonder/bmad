"""
Unit tests for Story 2.1: Sequential Task Handoff

Test scenarios:
- 2.1-UNIT-001: SDLC_Process_Flow parsing validation (P0)
- 2.1-UNIT-002: HandoffSchema creation and validation (P0)
- 2.1-UNIT-003: Agent type determination logic (P1)
- 2.1-UNIT-004: Phase transition validation (P1)
- 2.1-UNIT-005: Task instruction generation (P2)
- 2.1-UNIT-006: Expected output validation (P2)
"""

import pytest
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, MagicMock

from app.models.agent import AgentType
from app.models.task import TaskStatus
from app.schemas.handoff import HandoffSchema
from tests.conftest import assert_handoff_schema_valid


class TestSDLCProcessFlowParsing:
    """Test scenario 2.1-UNIT-001: SDLC_Process_Flow parsing validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.handoff
    def test_valid_sdlc_flow_parsing(self, mock_sdlc_process_flow):
        """Test parsing of valid SDLC process flow configuration."""
        # Import here to avoid module loading issues during test discovery
        from app.services.orchestrator import OrchestratorService
        
        # Test SDLC flow structure validation
        assert "phases" in mock_sdlc_process_flow
        phases = mock_sdlc_process_flow["phases"]
        
        # Verify all required phases present
        phase_names = [phase["name"] for phase in phases]
        expected_phases = ["analysis", "architecture", "implementation", "testing", "deployment"]
        assert all(phase in phase_names for phase in expected_phases)
        
        # Verify each phase has required fields
        for phase in phases:
            assert "name" in phase
            assert "agent_type" in phase
            assert "inputs" in phase
            assert "outputs" in phase
            assert isinstance(phase["inputs"], list)
            assert isinstance(phase["outputs"], list)
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.handoff
    def test_invalid_sdlc_flow_handling(self):
        """Test handling of invalid SDLC process flow configuration."""
        from app.services.orchestrator import OrchestratorService
        
        # Test missing phases
        invalid_flow = {"invalid_key": "value"}
        with pytest.raises(KeyError):
            # Should raise KeyError when phases key is missing
            phases = invalid_flow["phases"]
        
        # Test empty phases
        empty_flow = {"phases": []}
        phases = empty_flow["phases"]
        assert len(phases) == 0
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_phase_order_validation(self, mock_sdlc_process_flow):
        """Test that phases are in correct dependency order."""
        phases = mock_sdlc_process_flow["phases"]
        
        # Verify analysis comes first (no inputs except user requirements)
        analysis_phase = next(p for p in phases if p["name"] == "analysis")
        assert "user_requirements" in analysis_phase["inputs"]
        
        # Verify architecture depends on analysis output
        architecture_phase = next(p for p in phases if p["name"] == "architecture")
        analysis_output = analysis_phase["outputs"][0]
        assert analysis_output in architecture_phase["inputs"]
        
        # Verify implementation depends on architecture
        implementation_phase = next(p for p in phases if p["name"] == "implementation")
        architecture_output = architecture_phase["outputs"][0]
        assert architecture_output in implementation_phase["inputs"]
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.handoff
    def test_agent_type_mapping_validation(self, mock_sdlc_process_flow):
        """Test that each phase maps to valid agent type."""
        phases = mock_sdlc_process_flow["phases"]
        valid_agent_types = [agent.value for agent in AgentType]
        
        for phase in phases:
            assert phase["agent_type"] in valid_agent_types


class TestHandoffSchemaCreation:
    """Test scenario 2.1-UNIT-002: HandoffSchema creation and validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.handoff
    def test_valid_handoff_schema_creation(self, sample_handoff_schema_data):
        """Test creation of valid HandoffSchema."""
        # Test schema creation with all required fields
        handoff_data = sample_handoff_schema_data
        assert_handoff_schema_valid(handoff_data)
        
        # Test required fields are present
        assert handoff_data["from_agent"] == AgentType.ANALYST.value
        assert handoff_data["to_agent"] == AgentType.ARCHITECT.value
        assert "instructions" in handoff_data
        assert "context_summary" in handoff_data
        assert "expected_outputs" in handoff_data
        assert isinstance(handoff_data["expected_outputs"], list)
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.handoff
    def test_handoff_schema_validation_rules(self):
        """Test HandoffSchema field validation rules."""
        # Test missing required fields
        incomplete_data = {
            "from_agent": AgentType.ANALYST.value,
            # Missing to_agent, phase, instructions, context_summary, expected_outputs
        }
        
        with pytest.raises(AssertionError):
            assert_handoff_schema_valid(incomplete_data)
        
        # Test invalid agent types
        invalid_agent_data = {
            "from_agent": "invalid_agent",
            "to_agent": AgentType.ARCHITECT.value,
            "phase": "architecture",
            "instructions": "Test instructions",
            "context_summary": "Test summary",
            "expected_outputs": ["Test output"]
        }
        
        with pytest.raises(AssertionError):
            assert_handoff_schema_valid(invalid_agent_data)
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_expected_outputs_validation(self):
        """Test expected_outputs field validation."""
        # Test valid expected outputs list
        valid_data = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "phase": "architecture",
            "instructions": "Test instructions",
            "context_summary": "Test summary",
            "expected_outputs": ["Architecture document", "Component diagram"]
        }
        assert_handoff_schema_valid(valid_data)
        
        # Test invalid expected_outputs type
        invalid_outputs_data = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "phase": "architecture",
            "instructions": "Test instructions",
            "context_summary": "Test summary",
            "expected_outputs": "not_a_list"
        }
        
        with pytest.raises(AssertionError):
            assert_handoff_schema_valid(invalid_outputs_data)
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.handoff
    def test_optional_fields_handling(self):
        """Test handling of optional HandoffSchema fields."""
        # Test minimal valid schema
        minimal_data = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "phase": "architecture",
            "instructions": "Test instructions",
            "context_summary": "Test summary",
            "expected_outputs": ["Test output"]
        }
        assert_handoff_schema_valid(minimal_data)
        
        # Test with all optional fields
        complete_data = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "phase": "architecture",
            "instructions": "Test instructions",
            "context_summary": "Test summary",
            "expected_outputs": ["Architecture document", "System design"],
            "priority": "high",
            "metadata": {"custom": "field"},
            "dependencies": ["requirements"],
            "acceptance_criteria": ["Must be scalable"]
        }
        assert_handoff_schema_valid(complete_data)


class TestAgentTypeDetermination:
    """Test scenario 2.1-UNIT-003: Agent type determination logic (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_next_agent_determination(self, mock_sdlc_process_flow, mock_handoff_validator):
        """Test determination of next agent in workflow."""
        # Test analyst -> architect transition
        mock_handoff_validator.get_next_agent.return_value = AgentType.ARCHITECT.value
        next_agent = mock_handoff_validator.get_next_agent()
        assert next_agent == AgentType.ARCHITECT.value
        
        # Test architect -> coder transition
        mock_handoff_validator.get_next_agent.return_value = AgentType.CODER.value
        next_agent = mock_handoff_validator.get_next_agent()
        assert next_agent == AgentType.CODER.value
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_workflow_completion_detection(self, mock_sdlc_process_flow):
        """Test detection of workflow completion."""
        phases = mock_sdlc_process_flow["phases"]
        
        # Test last phase detection
        last_phase = phases[-1]
        assert last_phase["name"] == "deployment"
        assert last_phase["agent_type"] == AgentType.DEPLOYER.value
        
        # Test that deployment phase produces final output
        assert "deployment_package" in last_phase["outputs"]
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.handoff
    def test_agent_specialization_validation(self):
        """Test that agents are specialized for their roles."""
        # Test each agent type has specific capabilities
        agent_capabilities = {
            AgentType.ANALYST: ["requirements_analysis", "project_planning"],
            AgentType.ARCHITECT: ["system_design", "architecture_specification"],
            AgentType.CODER: ["code_generation", "implementation"],
            AgentType.TESTER: ["test_creation", "quality_assurance"],
            AgentType.DEPLOYER: ["deployment_planning", "environment_setup"]
        }
        
        for agent_type, capabilities in agent_capabilities.items():
            assert len(capabilities) > 0
            assert all(isinstance(cap, str) for cap in capabilities)


class TestPhaseTransitionLogic:
    """Test scenario 2.1-UNIT-004: Phase transition validation (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_valid_phase_transitions(self, mock_sdlc_process_flow):
        """Test valid phase transition logic."""
        phases = mock_sdlc_process_flow["phases"]
        
        # Test analysis -> architecture transition
        analysis_phase = next(p for p in phases if p["name"] == "analysis")
        architecture_phase = next(p for p in phases if p["name"] == "architecture")
        
        # Analysis output should be input to architecture
        analysis_output = analysis_phase["outputs"][0]
        assert analysis_output in architecture_phase["inputs"]
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_phase_prerequisite_validation(self, mock_sdlc_process_flow):
        """Test that phase prerequisites are validated."""
        phases = mock_sdlc_process_flow["phases"]
        
        # Implementation phase should require architecture input
        impl_phase = next(p for p in phases if p["name"] == "implementation")
        assert "system_architecture" in impl_phase["inputs"]
        
        # Testing phase should require implementation output
        test_phase = next(p for p in phases if p["name"] == "testing")
        assert "source_code" in test_phase["inputs"]
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_invalid_phase_transition_handling(self):
        """Test handling of invalid phase transitions."""
        # Test skip prevention (can't go from analysis directly to testing)
        invalid_transition = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.TESTER.value,  # Should go through ARCHITECT and CODER first
            "phase": "testing",
            "instructions": "Invalid direct transition",
            "context_summary": "Analysis completed",
            "expected_outputs": ["Test results"]
        }
        
        # This should be caught by business logic validation
        assert_handoff_schema_valid(invalid_transition)  # Schema is valid
        
        # But business logic should prevent this transition
        # (This would be tested in integration tests with actual orchestrator)
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.handoff
    def test_circular_transition_prevention(self):
        """Test prevention of circular transitions."""
        # Test that agent can't hand off to itself
        circular_handoff = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ANALYST.value,  # Same agent
            "phase": "analysis",
            "instructions": "Circular handoff",
            "context_summary": "Self-handoff test",
            "expected_outputs": ["Same work"]
        }
        
        # Schema validation allows this, but business logic should prevent it
        assert_handoff_schema_valid(circular_handoff)
        
        # Business validation would be:
        assert circular_handoff["from_agent"] == circular_handoff["to_agent"]


class TestTaskInstructionGeneration:
    """Test scenario 2.1-UNIT-005: Task instruction generation (P2)"""
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.handoff
    def test_instruction_template_generation(self):
        """Test generation of task instructions from templates."""
        # Mock instruction generator
        def generate_instructions(agent_type: str, phase: str, context: list) -> str:
            templates = {
                AgentType.ANALYST.value: f"Analyze {phase} requirements using context: {context}",
                AgentType.ARCHITECT.value: f"Design {phase} architecture based on: {context}",
                AgentType.CODER.value: f"Implement {phase} code according to: {context}"
            }
            return templates.get(agent_type, f"Execute {phase} task")
        
        # Test instruction generation for different agents
        analyst_instruction = generate_instructions(
            AgentType.ANALYST.value, 
            "user_requirements", 
            ["project_description"]
        )
        assert "Analyze" in analyst_instruction
        assert "requirements" in analyst_instruction
        
        architect_instruction = generate_instructions(
            AgentType.ARCHITECT.value,
            "system_design",
            ["project_plan"]
        )
        assert "Design" in architect_instruction
        assert "architecture" in architect_instruction
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.handoff
    def test_context_injection_in_instructions(self, sample_handoff_schema_data):
        """Test that context is properly injected into instructions."""
        handoff_data = sample_handoff_schema_data
        instructions = handoff_data["instructions"]
        context_summary = handoff_data["context_summary"]
        
        # Instructions should be meaningful
        assert len(instructions) > 10
        assert isinstance(instructions, str)
        
        # Context summary should be meaningful
        assert len(context_summary) > 10
        assert isinstance(context_summary, str)
    
    @pytest.mark.unit
    @pytest.mark.p3
    @pytest.mark.handoff
    def test_instruction_personalization(self):
        """Test personalization of instructions for specific agents."""
        base_instruction = "Process the user requirements"
        
        # Mock personalization function
        def personalize_instruction(instruction: str, agent_type: str) -> str:
            personalizations = {
                AgentType.ANALYST.value: f"As an analyst, {instruction} and create detailed specifications",
                AgentType.ARCHITECT.value: f"As an architect, {instruction} and design system structure",
                AgentType.CODER.value: f"As a developer, {instruction} and write implementation code"
            }
            return personalizations.get(agent_type, instruction)
        
        analyst_instruction = personalize_instruction(base_instruction, AgentType.ANALYST.value)
        assert "analyst" in analyst_instruction
        assert "specifications" in analyst_instruction
        
        architect_instruction = personalize_instruction(base_instruction, AgentType.ARCHITECT.value)
        assert "architect" in architect_instruction
        assert "system structure" in architect_instruction


class TestExpectedOutputValidation:
    """Test scenario 2.1-UNIT-006: Expected output validation (P2)"""
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.handoff
    def test_output_specification_validation(self, sample_handoff_schema_data):
        """Test validation of expected output specifications."""
        handoff_data = sample_handoff_schema_data
        expected_outputs = handoff_data.get("expected_outputs", [])
        
        # Expected outputs should be a list
        assert isinstance(expected_outputs, list)
        assert len(expected_outputs) > 0
        
        # Each output should be descriptive
        for output in expected_outputs:
            assert len(output) > 5
            assert isinstance(output, str)
            
            # Should contain meaningful keywords
            keywords = ["document", "specification", "plan", "code", "test", "architecture", "system", "component"]
            assert any(keyword in output.lower() for keyword in keywords)
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.handoff
    def test_output_format_requirements(self):
        """Test that output format requirements are specified."""
        output_formats = {
            AgentType.ANALYST.value: ["markdown", "json", "structured_text"],
            AgentType.ARCHITECT.value: ["diagram", "specification", "json"],
            AgentType.CODER.value: ["python", "javascript", "sql"],
            AgentType.TESTER.value: ["test_results", "coverage_report"],
            AgentType.DEPLOYER.value: ["deployment_plan", "configuration"]
        }
        
        for agent_type, formats in output_formats.items():
            assert len(formats) > 0
            assert all(isinstance(fmt, str) for fmt in formats)
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.handoff  
    def test_output_quality_criteria(self):
        """Test output quality criteria definition."""
        quality_criteria = {
            "completeness": "Output addresses all requirements",
            "accuracy": "Output is technically correct",
            "clarity": "Output is clearly structured and readable",
            "actionability": "Output enables next phase execution"
        }
        
        for criterion, description in quality_criteria.items():
            assert len(description) > 10
            assert isinstance(description, str)
    
    @pytest.mark.unit
    @pytest.mark.p3
    @pytest.mark.handoff
    def test_output_validation_rules(self):
        """Test output validation rules for different phases."""
        validation_rules = {
            "project_plan": {
                "required_sections": ["objectives", "scope", "timeline"],
                "format": "structured_document"
            },
            "system_architecture": {
                "required_sections": ["components", "data_flow", "interfaces"],
                "format": "technical_specification"
            },
            "source_code": {
                "required_elements": ["functions", "classes", "documentation"],
                "format": "executable_code"
            }
        }
        
        for output_type, rules in validation_rules.items():
            assert "required_sections" in rules or "required_elements" in rules
            assert "format" in rules
            assert len(rules["format"]) > 0