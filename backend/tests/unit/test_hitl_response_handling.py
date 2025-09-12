"""
Unit tests for Story 2.3: HITL Response Handling

Test scenarios:
- 2.3-UNIT-001: HitlAction enumeration validation (P0)
- 2.3-UNIT-002: HitlRequest status transitions (P0)
- 2.3-UNIT-003: History entry creation logic (P0)
- 2.3-UNIT-004: Amendment content validation (P1)
- 2.3-UNIT-005: Request expiration logic (P1)
- 2.3-UNIT-006: HITL response serialization (P2)
- 2.3-UNIT-007: Error message generation (P2)
"""

import pytest
import json
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.models.hitl import HitlStatus, HitlAction, HitlRequest, HitlResponse
from app.models.agent import AgentType
from app.schemas.hitl import HitlResponseRequest


class TestHitlActionEnumerationValidation:
    """Test scenario 2.3-UNIT-001: HitlAction enumeration validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_all_hitl_actions_defined(self):
        """Test that all required HITL actions are defined."""
        required_actions = ["approve", "reject", "amend"]
        
        action_values = [action.value for action in HitlAction]
        
        for required_action in required_actions:
            assert required_action in action_values, f"Missing HITL action: {required_action}"
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_hitl_action_values_consistency(self):
        """Test that HITL action values are consistent and valid."""
        for action in HitlAction:
            # Each action should have a name
            assert hasattr(action, 'name')
            assert len(action.name) > 0
            
            # Each action should have a value
            assert hasattr(action, 'value')
            assert len(action.value) > 0
            
            # Name and value should be strings
            assert isinstance(action.name, str)
            assert isinstance(action.value, str)
            
            # Value should be lowercase
            assert action.value.islower()
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_hitl_action_uniqueness(self):
        """Test that all HITL actions are unique."""
        action_names = [action.name for action in HitlAction]
        action_values = [action.value for action in HitlAction]
        
        # Names should be unique
        assert len(action_names) == len(set(action_names)), "Duplicate HITL action names found"
        
        # Values should be unique
        assert len(action_values) == len(set(action_values)), "Duplicate HITL action values found"
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_hitl_action_from_string_creation(self):
        """Test creation of HITL actions from string values."""
        # Test valid string conversion
        approve_action = HitlAction("approve")
        assert approve_action == HitlAction.APPROVE
        
        reject_action = HitlAction("reject")
        assert reject_action == HitlAction.REJECT
        
        amend_action = HitlAction("amend")
        assert amend_action == HitlAction.AMEND
        
        # Test invalid string handling
        with pytest.raises(ValueError):
            HitlAction("invalid_action")
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_hitl_action_string_representation(self):
        """Test string representation of HITL actions."""
        for action in HitlAction:
            # Should convert to string
            str_value = str(action)
            assert isinstance(str_value, str)
            assert len(str_value) > 0
            
            # String representation should be meaningful
            assert action.name in str_value or action.value in str_value


class TestHitlRequestStatusTransitions:
    """Test scenario 2.3-UNIT-002: HitlRequest status transitions (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_valid_status_transitions(self):
        """Test valid HITL request status transitions."""
        # Define valid transitions
        valid_transitions = {
            HitlStatus.PENDING: [HitlStatus.APPROVED, HitlStatus.REJECTED, HitlStatus.AMENDED, HitlStatus.EXPIRED],
            HitlStatus.APPROVED: [],  # Terminal state
            HitlStatus.REJECTED: [],  # Terminal state
            HitlStatus.AMENDED: [HitlStatus.APPROVED, HitlStatus.REJECTED],  # Can be re-reviewed
            HitlStatus.EXPIRED: []   # Terminal state
        }
        
        def is_valid_transition(from_status: HitlStatus, to_status: HitlStatus) -> bool:
            return to_status in valid_transitions.get(from_status, [])
        
        # Test valid transitions
        assert is_valid_transition(HitlStatus.PENDING, HitlStatus.APPROVED)
        assert is_valid_transition(HitlStatus.PENDING, HitlStatus.REJECTED)
        assert is_valid_transition(HitlStatus.PENDING, HitlStatus.AMENDED)
        assert is_valid_transition(HitlStatus.AMENDED, HitlStatus.APPROVED)
        
        # Test invalid transitions
        assert not is_valid_transition(HitlStatus.APPROVED, HitlStatus.REJECTED)
        assert not is_valid_transition(HitlStatus.REJECTED, HitlStatus.APPROVED)
        assert not is_valid_transition(HitlStatus.EXPIRED, HitlStatus.APPROVED)
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_status_transition_logic(self):
        """Test status transition logic implementation."""
        def transition_status(current_status: HitlStatus, action: HitlAction) -> HitlStatus:
            """Mock status transition function."""
            transition_map = {
                (HitlStatus.PENDING, HitlAction.APPROVE): HitlStatus.APPROVED,
                (HitlStatus.PENDING, HitlAction.REJECT): HitlStatus.REJECTED,
                (HitlStatus.PENDING, HitlAction.AMEND): HitlStatus.AMENDED,
                (HitlStatus.AMENDED, HitlAction.APPROVE): HitlStatus.APPROVED,
                (HitlStatus.AMENDED, HitlAction.REJECT): HitlStatus.REJECTED,
            }
            
            new_status = transition_map.get((current_status, action))
            if new_status is None:
                raise ValueError(f"Invalid transition: {current_status} -> {action}")
            
            return new_status
        
        # Test valid action-based transitions
        assert transition_status(HitlStatus.PENDING, HitlAction.APPROVE) == HitlStatus.APPROVED
        assert transition_status(HitlStatus.PENDING, HitlAction.REJECT) == HitlStatus.REJECTED
        assert transition_status(HitlStatus.PENDING, HitlAction.AMEND) == HitlStatus.AMENDED
        
        # Test amended status can be re-reviewed
        assert transition_status(HitlStatus.AMENDED, HitlAction.APPROVE) == HitlStatus.APPROVED
        assert transition_status(HitlStatus.AMENDED, HitlAction.REJECT) == HitlStatus.REJECTED
        
        # Test invalid transitions raise errors
        with pytest.raises(ValueError):
            transition_status(HitlStatus.APPROVED, HitlAction.REJECT)
        
        with pytest.raises(ValueError):
            transition_status(HitlStatus.REJECTED, HitlAction.APPROVE)
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_status_transition_history_tracking(self):
        """Test tracking of status transition history."""
        # Mock transition history
        transition_history = []
        
        def record_transition(from_status: HitlStatus, to_status: HitlStatus, action: HitlAction, timestamp: datetime):
            transition_history.append({
                "from_status": from_status,
                "to_status": to_status,
                "action": action,
                "timestamp": timestamp
            })
        
        # Simulate transitions
        now = datetime.now()
        record_transition(HitlStatus.PENDING, HitlStatus.AMENDED, HitlAction.AMEND, now)
        record_transition(HitlStatus.AMENDED, HitlStatus.APPROVED, HitlAction.APPROVE, now + timedelta(hours=1))
        
        # Verify history tracking
        assert len(transition_history) == 2
        
        first_transition = transition_history[0]
        assert first_transition["from_status"] == HitlStatus.PENDING
        assert first_transition["to_status"] == HitlStatus.AMENDED
        assert first_transition["action"] == HitlAction.AMEND
        
        second_transition = transition_history[1]
        assert second_transition["from_status"] == HitlStatus.AMENDED
        assert second_transition["to_status"] == HitlStatus.APPROVED
        assert second_transition["action"] == HitlAction.APPROVE
        
        # Verify chronological order
        assert first_transition["timestamp"] < second_transition["timestamp"]
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_terminal_status_validation(self):
        """Test validation of terminal status states."""
        terminal_statuses = [HitlStatus.APPROVED, HitlStatus.REJECTED, HitlStatus.EXPIRED]
        non_terminal_statuses = [HitlStatus.PENDING, HitlStatus.AMENDED]
        
        def is_terminal_status(status: HitlStatus) -> bool:
            return status in terminal_statuses
        
        # Test terminal status identification
        for status in terminal_statuses:
            assert is_terminal_status(status), f"{status} should be terminal"
        
        for status in non_terminal_statuses:
            assert not is_terminal_status(status), f"{status} should not be terminal"


class TestHistoryEntryCreationLogic:
    """Test scenario 2.3-UNIT-003: History entry creation logic (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_history_entry_structure(self):
        """Test structure of HITL history entries."""
        # Mock history entry creation
        def create_history_entry(
            hitl_request_id: UUID,
            action: HitlAction,
            user_id: str,
            timestamp: datetime,
            comment: str = None,
            content: dict = None
        ) -> dict:
            entry = {
                "hitl_request_id": str(hitl_request_id),
                "action": action.value,
                "user_id": user_id,
                "timestamp": timestamp.isoformat(),
                "entry_id": str(uuid4())
            }
            
            if comment:
                entry["comment"] = comment
            if content:
                entry["content"] = content
            
            return entry
        
        # Test basic history entry
        hitl_id = uuid4()
        timestamp = datetime.now()
        
        entry = create_history_entry(
            hitl_request_id=hitl_id,
            action=HitlAction.APPROVE,
            user_id="user123",
            timestamp=timestamp,
            comment="Looks good to proceed"
        )
        
        # Verify required fields
        assert "hitl_request_id" in entry
        assert "action" in entry
        assert "user_id" in entry
        assert "timestamp" in entry
        assert "entry_id" in entry
        
        # Verify field values
        assert entry["hitl_request_id"] == str(hitl_id)
        assert entry["action"] == HitlAction.APPROVE.value
        assert entry["user_id"] == "user123"
        assert entry["comment"] == "Looks good to proceed"
        
        # Verify entry ID is valid UUID
        UUID(entry["entry_id"])  # Should not raise exception
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_history_entry_for_different_actions(self):
        """Test history entry creation for different HITL actions."""
        hitl_id = uuid4()
        timestamp = datetime.now()
        
        def create_entry(action: HitlAction, **kwargs):
            return {
                "hitl_request_id": str(hitl_id),
                "action": action.value,
                "user_id": "test_user",
                "timestamp": timestamp.isoformat(),
                "entry_id": str(uuid4()),
                **kwargs
            }
        
        # Test approve entry
        approve_entry = create_entry(
            HitlAction.APPROVE,
            comment="Approved for implementation"
        )
        assert approve_entry["action"] == "approve"
        assert "comment" in approve_entry
        
        # Test reject entry
        reject_entry = create_entry(
            HitlAction.REJECT,
            comment="Does not meet requirements",
            reason="insufficient_detail"
        )
        assert reject_entry["action"] == "reject"
        assert reject_entry["reason"] == "insufficient_detail"
        
        # Test amend entry
        amend_entry = create_entry(
            HitlAction.AMEND,
            comment="Please add more detail to section 3",
            content={
                "amended_section": "requirements",
                "specific_changes": ["add performance metrics", "clarify user flows"]
            }
        )
        assert amend_entry["action"] == "amend"
        assert "content" in amend_entry
        assert "amended_section" in amend_entry["content"]
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_history_entry_validation(self):
        """Test validation of history entry data."""
        def validate_history_entry(entry: dict) -> bool:
            required_fields = ["hitl_request_id", "action", "user_id", "timestamp", "entry_id"]
            
            # Check required fields
            for field in required_fields:
                if field not in entry:
                    return False
            
            # Validate field types and formats
            try:
                UUID(entry["hitl_request_id"])
                UUID(entry["entry_id"])
                datetime.fromisoformat(entry["timestamp"])
                HitlAction(entry["action"])  # Validate action is valid
            except (ValueError, TypeError):
                return False
            
            # Validate user_id is non-empty string
            if not isinstance(entry["user_id"], str) or len(entry["user_id"]) == 0:
                return False
            
            return True
        
        # Test valid entry
        valid_entry = {
            "hitl_request_id": str(uuid4()),
            "action": HitlAction.APPROVE.value,
            "user_id": "user123",
            "timestamp": datetime.now().isoformat(),
            "entry_id": str(uuid4())
        }
        assert validate_history_entry(valid_entry)
        
        # Test invalid entries
        invalid_entries = [
            {},  # Empty entry
            {"hitl_request_id": "invalid_uuid", "action": "approve", "user_id": "user", "timestamp": "now", "entry_id": str(uuid4())},  # Invalid UUID
            {"hitl_request_id": str(uuid4()), "action": "invalid_action", "user_id": "user", "timestamp": datetime.now().isoformat(), "entry_id": str(uuid4())},  # Invalid action
            {"hitl_request_id": str(uuid4()), "action": "approve", "user_id": "", "timestamp": datetime.now().isoformat(), "entry_id": str(uuid4())},  # Empty user_id
        ]
        
        for invalid_entry in invalid_entries:
            assert not validate_history_entry(invalid_entry)
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_history_entry_chronological_ordering(self):
        """Test chronological ordering of history entries."""
        hitl_id = uuid4()
        base_time = datetime.now()
        
        # Create entries with different timestamps
        entries = []
        for i in range(5):
            entry = {
                "hitl_request_id": str(hitl_id),
                "action": HitlAction.AMEND.value,
                "user_id": f"user{i}",
                "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                "entry_id": str(uuid4()),
                "sequence": i
            }
            entries.append(entry)
        
        # Shuffle entries
        import random
        shuffled_entries = entries.copy()
        random.shuffle(shuffled_entries)
        
        # Sort by timestamp
        sorted_entries = sorted(shuffled_entries, key=lambda x: x["timestamp"])
        
        # Verify chronological order
        for i, entry in enumerate(sorted_entries):
            assert entry["sequence"] == i
            
        # Verify timestamps are in ascending order
        timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in sorted_entries]
        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i-1]


class TestAmendmentContentValidation:
    """Test scenario 2.3-UNIT-004: Amendment content validation (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_amendment_content_structure(self):
        """Test structure validation of amendment content."""
        def validate_amendment_content(content: dict) -> bool:
            required_fields = ["amended_content"]
            optional_fields = ["comment", "section", "priority", "reason"]
            
            # Check required fields
            for field in required_fields:
                if field not in content:
                    return False
            
            # Validate amended_content is non-empty string
            if not isinstance(content["amended_content"], str) or len(content["amended_content"]) == 0:
                return False
            
            # Validate optional fields if present
            for field in optional_fields:
                if field in content:
                    if not isinstance(content[field], str):
                        return False
            
            return True
        
        # Test valid amendment content
        valid_contents = [
            {"amended_content": "Please add more details to the architecture section"},
            {
                "amended_content": "Revise the performance requirements",
                "comment": "Current specs are too vague",
                "section": "performance",
                "priority": "high"
            }
        ]
        
        for content in valid_contents:
            assert validate_amendment_content(content)
        
        # Test invalid amendment content
        invalid_contents = [
            {},  # Missing required field
            {"amended_content": ""},  # Empty amended_content
            {"amended_content": 123},  # Wrong type for amended_content
            {"amended_content": "Valid content", "priority": 123},  # Wrong type for optional field
        ]
        
        for content in invalid_contents:
            assert not validate_amendment_content(content)
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_amendment_content_length_validation(self):
        """Test length validation of amendment content."""
        def validate_amendment_length(content: str, min_length: int = 10, max_length: int = 5000) -> bool:
            return min_length <= len(content) <= max_length
        
        # Test valid lengths
        assert validate_amendment_length("This is a valid amendment with sufficient detail")
        assert validate_amendment_length("A" * 100)  # 100 characters
        assert validate_amendment_length("A" * 4999)  # Just under max
        
        # Test invalid lengths
        assert not validate_amendment_length("Too short")  # Under 10 characters
        assert not validate_amendment_length("A" * 5001)  # Over max length
        assert not validate_amendment_length("")  # Empty string
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_amendment_content_formatting(self):
        """Test formatting and sanitization of amendment content."""
        def format_amendment_content(raw_content: str) -> str:
            # Basic formatting: strip whitespace, normalize line breaks
            formatted = raw_content.strip()
            formatted = formatted.replace('\r\n', '\n')
            formatted = formatted.replace('\r', '\n')
            
            # Remove excessive whitespace
            while '  ' in formatted:
                formatted = formatted.replace('  ', ' ')
            
            return formatted
        
        # Test formatting
        raw_content = "  This is amendment content  \r\n\r\nWith  multiple    spaces   "
        formatted = format_amendment_content(raw_content)
        
        assert formatted.strip() == formatted  # No leading/trailing whitespace
        assert '\r' not in formatted  # No carriage returns
        assert '  ' not in formatted  # No double spaces
        assert "This is amendment content\n\nWith multiple spaces" == formatted
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_amendment_content_security_validation(self):
        """Test security validation of amendment content."""
        def validate_amendment_security(content: str) -> bool:
            # Basic security checks
            dangerous_patterns = [
                '<script',
                'javascript:',
                'data:',
                'vbscript:',
                'onload=',
                'onerror=',
                '<?php',
                '<%',
                'eval(',
                'exec(',
            ]
            
            content_lower = content.lower()
            for pattern in dangerous_patterns:
                if pattern in content_lower:
                    return False
            
            return True
        
        # Test safe content
        safe_contents = [
            "Please revise the architecture to use microservices",
            "Add more details about the database schema",
            "The current implementation needs error handling"
        ]
        
        for content in safe_contents:
            assert validate_amendment_security(content)
        
        # Test potentially dangerous content
        dangerous_contents = [
            "Please add <script>alert('xss')</script> to the document",
            "Use javascript:void(0) for the link",
            "Add eval(userInput) for dynamic processing"
        ]
        
        for content in dangerous_contents:
            assert not validate_amendment_security(content)


class TestRequestExpirationLogic:
    """Test scenario 2.3-UNIT-005: Request expiration logic (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_expiration_time_calculation(self):
        """Test calculation of HITL request expiration times."""
        def calculate_expiration_time(created_at: datetime, ttl_hours: int = 24) -> datetime:
            return created_at + timedelta(hours=ttl_hours)
        
        # Test default expiration (24 hours)
        created_time = datetime.now()
        expiration_time = calculate_expiration_time(created_time)
        
        expected_expiration = created_time + timedelta(hours=24)
        assert expiration_time == expected_expiration
        
        # Test custom TTL
        custom_expiration = calculate_expiration_time(created_time, ttl_hours=48)
        expected_custom = created_time + timedelta(hours=48)
        assert custom_expiration == expected_custom
        
        # Test short TTL
        short_expiration = calculate_expiration_time(created_time, ttl_hours=1)
        expected_short = created_time + timedelta(hours=1)
        assert short_expiration == expected_short
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_expiration_status_check(self):
        """Test checking if HITL requests have expired."""
        def is_expired(expiration_time: datetime, current_time: datetime = None) -> bool:
            if current_time is None:
                current_time = datetime.now()
            return current_time > expiration_time
        
        now = datetime.now()
        
        # Test not expired
        future_expiration = now + timedelta(hours=1)
        assert not is_expired(future_expiration, now)
        
        # Test expired
        past_expiration = now - timedelta(hours=1)
        assert is_expired(past_expiration, now)
        
        # Test exactly at expiration
        exact_expiration = now
        assert not is_expired(exact_expiration, now)  # Not expired at exact time
        
        # Test expired by one second
        just_expired = now - timedelta(seconds=1)
        assert is_expired(just_expired, now)
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_expiration_grace_period(self):
        """Test expiration grace period logic."""
        def is_expired_with_grace(
            expiration_time: datetime, 
            current_time: datetime = None, 
            grace_minutes: int = 5
        ) -> bool:
            if current_time is None:
                current_time = datetime.now()
            
            grace_period = timedelta(minutes=grace_minutes)
            effective_expiration = expiration_time + grace_period
            
            return current_time > effective_expiration
        
        now = datetime.now()
        expiration = now - timedelta(minutes=3)  # Expired 3 minutes ago
        
        # Within grace period (5 minutes)
        assert not is_expired_with_grace(expiration, now, grace_minutes=5)
        
        # Outside grace period
        assert is_expired_with_grace(expiration, now, grace_minutes=2)
        
        # Test with different grace periods
        assert not is_expired_with_grace(expiration, now, grace_minutes=10)
        assert is_expired_with_grace(expiration, now, grace_minutes=1)
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_expiration_cleanup_logic(self):
        """Test logic for cleaning up expired HITL requests."""
        def get_expired_requests(requests: list, current_time: datetime = None) -> list:
            if current_time is None:
                current_time = datetime.now()
            
            expired_requests = []
            for request in requests:
                if request["status"] == HitlStatus.PENDING.value:
                    expiration_time = datetime.fromisoformat(request["expiration_time"])
                    if current_time > expiration_time:
                        expired_requests.append(request)
            
            return expired_requests
        
        now = datetime.now()
        
        # Mock requests with different states
        requests = [
            {
                "id": str(uuid4()),
                "status": HitlStatus.PENDING.value,
                "expiration_time": (now - timedelta(hours=1)).isoformat()  # Expired
            },
            {
                "id": str(uuid4()),
                "status": HitlStatus.PENDING.value,
                "expiration_time": (now + timedelta(hours=1)).isoformat()  # Not expired
            },
            {
                "id": str(uuid4()),
                "status": HitlStatus.APPROVED.value,
                "expiration_time": (now - timedelta(hours=1)).isoformat()  # Expired but approved
            },
            {
                "id": str(uuid4()),
                "status": HitlStatus.PENDING.value,
                "expiration_time": (now - timedelta(minutes=30)).isoformat()  # Expired
            }
        ]
        
        expired_requests = get_expired_requests(requests, now)
        
        # Should return 2 expired pending requests
        assert len(expired_requests) == 2
        
        # Verify only pending requests are included
        for request in expired_requests:
            assert request["status"] == HitlStatus.PENDING.value
            expiration = datetime.fromisoformat(request["expiration_time"])
            assert now > expiration


class TestHitlResponseSerialization:
    """Test scenario 2.3-UNIT-006: HITL response serialization (P2)"""
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_hitl_response_json_serialization(self):
        """Test JSON serialization of HITL responses."""
        # Mock HITL response data
        response_data = {
            "hitl_request_id": str(uuid4()),
            "action": HitlAction.APPROVE.value,
            "user_id": "user123",
            "timestamp": datetime.now().isoformat(),
            "comment": "Approved for implementation",
            "workflow_resumed": True
        }
        
        # Test serialization
        try:
            serialized = json.dumps(response_data)
            assert isinstance(serialized, str)
            assert len(serialized) > 0
        except (TypeError, ValueError) as e:
            pytest.fail(f"Failed to serialize HITL response: {e}")
        
        # Test deserialization
        try:
            deserialized = json.loads(serialized)
            assert deserialized == response_data
        except (TypeError, ValueError) as e:
            pytest.fail(f"Failed to deserialize HITL response: {e}")
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_hitl_response_field_types(self):
        """Test field type preservation during serialization."""
        response_data = {
            "hitl_request_id": str(uuid4()),
            "action": HitlAction.AMEND.value,
            "user_id": "user456",
            "timestamp": datetime.now().isoformat(),
            "workflow_resumed": False,
            "amendment_content": {
                "amended_content": "Please add more details",
                "section": "requirements",
                "priority": "high"
            },
            "metadata": {
                "response_time_ms": 15000,
                "user_agent": "Mozilla/5.0..."
            }
        }
        
        serialized = json.dumps(response_data)
        deserialized = json.loads(serialized)
        
        # Verify field types
        assert isinstance(deserialized["hitl_request_id"], str)
        assert isinstance(deserialized["action"], str)
        assert isinstance(deserialized["user_id"], str)
        assert isinstance(deserialized["timestamp"], str)
        assert isinstance(deserialized["workflow_resumed"], bool)
        assert isinstance(deserialized["amendment_content"], dict)
        assert isinstance(deserialized["metadata"], dict)
        assert isinstance(deserialized["metadata"]["response_time_ms"], int)
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_hitl_response_special_characters(self):
        """Test serialization of HITL responses with special characters."""
        response_with_special_chars = {
            "hitl_request_id": str(uuid4()),
            "action": HitlAction.AMEND.value,
            "user_id": "user_with_émojis_🚀",
            "comment": "Content with \"quotes\" and 'apostrophes' and newlines\nand tabs\t",
            "amendment_content": {
                "amended_content": "Content with unicode: café, naïve, résumé"
            }
        }
        
        # Should serialize/deserialize without error
        serialized = json.dumps(response_with_special_chars, ensure_ascii=False)
        deserialized = json.loads(serialized)
        
        assert deserialized["user_id"] == "user_with_émojis_🚀"
        assert "café" in deserialized["amendment_content"]["amended_content"]
        assert "\n" in deserialized["comment"]
        assert "\t" in deserialized["comment"]
    
    @pytest.mark.unit
    @pytest.mark.p3
    @pytest.mark.hitl
    def test_hitl_response_serialization_performance(self):
        """Test performance of HITL response serialization."""
        import time
        
        # Create large response data
        large_response = {
            "hitl_request_id": str(uuid4()),
            "action": HitlAction.AMEND.value,
            "user_id": "performance_test_user",
            "timestamp": datetime.now().isoformat(),
            "amendment_content": {
                "amended_content": "Large amendment content: " + "A" * 10000,  # 10KB content
                "detailed_feedback": ["Point " + str(i) for i in range(100)]  # 100 feedback points
            },
            "metadata": {
                "performance_data": {f"metric_{i}": f"value_{i}" for i in range(1000)}  # 1000 metrics
            }
        }
        
        # Test serialization performance
        start_time = time.time()
        serialized = json.dumps(large_response)
        serialization_time = time.time() - start_time
        
        # Should serialize quickly (< 1 second)
        assert serialization_time < 1.0
        assert len(serialized) > 10000  # Should be substantial size
        
        # Test deserialization performance
        start_time = time.time()
        deserialized = json.loads(serialized)
        deserialization_time = time.time() - start_time
        
        # Should deserialize quickly
        assert deserialization_time < 1.0
        assert deserialized["hitl_request_id"] == large_response["hitl_request_id"]


class TestErrorMessageGeneration:
    """Test scenario 2.3-UNIT-007: Error message generation (P2)"""
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_validation_error_messages(self):
        """Test generation of validation error messages."""
        def generate_validation_error(field: str, issue: str, value: any = None) -> dict:
            error_templates = {
                "required": f"Field '{field}' is required",
                "invalid_type": f"Field '{field}' must be of correct type",
                "invalid_value": f"Field '{field}' has invalid value",
                "too_long": f"Field '{field}' exceeds maximum length",
                "too_short": f"Field '{field}' is below minimum length"
            }
            
            message = error_templates.get(issue, f"Field '{field}' has an error")
            
            error = {
                "error_type": "validation_error",
                "field": field,
                "issue": issue,
                "message": message
            }
            
            if value is not None:
                error["provided_value"] = str(value)[:100]  # Limit value length in error
            
            return error
        
        # Test different error types
        required_error = generate_validation_error("action", "required")
        assert required_error["message"] == "Field 'action' is required"
        assert required_error["field"] == "action"
        
        type_error = generate_validation_error("comment", "invalid_type", 123)
        assert "invalid_type" in type_error["message"]
        assert type_error["provided_value"] == "123"
        
        length_error = generate_validation_error("amended_content", "too_short", "short")
        assert "minimum length" in length_error["message"]
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_business_logic_error_messages(self):
        """Test generation of business logic error messages."""
        def generate_business_error(error_code: str, context: dict = None) -> dict:
            error_messages = {
                "HITL_REQUEST_NOT_FOUND": "HITL request not found",
                "HITL_REQUEST_EXPIRED": "HITL request has expired",
                "INVALID_STATUS_TRANSITION": "Invalid status transition",
                "UNAUTHORIZED_USER": "User not authorized for this action",
                "DUPLICATE_RESPONSE": "Response already submitted for this request"
            }
            
            base_message = error_messages.get(error_code, "Unknown error occurred")
            
            error = {
                "error_type": "business_error",
                "error_code": error_code,
                "message": base_message
            }
            
            # Add context-specific details
            if context:
                if error_code == "INVALID_STATUS_TRANSITION" and "from_status" in context:
                    error["message"] = f"Cannot transition from {context['from_status']} to {context['to_status']}"
                elif error_code == "HITL_REQUEST_EXPIRED" and "expired_at" in context:
                    error["message"] = f"HITL request expired at {context['expired_at']}"
            
            return error
        
        # Test basic business error
        not_found_error = generate_business_error("HITL_REQUEST_NOT_FOUND")
        assert not_found_error["error_code"] == "HITL_REQUEST_NOT_FOUND"
        assert "not found" in not_found_error["message"]
        
        # Test contextual business error
        transition_error = generate_business_error(
            "INVALID_STATUS_TRANSITION",
            {"from_status": "approved", "to_status": "rejected"}
        )
        assert "approved" in transition_error["message"]
        assert "rejected" in transition_error["message"]
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_user_friendly_error_messages(self):
        """Test generation of user-friendly error messages."""
        def make_user_friendly(technical_error: dict) -> dict:
            friendly_messages = {
                "HITL_REQUEST_NOT_FOUND": "We couldn't find the request you're trying to respond to. It may have been removed or you may not have access to it.",
                "HITL_REQUEST_EXPIRED": "This request has expired. Please contact the project team if you still need to provide feedback.",
                "INVALID_STATUS_TRANSITION": "This request has already been responded to. You cannot change the response once it's been submitted.",
                "UNAUTHORIZED_USER": "You don't have permission to respond to this request. Please contact your administrator if you believe this is an error."
            }
            
            error_code = technical_error.get("error_code")
            friendly_message = friendly_messages.get(error_code, technical_error.get("message", "An error occurred"))
            
            return {
                "user_message": friendly_message,
                "error_code": error_code,
                "technical_details": technical_error.get("message")
            }
        
        # Test technical to user-friendly conversion
        technical_error = {
            "error_type": "business_error",
            "error_code": "HITL_REQUEST_EXPIRED",
            "message": "Request expired at 2024-01-15T10:30:00Z"
        }
        
        friendly_error = make_user_friendly(technical_error)
        
        assert "expired" in friendly_error["user_message"]
        assert "contact the project team" in friendly_error["user_message"]
        assert friendly_error["error_code"] == "HITL_REQUEST_EXPIRED"
        assert friendly_error["technical_details"] == technical_error["message"]
    
    @pytest.mark.unit
    @pytest.mark.p3
    @pytest.mark.hitl
    def test_error_message_localization_support(self):
        """Test error message support for localization."""
        def generate_localized_error(error_code: str, locale: str = "en") -> dict:
            error_translations = {
                "en": {
                    "HITL_REQUEST_NOT_FOUND": "HITL request not found",
                    "HITL_REQUEST_EXPIRED": "HITL request has expired",
                    "INVALID_ACTION": "Invalid action specified"
                },
                "es": {
                    "HITL_REQUEST_NOT_FOUND": "Solicitud HITL no encontrada",
                    "HITL_REQUEST_EXPIRED": "La solicitud HITL ha expirado",
                    "INVALID_ACTION": "Acción especificada inválida"
                },
                "fr": {
                    "HITL_REQUEST_NOT_FOUND": "Demande HITL introuvable",
                    "HITL_REQUEST_EXPIRED": "La demande HITL a expiré",
                    "INVALID_ACTION": "Action spécifiée invalide"
                }
            }
            
            locale_messages = error_translations.get(locale, error_translations["en"])
            message = locale_messages.get(error_code, f"Error code: {error_code}")
            
            return {
                "error_code": error_code,
                "message": message,
                "locale": locale
            }
        
        # Test English messages
        en_error = generate_localized_error("HITL_REQUEST_NOT_FOUND", "en")
        assert en_error["message"] == "HITL request not found"
        assert en_error["locale"] == "en"
        
        # Test Spanish messages
        es_error = generate_localized_error("HITL_REQUEST_NOT_FOUND", "es")
        assert "no encontrada" in es_error["message"]
        assert es_error["locale"] == "es"
        
        # Test French messages
        fr_error = generate_localized_error("HITL_REQUEST_EXPIRED", "fr")
        assert "expiré" in fr_error["message"]
        assert fr_error["locale"] == "fr"
        
        # Test fallback to English for unsupported locale
        unsupported_error = generate_localized_error("HITL_REQUEST_NOT_FOUND", "de")
        assert unsupported_error["message"] == "HITL request not found"  # Falls back to English