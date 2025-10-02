"""
YAML Parser Utilities for BMAD Core Template System

This module provides robust YAML parsing with validation, error handling,
and variable substitution capabilities for workflow and template files.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic_core import PydanticCustomError


class ParserError(Exception):
    """Base exception for YAML parser errors."""
    pass


class ValidationError(ParserError):
    """Raised when YAML validation fails."""
    pass


class FileNotFoundError(ParserError):
    """Raised when YAML file is not found."""
    pass


class ParseError(ParserError):
    """Raised when YAML parsing fails."""
    pass


class TemplateError(ParserError):
    """Raised when template processing fails."""
    pass


class VariableSubstitutionError(TemplateError):
    """Raised when variable substitution fails."""
    pass


@dataclass
class ValidationResult:
    """Result of YAML validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class ParseResult:
    """Result of YAML parsing."""
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    validation_result: ValidationResult


class VariableSubstitutionEngine:
    """Engine for handling variable substitution in templates."""

    VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

    @staticmethod
    def substitute_variables(template_str: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables in template string.

        Args:
            template_str: Template string with {{variable}} placeholders
            variables: Dictionary of variable values

        Returns:
            String with variables substituted

        Raises:
            VariableSubstitutionError: If substitution fails
        """
        try:
            def replace_var(match):
                var_name = match.group(1).strip()
                if var_name not in variables:
                    raise VariableSubstitutionError(f"Undefined variable: {var_name}")
                value = variables[var_name]
                if value is None:
                    return ""
                return str(value)

            return VariableSubstitutionEngine.VARIABLE_PATTERN.sub(replace_var, template_str)

        except Exception as e:
            raise VariableSubstitutionError(f"Variable substitution failed: {str(e)}")

    @staticmethod
    def extract_variables(template_str: str) -> List[str]:
        """
        Extract all variable names from template string.

        Args:
            template_str: Template string with {{variable}} placeholders

        Returns:
            List of variable names found in template
        """
        matches = VariableSubstitutionEngine.VARIABLE_PATTERN.findall(template_str)
        return [match.strip() for match in matches]

    @staticmethod
    def validate_variables(template_str: str, variables: Dict[str, Any]) -> ValidationResult:
        """
        Validate that all required variables are provided.

        Args:
            template_str: Template string with {{variable}} placeholders
            variables: Dictionary of variable values

        Returns:
            ValidationResult with any missing variables
        """
        required_vars = VariableSubstitutionEngine.extract_variables(template_str)
        missing_vars = [var for var in required_vars if var not in variables]

        errors = []
        warnings = []

        if missing_vars:
            errors.append(f"Missing required variables: {', '.join(missing_vars)}")

        # Check for unused variables
        provided_vars = set(variables.keys())
        used_vars = set(required_vars)
        unused_vars = provided_vars - used_vars

        if unused_vars:
            warnings.append(f"Unused variables provided: {', '.join(unused_vars)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class SchemaValidator:
    """Schema validation for YAML files."""

    WORKFLOW_SCHEMA = {
        "type": "object",
        "required": ["workflow"],
        "properties": {
            "workflow": {
                "type": "object",
                "required": ["id", "name", "sequence"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "type": {"type": "string"},
                    "sequence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["agent"],
                            "properties": {
                                "agent": {"type": "string"},
                                "creates": {"type": "string"},
                                "requires": {"type": ["string", "array"]},
                                "condition": {"type": "string"},
                                "notes": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }

    TEMPLATE_SCHEMA = {
        "type": "object",
        "required": ["template"],
        "properties": {
            "template": {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "version": {"type": "string"},
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "type": {"type": "string"},
                                "instruction": {"type": "string"},
                                "sections": {"type": "array"}
                            }
                        }
                    }
                }
            }
        }
    }

    @staticmethod
    def validate_workflow(data: Dict[str, Any]) -> ValidationResult:
        """Validate workflow YAML against schema."""
        return SchemaValidator._validate_data(data, SchemaValidator.WORKFLOW_SCHEMA, "workflow")

    @staticmethod
    def validate_template(data: Dict[str, Any]) -> ValidationResult:
        """Validate template YAML against schema."""
        return SchemaValidator._validate_data(data, SchemaValidator.TEMPLATE_SCHEMA, "template")

    @staticmethod
    def _validate_data(data: Dict[str, Any], schema: Dict[str, Any], data_type: str) -> ValidationResult:
        """Generic validation method."""
        errors = []
        warnings = []

        # Basic structure validation
        if not isinstance(data, dict):
            errors.append(f"Root must be a dictionary, got {type(data)}")
            return ValidationResult(False, errors, warnings)

        if data_type not in data:
            errors.append(f"Missing required '{data_type}' section")
            return ValidationResult(False, errors, warnings)

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate workflow/template structure
        if data_type in data:
            section_data = data[data_type]
            section_schema = schema["properties"][data_type]

            # Check required section fields
            section_required = section_schema.get("required", [])
            for field in section_required:
                if field not in section_data:
                    errors.append(f"Missing required {data_type} field: {field}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class YAMLParser:
    """
    Robust YAML parser with validation and error handling.

    Features:
    - Schema validation for workflows and templates
    - Comprehensive error handling with detailed messages
    - Variable substitution support
    - Metadata extraction
    - File existence and permission checking
    """

    def __init__(self):
        self.validator = SchemaValidator()
        self.variable_engine = VariableSubstitutionEngine()

    def load_workflow(self, file_path: Union[str, Path]) -> 'WorkflowDefinition':
        """
        Load and validate a workflow YAML file.

        Args:
            file_path: Path to the workflow YAML file

        Returns:
            WorkflowDefinition object

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If YAML parsing fails
            ValidationError: If validation fails
        """
        data = self._load_yaml_file(file_path)
        validation_result = self.validator.validate_workflow(data)

        if not validation_result.is_valid:
            raise ValidationError(f"Workflow validation failed: {'; '.join(validation_result.errors)}")

        return self._parse_workflow_data(data)

    def load_template(self, file_path: Union[str, Path]) -> 'TemplateDefinition':
        """
        Load and validate a template YAML file.

        Args:
            file_path: Path to the template YAML file

        Returns:
            TemplateDefinition object

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If YAML parsing fails
            ValidationError: If validation fails
        """
        data = self._load_yaml_file(file_path)
        validation_result = self.validator.validate_template(data)

        if not validation_result.is_valid:
            raise ValidationError(f"Template validation failed: {'; '.join(validation_result.errors)}")

        return self._parse_template_data(data)

    def substitute_variables_in_template(self, template_str: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables in a template string.

        Args:
            template_str: Template string with {{variable}} placeholders
            variables: Dictionary of variable values

        Returns:
            String with variables substituted

        Raises:
            VariableSubstitutionError: If substitution fails
        """
        return self.variable_engine.substitute_variables(template_str, variables)

    def validate_template_variables(self, template_str: str, variables: Dict[str, Any]) -> ValidationResult:
        """
        Validate variables for a template string.

        Args:
            template_str: Template string with {{variable}} placeholders
            variables: Dictionary of variable values

        Returns:
            ValidationResult with validation status
        """
        return self.variable_engine.validate_variables(template_str, variables)

    def _load_yaml_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load and parse YAML file with error handling.

        Args:
            file_path: Path to the YAML file

        Returns:
            Parsed YAML data as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If YAML parsing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")

        if not file_path.is_file():
            raise FileNotFoundError(f"Path is not a file: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                raise ParseError(f"YAML file is empty: {file_path}")

            if not isinstance(data, dict):
                raise ParseError(f"YAML root must be a dictionary, got {type(data)}: {file_path}")

            return data

        except yaml.YAMLError as e:
            raise ParseError(f"YAML parsing failed for {file_path}: {str(e)}")
        except PermissionError:
            raise ParseError(f"Permission denied reading {file_path}")
        except Exception as e:
            raise ParseError(f"Unexpected error reading {file_path}: {str(e)}")

    def _parse_workflow_data(self, data: Dict[str, Any]) -> 'WorkflowDefinition':
        """Parse workflow data into WorkflowDefinition object."""
        workflow_data = data.get('workflow', {})

        # Extract metadata
        metadata = {
            'file_version': data.get('version', '1.0'),
            'last_modified': data.get('last_modified'),
            'author': data.get('author')
        }

        # Parse sequence
        sequence = []
        for step_data in workflow_data.get('sequence', []):
            step = WorkflowStep(
                agent=step_data.get('agent'),  # Make agent optional for non-agent steps
                creates=step_data.get('creates'),
                requires=step_data.get('requires', []),
                condition=step_data.get('condition'),
                notes=step_data.get('notes'),
                optional_steps=step_data.get('optional_steps', []),
                action=step_data.get('action'),
                repeatable=step_data.get('repeatable', False)
            )
            sequence.append(step)

        return WorkflowDefinition(
            id=workflow_data['id'],
            name=workflow_data['name'],
            description=workflow_data.get('description', ''),
            type=workflow_data.get('type', 'generic'),
            project_types=workflow_data.get('project_types', []),
            sequence=sequence,
            flow_diagram=workflow_data.get('flow_diagram', ''),
            decision_guidance=workflow_data.get('decision_guidance', {}),
            handoff_prompts=workflow_data.get('handoff_prompts', {}),
            metadata=metadata
        )

    def _parse_template_data(self, data: Dict[str, Any]) -> 'TemplateDefinition':
        """Parse template data into TemplateDefinition object."""
        template_data = data.get('template', {})

        # Extract metadata
        metadata = {
            'file_version': data.get('version', '1.0'),
            'last_modified': data.get('last_modified'),
            'author': data.get('author')
        }

        # Parse sections recursively
        sections = self._parse_sections(template_data.get('sections', []))

        return TemplateDefinition(
            id=template_data['id'],
            name=template_data['name'],
            version=template_data.get('version', '1.0'),
            output=template_data.get('output', {}),
            workflow=template_data.get('workflow', {}),
            sections=sections,
            metadata=metadata
        )

    def _parse_sections(self, sections_data: List[Dict[str, Any]]) -> List['TemplateSection']:
        """Recursively parse template sections."""
        sections = []

        for section_data in sections_data:
            # Parse subsections recursively
            subsections = self._parse_sections(section_data.get('sections', []))

            section = TemplateSection(
                id=section_data.get('id', ''),
                title=section_data.get('title', ''),
                type=section_data.get('type', 'paragraphs'),
                instruction=section_data.get('instruction', ''),
                sections=subsections,
                repeatable=section_data.get('repeatable', False),
                template=section_data.get('template', ''),
                elicit=section_data.get('elicit', False),
                choices=section_data.get('choices', {}),
                prefix=section_data.get('prefix', ''),
                examples=section_data.get('examples', []),
                condition=section_data.get('condition'),
                item_template=section_data.get('item_template'),
                columns=section_data.get('columns', [])
            )
            sections.append(section)

        return sections


# Forward declarations for type hints
class WorkflowStep(BaseModel):
    """Represents a single step in a workflow."""
    agent: Optional[str] = None  # Make optional for non-agent workflow steps
    creates: Optional[str] = None
    requires: Union[str, List[str]] = Field(default_factory=list)
    condition: Optional[str] = None
    notes: Optional[str] = None
    optional_steps: List[str] = Field(default_factory=list)
    action: Optional[str] = None
    repeatable: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""
    id: str
    name: str
    description: str = ""
    type: str = "generic"
    project_types: List[str] = Field(default_factory=list)
    sequence: List[WorkflowStep] = Field(default_factory=list)
    flow_diagram: str = ""
    decision_guidance: Dict[str, Any] = Field(default_factory=dict)
    handoff_prompts: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TemplateSection(BaseModel):
    """Represents a section in a template."""
    id: str = ""
    title: str = ""
    type: str = "paragraphs"
    instruction: str = ""
    sections: List['TemplateSection'] = Field(default_factory=list)
    repeatable: bool = False
    template: str = ""
    elicit: bool = False
    choices: Dict[str, Any] = Field(default_factory=dict)
    prefix: str = ""
    examples: List[str] = Field(default_factory=list)
    condition: Optional[str] = None
    item_template: Optional[str] = None
    columns: List[str] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TemplateDefinition(BaseModel):
    """Complete template definition."""
    id: str
    name: str
    version: str = "1.0"
    output: Dict[str, Any] = Field(default_factory=dict)
    workflow: Dict[str, Any] = Field(default_factory=dict)
    sections: List[TemplateSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)
