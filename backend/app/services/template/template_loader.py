"""
Template Loader - Handles template loading and caching.

Responsible for loading templates from files, managing cache, and template discovery.
"""

import logging
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

        self._template_cache: Dict[str, TemplateDefinition] = {}
        self._cache_enabled = True

        logger.info("Template loader initialized", base_path=str(self.template_base_path))

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