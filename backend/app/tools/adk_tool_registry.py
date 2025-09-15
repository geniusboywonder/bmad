"""ADK Tool Registry System for managing comprehensive tool ecosystem."""

from typing import Dict, Any, List, Optional, Type
import structlog
from datetime import datetime

from google.adk.tools import BaseTool, FunctionTool
from app.tools.adk_openapi_tools import BMADOpenAPITool
from app.models.agent import AgentType

logger = structlog.get_logger(__name__)


class ADKToolRegistry:
    """Registry for managing ADK tools with BMAD integration and enterprise controls."""

    def __init__(self):
        self.registered_tools: Dict[str, BaseTool] = {}
        self.openapi_tools: Dict[str, BMADOpenAPITool] = {}
        self.function_tools: Dict[str, FunctionTool] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        self.agent_tool_mappings: Dict[AgentType, List[str]] = {}

        # Initialize default agent tool mappings
        self._initialize_agent_tool_mappings()

        logger.info("ADK Tool Registry initialized")

    def _initialize_agent_tool_mappings(self):
        """Initialize default tool mappings for each agent type."""
        self.agent_tool_mappings = {
            AgentType.ANALYST: [
                "data_analysis", "report_generator", "api_health_checker",
                "project_metrics_query", "code_analyzer"
            ],
            AgentType.ARCHITECT: [
                "system_design", "api_validator", "code_analyzer",
                "deployment_architecture", "security_assessment"
            ],
            AgentType.CODER: [
                "code_generator", "syntax_checker", "api_client",
                "code_analyzer", "test_runner"
            ],
            AgentType.TESTER: [
                "test_runner", "coverage_analyzer", "api_health_checker",
                "code_analyzer", "performance_tester"
            ],
            AgentType.DEPLOYER: [
                "deployment_tools", "health_checker", "api_client",
                "infrastructure_manager", "monitoring_setup"
            ]
        }

    async def register_openapi_tool(self, name: str, openapi_spec: Dict[str, Any]) -> bool:
        """Register OpenAPI specification as ADK tool.

        Args:
            name: Tool name identifier
            openapi_spec: OpenAPI specification dictionary

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Create BMAD OpenAPI tool wrapper
            bmad_tool = BMADOpenAPITool(openapi_spec, name)

            # Initialize the tool
            if not await bmad_tool.initialize():
                logger.error("Failed to initialize OpenAPI tool", tool_name=name)
                return False

            # Register in collections
            self.openapi_tools[name] = bmad_tool
            self.registered_tools[name] = bmad_tool.adk_tool

            # Store metadata
            self.tool_metadata[name] = {
                "type": "openapi",
                "tool_name": name,
                "base_url": bmad_tool.base_url,
                "endpoint_count": len(bmad_tool.endpoints),
                "registered_at": datetime.now().isoformat(),
                "status": "active"
            }

            logger.info("OpenAPI tool registered successfully",
                       tool_name=name,
                       endpoint_count=len(bmad_tool.endpoints))
            return True

        except Exception as e:
            logger.error("Failed to register OpenAPI tool",
                        tool_name=name,
                        error=str(e))
            return False

    def register_function_tool(self, name: str, func: callable,
                             description: str,
                             parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Register a custom function as ADK tool.

        Args:
            name: Tool name identifier
            func: Function to register
            description: Tool description
            parameters: Optional parameter schema

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Create ADK FunctionTool
            tool = FunctionTool(
                func=func,
                description=description,
                name=name
            )

            # Register in collections
            self.function_tools[name] = tool
            self.registered_tools[name] = tool

            # Store metadata
            self.tool_metadata[name] = {
                "type": "function",
                "tool_name": name,
                "description": description,
                "parameters": parameters or {},
                "registered_at": datetime.now().isoformat(),
                "status": "active"
            }

            logger.info("Function tool registered successfully", tool_name=name)
            return True

        except Exception as e:
            logger.error("Failed to register function tool",
                        tool_name=name,
                        error=str(e))
            return False

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool from the registry.

        Args:
            name: Tool name to unregister

        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if name not in self.registered_tools:
                logger.warning("Tool not found for unregistration", tool_name=name)
                return False

            # Remove from all collections
            if name in self.openapi_tools:
                del self.openapi_tools[name]
            if name in self.function_tools:
                del self.function_tools[name]

            del self.registered_tools[name]

            # Update metadata
            if name in self.tool_metadata:
                self.tool_metadata[name]["status"] = "unregistered"
                self.tool_metadata[name]["unregistered_at"] = datetime.now().isoformat()

            logger.info("Tool unregistered successfully", tool_name=name)
            return True

        except Exception as e:
            logger.error("Failed to unregister tool",
                        tool_name=name,
                        error=str(e))
            return False

    def get_tools_for_agent(self, agent_type: AgentType) -> List[BaseTool]:
        """Get appropriate tools for specific agent type.

        Args:
            agent_type: The agent type to get tools for

        Returns:
            List of ADK tools for the agent type
        """
        tool_names = self.agent_tool_mappings.get(agent_type, [])
        tools = []

        for tool_name in tool_names:
            if tool_name in self.registered_tools:
                tools.append(self.registered_tools[tool_name])
            else:
                logger.debug("Tool not available for agent",
                           tool_name=tool_name,
                           agent_type=agent_type.value)

        logger.debug("Retrieved tools for agent",
                    agent_type=agent_type.value,
                    requested_tools=tool_names,
                    available_tools=len(tools))

        return tools

    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """Get a specific tool by name.

        Args:
            name: Tool name to retrieve

        Returns:
            ADK tool instance or None if not found
        """
        return self.registered_tools.get(name)

    def update_agent_tool_mapping(self, agent_type: AgentType, tool_names: List[str]) -> bool:
        """Update tool mapping for an agent type.

        Args:
            agent_type: Agent type to update
            tool_names: List of tool names to assign

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate tool names exist
            invalid_tools = [name for name in tool_names if name not in self.registered_tools]
            if invalid_tools:
                logger.warning("Some tools not found in registry",
                             invalid_tools=invalid_tools,
                             agent_type=agent_type.value)
                # Remove invalid tools
                tool_names = [name for name in tool_names if name in self.registered_tools]

            self.agent_tool_mappings[agent_type] = tool_names

            logger.info("Agent tool mapping updated",
                       agent_type=agent_type.value,
                       tool_count=len(tool_names))
            return True

        except Exception as e:
            logger.error("Failed to update agent tool mapping",
                        agent_type=agent_type.value,
                        error=str(e))
            return False

    def get_available_tools(self) -> Dict[str, List[str]]:
        """Get all available tools organized by category.

        Returns:
            Dictionary with tool categories and names
        """
        return {
            "function_tools": list(self.function_tools.keys()),
            "openapi_tools": list(self.openapi_tools.keys()),
            "all_tools": list(self.registered_tools.keys()),
            "total_count": len(self.registered_tools)
        }

    def get_tool_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific tool.

        Args:
            name: Tool name to get metadata for

        Returns:
            Tool metadata dictionary or None if not found
        """
        return self.tool_metadata.get(name)

    def get_registry_status(self) -> Dict[str, Any]:
        """Get comprehensive registry status and statistics.

        Returns:
            Dictionary with registry status information
        """
        status = {
            "total_tools": len(self.registered_tools),
            "function_tools": len(self.function_tools),
            "openapi_tools": len(self.openapi_tools),
            "agent_mappings": {}
        }

        # Add agent tool mapping counts
        for agent_type, tools in self.agent_tool_mappings.items():
            status["agent_mappings"][agent_type.value] = {
                "tool_count": len(tools),
                "available_tools": len([t for t in tools if t in self.registered_tools])
            }

        # Add tool health status
        tool_health = {}
        for name, metadata in self.tool_metadata.items():
            tool_health[name] = {
                "type": metadata.get("type"),
                "status": metadata.get("status"),
                "registered_at": metadata.get("registered_at")
            }

        status["tool_health"] = tool_health

        return status

    def search_tools(self, query: str, tool_type: Optional[str] = None) -> List[str]:
        """Search for tools by name or description.

        Args:
            query: Search query string
            tool_type: Optional tool type filter ("function" or "openapi")

        Returns:
            List of matching tool names
        """
        query_lower = query.lower()
        matches = []

        for name, metadata in self.tool_metadata.items():
            if tool_type and metadata.get("type") != tool_type:
                continue

            # Search in name and description
            if (query_lower in name.lower() or
                query_lower in metadata.get("description", "").lower()):
                matches.append(name)

        return matches

    def validate_tool_compatibility(self, agent_type: AgentType, tool_names: List[str]) -> Dict[str, Any]:
        """Validate tool compatibility with agent type.

        Args:
            agent_type: Agent type to validate against
            tool_names: List of tool names to validate

        Returns:
            Validation result with compatibility assessment
        """
        result = {
            "agent_type": agent_type.value,
            "requested_tools": tool_names,
            "compatible_tools": [],
            "incompatible_tools": [],
            "missing_tools": [],
            "compatibility_score": 0.0
        }

        compatible_count = 0

        for tool_name in tool_names:
            if tool_name not in self.registered_tools:
                result["missing_tools"].append(tool_name)
            elif self._is_tool_compatible_with_agent(tool_name, agent_type):
                result["compatible_tools"].append(tool_name)
                compatible_count += 1
            else:
                result["incompatible_tools"].append(tool_name)

        # Calculate compatibility score
        if tool_names:
            result["compatibility_score"] = compatible_count / len(tool_names)

        return result

    def _is_tool_compatible_with_agent(self, tool_name: str, agent_type: AgentType) -> bool:
        """Check if a tool is compatible with an agent type.

        Args:
            tool_name: Tool name to check
            agent_type: Agent type to check against

        Returns:
            True if compatible, False otherwise
        """
        # Get tool metadata
        metadata = self.tool_metadata.get(tool_name, {})
        tool_type = metadata.get("type", "unknown")

        # Define compatibility rules
        compatibility_matrix = {
            AgentType.ANALYST: ["function", "openapi"],
            AgentType.ARCHITECT: ["function", "openapi"],
            AgentType.CODER: ["function", "openapi"],
            AgentType.TESTER: ["function", "openapi"],
            AgentType.DEPLOYER: ["function", "openapi"]
        }

        allowed_types = compatibility_matrix.get(agent_type, [])
        return tool_type in allowed_types

    def export_tool_configuration(self) -> Dict[str, Any]:
        """Export tool registry configuration for backup or migration.

        Returns:
            Complete tool registry configuration
        """
        return {
            "exported_at": datetime.now().isoformat(),
            "tool_metadata": self.tool_metadata.copy(),
            "agent_mappings": {
                agent.value: tools for agent, tools in self.agent_tool_mappings.items()
            },
            "registry_stats": self.get_registry_status()
        }

    def import_tool_configuration(self, config: Dict[str, Any]) -> bool:
        """Import tool registry configuration.

        Args:
            config: Configuration to import

        Returns:
            True if import successful, False otherwise
        """
        try:
            # This would implement configuration import logic
            # For now, just validate the structure
            if "tool_metadata" not in config or "agent_mappings" not in config:
                logger.error("Invalid configuration format for import")
                return False

            logger.info("Tool configuration import validated (not yet implemented)")
            return True

        except Exception as e:
            logger.error("Failed to import tool configuration", error=str(e))
            return False

    def cleanup_inactive_tools(self, max_age_hours: int = 24) -> int:
        """Clean up tools that have been inactive for too long.

        Args:
            max_age_hours: Maximum age in hours for cleanup

        Returns:
            Number of tools cleaned up
        """
        try:
            current_time = datetime.now()
            to_cleanup = []

            for name, metadata in self.tool_metadata.items():
                if metadata.get("status") == "unregistered":
                    unregistered_at = metadata.get("unregistered_at")
                    if unregistered_at:
                        # Parse timestamp and check age
                        # This would need proper timestamp parsing
                        pass

            # For now, just return 0 as cleanup logic needs timestamp parsing
            logger.info("Tool cleanup check completed", checked_tools=len(self.tool_metadata))
            return 0

        except Exception as e:
            logger.error("Failed to cleanup inactive tools", error=str(e))
            return 0


# Global tool registry instance
tool_registry = ADKToolRegistry()


def get_tool_registry() -> ADKToolRegistry:
    """Get the global ADK tool registry instance.

    Returns:
        Global ADKToolRegistry instance
    """
    return tool_registry
