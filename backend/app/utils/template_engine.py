"""Template engine utility for variable substitution and rendering.

This module provides Jinja2-based template rendering with enhanced features
for the BMAD template system, including variable substitution, conditional
logic, and error handling.
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog
from jinja2 import Environment, FileSystemLoader, TemplateError, TemplateNotFound

logger = structlog.get_logger(__name__)


class TemplateEngine:
    """Jinja2-based template engine for BMAD template system.

    Provides enhanced template rendering with:
    - Variable substitution using {{variable}} syntax
    - Conditional rendering with {% if %} blocks
    - Loops and iterations
    - Custom filters and functions
    - Error handling and validation
    - Template inheritance and includes
    """

    def __init__(self, template_dirs: Optional[List[str]] = None):
        """Initialize the template engine.

        Args:
            template_dirs: List of directories to search for templates.
                          Defaults to standard BMAD template locations.
        """
        if template_dirs is None:
            # Default BMAD template directories
            template_dirs = [
                ".bmad-core/templates",
                "backend/app/templates",
                "docs/templates"
            ]

        # Filter out directories that don't exist
        existing_dirs = []
        for template_dir in template_dirs:
            if os.path.exists(template_dir):
                existing_dirs.append(template_dir)
                logger.debug("Template directory found", directory=template_dir)
            else:
                logger.warning("Template directory not found", directory=template_dir)

        if not existing_dirs:
            logger.warning("No template directories found, using current directory")
            existing_dirs = ["."]

        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(existing_dirs),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False  # We handle escaping at the application level
        )

        # Add custom filters
        self._add_custom_filters()

        # Add custom functions
        self._add_custom_functions()

        logger.info("Template engine initialized",
                   template_dirs=existing_dirs,
                   filters=list(self.env.filters.keys()),
                   functions=list(self.env.globals.keys()))

    def _add_custom_filters(self):
        """Add custom Jinja2 filters for enhanced templating."""

        def format_date(value, format_str="%Y-%m-%d"):
            """Format datetime objects."""
            if hasattr(value, 'strftime'):
                return value.strftime(format_str)
            return str(value)

        def to_json(value):
            """Convert value to JSON string."""
            import json
            return json.dumps(value, indent=2, default=str)

        def truncate(value, length=100, suffix="..."):
            """Truncate string to specified length."""
            if isinstance(value, str) and len(value) > length:
                return value[:length - len(suffix)] + suffix
            return value

        def capitalize_words(value):
            """Capitalize first letter of each word."""
            if isinstance(value, str):
                return value.title()
            return value

        # Register filters
        self.env.filters['format_date'] = format_date
        self.env.filters['to_json'] = to_json
        self.env.filters['truncate'] = truncate
        self.env.filters['capitalize_words'] = capitalize_words

    def _add_custom_functions(self):
        """Add custom Jinja2 functions for enhanced templating."""

        def now():
            """Get current datetime."""
            from datetime import datetime, timezone
            return datetime.now(timezone.utc)

        def uuid4():
            """Generate a UUID4."""
            from uuid import uuid4
            return str(uuid4())

        def enumerate_list(items):
            """Enumerate a list with 1-based indexing."""
            return enumerate(items, 1)

        def get_env_var(name, default=""):
            """Get environment variable."""
            return os.getenv(name, default)

        # Register functions
        self.env.globals['now'] = now
        self.env.globals['uuid4'] = uuid4
        self.env.globals['enumerate'] = enumerate_list
        self.env.globals['env'] = get_env_var

    def render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Render a template with the given variables.

        Args:
            template_name: Name of the template file (without extension if .yaml/.yml)
            variables: Dictionary of variables to substitute in the template

        Returns:
            Rendered template as a string

        Raises:
            TemplateNotFound: If template file is not found
            TemplateError: If template rendering fails
            ValueError: If template_name is invalid
        """
        if not template_name:
            raise ValueError("Template name cannot be empty")

        # Ensure template has extension
        if not template_name.endswith(('.yaml', '.yml', '.md', '.txt', '.json')):
            # Try different extensions in order of preference
            for ext in ['.yaml', '.yml', '.md', '.txt', '.json']:
                try:
                    template = self.env.get_template(template_name + ext)
                    break
                except TemplateNotFound:
                    continue
            else:
                # If no extension works, try without extension
                template = self.env.get_template(template_name)
        else:
            template = self.env.get_template(template_name)

        logger.debug("Rendering template",
                    template_name=template_name,
                    variables=list(variables.keys()))

        try:
            # Render the template
            rendered = template.render(**variables)

            logger.info("Template rendered successfully",
                       template_name=template_name,
                       output_length=len(rendered))

            return rendered

        except TemplateError as e:
            logger.error("Template rendering failed",
                        template_name=template_name,
                        error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error during template rendering",
                        template_name=template_name,
                        error=str(e))
            raise TemplateError(f"Unexpected error: {str(e)}")

    def render_string_template(self, template_string: str, variables: Dict[str, Any]) -> str:
        """Render a template from a string rather than a file.

        Args:
            template_string: Template content as a string
            variables: Dictionary of variables to substitute

        Returns:
            Rendered template as a string

        Raises:
            TemplateError: If template rendering fails
        """
        try:
            template = self.env.from_string(template_string)
            rendered = template.render(**variables)

            logger.debug("String template rendered successfully",
                        template_length=len(template_string),
                        output_length=len(rendered))

            return rendered

        except TemplateError as e:
            logger.error("String template rendering failed", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error during string template rendering", error=str(e))
            raise TemplateError(f"Unexpected error: {str(e)}")

    def validate_template(self, template_name: str) -> bool:
        """Validate that a template exists and is syntactically correct.

        Args:
            template_name: Name of the template to validate

        Returns:
            True if template is valid, False otherwise
        """
        try:
            # Try to load the template
            if not template_name.endswith(('.yaml', '.yml', '.md', '.txt', '.json')):
                for ext in ['.yaml', '.yml', '.md', '.txt', '.json']:
                    try:
                        self.env.get_template(template_name + ext)
                        return True
                    except TemplateNotFound:
                        continue
                self.env.get_template(template_name)
            else:
                self.env.get_template(template_name)

            return True

        except TemplateNotFound:
            logger.warning("Template not found", template_name=template_name)
            return False
        except TemplateError as e:
            logger.error("Template validation failed",
                        template_name=template_name,
                        error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error during template validation",
                        template_name=template_name,
                        error=str(e))
            return False

    def list_available_templates(self) -> List[str]:
        """List all available templates in the template directories.

        Returns:
            List of available template names
        """
        templates = []

        for loader in self.env.loader.loaders:
            if hasattr(loader, 'list_templates'):
                try:
                    loader_templates = loader.list_templates()
                    templates.extend(loader_templates)
                except Exception as e:
                    logger.warning("Failed to list templates from loader", error=str(e))

        # Remove duplicates and sort
        unique_templates = list(set(templates))
        unique_templates.sort()

        logger.debug("Available templates listed", count=len(unique_templates))
        return unique_templates

    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific template.

        Args:
            template_name: Name of the template

        Returns:
            Dictionary with template information, or None if not found
        """
        if not self.validate_template(template_name):
            return None

        try:
            template = self.env.get_template(template_name)
            return {
                "name": template_name,
                "filename": getattr(template, 'filename', None),
                "exists": True,
                "valid": True
            }
        except Exception as e:
            logger.error("Failed to get template info",
                        template_name=template_name,
                        error=str(e))
            return None

    def reload_templates(self):
        """Reload all templates from the filesystem.

        Useful for development when templates are modified.
        """
        # Clear template cache
        self.env.cache = {}

        # Reinitialize loaders
        for loader in self.env.loader.loaders:
            if hasattr(loader, '_cache'):
                loader._cache.clear()

        logger.info("Templates reloaded from filesystem")


# Global template engine instance
_template_engine = None


def get_template_engine() -> TemplateEngine:
    """Get the global template engine instance."""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine()
    return _template_engine


def render_template(template_name: str, variables: Dict[str, Any]) -> str:
    """Convenience function to render a template."""
    return get_template_engine().render_template(template_name, variables)


def render_string_template(template_string: str, variables: Dict[str, Any]) -> str:
    """Convenience function to render a string template."""
    return get_template_engine().render_string_template(template_string, variables)
