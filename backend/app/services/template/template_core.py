"""
Template Core Service - Main coordination logic with dependency injection.

Handles main template coordination and delegates to specialized services.
Maintains backward compatibility while following SOLID principles.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ...models.template import TemplateDefinition, TemplateOutputFormat
from .template_loader import TemplateLoader
from .template_renderer import TemplateRenderer

logger = logging.getLogger(__name__)


class TemplateError(Exception):
    """Raised when template processing fails."""
    pass


class TemplateCore:
    """
    Core template service that coordinates specialized components.

    Follows Single Responsibility Principle by delegating specialized tasks
    to focused service components.
    """

    def __init__(self, template_base_path: Optional[Union[str, Path]] = None):
        """
        Initialize the template core service.

        Args:
            template_base_path: Base path for template files (defaults to backend/app/templates)
        """
        # Initialize specialized services
        self.template_loader = TemplateLoader(template_base_path)
        self.template_renderer = TemplateRenderer()

        logger.info("Template core service initialized with specialized components")

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
        return self.template_loader.load_template(template_id, use_cache)

    def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        output_format: Optional[TemplateOutputFormat] = None
    ) -> str:
        """
        Render a template with the provided variables.

        Args:
            template_id: ID of the template to render
            variables: Dictionary of variable values
            output_format: Desired output format (overrides template default)

        Returns:
            Rendered template as string

        Raises:
            TemplateError: If rendering fails
            VariableSubstitutionError: If variable substitution fails
        """
        try:
            # Load template using loader
            template = self.template_loader.load_template(template_id)

            # Render template using renderer
            rendered_content = self.template_renderer.render_template(
                template, variables, output_format
            )

            logger.info(f"Successfully rendered template '{template_id}'")
            return rendered_content

        except Exception as e:
            logger.error(f"Failed to render template '{template_id}': {str(e)}")
            raise TemplateError(f"Template rendering failed: {str(e)}")

    def validate_template_variables(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate variables for a template.

        Args:
            template_id: ID of the template to validate against
            variables: Dictionary of variable values

        Returns:
            Dictionary with validation results
        """
        try:
            template = self.template_loader.load_template(template_id)
            return self.template_renderer.validate_template_variables(template, variables)

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "required_variables": [],
                "provided_variables": list(variables.keys()),
                "missing_variables": [],
                "unused_variables": []
            }

    def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """
        Get metadata for a template.

        Args:
            template_id: ID of the template

        Returns:
            Dictionary with template metadata
        """
        return self.template_loader.get_template_metadata(template_id)

    def list_available_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates.

        Returns:
            List of template metadata dictionaries
        """
        return self.template_loader.list_available_templates()

    def clear_cache(self):
        """Clear the template cache."""
        self.template_loader.clear_cache()

    def enable_cache(self, enabled: bool = True):
        """Enable or disable template caching."""
        self.template_loader.enable_cache(enabled)

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of template service components."""
        return {
            "template_loader": {
                "cache_stats": self.template_loader.get_cache_stats(),
                "base_path": str(self.template_loader.template_base_path)
            },
            "template_renderer": {
                "supported_formats": self.template_renderer.get_supported_formats()
            }
        }

    def validate_template_structure(self, template_id: str) -> Dict[str, Any]:
        """
        Validate template structure.

        Args:
            template_id: ID of the template to validate

        Returns:
            Dictionary with validation results
        """
        return self.template_loader.validate_template_structure(template_id)

    def estimate_rendering_complexity(self, template_id: str) -> Dict[str, Any]:
        """
        Estimate rendering complexity for a template.

        Args:
            template_id: ID of the template to analyze

        Returns:
            Dictionary with complexity metrics
        """
        try:
            template = self.template_loader.load_template(template_id)
            return self.template_renderer.estimate_rendering_complexity(template)

        except Exception as e:
            return {
                "error": f"Failed to estimate complexity: {str(e)}",
                "complexity_score": -1
            }