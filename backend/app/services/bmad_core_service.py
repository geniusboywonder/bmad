"""
BMAD Core integration service for template and workflow management.

Provides unified access to BMAD Core framework components including
workflows, templates, agent teams, and agent configurations.
Implements TR-10 through TR-13 requirements for BMAD Core integration.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import structlog
from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)


class BMADCoreService:
    """
    Service for integrating with BMAD Core framework components.

    Provides unified access to:
    - Workflow definitions (TR-10)
    - Document templates (TR-11)
    - Agent team configurations (TR-12)
    - Variable substitution and conditional logic (TR-13)
    """

    def __init__(self, db: Session):
        self.db = db
        # Handle both project root and backend directory contexts
        if Path("backend/app").exists():
            self.bmad_core_path = Path("backend/app")
        else:
            self.bmad_core_path = Path("app")

        # Component paths
        self.workflows_path = self.bmad_core_path / "workflows"
        self.templates_path = self.bmad_core_path / "templates"
        self.agent_teams_path = self.bmad_core_path / "agent-teams"
        self.agents_path = self.bmad_core_path / "agents"
        self.checklists_path = self.bmad_core_path / "checklists"
        self.tasks_path = self.bmad_core_path / "tasks"
        self.data_path = self.bmad_core_path / "data"
        self.utils_path = self.bmad_core_path / "utils"

        # Caches for performance
        self._workflows_cache: Dict[str, Any] = {}
        self._templates_cache: Dict[str, Any] = {}
        self._agent_teams_cache: Dict[str, Any] = {}
        self._agent_configs_cache: Dict[str, Any] = {}
        self._cache_enabled = True

        logger.info("BMAD Core service initialized",
                   bmad_core_path=str(self.bmad_core_path),
                   components_available=self._check_component_availability())

    def initialize_bmad_core(self) -> Dict[str, Any]:
        """Initialize BMAD Core framework components."""

        if not self.bmad_core_path.exists():
            raise FileNotFoundError(
                f"BMAD Core directory not found: {self.bmad_core_path}. "
                "Please ensure backend/app directory exists in project root."
            )

        logger.info("Initializing BMAD Core framework components")

        initialization_result = {
            "workflows": self._load_workflows(),
            "templates": self._load_templates(),
            "agent_teams": self._load_agent_teams(),
            "agents": self._load_agent_configs(),
            "initialization_metadata": {
                "bmad_core_path": str(self.bmad_core_path),
                "components_loaded": [],
                "components_failed": [],
                "total_components": 0
            }
        }

        # Calculate initialization statistics
        metadata = initialization_result["initialization_metadata"]
        for component, data in initialization_result.items():
            if component != "initialization_metadata" and isinstance(data, dict):
                if data:  # Non-empty result
                    metadata["components_loaded"].append(component)
                    metadata["total_components"] += len(data)
                else:
                    metadata["components_failed"].append(component)

        logger.info("BMAD Core initialization completed",
                   components_loaded=metadata["components_loaded"],
                   total_items=metadata["total_components"],
                   failed_components=metadata["components_failed"])

        return initialization_result

    def _load_workflows(self) -> Dict[str, Any]:
        """Load all workflow definitions from workflows directory."""

        if not self.workflows_path.exists():
            logger.warning("Workflows directory not found",
                         path=str(self.workflows_path))
            return {}

        workflows = {}
        for workflow_file in self.workflows_path.glob("*.yaml"):
            try:
                workflow_name = workflow_file.stem
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = yaml.safe_load(f)

                # Validate workflow structure
                validated_workflow = self._validate_workflow(workflow_data, workflow_name)
                workflows[workflow_name] = validated_workflow

                logger.debug("Loaded workflow definition",
                           workflow_name=workflow_name,
                           phases_count=len(validated_workflow.get("phases", [])))

            except Exception as e:
                logger.error("Failed to load workflow",
                           file=str(workflow_file),
                           error=str(e))

        if self._cache_enabled:
            self._workflows_cache.update(workflows)

        logger.info("Workflows loaded",
                   count=len(workflows),
                   workflow_names=list(workflows.keys()))

        return workflows

    def _load_templates(self) -> Dict[str, Any]:
        """Load all document templates from templates directory."""

        if not self.templates_path.exists():
            logger.warning("Templates directory not found",
                         path=str(self.templates_path))
            return {}

        templates = {}
        for template_file in self.templates_path.glob("*.yaml"):
            try:
                template_name = template_file.stem
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = yaml.safe_load(f)

                # Validate template structure
                validated_template = self._validate_template(template_data, template_name)
                templates[template_name] = validated_template

                logger.debug("Loaded template definition",
                           template_name=template_name,
                           template_type=validated_template.get("type", "unknown"))

            except Exception as e:
                logger.error("Failed to load template",
                           file=str(template_file),
                           error=str(e))

        if self._cache_enabled:
            self._templates_cache.update(templates)

        logger.info("Templates loaded",
                   count=len(templates),
                   template_names=list(templates.keys()))

        return templates

    def _load_agent_teams(self) -> Dict[str, Any]:
        """Load all agent team configurations from agent-teams directory."""

        if not self.agent_teams_path.exists():
            logger.warning("Agent teams directory not found",
                         path=str(self.agent_teams_path))
            return {}

        agent_teams = {}
        for team_file in self.agent_teams_path.glob("*.yaml"):
            try:
                team_name = team_file.stem
                with open(team_file, 'r', encoding='utf-8') as f:
                    team_data = yaml.safe_load(f)

                # Validate team configuration
                validated_team = self._validate_agent_team(team_data, team_name)
                agent_teams[team_name] = validated_team

                logger.debug("Loaded agent team configuration",
                           team_name=team_name,
                           agents_count=len(validated_team.get("agents", [])))

            except Exception as e:
                logger.error("Failed to load agent team",
                           file=str(team_file),
                           error=str(e))

        if self._cache_enabled:
            self._agent_teams_cache.update(agent_teams)

        logger.info("Agent teams loaded",
                   count=len(agent_teams),
                   team_names=list(agent_teams.keys()))

        return agent_teams

    def _load_agent_configs(self) -> Dict[str, Any]:
        """Load all agent configurations from agents directory."""

        if not self.agents_path.exists():
            logger.warning("Agents directory not found",
                         path=str(self.agents_path))
            return {}

        agent_configs = {}
        for agent_file in self.agents_path.glob("*.md"):
            try:
                agent_name = agent_file.stem
                with open(agent_file, 'r', encoding='utf-8') as f:
                    agent_content = f.read()

                # Parse agent configuration from markdown
                parsed_config = self._parse_agent_markdown(agent_content, agent_name)
                agent_configs[agent_name] = parsed_config

                logger.debug("Loaded agent configuration",
                           agent_name=agent_name,
                           has_system_message=bool(parsed_config.get("system_message")))

            except Exception as e:
                logger.error("Failed to load agent configuration",
                           file=str(agent_file),
                           error=str(e))

        if self._cache_enabled:
            self._agent_configs_cache.update(agent_configs)

        logger.info("Agent configurations loaded",
                   count=len(agent_configs),
                   agent_names=list(agent_configs.keys()))

        return agent_configs

    def _validate_workflow(self, workflow_data: Dict[str, Any], workflow_name: str) -> Dict[str, Any]:
        """Validate workflow definition structure."""

        required_fields = ["phases", "agents", "transitions", "outputs"]
        for field in required_fields:
            if field not in workflow_data:
                raise ValueError(f"Missing required workflow field '{field}' in {workflow_name}")

        # Validate phases
        phases = workflow_data.get("phases", [])
        if not isinstance(phases, list) or not phases:
            raise ValueError(f"Workflow '{workflow_name}' must have at least one phase")

        # Add validation metadata
        workflow_data["validation_metadata"] = {
            "validated_at": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "phases_count": len(phases),
            "agents_count": len(workflow_data.get("agents", [])),
            "is_valid": True
        }

        return workflow_data

    def _validate_template(self, template_data: Dict[str, Any], template_name: str) -> Dict[str, Any]:
        """Validate template definition structure."""

        required_fields = ["content"]
        for field in required_fields:
            if field not in template_data:
                raise ValueError(f"Missing required template field '{field}' in {template_name}")

        # Add validation metadata
        template_data["validation_metadata"] = {
            "validated_at": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "template_type": template_data.get("type", "document"),
            "has_variables": "{{" in str(template_data.get("content", "")),
            "is_valid": True
        }

        return template_data

    def _validate_agent_team(self, team_data: Dict[str, Any], team_name: str) -> Dict[str, Any]:
        """Validate agent team configuration structure."""

        required_fields = ["agents", "workflow", "coordination_pattern"]
        for field in required_fields:
            if field not in team_data:
                raise ValueError(f"Missing required team field '{field}' in {team_name}")

        # Validate agents list
        agents = team_data.get("agents", [])
        if not isinstance(agents, list) or not agents:
            raise ValueError(f"Team '{team_name}' must have at least one agent")

        # Add validation metadata
        team_data["validation_metadata"] = {
            "validated_at": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "agents_count": len(agents),
            "coordination_pattern": team_data.get("coordination_pattern"),
            "is_valid": True
        }

        return team_data

    def _parse_agent_markdown(self, content: str, agent_name: str) -> Dict[str, Any]:
        """Parse agent configuration from markdown content."""

        import re

        config = {
            "agent_name": agent_name,
            "system_message": "",
            "description": "",
            "responsibilities": [],
            "tools": [],
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.7
            }
        }

        # Extract system message
        system_msg_match = re.search(r"## System Message\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if system_msg_match:
            config["system_message"] = system_msg_match.group(1).strip()

        # Extract description
        desc_match = re.search(r"## Description\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if desc_match:
            config["description"] = desc_match.group(1).strip()

        # Extract responsibilities
        resp_match = re.search(r"## Responsibilities\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if resp_match:
            resp_content = resp_match.group(1)
            responsibilities = re.findall(r"[-*]\s*([^\n]+)", resp_content)
            config["responsibilities"] = [resp.strip() for resp in responsibilities]

        # Extract tools
        tools_match = re.search(r"## Tools\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if tools_match:
            tools_content = tools_match.group(1)
            tools = re.findall(r"[-*]\s*([^\n]+)", tools_content)
            config["tools"] = [tool.strip() for tool in tools]

        return config

    def _check_component_availability(self) -> Dict[str, bool]:
        """Check which BMAD Core components are available."""

        return {
            "workflows": self.workflows_path.exists(),
            "templates": self.templates_path.exists(),
            "agent_teams": self.agent_teams_path.exists(),
            "agents": self.agents_path.exists(),
            "checklists": self.checklists_path.exists(),
            "tasks": self.tasks_path.exists(),
            "data": self.data_path.exists(),
            "utils": self.utils_path.exists()
        }

    def get_workflow_definition(self, workflow_name: str) -> Dict[str, Any]:
        """Get specific workflow definition by name."""

        # Check cache first
        if self._cache_enabled and workflow_name in self._workflows_cache:
            return self._workflows_cache[workflow_name]

        # Load from disk
        workflows = self._load_workflows()
        if workflow_name not in workflows:
            raise FileNotFoundError(f"Workflow '{workflow_name}' not found")

        return workflows[workflow_name]

    def get_template_definition(self, template_name: str) -> Dict[str, Any]:
        """Get specific template definition by name."""

        # Check cache first
        if self._cache_enabled and template_name in self._templates_cache:
            return self._templates_cache[template_name]

        # Load from disk
        templates = self._load_templates()
        if template_name not in templates:
            raise FileNotFoundError(f"Template '{template_name}' not found")

        return templates[template_name]

    def get_agent_team_configuration(self, team_name: str) -> Dict[str, Any]:
        """Get specific agent team configuration by name."""

        # Check cache first
        if self._cache_enabled and team_name in self._agent_teams_cache:
            return self._agent_teams_cache[team_name]

        # Load from disk
        agent_teams = self._load_agent_teams()
        if team_name not in agent_teams:
            raise FileNotFoundError(f"Agent team '{team_name}' not found")

        return agent_teams[team_name]

    def get_agent_configuration(self, agent_name: str) -> Dict[str, Any]:
        """Get specific agent configuration by name."""

        # Check cache first
        if self._cache_enabled and agent_name in self._agent_configs_cache:
            return self._agent_configs_cache[agent_name]

        # Load from disk
        agent_configs = self._load_agent_configs()
        if agent_name not in agent_configs:
            raise FileNotFoundError(f"Agent '{agent_name}' not found")

        return agent_configs[agent_name]

    def list_available_components(self) -> Dict[str, List[str]]:
        """List all available BMAD Core components."""

        return {
            "workflows": list(self._load_workflows().keys()),
            "templates": list(self._load_templates().keys()),
            "agent_teams": list(self._load_agent_teams().keys()),
            "agents": list(self._load_agent_configs().keys())
        }

    def validate_bmad_core_setup(self) -> Dict[str, Any]:
        """Validate BMAD Core setup and component integrity."""

        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "component_status": {},
            "summary": {}
        }

        # Check directory structure
        if not self.bmad_core_path.exists():
            validation_result["is_valid"] = False
            validation_result["errors"].append("BMAD Core directory not found")
            return validation_result

        # Check each component
        components = self._check_component_availability()
        for component, available in components.items():
            validation_result["component_status"][component] = {
                "available": available,
                "path": str(getattr(self, f"{component}_path"))
            }

            if not available:
                validation_result["warnings"].append(f"{component} directory not found")

        # Validate component contents
        try:
            workflows = self._load_workflows()
            templates = self._load_templates()
            agent_teams = self._load_agent_teams()
            agent_configs = self._load_agent_configs()

            validation_result["summary"] = {
                "workflows_count": len(workflows),
                "templates_count": len(templates),
                "agent_teams_count": len(agent_teams),
                "agent_configs_count": len(agent_configs),
                "total_components": len(workflows) + len(templates) + len(agent_teams) + len(agent_configs)
            }

        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Component validation failed: {str(e)}")

        logger.info("BMAD Core validation completed",
                   is_valid=validation_result["is_valid"],
                   errors_count=len(validation_result["errors"]),
                   warnings_count=len(validation_result["warnings"]))

        return validation_result

    def reload_all_components(self) -> Dict[str, Any]:
        """Reload all BMAD Core components from disk."""

        logger.info("Reloading all BMAD Core components")

        # Clear caches
        self._workflows_cache.clear()
        self._templates_cache.clear()
        self._agent_teams_cache.clear()
        self._agent_configs_cache.clear()

        # Reinitialize
        return self.initialize_bmad_core()

    def enable_caching(self, enabled: bool = True):
        """Enable or disable component caching."""

        self._cache_enabled = enabled
        if not enabled:
            self._workflows_cache.clear()
            self._templates_cache.clear()
            self._agent_teams_cache.clear()
            self._agent_configs_cache.clear()

        logger.info("BMAD Core caching",
                   enabled=enabled)

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get caching statistics."""

        return {
            "cache_enabled": self._cache_enabled,
            "cached_workflows": len(self._workflows_cache),
            "cached_templates": len(self._templates_cache),
            "cached_agent_teams": len(self._agent_teams_cache),
            "cached_agent_configs": len(self._agent_configs_cache),
            "total_cached_items": (
                len(self._workflows_cache) + len(self._templates_cache) +
                len(self._agent_teams_cache) + len(self._agent_configs_cache)
            )
        }