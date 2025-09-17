"""
Agent Team Service for BMAD Core Template System

This module provides services for loading and managing agent team configurations
from the BMAD Core system.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utils.yaml_parser import YAMLParser, ParserError
from ..models.agent import AgentType

logger = logging.getLogger(__name__)


class AgentTeamConfiguration:
    """
    Represents an agent team configuration loaded from YAML.

    This class encapsulates the structure of an agent team configuration
    including team composition, roles, and workflow assignments.
    """

    def __init__(
        self,
        team_id: str,
        name: str,
        description: str = "",
        agents: Optional[List[Dict[str, Any]]] = None,
        workflows: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent team configuration.

        Args:
            team_id: Unique identifier for the team
            name: Human-readable name of the team
            description: Description of the team and its purpose
            agents: List of agent configurations in the team
            workflows: List of workflow IDs this team is optimized for
            metadata: Additional metadata for the team
        """
        self.team_id = team_id
        self.name = name
        self.description = description
        self.agents = agents or []
        self.workflows = workflows or []
        self.metadata = metadata or {}

    def get_agent_by_type(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        Get agent configuration by type.

        Args:
            agent_type: Type of agent to find

        Returns:
            Agent configuration dictionary or None if not found
        """
        for agent in self.agents:
            if agent.get('type') == agent_type:
                return agent
        return None

    def get_agent_types(self) -> List[str]:
        """
        Get list of all agent types in this team.

        Returns:
            List of agent type strings
        """
        return [agent.get('type', '') for agent in self.agents if agent.get('type')]

    def has_agent_type(self, agent_type: str) -> bool:
        """
        Check if team has a specific agent type.

        Args:
            agent_type: Type of agent to check for

        Returns:
            True if agent type is present in team
        """
        return any(agent.get('type') == agent_type for agent in self.agents)

    def get_workflow_compatibility(self, workflow_id: str) -> bool:
        """
        Check if this team is compatible with a specific workflow.

        Args:
            workflow_id: ID of the workflow to check

        Returns:
            True if team is compatible with the workflow
        """
        return workflow_id in self.workflows

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert team configuration to dictionary.

        Returns:
            Dictionary representation of the team configuration
        """
        return {
            "team_id": self.team_id,
            "name": self.name,
            "description": self.description,
            "agents": self.agents,
            "workflows": self.workflows,
            "metadata": self.metadata
        }


class AgentTeamService:
    """
    Service for managing agent team configurations.

    This service provides functionality to:
    - Load agent team configurations from YAML files
    - Validate team compositions
    - Match teams to workflows
    - Manage team metadata and capabilities
    """

    def __init__(self, team_base_path: Optional[Union[str, Path]] = None):
        """
        Initialize the agent team service.

        Args:
            team_base_path: Base path for team files (defaults to backend/app/teams)
        """
        self.yaml_parser = YAMLParser()

        if team_base_path is None:
            # Default to backend/app/teams relative to project root
            self.team_base_path = Path("backend/app/teams")
        else:
            self.team_base_path = Path(team_base_path)

        self._team_cache: Dict[str, AgentTeamConfiguration] = {}
        self._cache_enabled = True

    def load_team(self, team_id: str, use_cache: bool = True) -> AgentTeamConfiguration:
        """
        Load an agent team configuration by its ID.

        Args:
            team_id: Unique identifier for the team
            use_cache: Whether to use cached teams

        Returns:
            AgentTeamConfiguration object

        Raises:
            FileNotFoundError: If team file doesn't exist
            ParserError: If team parsing fails
            ValueError: If team validation fails
        """
        # Check cache first
        if use_cache and self._cache_enabled and team_id in self._team_cache:
            logger.debug(f"Loading team '{team_id}' from cache")
            return self._team_cache[team_id]

        # Find team file
        team_file = self._find_team_file(team_id)
        if not team_file:
            raise FileNotFoundError(f"Agent team '{team_id}' not found")

        # Load and parse team configuration
        logger.info(f"Loading agent team '{team_id}' from {team_file}")
        team_data = self._load_team_data(team_file)

        # Validate team configuration
        self._validate_team_data(team_data)

        # Create team configuration object
        team_config = AgentTeamConfiguration(
            team_id=team_data.get('team_id', team_id),
            name=team_data.get('name', ''),
            description=team_data.get('description', ''),
            agents=team_data.get('agents', []),
            workflows=team_data.get('workflows', []),
            metadata=team_data.get('metadata', {})
        )

        # Cache team
        if self._cache_enabled:
            self._team_cache[team_id] = team_config

        return team_config

    def get_compatible_teams(self, workflow_id: str) -> List[AgentTeamConfiguration]:
        """
        Get all teams compatible with a specific workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            List of compatible AgentTeamConfiguration objects
        """
        compatible_teams = []

        try:
            for team_file in self.team_base_path.glob("*.yaml"):
                try:
                    team_id = team_file.stem
                    team_config = self.load_team(team_id)

                    if team_config.get_workflow_compatibility(workflow_id):
                        compatible_teams.append(team_config)

                except Exception as e:
                    logger.warning(f"Failed to load team '{team_file}' for compatibility check: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Failed to get compatible teams for workflow '{workflow_id}': {str(e)}")

        return compatible_teams

    def get_team_for_workflow(self, workflow_id: str) -> Optional[AgentTeamConfiguration]:
        """
        Get the best team for a specific workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Best matching AgentTeamConfiguration or None if no compatible team found
        """
        compatible_teams = self.get_compatible_teams(workflow_id)

        if not compatible_teams:
            return None

        # For now, return the first compatible team
        # In the future, this could implement more sophisticated team selection
        return compatible_teams[0]

    def list_available_teams(self) -> List[Dict[str, Any]]:
        """
        List all available agent teams.

        Returns:
            List of team metadata dictionaries
        """
        teams = []

        try:
            if self.team_base_path.exists():
                for team_file in self.team_base_path.glob("*.yaml"):
                    try:
                        team_id = team_file.stem
                        team_config = self.load_team(team_id)
                        teams.append({
                            "team_id": team_config.team_id,
                            "name": team_config.name,
                            "description": team_config.description,
                            "agent_count": len(team_config.agents),
                            "agent_types": team_config.get_agent_types(),
                            "workflows": team_config.workflows,
                            "metadata": team_config.metadata
                        })
                    except Exception as e:
                        logger.warning(f"Failed to load team '{team_file}': {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Failed to list teams: {str(e)}")

        return teams

    def get_team_metadata(self, team_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific team.

        Args:
            team_id: ID of the team

        Returns:
            Dictionary with team metadata
        """
        try:
            team_config = self.load_team(team_id)

            return {
                "team_id": team_config.team_id,
                "name": team_config.name,
                "description": team_config.description,
                "agent_count": len(team_config.agents),
                "agent_types": team_config.get_agent_types(),
                "workflows": team_config.workflows,
                "capabilities": self._analyze_team_capabilities(team_config),
                "metadata": team_config.metadata
            }

        except Exception as e:
            logger.error(f"Failed to get metadata for team '{team_id}': {str(e)}")
            return None

    def validate_team_composition(self, team_id: str) -> Dict[str, Any]:
        """
        Validate the composition of an agent team.

        Args:
            team_id: ID of the team to validate

        Returns:
            Dictionary with validation results
        """
        try:
            team_config = self.load_team(team_id)

            errors = []
            warnings = []

            # Check for required agent types
            required_types = ['orchestrator', 'analyst', 'architect']
            for required_type in required_types:
                if not team_config.has_agent_type(required_type):
                    errors.append(f"Missing required agent type: {required_type}")

            # Check for duplicate agent types
            agent_types = team_config.get_agent_types()
            if len(agent_types) != len(set(agent_types)):
                duplicates = [t for t in agent_types if agent_types.count(t) > 1]
                warnings.append(f"Duplicate agent types found: {list(set(duplicates))}")

            # Validate agent configurations
            for agent in team_config.agents:
                if not agent.get('type'):
                    errors.append("Agent missing type specification")
                if not agent.get('name'):
                    warnings.append(f"Agent '{agent.get('type', 'unknown')}' missing name")

            # Check workflow compatibility
            if not team_config.workflows:
                warnings.append("Team has no associated workflows")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "agent_count": len(team_config.agents),
                "workflow_count": len(team_config.workflows)
            }

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "agent_count": 0,
                "workflow_count": 0
            }

    def clear_cache(self):
        """Clear the team cache."""
        self._team_cache.clear()
        logger.info("Agent team cache cleared")

    def enable_cache(self, enabled: bool = True):
        """Enable or disable team caching."""
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()
        logger.info(f"Agent team cache {'enabled' if enabled else 'disabled'}")

    def _find_team_file(self, team_id: str) -> Optional[Path]:
        """
        Find the team file for a given team ID.

        Args:
            team_id: Team identifier

        Returns:
            Path to team file or None if not found
        """
        # Try different file extensions
        for ext in ['.yaml', '.yml']:
            team_file = self.team_base_path / f"{team_id}{ext}"
            if team_file.exists():
                return team_file

        return None

    def _load_team_data(self, team_file: Path) -> Dict[str, Any]:
        """
        Load team data from YAML file.

        Args:
            team_file: Path to the team YAML file

        Returns:
            Parsed team data dictionary

        Raises:
            ParserError: If parsing fails
        """
        try:
            with open(team_file, 'r', encoding='utf-8') as f:
                data = self.yaml_parser.yaml_parser.safe_load(f)

            if data is None:
                raise ParserError(f"Team file is empty: {team_file}")

            if not isinstance(data, dict):
                raise ParserError(f"Team file root must be a dictionary, got {type(data)}: {team_file}")

            return data

        except Exception as e:
            raise ParserError(f"Failed to load team data from {team_file}: {str(e)}")

    def _validate_team_data(self, team_data: Dict[str, Any]):
        """
        Validate team configuration data.

        Args:
            team_data: Team configuration data

        Raises:
            ValueError: If validation fails
        """
        if not team_data.get('name'):
            raise ValueError("Team configuration missing required 'name' field")

        agents = team_data.get('agents', [])
        if not agents:
            raise ValueError("Team configuration must have at least one agent")

        # Validate agent configurations
        for i, agent in enumerate(agents):
            if not isinstance(agent, dict):
                raise ValueError(f"Agent {i} must be a dictionary")

            if not agent.get('type'):
                raise ValueError(f"Agent {i} missing required 'type' field")

            # Validate agent type is known
            try:
                AgentType(agent['type'])
            except ValueError:
                raise ValueError(f"Agent {i} has unknown type: {agent['type']}")

    def _analyze_team_capabilities(self, team_config: AgentTeamConfiguration) -> Dict[str, Any]:
        """
        Analyze the capabilities of an agent team.

        Args:
            team_config: Team configuration to analyze

        Returns:
            Dictionary with capability analysis
        """
        capabilities = {
            "has_orchestrator": team_config.has_agent_type("orchestrator"),
            "has_analyst": team_config.has_agent_type("analyst"),
            "has_architect": team_config.has_agent_type("architect"),
            "has_developer": team_config.has_agent_type("coder"),
            "has_tester": team_config.has_agent_type("tester"),
            "has_deployer": team_config.has_agent_type("deployer"),
            "agent_types": team_config.get_agent_types(),
            "workflow_count": len(team_config.workflows),
            "is_full_stack": all(team_config.has_agent_type(t) for t in
                               ["orchestrator", "analyst", "architect", "coder", "tester", "deployer"])
        }

        return capabilities
