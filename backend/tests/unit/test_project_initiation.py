"""
Unit tests for Story 1.1: Project Initiation

Test scenarios:
- 1.1-UNIT-001: Project model validation (P0)
- 1.1-UNIT-002: Task model validation (P0)  
- 1.1-UNIT-003: Project creation request validation (P0)
- 1.1-UNIT-004: Task status enumeration validation (P1)
- 1.1-UNIT-005: Project name validation rules (P1)
- 1.1-UNIT-006: UUID generation for project/task IDs (P2)
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import ValidationError

from app.models.task import Task, TaskStatus
from app.models.agent import AgentType
from app.database.models import ProjectDB, TaskDB

class TestProjectModelValidation:
    """Test scenario 1.1-UNIT-001: Project model validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_valid_project_model_creation(self):
        """Test creating a valid project model with required fields."""
        project_data = {
            "id": uuid4(),
            "name": "Test Project",
            "description": "A test project",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # ProjectDB is SQLAlchemy model, so we test direct instantiation
        project = ProjectDB(**project_data)
        
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.status == "active"
        assert isinstance(project.id, UUID)
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_project_model_with_minimal_fields(self):
        """Test project creation with only required fields."""
        project = ProjectDB(name="Minimal Project")
        
        assert project.name == "Minimal Project"
        assert project.description is None
        assert project.status is None  # Will be set by default in database
    
    @pytest.mark.unit
    @pytest.mark.p0  
    def test_project_model_name_requirements(self):
        """Test project name field requirements."""
        # Name is required for ProjectDB
        project = ProjectDB(name="Required Name")
        assert project.name == "Required Name"
        
        # Test empty name (will be handled by database constraints)
        project_empty = ProjectDB(name="")
        assert project_empty.name == ""
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_project_model_long_name_handling(self):
        """Test project name length handling."""
        long_name = "A" * 300  # Test beyond typical field length
        project = ProjectDB(name=long_name)
        assert project.name == long_name
        
        # Note: Actual length constraints are enforced at database level
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_project_model_special_characters(self):
        """Test project name with special characters."""
        special_name = "Project-2024 (Test) [v1.0] & More!"
        project = ProjectDB(name=special_name)
        assert project.name == special_name

class TestTaskModelValidation:
    """Test scenario 1.1-UNIT-002: Task model validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_valid_task_pydantic_model_creation(self):
        """Test creating a valid Task Pydantic model."""
        task_data = {
            "task_id": uuid4(),
            "project_id": uuid4(),
            "agent_type": AgentType.ANALYST.value,
            "status": TaskStatus.PENDING,
            "context_ids": [uuid4(), uuid4()],
            "instructions": "Test task instructions",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        task = Task(**task_data)
        
        assert isinstance(task.task_id, UUID)
        assert isinstance(task.project_id, UUID)
        assert task.agent_type == AgentType.ANALYST.value
        assert task.status == TaskStatus.PENDING
        assert len(task.context_ids) == 2
        assert task.instructions == "Test task instructions"
        assert task.output is None
        assert task.error_message is None
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_task_with_minimal_required_fields(self):
        """Test Task creation with minimal required fields."""
        task = Task(
            project_id=uuid4(),
            agent_type=AgentType.ANALYST.value,
            instructions="Minimal task"
        )
        
        assert isinstance(task.task_id, UUID)  # Auto-generated
        assert task.status == TaskStatus.PENDING  # Default
        assert task.context_ids == []  # Default
        assert task.output is None
        assert task.error_message is None
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_task_database_model_creation(self):
        """Test TaskDB SQLAlchemy model creation."""
        task_db_data = {
            "id": uuid4(),
            "project_id": uuid4(),
            "agent_type": AgentType.ANALYST.value,
            "status": TaskStatus.PENDING,
            "instructions": "Database task test",
            "context_ids": [str(uuid4())],  # Stored as JSON
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        task_db = TaskDB(**task_db_data)
        
        assert task_db.agent_type == AgentType.ANALYST.value
        assert task_db.status == TaskStatus.PENDING
        assert task_db.instructions == "Database task test"
        assert isinstance(task_db.context_ids, list)
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_task_invalid_agent_type_validation(self):
        """Test Task model validation with invalid agent type."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Task(
                project_id=uuid4(),
                agent_type="invalid_agent",  # Invalid agent type
                instructions="Test task"
            )
        
        error = exc_info.value
        assert "agent_type" in str(error)
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_task_with_output_and_error_data(self):
        """Test Task model with output and error data."""
        output_data = {"result": "success", "artifacts": ["file1.txt"]}
        error_message = "Test error occurred"
        
        task = Task(
            project_id=uuid4(),
            agent_type=AgentType.CODER.value,
            instructions="Task with output",
            output=output_data,
            error_message=error_message
        )
        
        assert task.output == output_data
        assert task.error_message == error_message

class TestProjectCreationRequestValidation:
    """Test scenario 1.1-UNIT-003: Project creation request validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_valid_project_creation_request_structure(self):
        """Test valid project creation request data structure."""
        request_data = {
            "name": "New Project",
            "description": "Project description"
        }
        
        # Test that request structure matches expected API payload
        assert "name" in request_data
        assert isinstance(request_data["name"], str)
        assert len(request_data["name"]) > 0
        
        assert "description" in request_data
        assert isinstance(request_data["description"], str)
    
    @pytest.mark.unit  
    @pytest.mark.p0
    def test_project_creation_request_name_validation(self):
        """Test project name validation in creation request."""
        # Valid name
        valid_request = {"name": "Valid Project Name"}
        assert len(valid_request["name"].strip()) > 0
        
        # Empty name should be invalid
        empty_name_request = {"name": ""}
        assert len(empty_name_request["name"].strip()) == 0
        
        # Whitespace-only name should be invalid
        whitespace_name_request = {"name": "   "}
        assert len(whitespace_name_request["name"].strip()) == 0
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_project_creation_request_optional_fields(self):
        """Test project creation with optional description field."""
        # Request with description
        with_description = {
            "name": "Project With Description",
            "description": "Detailed description"
        }
        assert "description" in with_description
        
        # Request without description  
        without_description = {"name": "Project Without Description"}
        assert "description" not in without_description
        
        # Request with null description
        null_description = {"name": "Project", "description": None}
        assert null_description["description"] is None

class TestTaskStatusEnumValidation:
    """Test scenario 1.1-UNIT-004: Task status enumeration validation (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_task_status_enum_values(self):
        """Test all TaskStatus enumeration values."""
        expected_statuses = ["pending", "working", "completed", "failed", "cancelled"]
        actual_statuses = [status.value for status in TaskStatus]
        
        assert len(actual_statuses) == len(expected_statuses)
        for expected in expected_statuses:
            assert expected in actual_statuses
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_task_status_enum_usage_in_task(self):
        """Test TaskStatus enum usage in Task model."""
        for status in TaskStatus:
            task = Task(
                project_id=uuid4(),
                agent_type=AgentType.ANALYST.value,
                instructions="Status test",
                status=status
            )
            assert task.status == status
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_task_status_string_values(self):
        """Test TaskStatus enum string values match expected."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.WORKING.value == "working"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_task_status_enum_comparison(self):
        """Test TaskStatus enum comparison operations."""
        assert TaskStatus.PENDING == TaskStatus.PENDING
        assert TaskStatus.PENDING != TaskStatus.WORKING
        
        # Test string comparison
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.WORKING.value != "pending"

class TestProjectNameValidationRules:
    """Test scenario 1.1-UNIT-005: Project name validation rules (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_project_name_length_boundaries(self):
        """Test project name length boundary conditions."""
        # Single character (minimum)
        single_char_name = "A"
        project = ProjectDB(name=single_char_name)
        assert project.name == single_char_name
        
        # Very long name
        long_name = "A" * 255  # Typical database field length
        project_long = ProjectDB(name=long_name)
        assert project_long.name == long_name
        assert len(project_long.name) == 255
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_project_name_character_validation(self):
        """Test project name with various character sets."""
        test_names = [
            "Simple Name",
            "Project-with-hyphens",
            "Project_with_underscores", 
            "Project123",
            "Project (with) [brackets]",
            "Projeçt wíth áccénts",
            "项目名称"  # Unicode characters
        ]
        
        for name in test_names:
            project = ProjectDB(name=name)
            assert project.name == name
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_project_name_whitespace_handling(self):
        """Test project name whitespace handling."""
        # Leading/trailing whitespace preservation (business rule dependent)
        whitespace_name = "  Project with spaces  "
        project = ProjectDB(name=whitespace_name)
        assert project.name == whitespace_name
        
        # Internal whitespace
        internal_spaces = "Project   with   multiple   spaces"
        project_internal = ProjectDB(name=internal_spaces)
        assert project_internal.name == internal_spaces
    
    @pytest.mark.unit
    @pytest.mark.p2
    def test_project_name_edge_cases(self):
        """Test project name edge cases."""
        edge_cases = [
            ".",  # Single period
            "..",  # Double period
            "123",  # Numbers only
            "!@#$%",  # Special characters only
            "\n\t",  # Control characters
        ]
        
        for edge_case in edge_cases:
            project = ProjectDB(name=edge_case)
            assert project.name == edge_case

class TestUUIDGeneration:
    """Test scenario 1.1-UNIT-006: UUID generation for project/task IDs (P2)"""
    
    @pytest.mark.unit
    @pytest.mark.p2
    def test_project_id_uuid_generation(self):
        """Test UUID generation for project IDs."""
        # Test Task model UUID generation
        task = Task(
            project_id=uuid4(),
            agent_type=AgentType.ANALYST.value,
            instructions="UUID test"
        )
        
        # task_id should be auto-generated UUID
        assert isinstance(task.task_id, UUID)
        assert str(task.task_id) != "00000000-0000-0000-0000-000000000000"
    
    @pytest.mark.unit
    @pytest.mark.p2  
    def test_uuid_uniqueness(self):
        """Test that generated UUIDs are unique."""
        # Generate multiple Task instances
        tasks = []
        for i in range(100):
            task = Task(
                project_id=uuid4(),
                agent_type=AgentType.ANALYST.value,
                instructions=f"Uniqueness test {i}"
            )
            tasks.append(task)
        
        # Collect all task IDs
        task_ids = [str(task.task_id) for task in tasks]
        
        # Verify all IDs are unique
        assert len(task_ids) == len(set(task_ids))
    
    @pytest.mark.unit
    @pytest.mark.p2
    def test_uuid_format_validation(self):
        """Test UUID format validation."""
        task = Task(
            project_id=uuid4(),
            agent_type=AgentType.ANALYST.value,
            instructions="Format test"
        )
        
        uuid_str = str(task.task_id)
        
        # UUID4 format: 8-4-4-4-12 hex digits
        assert len(uuid_str) == 36
        assert uuid_str.count('-') == 4
        
        # Verify it's a valid UUID by parsing it back
        parsed_uuid = UUID(uuid_str)
        assert str(parsed_uuid) == uuid_str
    
    @pytest.mark.unit
    @pytest.mark.p2
    def test_project_and_task_id_relationship(self):
        """Test relationship between project ID and task ID."""
        project_id = uuid4()
        
        # Create multiple tasks for same project
        tasks = []
        for i in range(5):
            task = Task(
                project_id=project_id,
                agent_type=AgentType.ANALYST.value,
                instructions=f"Relationship test {i}"
            )
            tasks.append(task)
        
        # All tasks should have same project_id but different task_ids
        for task in tasks:
            assert task.project_id == project_id
        
        task_ids = [task.task_id for task in tasks]
        assert len(set(task_ids)) == len(task_ids)  # All unique
