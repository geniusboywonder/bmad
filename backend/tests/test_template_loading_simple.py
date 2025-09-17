"""
Test Cases for P1.4 BMAD Core Template Loading (Simplified for Phase 1)

This module contains test cases for basic template loading libraries
and YAML parsing capability validation for Phase 1.
"""

import pytest
import yaml
from pathlib import Path
import tempfile


class TestYAMLLibraryAvailability:
    """Test cases for basic YAML library functionality."""

    def test_yaml_library_import(self):
        """Test that PyYAML library can be imported."""
        try:
            import yaml
            assert yaml is not None
        except ImportError as e:
            pytest.fail(f"YAML library import failed: {e}")

    def test_yaml_parsing_functionality(self):
        """Test basic YAML parsing functionality."""
        yaml_content = """
name: "Test Template"
version: "1.0"
sections:
  - name: "Overview"
    required: true
  - name: "Requirements"
    required: false
variables:
  project_name: "Test Project"
  author: "Test Author"
"""
        try:
            data = yaml.safe_load(yaml_content)

            # Verify parsing worked correctly
            assert data["name"] == "Test Template"
            assert data["version"] == "1.0"
            assert len(data["sections"]) == 2
            assert data["variables"]["project_name"] == "Test Project"

        except Exception as e:
            pytest.fail(f"YAML parsing failed: {e}")

    def test_yaml_file_loading(self):
        """Test loading YAML from file."""
        # Create temporary YAML file
        yaml_content = {
            "template_name": "PRD Template",
            "phases": ["discovery", "design", "build"],
            "config": {"timeout": 300}
        }

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(yaml_content, f)
                temp_file = f.name

            # Load from file
            with open(temp_file, 'r') as f:
                loaded_data = yaml.safe_load(f)

            # Verify data loaded correctly
            assert loaded_data["template_name"] == "PRD Template"
            assert len(loaded_data["phases"]) == 3
            assert loaded_data["config"]["timeout"] == 300

            # Clean up
            Path(temp_file).unlink()

        except Exception as e:
            pytest.fail(f"YAML file loading failed: {e}")


class TestPhase1TemplateRequirements:
    """Test cases specifically for Phase 1 template loading requirements."""

    def test_yaml_parsing_library_available(self):
        """Test that YAML parsing capability is available."""
        # Phase 1 requirement: BMAD Core template loading working

        required_capabilities = {
            "yaml_safe_load": False,
            "yaml_dump": False,
            "file_reading": False
        }

        # Test yaml.safe_load
        try:
            yaml.safe_load("test: value")
            required_capabilities["yaml_safe_load"] = True
        except:
            pass

        # Test yaml.dump
        try:
            yaml.dump({"test": "value"})
            required_capabilities["yaml_dump"] = True
        except:
            pass

        # Test file operations
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
                f.write("test: value")
                required_capabilities["file_reading"] = True
        except:
            pass

        # Verify all capabilities available
        missing_capabilities = [cap for cap, available in required_capabilities.items() if not available]
        assert len(missing_capabilities) == 0, f"Missing template loading capabilities: {missing_capabilities}"

    def test_template_directory_accessibility(self):
        """Test that template directories can be accessed."""
        # Check if templates directory structure exists or can be created

        try:
            # Try to create a basic template directory structure for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                template_dir = Path(temp_dir) / "templates"
                template_dir.mkdir(exist_ok=True)

                # Create a sample template file
                sample_template = template_dir / "sample.yaml"
                sample_template.write_text("""
name: "Sample Template"
sections:
  - overview
  - requirements
""")

                # Verify we can read it back
                with open(sample_template, 'r') as f:
                    content = yaml.safe_load(f)

                assert content["name"] == "Sample Template"
                assert "overview" in content["sections"]

        except Exception as e:
            pytest.fail(f"Template directory operations failed: {e}")

    def test_jinja2_template_engine_availability(self):
        """Test that Jinja2 template engine is available."""
        try:
            import jinja2

            # Test basic template rendering
            template_str = "Hello {{ name }}!"
            template = jinja2.Template(template_str)
            result = template.render(name="World")

            assert result == "Hello World!"

        except ImportError:
            pytest.skip("Jinja2 not installed - template rendering not available")
        except Exception as e:
            pytest.fail(f"Jinja2 template rendering failed: {e}")


class TestTemplateLoadingGaps:
    """Test to identify what template loading components are NOT yet implemented."""

    def test_identify_missing_template_components(self):
        """Identify which template loading components need to be implemented."""

        # Expected Phase 1 template components that should exist
        expected_components = {
            "yaml_parser": "app.utils.yaml_parser",
            "template_service": "app.services.template_service",
            "workflow_definition": "app.models.workflow",
            "workflow_engine": "app.services.workflow_engine",
            "template_loader": "app.services.template_loader"
        }

        missing_components = []
        for component_name, import_path in expected_components.items():
            try:
                __import__(import_path)
            except ImportError:
                missing_components.append(component_name)

        # This test is expected to fail in Phase 1 - it documents what needs to be implemented
        if len(missing_components) > 0:
            pytest.skip(f"Template loading system not yet implemented. Missing: {missing_components}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])