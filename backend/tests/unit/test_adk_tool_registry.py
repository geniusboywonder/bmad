"""Tests for ADK Tool Registry."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.tools.adk_tool_registry import ADKToolRegistry
from app.models.agent import AgentType


@pytest.fixture
def tool_registry():
    """Create a fresh ADK Tool Registry for testing."""
    return ADKToolRegistry()


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification for testing."""
    return {
        "openapi": "3.0.1",
        "info": {"title": "Test API", "version": "1.0.0"},
        "servers": [{"url": "https://api.test.com"}],
        "paths": {
            "/users": {
                "get": {"summary": "Get users"}
            }
        }
    }


class TestADKToolRegistry:
    """Test ADK Tool Registry functionality."""

    def test_registry_initialization(self, tool_registry):
        """Test registry initialization with default agent mappings."""
        assert isinstance(tool_registry.registered_tools, dict)
        assert isinstance(tool_registry.openapi_tools, dict)
        assert isinstance(tool_registry.function_tools, dict)
        assert isinstance(tool_registry.agent_tool_mappings, dict)

        # Check default agent mappings exist
        assert AgentType.ANALYST in tool_registry.agent_tool_mappings
        assert AgentType.ARCHITECT in tool_registry.agent_tool_mappings
        assert AgentType.CODER in tool_registry.agent_tool_mappings
        assert AgentType.TESTER in tool_registry.agent_tool_mappings
        assert AgentType.DEPLOYER in tool_registry.agent_tool_mappings

    def test_register_function_tool_success(self, tool_registry):
        """Test successful function tool registration."""
        def test_function(param: str) -> str:
            return f"Processed: {param}"

        result = tool_registry.register_function_tool(
            "test_tool",
            test_function,
            "A test function tool"
        )

        assert result is True
        assert "test_tool" in tool_registry.registered_tools
        assert "test_tool" in tool_registry.function_tools
        assert tool_registry.tool_metadata["test_tool"]["type"] == "function"
        assert tool_registry.tool_metadata["test_tool"]["description"] == "A test function tool"

    def test_register_function_tool_failure(self, tool_registry):
        """Test function tool registration failure."""
        # Invalid function
        result = tool_registry.register_function_tool(
            "invalid_tool",
            "not_a_function",  # Invalid function
            "Invalid tool"
        )

        assert result is False
        assert "invalid_tool" not in tool_registry.registered_tools

    @patch('app.tools.adk_tool_registry.BMADOpenAPITool')
    def test_register_openapi_tool_success(self, mock_openapi_tool_class, tool_registry, sample_openapi_spec):
        """Test successful OpenAPI tool registration."""
        # Mock BMADOpenAPITool
        mock_tool = Mock()
        mock_tool.initialize.return_value = True
        mock_tool.adk_tool = Mock()
        mock_openapi_tool_class.return_value = mock_tool

        result = tool_registry.register_openapi_tool("api_tool", sample_openapi_spec)

        assert result is True
        assert "api_tool" in tool_registry.registered_tools
        assert "api_tool" in tool_registry.openapi_tools
        assert tool_registry.tool_metadata["api_tool"]["type"] == "openapi"
        mock_tool.initialize.assert_called_once()

    @patch('app.tools.adk_tool_registry.BMADOpenAPITool')
    def test_register_openapi_tool_initialization_failure(self, mock_openapi_tool_class, tool_registry, sample_openapi_spec):
        """Test OpenAPI tool registration with initialization failure."""
        mock_tool = Mock()
        mock_tool.initialize.return_value = False
        mock_openapi_tool_class.return_value = mock_tool

        result = tool_registry.register_openapi_tool("failing_tool", sample_openapi_spec)

        assert result is False
        assert "failing_tool" not in tool_registry.registered_tools

    def test_unregister_tool_success(self, tool_registry):
        """Test successful tool unregistration."""
        # First register a tool
        def test_func():
            return "test"

        tool_registry.register_function_tool("test_tool", test_func, "Test tool")

        # Then unregister it
        result = tool_registry.unregister_tool("test_tool")

        assert result is True
        assert "test_tool" not in tool_registry.registered_tools
        assert "test_tool" not in tool_registry.function_tools
        assert tool_registry.tool_metadata["test_tool"]["status"] == "unregistered"

    def test_unregister_tool_not_found(self, tool_registry):
        """Test unregistration of non-existent tool."""
        result = tool_registry.unregister_tool("non_existent_tool")

        assert result is False

    def test_get_tools_for_agent(self, tool_registry):
        """Test getting tools for a specific agent type."""
        # Register some tools
        def code_analyzer(code: str) -> dict:
            return {"lines": len(code.split('\n'))}

        def api_checker(url: str) -> dict:
            return {"url": url, "status": "ok"}

        tool_registry.register_function_tool("code_analyzer", code_analyzer, "Analyze code")
        tool_registry.register_function_tool("api_checker", api_checker, "Check API")

        # Update agent mapping to include our test tools
        tool_registry.update_agent_tool_mapping(AgentType.ANALYST, ["code_analyzer", "api_checker"])

        tools = tool_registry.get_tools_for_agent(AgentType.ANALYST)

        assert len(tools) == 2
        # Tools should be ADK FunctionTool instances
        assert all(hasattr(tool, 'func') for tool in tools)

    def test_get_tools_for_agent_with_missing_tools(self, tool_registry):
        """Test getting tools for agent when some tools don't exist."""
        # Set mapping that includes non-existent tool
        tool_registry.agent_tool_mappings[AgentType.CODER] = ["existing_tool", "missing_tool"]

        # Register only one tool
        def existing_func():
            return "exists"

        tool_registry.register_function_tool("existing_tool", existing_func, "Existing tool")

        tools = tool_registry.get_tools_for_agent(AgentType.CODER)

        # Should only return the existing tool
        assert len(tools) == 1

    def test_get_tool_by_name(self, tool_registry):
        """Test getting tool by name."""
        def test_func():
            return "test"

        tool_registry.register_function_tool("named_tool", test_func, "Named tool")

        tool = tool_registry.get_tool_by_name("named_tool")
        assert tool is not None

        # Non-existent tool
        tool = tool_registry.get_tool_by_name("non_existent")
        assert tool is None

    def test_update_agent_tool_mapping_success(self, tool_registry):
        """Test successful agent tool mapping update."""
        # Register tools first
        def tool1():
            return "tool1"

        def tool2():
            return "tool2"

        tool_registry.register_function_tool("tool1", tool1, "Tool 1")
        tool_registry.register_function_tool("tool2", tool2, "Tool 2")

        # Update mapping
        result = tool_registry.update_agent_tool_mapping(AgentType.TESTER, ["tool1", "tool2"])

        assert result is True
        assert tool_registry.agent_tool_mappings[AgentType.TESTER] == ["tool1", "tool2"]

    def test_update_agent_tool_mapping_with_invalid_tools(self, tool_registry):
        """Test agent tool mapping update with invalid tool names."""
        # Register only one tool
        def valid_tool():
            return "valid"

        tool_registry.register_function_tool("valid_tool", valid_tool, "Valid tool")

        # Try to update with mix of valid and invalid tools
        result = tool_registry.update_agent_tool_mapping(
            AgentType.TESTER, ["valid_tool", "invalid_tool"]
        )

        assert result is True
        # Should only include valid tools
        assert tool_registry.agent_tool_mappings[AgentType.TESTER] == ["valid_tool"]

    def test_get_available_tools(self, tool_registry):
        """Test getting available tools summary."""
        # Register some tools
        def func_tool():
            return "func"

        tool_registry.register_function_tool("func_tool", func_tool, "Function tool")

        with patch.object(tool_registry, 'register_openapi_tool', return_value=True):
            tool_registry.register_openapi_tool("api_tool", {})

        available = tool_registry.get_available_tools()

        assert "function_tools" in available
        assert "openapi_tools" in available
        assert "all_tools" in available
        assert "total_count" in available
        assert available["total_count"] >= 1
        assert "func_tool" in available["function_tools"]

    def test_get_tool_metadata(self, tool_registry):
        """Test getting tool metadata."""
        def test_tool():
            return "test"

        tool_registry.register_function_tool("meta_tool", test_tool, "Metadata test", {"param1": "value1"})

        metadata = tool_registry.get_tool_metadata("meta_tool")

        assert metadata is not None
        assert metadata["type"] == "function"
        assert metadata["description"] == "Metadata test"
        assert metadata["parameters"] == {"param1": "value1"}
        assert "registered_at" in metadata
        assert metadata["status"] == "active"

    def test_get_registry_status(self, tool_registry):
        """Test getting comprehensive registry status."""
        # Register a tool
        def status_tool():
            return "status"

        tool_registry.register_function_tool("status_tool", status_tool, "Status tool")

        status = tool_registry.get_registry_status()

        assert "total_tools" in status
        assert "function_tools" in status
        assert "openapi_tools" in status
        assert "agent_mappings" in status
        assert "tool_health" in status

        assert status["total_tools"] >= 1
        assert status["function_tools"] >= 1

        # Check agent mappings structure
        assert AgentType.ANALYST.value in status["agent_mappings"]
        analyst_mapping = status["agent_mappings"][AgentType.ANALYST.value]
        assert "tool_count" in analyst_mapping
        assert "available_tools" in analyst_mapping

    def test_search_tools_by_name(self, tool_registry):
        """Test searching tools by name."""
        def searchable_tool():
            return "searchable"

        tool_registry.register_function_tool("searchable_tool", searchable_tool, "Searchable tool")

        results = tool_registry.search_tools("searchable")
        assert "searchable_tool" in results

        # Search by partial name
        results = tool_registry.search_tools("tool")
        assert "searchable_tool" in results

        # No matches
        results = tool_registry.search_tools("nonexistent")
        assert len(results) == 0

    def test_search_tools_by_description(self, tool_registry):
        """Test searching tools by description."""
        def desc_tool():
            return "desc"

        tool_registry.register_function_tool("desc_tool", desc_tool, "This is a searchable description")

        results = tool_registry.search_tools("searchable")
        assert "desc_tool" in results

    def test_search_tools_with_type_filter(self, tool_registry):
        """Test searching tools with type filter."""
        def func_tool():
            return "func"

        tool_registry.register_function_tool("func_tool", func_tool, "Function tool")

        # Search with matching type
        results = tool_registry.search_tools("tool", "function")
        assert "func_tool" in results

        # Search with non-matching type
        results = tool_registry.search_tools("tool", "openapi")
        assert "func_tool" not in results

    def test_validate_tool_compatibility(self, tool_registry):
        """Test tool compatibility validation."""
        # Register tools
        def analyst_tool():
            return "analyst"

        def coder_tool():
            return "coder"

        tool_registry.register_function_tool("analyst_tool", analyst_tool, "Analyst tool")
        tool_registry.register_function_tool("coder_tool", coder_tool, "Coder tool")

        # Test compatibility
        compatibility = tool_registry.validate_tool_compatibility(
            AgentType.ANALYST, ["analyst_tool", "coder_tool", "non_existent"]
        )

        assert compatibility["agent_type"] == "analyst"
        assert "analyst_tool" in compatibility["compatible_tools"]
        assert "coder_tool" in compatibility["compatible_tools"]  # All tools are compatible in our simple model
        assert "non_existent" in compatibility["missing_tools"]
        assert compatibility["compatibility_score"] > 0

    def test_export_tool_configuration(self, tool_registry):
        """Test exporting tool configuration."""
        # Register a tool
        def export_tool():
            return "export"

        tool_registry.register_function_tool("export_tool", export_tool, "Export test")

        config = tool_registry.export_tool_configuration()

        assert "exported_at" in config
        assert "tool_metadata" in config
        assert "agent_mappings" in config
        assert "registry_stats" in config

        assert "export_tool" in config["tool_metadata"]

    def test_import_tool_configuration_validation(self, tool_registry):
        """Test tool configuration import validation."""
        # Valid config
        valid_config = {
            "tool_metadata": {"test": {"type": "function"}},
            "agent_mappings": {"analyst": ["test"]}
        }

        result = tool_registry.import_tool_configuration(valid_config)
        # Our implementation just validates - doesn't actually import
        assert result is True

        # Invalid config
        invalid_config = {
            "tool_metadata": {"test": {"type": "function"}}
            # Missing agent_mappings
        }

        result = tool_registry.import_tool_configuration(invalid_config)
        assert result is False

    def test_cleanup_inactive_tools(self, tool_registry):
        """Test cleanup of inactive tools."""
        # This test would need timestamp mocking for proper testing
        result = tool_registry.cleanup_inactive_tools()
        assert isinstance(result, int)
        assert result >= 0


class TestADKToolRegistryIntegration:
    """Integration tests for ADK Tool Registry."""

    def test_full_tool_lifecycle(self, tool_registry):
        """Test complete tool registration to usage lifecycle."""
        # Register a tool
        def lifecycle_tool(param: str) -> str:
            return f"Processed: {param}"

        result = tool_registry.register_function_tool(
            "lifecycle_tool",
            lifecycle_tool,
            "Lifecycle test tool"
        )
        assert result is True

        # Get tool
        tool = tool_registry.get_tool_by_name("lifecycle_tool")
        assert tool is not None

        # Check metadata
        metadata = tool_registry.get_tool_metadata("lifecycle_tool")
        assert metadata["status"] == "active"

        # Update agent mapping
        result = tool_registry.update_agent_tool_mapping(AgentType.CODER, ["lifecycle_tool"])
        assert result is True

        # Get tools for agent
        agent_tools = tool_registry.get_tools_for_agent(AgentType.CODER)
        assert len(agent_tools) >= 1

        # Get registry status
        status = tool_registry.get_registry_status()
        assert status["total_tools"] >= 1

        # Unregister tool
        result = tool_registry.unregister_tool("lifecycle_tool")
        assert result is True

        # Verify removal
        tool = tool_registry.get_tool_by_name("lifecycle_tool")
        assert tool is None

        metadata = tool_registry.get_tool_metadata("lifecycle_tool")
        assert metadata["status"] == "unregistered"

    def test_multiple_tool_types_management(self, tool_registry):
        """Test managing multiple tool types simultaneously."""
        # Register function tools
        def func1():
            return "func1"

        def func2():
            return "func2"

        tool_registry.register_function_tool("func1", func1, "Function 1")
        tool_registry.register_function_tool("func2", func2, "Function 2")

        # Mock OpenAPI tool registration
        with patch.object(tool_registry, 'register_openapi_tool', return_value=True) as mock_register:
            tool_registry.register_openapi_tool("api1", {})
            tool_registry.register_openapi_tool("api2", {})

        # Check available tools
        available = tool_registry.get_available_tools()

        assert len(available["function_tools"]) >= 2
        assert len(available["openapi_tools"]) >= 2
        assert available["total_count"] >= 4

        # Test search across all tools
        results = tool_registry.search_tools("func")
        assert len(results) >= 2

    def test_agent_tool_mapping_edge_cases(self, tool_registry):
        """Test agent tool mapping edge cases."""
        # Empty mapping
        result = tool_registry.update_agent_tool_mapping(AgentType.TESTER, [])
        assert result is True
        assert tool_registry.agent_tool_mappings[AgentType.TESTER] == []

        tools = tool_registry.get_tools_for_agent(AgentType.TESTER)
        assert tools == []

        # Mapping with only invalid tools
        result = tool_registry.update_agent_tool_mapping(AgentType.TESTER, ["invalid1", "invalid2"])
        assert result is True
        assert tool_registry.agent_tool_mappings[AgentType.TESTER] == []

    def test_tool_health_monitoring(self, tool_registry):
        """Test tool health status monitoring."""
        # Register tools
        def healthy_tool():
            return "healthy"

        def another_tool():
            return "another"

        tool_registry.register_function_tool("healthy_tool", healthy_tool, "Healthy tool")
        tool_registry.register_function_tool("another_tool", another_tool, "Another tool")

        status = tool_registry.get_registry_status()

        assert "tool_health" in status
        assert "healthy_tool" in status["tool_health"]
        assert "another_tool" in status["tool_health"]

        # Check health structure
        healthy_info = status["tool_health"]["healthy_tool"]
        assert "type" in healthy_info
        assert "status" in healthy_info
        assert "registered_at" in healthy_info
        assert healthy_info["status"] == "active"
