"""
Template Service Package - Refactored into focused services following SOLID principles.

This package maintains backward compatibility while providing specialized services:
- TemplateCore: Main coordination logic
- TemplateLoader: Template loading and caching
- TemplateRenderer: Template rendering and output formatting
"""

from .template_core import TemplateCore, TemplateError
from .template_loader import TemplateLoader
from .template_renderer import TemplateRenderer

# For backward compatibility, expose TemplateCore as TemplateService
TemplateService = TemplateCore

__all__ = [
    "TemplateCore",
    "TemplateService",  # Backward compatibility alias
    "TemplateLoader",
    "TemplateRenderer",
    "TemplateError"
]