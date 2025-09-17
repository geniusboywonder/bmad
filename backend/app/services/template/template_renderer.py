"""
Template Renderer - Handles template rendering and output formatting.

Responsible for rendering templates with variable substitution and formatting
output in various formats (Markdown, HTML, JSON, YAML).
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from ...utils.yaml_parser import YAMLParser, VariableSubstitutionError
from ...utils.template_engine import render_template as jinja_render
from ...models.template import (
    TemplateDefinition,
    TemplateSection,
    TemplateSectionType,
    TemplateOutputFormat
)

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Handles template rendering and output formatting.

    Follows Single Responsibility Principle by focusing solely on rendering logic.
    """

    def __init__(self):
        """Initialize the template renderer."""
        self.yaml_parser = YAMLParser()
        logger.info("Template renderer initialized")

    def render_template(
        self,
        template: TemplateDefinition,
        variables: Dict[str, Any],
        output_format: Optional[TemplateOutputFormat] = None
    ) -> str:
        """
        Render a template with the provided variables.

        Args:
            template: Template definition to render
            variables: Dictionary of variable values
            output_format: Desired output format (overrides template default)

        Returns:
            Rendered template as string

        Raises:
            VariableSubstitutionError: If variable substitution fails
        """
        try:
            # Validate variables
            validation_result = self.yaml_parser.validate_template_variables(
                self._template_to_string(template),
                variables
            )

            if not validation_result.is_valid:
                logger.warning(f"Variable validation warnings for template '{template.id}': {validation_result.warnings}")

            # Render template sections
            rendered_content = self._render_template_sections(template.sections, variables)

            # Apply output formatting
            final_format = output_format or template.output.format
            formatted_content = self._format_output(rendered_content, final_format, template, variables)

            logger.info(f"Successfully rendered template '{template.id}'")
            return formatted_content

        except Exception as e:
            logger.error(f"Failed to render template '{template.id}': {str(e)}")
            raise

    def validate_template_variables(
        self,
        template: TemplateDefinition,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate variables for a template.

        Args:
            template: Template definition to validate against
            variables: Dictionary of variable values

        Returns:
            Dictionary with validation results
        """
        try:
            template_str = self._template_to_string(template)
            validation_result = self.yaml_parser.validate_template_variables(template_str, variables)
            required_vars = template.get_all_required_variables()

            return {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "required_variables": required_vars,
                "provided_variables": list(variables.keys()),
                "missing_variables": [v for v in required_vars if v not in variables],
                "unused_variables": [v for v in variables.keys() if v not in required_vars]
            }

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

    def _render_template_sections(
        self,
        sections: List[TemplateSection],
        variables: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render template sections recursively.

        Args:
            sections: List of template sections to render
            variables: Variable values for substitution
            context: Additional context for conditional rendering

        Returns:
            Rendered content as string
        """
        if context is None:
            context = {}

        rendered_parts = []

        for section in sections:
            # Check conditional rendering
            if not section.should_render({**variables, **context}):
                continue

            # Render section content
            section_content = self._render_section(section, variables, context)
            if section_content:
                rendered_parts.append(section_content)

        return "\n\n".join(rendered_parts)

    def _render_section(
        self,
        section: TemplateSection,
        variables: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Render a single template section.

        Args:
            section: Template section to render
            variables: Variable values
            context: Rendering context

        Returns:
            Rendered section content
        """
        content_parts = []

        # Render section title
        if section.title:
            if section.type == TemplateSectionType.HEADING:
                content_parts.append(f"# {section.title}")
            else:
                content_parts.append(f"## {section.title}")

        # Render section instruction
        if section.instruction:
            content_parts.append(f"*{section.instruction}*")

        # Render main content
        if section.template:
            try:
                # Use Jinja2 template engine for variable substitution
                rendered_template = jinja_render(
                    section.template,
                    variables
                )
                content_parts.append(rendered_template)
            except Exception as e:
                logger.warning(f"Variable substitution failed in section '{section.id}': {str(e)}")
                # Fallback to original template content
                content_parts.append(section.template)
                content_parts.append(f"*[Template rendering error: {str(e)}]*")

        # Render subsections
        if section.sections:
            subsection_content = self._render_template_sections(
                section.sections,
                variables,
                context
            )
            if subsection_content:
                content_parts.append(subsection_content)

        return "\n\n".join(content_parts)

    def _format_output(
        self,
        content: str,
        output_format: TemplateOutputFormat,
        template: TemplateDefinition,
        variables: Dict[str, Any]
    ) -> str:
        """
        Format rendered content according to output format.

        Args:
            content: Raw rendered content
            output_format: Desired output format
            template: Template definition
            variables: Template variables

        Returns:
            Formatted content
        """
        if output_format == TemplateOutputFormat.MARKDOWN:
            return self._format_markdown(content, template, variables)
        elif output_format == TemplateOutputFormat.HTML:
            return self._format_html(content, template, variables)
        elif output_format == TemplateOutputFormat.JSON:
            return self._format_json(content, template, variables)
        elif output_format == TemplateOutputFormat.YAML:
            return self._format_yaml(content, template, variables)
        else:
            return content

    def _format_markdown(
        self,
        content: str,
        template: TemplateDefinition,
        variables: Dict[str, Any]
    ) -> str:
        """Format content as Markdown."""
        lines = []

        # Add title
        if template.output.title:
            try:
                title = self.yaml_parser.substitute_variables_in_template(
                    template.output.title,
                    variables
                )
                lines.append(f"# {title}")
                lines.append("")
            except VariableSubstitutionError:
                lines.append(f"# {template.name}")
                lines.append("")

        # Add metadata header
        lines.append("---")
        lines.append(f"template: {template.id}")
        lines.append(f"version: {template.version}")
        lines.append(f"generated: {datetime.now(timezone.utc).isoformat()}")
        lines.append("---")
        lines.append("")

        # Add content
        lines.append(content)

        return "\n".join(lines)

    def _format_html(
        self,
        content: str,
        template: TemplateDefinition,
        variables: Dict[str, Any]
    ) -> str:
        """Format content as HTML."""
        # Basic HTML formatting - can be enhanced
        html_content = content.replace("\n", "<br>\n")
        html_content = f"<h1>{template.name}</h1>\n\n{html_content}"

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{template.name}</title>
    <meta charset="utf-8">
</head>
<body>
{html_content}
</body>
</html>"""

    def _format_json(
        self,
        content: str,
        template: TemplateDefinition,
        variables: Dict[str, Any]
    ) -> str:
        """Format content as JSON."""
        import json

        data = {
            "template": template.id,
            "name": template.name,
            "version": template.version,
            "generated": datetime.now(timezone.utc).isoformat(),
            "variables": variables,
            "content": content
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def _format_yaml(
        self,
        content: str,
        template: TemplateDefinition,
        variables: Dict[str, Any]
    ) -> str:
        """Format content as YAML."""
        import yaml

        data = {
            "template": template.id,
            "name": template.name,
            "version": template.version,
            "generated": datetime.now(timezone.utc).isoformat(),
            "variables": variables,
            "content": content
        }

        return yaml.dump(data, default_flow_style=False, allow_unicode=True)

    def _template_to_string(self, template: TemplateDefinition) -> str:
        """Convert template to string representation for variable extraction."""
        # Simple conversion - extract all text content from template
        content_parts = []

        def extract_text(section: TemplateSection):
            if section.template:
                content_parts.append(section.template)
            if section.item_template:
                content_parts.append(section.item_template)
            for subsection in section.sections:
                extract_text(subsection)

        for section in template.sections:
            extract_text(section)

        return "\n".join(content_parts)

    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return [fmt.value for fmt in TemplateOutputFormat]

    def estimate_rendering_complexity(self, template: TemplateDefinition) -> Dict[str, Any]:
        """
        Estimate rendering complexity for a template.

        Args:
            template: Template to analyze

        Returns:
            Dictionary with complexity metrics
        """
        total_sections = len(template.sections)
        nested_sections = sum(1 for section in template.sections if section.sections)
        template_content_length = len(self._template_to_string(template))

        return {
            "total_sections": total_sections,
            "nested_sections": nested_sections,
            "template_content_length": template_content_length,
            "complexity_score": template.estimate_complexity(),
            "estimated_render_time_ms": total_sections * 10 + template_content_length * 0.01
        }