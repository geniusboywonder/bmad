"""
Template Renderer - Handles template rendering and output formatting.

Responsible for rendering templates with variable substitution and formatting
output in various formats (Markdown, HTML, JSON, YAML).
Implements TR-11: Document template processing from backend/app/templates/.
Implements TR-13: Variable substitution and conditional logic support.
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from jinja2 import Template, Environment, meta

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

        # BMAD Core template paths (TR-11)
        # Handle both project root and backend directory contexts
        if Path("backend/app").exists():
            self.bmad_core_path = Path("backend/app")
        else:
            self.bmad_core_path = Path("app")
        self.templates_path = self.bmad_core_path / "templates"

        # Jinja2 environment for advanced template processing (TR-13)
        self.jinja_env = Environment(
            trim_blocks=True,
            lstrip_blocks=True
        )

        logger.info("Template renderer initialized",
                   bmad_core_path=str(self.bmad_core_path),
                   templates_path=str(self.templates_path))

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

    def process_document_template(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> str:
        """Process document template with variable substitution and conditional logic (TR-11, TR-13)."""

        template_path = self.templates_path / f"{template_name}.yaml"

        if not template_path.exists():
            raise FileNotFoundError(f"BMAD Core template not found: {template_path}")

        logger.info("Processing BMAD Core document template",
                   template_name=template_name,
                   template_path=str(template_path))

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)

            # Process template with Jinja2 for variable substitution
            content = template_data.get('content', '')
            if isinstance(content, dict):
                # Handle structured template content
                processed_content = self._process_structured_template(content, variables)
            else:
                # Handle simple text template
                processed_content = self._process_conditional_logic(content, variables)

            result = {
                "template_name": template_name,
                "processed_content": processed_content,
                "variables_used": self._extract_template_variables(content),
                "processing_metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "variables_provided": list(variables.keys()),
                    "template_type": "bmad_core_document"
                }
            }

            logger.info("BMAD Core template processed successfully",
                       template_name=template_name,
                       content_length=len(processed_content))

            return processed_content

        except Exception as e:
            logger.error("Failed to process BMAD Core template",
                        template_name=template_name,
                        error=str(e))
            raise

    def _process_conditional_logic(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Process conditional logic within templates using Jinja2 (TR-13)."""

        try:
            template = self.jinja_env.from_string(template_content)

            # Add custom filters and functions for BMAD Core
            self.jinja_env.filters.update({
                'format_date': self._format_date_filter,
                'to_title_case': self._to_title_case_filter,
                'markdown_list': self._markdown_list_filter
            })

            # Add global functions
            template.globals.update({
                'now': datetime.now,
                'len': len,
                'enumerate': enumerate
            })

            rendered_content = template.render(**variables)

            logger.debug("Template conditional logic processed",
                        original_length=len(template_content),
                        rendered_length=len(rendered_content))

            return rendered_content

        except Exception as e:
            logger.error("Conditional logic processing failed",
                        error=str(e),
                        template_content=template_content[:100] + "..." if len(template_content) > 100 else template_content)
            # Return original content as fallback
            return template_content

    def _process_structured_template(self, template_structure: Dict[str, Any], variables: Dict[str, Any]) -> str:
        """Process structured template with sections and conditional blocks."""

        processed_sections = []

        for section_name, section_content in template_structure.items():
            if isinstance(section_content, dict):
                # Handle conditional sections
                if 'condition' in section_content:
                    condition = section_content['condition']
                    if self._evaluate_condition(condition, variables):
                        content = section_content.get('content', '')
                        processed_content = self._process_conditional_logic(content, variables)
                        processed_sections.append(f"## {section_name}\n\n{processed_content}")
                else:
                    # Regular section
                    content = section_content.get('content', str(section_content))
                    processed_content = self._process_conditional_logic(content, variables)
                    processed_sections.append(f"## {section_name}\n\n{processed_content}")
            else:
                # Simple content
                processed_content = self._process_conditional_logic(str(section_content), variables)
                processed_sections.append(f"## {section_name}\n\n{processed_content}")

        return "\n\n".join(processed_sections)

    def _evaluate_condition(self, condition: str, variables: Dict[str, Any]) -> bool:
        """Evaluate conditional expressions safely."""

        try:
            # Create a safe evaluation environment
            template = self.jinja_env.from_string(f"{{{{ {condition} }}}}")
            result = template.render(**variables)

            # Convert string result to boolean
            if isinstance(result, str):
                return result.lower() in ('true', '1', 'yes', 'on')
            return bool(result)

        except Exception as e:
            logger.warning("Condition evaluation failed",
                         condition=condition,
                         error=str(e))
            return False

    def _extract_template_variables(self, template_content: str) -> List[str]:
        """Extract variable names used in template."""

        try:
            env = Environment()
            ast = env.parse(template_content)
            variables = meta.find_undeclared_variables(ast)
            return list(variables)

        except Exception as e:
            logger.warning("Variable extraction failed",
                         error=str(e))
            return []

    def _format_date_filter(self, date_value, format_string="%Y-%m-%d"):
        """Jinja2 filter for date formatting."""
        if isinstance(date_value, str):
            try:
                date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except ValueError:
                return date_value

        if isinstance(date_value, datetime):
            return date_value.strftime(format_string)
        return str(date_value)

    def _to_title_case_filter(self, text):
        """Jinja2 filter for title case conversion."""
        return str(text).title()

    def _markdown_list_filter(self, items, ordered=False):
        """Jinja2 filter for creating markdown lists."""
        if not items:
            return ""

        if ordered:
            return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
        else:
            return "\n".join(f"- {item}" for item in items)

    def load_bmad_template_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load all BMAD Core template definitions."""

        if not self.templates_path.exists():
            logger.warning("BMAD Core templates directory not found",
                         path=str(self.templates_path))
            return {}

        templates = {}
        templates_loaded = 0

        for template_file in self.templates_path.glob("*.yaml"):
            try:
                template_name = template_file.stem
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = yaml.safe_load(f)

                # Extract template metadata
                metadata = {
                    "name": template_name,
                    "description": template_data.get("description", ""),
                    "version": template_data.get("version", "1.0"),
                    "variables": self._extract_template_variables(
                        str(template_data.get("content", ""))
                    ),
                    "file_path": str(template_file),
                    "template_type": template_data.get("type", "document")
                }

                templates[template_name] = {
                    "metadata": metadata,
                    "definition": template_data
                }

                templates_loaded += 1

                logger.debug("Loaded BMAD template definition",
                           template_name=template_name,
                           variables_count=len(metadata["variables"]))

            except Exception as e:
                logger.error("Failed to load BMAD template definition",
                           file=str(template_file),
                           error=str(e))

        logger.info("BMAD Core template definitions loaded",
                   total_templates=templates_loaded,
                   template_names=list(templates.keys()))

        return templates

    def list_available_bmad_templates(self) -> List[Dict[str, Any]]:
        """List all available BMAD Core templates."""

        templates = self.load_bmad_template_definitions()
        template_list = []

        for name, template_info in templates.items():
            metadata = template_info["metadata"]
            template_summary = {
                "name": name,
                "description": metadata["description"],
                "version": metadata["version"],
                "variables_required": metadata["variables"],
                "template_type": metadata["template_type"],
                "file_path": metadata["file_path"]
            }
            template_list.append(template_summary)

        return template_list

    def validate_bmad_template(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate variables against BMAD Core template requirements."""

        try:
            templates = self.load_bmad_template_definitions()
            if template_name not in templates:
                return {
                    "is_valid": False,
                    "errors": [f"Template '{template_name}' not found"],
                    "warnings": []
                }

            template_info = templates[template_name]
            required_variables = template_info["metadata"]["variables"]
            provided_variables = list(variables.keys())

            missing_vars = [var for var in required_variables if var not in variables]
            unused_vars = [var for var in provided_variables if var not in required_variables]

            is_valid = len(missing_vars) == 0

            result = {
                "is_valid": is_valid,
                "errors": [f"Missing required variable: {var}" for var in missing_vars],
                "warnings": [f"Unused variable: {var}" for var in unused_vars],
                "template_name": template_name,
                "required_variables": required_variables,
                "provided_variables": provided_variables,
                "missing_variables": missing_vars,
                "unused_variables": unused_vars
            }

            logger.debug("BMAD template validation completed",
                       template_name=template_name,
                       is_valid=is_valid,
                       missing_count=len(missing_vars))

            return result

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": []
            }