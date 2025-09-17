"""
Template Service - Backward compatibility alias module.

This module maintains backward compatibility while the template service has been
refactored into focused, single-responsibility services following SOLID principles.
"""

# Import the refactored template core service
from .template import TemplateCore, TemplateError

# For backward compatibility, expose TemplateCore as TemplateService
TemplateService = TemplateCore

# Also expose individual services for direct access if needed
from .template import (
    TemplateLoader,
    TemplateRenderer
)

__all__ = [
    "TemplateService",
    "TemplateCore",
    "TemplateLoader",
    "TemplateRenderer",
    "TemplateError"
]