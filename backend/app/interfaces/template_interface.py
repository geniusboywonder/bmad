"""
Template Service Interface - Interface definitions for template services.

Defines interfaces for all template-related services following Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.models.template import TemplateDefinition, TemplateOutputFormat


class ITemplateCore(ABC):
    """Interface for template core coordination service."""

    @abstractmethod
    def load_template(self, template_id: str, use_cache: bool = True) -> TemplateDefinition:
        """Load a template by its ID."""
        pass

    @abstractmethod
    def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        output_format: Optional[TemplateOutputFormat] = None
    ) -> str:
        """Render a template with the provided variables."""
        pass

    @abstractmethod
    def validate_template_variables(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate variables for a template."""
        pass

    @abstractmethod
    def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """Get metadata for a template."""
        pass

    @abstractmethod
    def list_available_templates(self) -> List[Dict[str, Any]]:
        """List all available templates."""
        pass

    @abstractmethod
    def clear_cache(self):
        """Clear the template cache."""
        pass

    @abstractmethod
    def enable_cache(self, enabled: bool = True):
        """Enable or disable template caching."""
        pass


class ITemplateLoader(ABC):
    """Interface for template loading and caching."""

    @abstractmethod
    def load_template(self, template_id: str, use_cache: bool = True) -> TemplateDefinition:
        """Load a template by its ID."""
        pass

    @abstractmethod
    def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """Get metadata for a template."""
        pass

    @abstractmethod
    def list_available_templates(self) -> List[Dict[str, Any]]:
        """List all available templates."""
        pass

    @abstractmethod
    def clear_cache(self):
        """Clear the template cache."""
        pass

    @abstractmethod
    def enable_cache(self, enabled: bool = True):
        """Enable or disable template caching."""
        pass

    @abstractmethod
    def is_template_cached(self, template_id: str) -> bool:
        """Check if template is in cache."""
        pass

    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass

    @abstractmethod
    def validate_template_structure(self, template_id: str) -> Dict[str, Any]:
        """Validate template structure without loading into cache."""
        pass


class ITemplateRenderer(ABC):
    """Interface for template rendering and output formatting."""

    @abstractmethod
    def render_template(
        self,
        template: TemplateDefinition,
        variables: Dict[str, Any],
        output_format: Optional[TemplateOutputFormat] = None
    ) -> str:
        """Render a template with the provided variables."""
        pass

    @abstractmethod
    def validate_template_variables(
        self,
        template: TemplateDefinition,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate variables for a template."""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        pass

    @abstractmethod
    def estimate_rendering_complexity(self, template: TemplateDefinition) -> Dict[str, Any]:
        """Estimate rendering complexity for a template."""
        pass