"""
Template Loader - Handles template loading and caching.

Responsible for loading templates from files, managing cache, and template discovery.
Implements TR-10: Dynamic workflow loading from backend/app/workflows/ directory.
Implements TR-11: Document template processing from backend/app/templates/.
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError

from ...utils.yaml_parser import YAMLParser, ParserError
from ...models.template import TemplateDefinition

logger = logging.getLogger(__name__)


class TemplateLoader:
    """
    Manages template loading and caching operations.

    Follows Single Responsibility Principle by focusing solely on template loading.
    """

    def __init__(self, template_base_path: Optional[Union[str, Path]] = None):
        """
        Initialize the template loader.

        Args:
            template_base_path: Base path for template files (defaults to backend/app/templates)
        """
        self.yaml_parser = YAMLParser()

        if template_base_path is None:
            # Default to backend/app/templates relative to project root
            self.template_base_path = Path("backend/app/templates")
        else:
            self.template_base_path = Path(template_base_path)

        # BMAD Core paths for TR-10, TR-11, TR-12
        # Handle both project root and backend directory contexts
        if Path("backend/app").exists():
            self.bmad_core_path = Path("backend/app")
        else:
            self.bmad_core_path = Path("app")
        self.workflows_path = self.bmad_core_path / "workflows"
        self.templates_path = self.bmad_core_path / "templates"
        self.agent_teams_path = self.bmad_core_path / "agent-teams"

        self._template_cache: Dict[str, TemplateDefinition] = {}
        self._workflow_cache: Dict[str, Dict[str, Any]] = {}
        self._team_config_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_enabled = True

        logger.info("Template loader initialized",
                   base_path=str(self.template_base_path),
                   bmad_core_path=str(self.bmad_core_path),
                   workflows_path=str(self.workflows_path))

    def load_template(self, template_id: str, use_cache: bool = True) -> TemplateDefinition:
        """
        Load a template by its ID.

        Args:
            template_id: Unique identifier for the template
            use_cache: Whether to use cached templates

        Returns:
            TemplateDefinition object

        Raises:
            FileNotFoundError: If template file doesn't exist
            ParserError: If template parsing fails
            ValidationError: If template validation fails
        """
        # Check cache first
        if use_cache and self._cache_enabled and template_id in self._template_cache:
            logger.debug(f"Loading template '{template_id}' from cache")
            return self._template_cache[template_id]

        # Find template file
        template_file = self._find_template_file(template_id)
        if not template_file:
            raise FileNotFoundError(f"Template '{template_id}' not found")

        # Load and parse template
        logger.info(f"Loading template '{template_id}' from {template_file}")
        template = self.yaml_parser.load_template(template_file)

        # Validate template
        validation_errors = template.validate_template()
        if validation_errors:
            logger.error(f"Template validation failed for '{template_id}': {validation_errors}")
            raise ValueError(f"Template validation failed: {'; '.join(validation_errors)}")

        # Cache template
        if self._cache_enabled:
            self._template_cache[template_id] = template

        return template

    def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """
        Get metadata for a template.

        Args:
            template_id: ID of the template

        Returns:
            Dictionary with template metadata
        """
        try:
            template = self.load_template(template_id)

            return {
                "id": template.id,
                "name": template.name,
                "version": template.version,
                "description": template.description,
                "output_format": template.output.format.value,
                "sections_count": len(template.sections),
                "elicitation_sections": len(template.get_elicitation_sections()),
                "complexity": template.estimate_complexity(),
                "tags": template.tags,
                "metadata": template.metadata
            }

        except Exception as e:
            logger.error(f"Failed to get metadata for template '{template_id}': {str(e)}")
            return {"error": str(e)}

    def list_available_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates.

        Returns:
            List of template metadata dictionaries
        """
        templates = []

        try:
            # Check if base path exists and is a directory
            if self.template_base_path.exists() and self.template_base_path.is_dir():
                for template_file in self.template_base_path.glob("*.yaml"):
                    try:
                        template_id = template_file.stem
                        metadata = self.get_template_metadata(template_id)
                        if "error" not in metadata:
                            templates.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to load template '{template_file}': {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")

        return templates

    def clear_cache(self):
        """Clear the template cache."""
        self._template_cache.clear()
        logger.info("Template cache cleared")

    def enable_cache(self, enabled: bool = True):
        """Enable or disable template caching."""
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()
        logger.info(f"Template cache {'enabled' if enabled else 'disabled'}")

    def is_template_cached(self, template_id: str) -> bool:
        """Check if template is in cache."""
        return template_id in self._template_cache

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_enabled": self._cache_enabled,
            "cached_templates": len(self._template_cache),
            "template_ids": list(self._template_cache.keys())
        }

    def _find_template_file(self, template_id: str) -> Optional[Path]:
        """
        Find the template file for a given template ID.

        Args:
            template_id: Template identifier

        Returns:
            Path to template file or None if not found
        """
        try:
            # Ensure template_base_path is a Path object
            base_path = Path(self.template_base_path)

            # Try different file extensions
            for ext in ['.yaml', '.yml']:
                template_file = base_path / f"{template_id}{ext}"
                if template_file.exists() and template_file.is_file():
                    return template_file

        except Exception as e:
            logger.warning(f"Error finding template file for '{template_id}': {str(e)}")

        return None

    def validate_template_structure(self, template_id: str) -> Dict[str, Any]:
        """
        Validate template structure without loading into cache.

        Args:
            template_id: ID of the template to validate

        Returns:
            Dictionary with validation results
        """
        try:
            # Find template file
            template_file = self._find_template_file(template_id)
            if not template_file:
                return {
                    "is_valid": False,
                    "errors": [f"Template file not found for '{template_id}'"],
                    "warnings": []
                }

            # Load and validate template
            template = self.yaml_parser.load_template(template_file)
            validation_errors = template.validate_template()

            return {
                "is_valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "warnings": [],
                "metadata": {
                    "sections_count": len(template.sections),
                    "has_elicitation": len(template.get_elicitation_sections()) > 0,
                    "complexity": template.estimate_complexity()
                }
            }

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Template validation failed: {str(e)}"],
                "warnings": []
            }

    def load_workflow_definitions(self) -> Dict[str, Any]:
        """Load workflow definitions from backend/app/workflows/ directory (TR-10)."""

        if not self.workflows_path.exists():
            logger.warning("BMAD Core workflows directory not found",
                         path=str(self.workflows_path))
            return {}

        logger.info("Loading workflow definitions from BMAD Core",
                   path=str(self.workflows_path))

        workflows = {}
        workflows_loaded = 0

        for workflow_file in self.workflows_path.glob("*.yaml"):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = yaml.safe_load(f)
                    workflow_name = workflow_file.stem

                # Validate workflow schema
                validated_workflow = self._validate_workflow_schema(workflow_data, workflow_name)
                workflows[workflow_name] = validated_workflow
                workflows_loaded += 1

                logger.debug("Loaded workflow definition",
                           workflow_name=workflow_name,
                           phases_count=len(validated_workflow.get("phases", [])))

            except Exception as e:
                logger.error("Failed to load workflow definition",
                           file=str(workflow_file),
                           error=str(e))

        # Cache workflows if caching is enabled
        if self._cache_enabled:
            self._workflow_cache.update(workflows)

        logger.info("Workflow definitions loaded",
                   total_workflows=workflows_loaded,
                   workflow_names=list(workflows.keys()))

        return workflows

    def _validate_workflow_schema(self, workflow_data: Dict[str, Any], workflow_name: str) -> Dict[str, Any]:
        """Validate workflow definition against BMAD schema."""

        required_fields = ["phases", "agents", "transitions", "outputs"]

        for field in required_fields:
            if field not in workflow_data:
                raise ValueError(f"Missing required workflow field '{field}' in {workflow_name}")

        # Validate phases structure
        phases = workflow_data.get("phases", [])
        if not isinstance(phases, list) or not phases:
            raise ValueError(f"Workflow '{workflow_name}' must have at least one phase")

        for i, phase in enumerate(phases):
            if not isinstance(phase, dict):
                raise ValueError(f"Phase {i} in workflow '{workflow_name}' must be a dictionary")

            required_phase_fields = ["name", "description", "agents", "outputs"]
            for field in required_phase_fields:
                if field not in phase:
                    logger.warning(f"Phase {i} in workflow '{workflow_name}' missing field '{field}'")

        # Validate agents structure
        agents = workflow_data.get("agents", [])
        if not isinstance(agents, list) or not agents:
            raise ValueError(f"Workflow '{workflow_name}' must specify at least one agent")

        # Validate transitions
        transitions = workflow_data.get("transitions", [])
        if not isinstance(transitions, list):
            raise ValueError(f"Transitions in workflow '{workflow_name}' must be a list")

        # Add metadata
        workflow_data["metadata"] = {
            "validation_timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "phases_count": len(phases),
            "agents_count": len(agents),
            "transitions_count": len(transitions),
            "validated": True
        }

        logger.debug("Workflow schema validation successful",
                   workflow_name=workflow_name,
                   phases=len(phases),
                   agents=len(agents))

        return workflow_data

    def load_agent_team_configurations(self) -> Dict[str, Any]:
        """Load agent team configurations from backend/app/agent-teams/ (TR-12)."""

        if not self.agent_teams_path.exists():
            logger.warning("BMAD Core agent teams directory not found",
                         path=str(self.agent_teams_path))
            return {}

        logger.info("Loading agent team configurations from BMAD Core",
                   path=str(self.agent_teams_path))

        team_configs = {}
        teams_loaded = 0

        for team_file in self.agent_teams_path.glob("*.yaml"):
            try:
                with open(team_file, 'r', encoding='utf-8') as f:
                    team_data = yaml.safe_load(f)
                    team_name = team_file.stem

                # Validate team configuration
                validated_team = self._validate_team_config(team_data, team_name)
                team_configs[team_name] = validated_team
                teams_loaded += 1

                logger.debug("Loaded team configuration",
                           team_name=team_name,
                           agents_count=len(validated_team.get("agents", [])))

            except Exception as e:
                logger.error("Failed to load team configuration",
                           file=str(team_file),
                           error=str(e))

        # Cache team configs if caching is enabled
        if self._cache_enabled:
            self._team_config_cache.update(team_configs)

        logger.info("Agent team configurations loaded",
                   total_teams=teams_loaded,
                   team_names=list(team_configs.keys()))

        return team_configs

    def _validate_team_config(self, team_data: Dict[str, Any], team_name: str) -> Dict[str, Any]:
        """Validate agent team configuration."""

        required_fields = ["agents", "workflow", "coordination_pattern"]

        for field in required_fields:
            if field not in team_data:
                raise ValueError(f"Missing required team config field '{field}' in {team_name}")

        # Validate agents structure
        agents = team_data.get("agents", [])
        if not isinstance(agents, list) or not agents:
            raise ValueError(f"Team '{team_name}' must have at least one agent")

        for i, agent in enumerate(agents):
            if not isinstance(agent, dict):
                raise ValueError(f"Agent {i} in team '{team_name}' must be a dictionary")

            required_agent_fields = ["type", "role"]
            for field in required_agent_fields:
                if field not in agent:
                    logger.warning(f"Agent {i} in team '{team_name}' missing field '{field}'")

        # Validate coordination pattern
        valid_patterns = ["sequential", "parallel", "hybrid", "round_robin", "priority_based"]
        coordination = team_data.get("coordination_pattern", "")
        if coordination not in valid_patterns:
            logger.warning(f"Team '{team_name}' has invalid coordination pattern: {coordination}")

        # Add metadata
        team_data["metadata"] = {
            "validation_timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "agents_count": len(agents),
            "coordination_pattern": coordination,
            "validated": True
        }

        logger.debug("Team configuration validation successful",
                   team_name=team_name,
                   agents=len(agents),
                   coordination=coordination)

        return team_data

    def get_workflow_definition(self, workflow_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get specific workflow definition."""

        # Check cache first
        if use_cache and self._cache_enabled and workflow_name in self._workflow_cache:
            logger.debug("Loading workflow from cache", workflow_name=workflow_name)
            return self._workflow_cache[workflow_name]

        # Load all workflows and return specific one
        workflows = self.load_workflow_definitions()
        if workflow_name not in workflows:
            raise FileNotFoundError(f"Workflow '{workflow_name}' not found")

        return workflows[workflow_name]

    def get_team_configuration(self, team_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get specific team configuration."""

        # Check cache first
        if use_cache and self._cache_enabled and team_name in self._team_config_cache:
            logger.debug("Loading team config from cache", team_name=team_name)
            return self._team_config_cache[team_name]

        # Load all team configs and return specific one
        team_configs = self.load_agent_team_configurations()
        if team_name not in team_configs:
            raise FileNotFoundError(f"Team configuration '{team_name}' not found")

        return team_configs[team_name]

    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflow definitions."""

        workflows = self.load_workflow_definitions()
        workflow_list = []

        for name, definition in workflows.items():
            metadata = definition.get("metadata", {})
            workflow_info = {
                "name": name,
                "description": definition.get("description", ""),
                "phases_count": metadata.get("phases_count", 0),
                "agents_count": metadata.get("agents_count", 0),
                "coordination_pattern": definition.get("coordination_pattern", "sequential"),
                "validated": metadata.get("validated", False)
            }
            workflow_list.append(workflow_info)

        return workflow_list

    def list_available_teams(self) -> List[Dict[str, Any]]:
        """List all available team configurations."""

        teams = self.load_agent_team_configurations()
        team_list = []

        for name, config in teams.items():
            metadata = config.get("metadata", {})
            team_info = {
                "name": name,
                "description": config.get("description", ""),
                "agents_count": metadata.get("agents_count", 0),
                "coordination_pattern": metadata.get("coordination_pattern", "sequential"),
                "workflow": config.get("workflow", ""),
                "validated": metadata.get("validated", False)
            }
            team_list.append(team_info)

        return team_list

    def clear_bmad_cache(self):
        """Clear BMAD Core caches (workflows, teams)."""

        self._workflow_cache.clear()
        self._team_config_cache.clear()
        logger.info("BMAD Core caches cleared")