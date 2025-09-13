"""
Template Data Models for BMAD Core Template System

This module defines Pydantic models for document templates and their sections.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TemplateSectionType(str, Enum):
    """Enumeration of supported template section types."""
    PARAGRAPHS = "paragraphs"
    BULLET_LIST = "bullet-list"
    NUMBERED_LIST = "numbered-list"
    TABLE = "table"
    CODE_BLOCK = "code-block"
    HEADING = "heading"
    QUOTE = "quote"
    CHECKLIST = "checklist"


class TemplateOutputFormat(str, Enum):
    """Enumeration of supported output formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    YAML = "yaml"
    PLAIN_TEXT = "plain_text"


class TemplateWorkflowMode(str, Enum):
    """Enumeration of template workflow modes."""
    INTERACTIVE = "interactive"
    AUTOMATED = "automated"
    HYBRID = "hybrid"


class TemplateSection(BaseModel):
    """
    Represents a section within a document template.

    This model defines the structure of individual template sections including
    their type, content requirements, and hierarchical relationships.
    """
    id: str = Field("", description="Unique identifier for the section")
    title: str = Field("", description="Human-readable title of the section")
    type: TemplateSectionType = Field(default=TemplateSectionType.PARAGRAPHS, description="Type of section content")
    instruction: str = Field("", description="Instructions for filling out this section")
    sections: List['TemplateSection'] = Field(default_factory=list, description="Nested subsections")
    repeatable: bool = Field(False, description="Whether this section can be repeated")
    template: str = Field("", description="Template string with variable placeholders")
    elicit: bool = Field(False, description="Whether this section requires user input")
    choices: Dict[str, Any] = Field(default_factory=dict, description="Predefined choices for user selection")
    prefix: str = Field("", description="Prefix to add to each item (e.g., 'FR' for functional requirements)")
    examples: List[str] = Field(default_factory=list, description="Example content for this section")
    condition: Optional[str] = Field(None, description="Conditional rendering criteria")
    item_template: Optional[str] = Field(None, description="Template for individual list/table items")
    columns: List[str] = Field(default_factory=list, description="Column headers for table sections")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_required_variables(self) -> List[str]:
        """Extract all required variables from this section and its subsections."""
        variables = []

        # Extract from main template
        if self.template:
            variables.extend(self._extract_variables_from_text(self.template))

        # Extract from item template
        if self.item_template:
            variables.extend(self._extract_variables_from_text(self.item_template))

        # Extract from subsections recursively
        for subsection in self.sections:
            variables.extend(subsection.get_required_variables())

        return list(set(variables))  # Remove duplicates

    def _extract_variables_from_text(self, text: str) -> List[str]:
        """Extract variable names from template text using {{variable}} pattern."""
        import re
        pattern = re.compile(r'\{\{([^}]+)\}\}')
        matches = pattern.findall(text)
        return [match.strip() for match in matches]

    def validate_section(self) -> List[str]:
        """
        Validate this section for consistency and completeness.

        Returns:
            List of validation error messages
        """
        errors = []

        if not self.id and self.title:
            errors.append(f"Section '{self.title}' is missing an ID")

        if self.type == TemplateSectionType.TABLE and not self.columns:
            errors.append(f"Table section '{self.id}' must define columns")

        if self.type in [TemplateSectionType.BULLET_LIST, TemplateSectionType.NUMBERED_LIST] and not self.item_template:
            errors.append(f"List section '{self.id}' should define an item_template")

        if self.repeatable and not self.item_template:
            errors.append(f"Repeatable section '{self.id}' should define an item_template")

        # Validate subsections recursively
        for subsection in self.sections:
            errors.extend(subsection.validate_section())

        return errors

    def is_conditional(self) -> bool:
        """Check if this section has conditional rendering."""
        return self.condition is not None

    def should_render(self, context: Dict[str, Any]) -> bool:
        """Determine if this section should be rendered based on context."""
        if not self.condition:
            return True

        # Simple condition evaluation - can be extended for complex logic
        try:
            # For now, support simple variable existence checks
            if self.condition.startswith("variable_exists:"):
                var_name = self.condition.split(":", 1)[1].strip()
                return var_name in context
            elif self.condition.startswith("variable_equals:"):
                parts = self.condition.split(":", 2)
                if len(parts) >= 3:
                    var_name = parts[1].strip()
                    expected_value = parts[2].strip()
                    return context.get(var_name) == expected_value

            # Default to True if condition format is not recognized
            return True
        except Exception:
            # If condition evaluation fails, default to rendering
            return True


class TemplateOutput(BaseModel):
    """
    Defines the output configuration for a template.

    This model specifies how the rendered template should be formatted and saved.
    """
    format: TemplateOutputFormat = Field(default=TemplateOutputFormat.MARKDOWN, description="Output format")
    filename: str = Field("", description="Output filename with variables")
    title: str = Field("", description="Document title with variables")
    directory: str = Field("", description="Output directory path")
    encoding: str = Field("utf-8", description="File encoding for output")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TemplateWorkflow(BaseModel):
    """
    Defines workflow configuration for template processing.

    This model specifies how the template should be processed in a workflow context.
    """
    mode: TemplateWorkflowMode = Field(default=TemplateWorkflowMode.INTERACTIVE, description="Workflow processing mode")
    elicitation: str = Field("", description="Elicitation method to use")
    agent_sequence: List[str] = Field(default_factory=list, description="Sequence of agents for processing")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules for the template")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TemplateDefinition(BaseModel):
    """
    Complete template definition loaded from YAML.

    This model represents a complete document template with all its sections,
    output configuration, workflow settings, and metadata.
    """
    id: str = Field(..., description="Unique identifier for the template")
    name: str = Field(..., description="Human-readable name of the template")
    version: str = Field("1.0", description="Version of the template")
    description: str = Field("", description="Detailed description of the template")
    output: TemplateOutput = Field(default_factory=TemplateOutput, description="Output configuration")
    workflow: TemplateWorkflow = Field(default_factory=TemplateWorkflow, description="Workflow configuration")
    sections: List[TemplateSection] = Field(default_factory=list, description="Template sections")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            TemplateSectionType: lambda v: v.value,
            TemplateOutputFormat: lambda v: v.value,
            TemplateWorkflowMode: lambda v: v.value,
            TemplateSection: lambda v: v.model_dump(),
            TemplateOutput: lambda v: v.model_dump(),
            TemplateWorkflow: lambda v: v.model_dump(),
            dict: lambda v: v,
            list: lambda v: v
        }
    )

    def get_all_required_variables(self) -> List[str]:
        """Get all required variables from all sections."""
        variables = []
        for section in self.sections:
            variables.extend(section.get_required_variables())
        return list(set(variables))  # Remove duplicates

    def validate_template(self) -> List[str]:
        """
        Validate the entire template for consistency and completeness.

        Returns:
            List of validation error messages
        """
        errors = []

        if not self.id:
            errors.append("Template is missing an ID")

        if not self.name:
            errors.append("Template is missing a name")

        if not self.sections:
            errors.append("Template must have at least one section")

        # Validate output configuration
        if self.output.filename and not self.output.filename.endswith(('.md', '.html', '.json', '.yaml', '.txt')):
            errors.append("Output filename should have appropriate extension")

        # Validate all sections
        for section in self.sections:
            errors.extend(section.validate_section())

        # Check for duplicate section IDs
        section_ids = []
        for section in self.sections:
            self._collect_section_ids(section, section_ids)

        if len(section_ids) != len(set(section_ids)):
            errors.append("Duplicate section IDs found in template")

        return errors

    def _collect_section_ids(self, section: TemplateSection, ids: List[str]):
        """Recursively collect all section IDs."""
        if section.id:
            ids.append(section.id)
        for subsection in section.sections:
            self._collect_section_ids(subsection, ids)

    def get_section_by_id(self, section_id: str) -> Optional[TemplateSection]:
        """Find a section by its ID."""
        for section in self.sections:
            result = self._find_section_by_id(section, section_id)
            if result:
                return result
        return None

    def _find_section_by_id(self, section: TemplateSection, section_id: str) -> Optional[TemplateSection]:
        """Recursively find a section by ID."""
        if section.id == section_id:
            return section

        for subsection in section.sections:
            result = self._find_section_by_id(subsection, section_id)
            if result:
                return result

        return None

    def get_sections_by_type(self, section_type: TemplateSectionType) -> List[TemplateSection]:
        """Get all sections of a specific type."""
        sections = []
        for section in self.sections:
            self._collect_sections_by_type(section, section_type, sections)
        return sections

    def _collect_sections_by_type(self, section: TemplateSection, section_type: TemplateSectionType, results: List[TemplateSection]):
        """Recursively collect sections by type."""
        if section.type == section_type:
            results.append(section)

        for subsection in section.sections:
            self._collect_sections_by_type(subsection, section_type, results)

    def get_elicitation_sections(self) -> List[TemplateSection]:
        """Get all sections that require user elicitation."""
        sections = []
        for section in self.sections:
            self._collect_elicitation_sections(section, sections)
        return sections

    def _collect_elicitation_sections(self, section: TemplateSection, results: List[TemplateSection]):
        """Recursively collect sections requiring elicitation."""
        if section.elicit:
            results.append(section)

        for subsection in section.sections:
            self._collect_elicitation_sections(subsection, results)

    def estimate_complexity(self) -> Dict[str, Any]:
        """
        Estimate the complexity of filling out this template.

        Returns:
            Dictionary with complexity metrics
        """
        total_sections = 0
        elicitation_sections = 0
        conditional_sections = 0
        repeatable_sections = 0

        for section in self.sections:
            metrics = self._calculate_section_metrics(section)
            total_sections += metrics['total_sections']
            elicitation_sections += metrics['elicitation_sections']
            conditional_sections += metrics['conditional_sections']
            repeatable_sections += metrics['repeatable_sections']

        return {
            'total_sections': total_sections,
            'elicitation_sections': elicitation_sections,
            'conditional_sections': conditional_sections,
            'repeatable_sections': repeatable_sections,
            'complexity_score': self._calculate_complexity_score(
                total_sections, elicitation_sections, conditional_sections, repeatable_sections
            )
        }

    def _calculate_section_metrics(self, section: TemplateSection) -> Dict[str, int]:
        """Calculate metrics for a section and its subsections."""
        metrics = {
            'total_sections': 1,
            'elicitation_sections': 1 if section.elicit else 0,
            'conditional_sections': 1 if section.is_conditional() else 0,
            'repeatable_sections': 1 if section.repeatable else 0
        }

        for subsection in section.sections:
            sub_metrics = self._calculate_section_metrics(subsection)
            for key in metrics:
                metrics[key] += sub_metrics[key]

        return metrics

    def _calculate_complexity_score(self, total: int, elicitation: int, conditional: int, repeatable: int) -> str:
        """Calculate a complexity score based on template metrics."""
        score = total + (elicitation * 2) + (conditional * 1.5) + (repeatable * 1.5)

        if score < 5:
            return "Low"
        elif score < 15:
            return "Medium"
        elif score < 25:
            return "High"
        else:
            return "Very High"
