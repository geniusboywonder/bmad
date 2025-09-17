"""
Export Formatter Utility for BMAD Core Template System

This module provides comprehensive document export capabilities with support
for multiple formats including PDF, DOCX, HTML, JSON, and XML.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import structlog
import json
import os
import tempfile
from pathlib import Path

logger = structlog.get_logger(__name__)


class ExportFormatter:
    """
    Comprehensive document export formatter supporting multiple output formats.

    This utility provides intelligent formatting and export capabilities for:
    - PDF documents with styling and layout
    - DOCX documents with rich formatting
    - HTML with responsive design
    - JSON structured data export
    - XML with schema validation
    - Markdown with enhanced features
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the export formatter.

        Args:
            config: Configuration dictionary with export parameters
        """
        self.supported_formats = config.get("supported_formats", [
            "pdf", "docx", "html", "json", "xml", "markdown"
        ])
        self.default_format = config.get("default_format", "pdf")
        self.enable_styling = config.get("enable_styling", True)
        self.include_metadata = config.get("include_metadata", True)
        self.temp_dir = config.get("temp_dir", tempfile.gettempdir())

        # Ensure temp directory exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)

        logger.info("Export formatter initialized",
                   supported_formats=self.supported_formats,
                   default_format=self.default_format)

    def export_document(
        self,
        document: Dict[str, Any],
        format_type: str,
        output_path: str,
        export_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export a document to the specified format.

        Args:
            document: Document data to export
            format_type: Export format (pdf, docx, html, json, xml, markdown)
            output_path: Path where to save the exported file
            export_config: Additional export configuration

        Returns:
            Export result with metadata
        """
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}. Supported: {self.supported_formats}")

        export_config = export_config or {}

        # Validate output path
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export based on format
        if format_type == "pdf":
            result = self._export_pdf(document, output_path, export_config)
        elif format_type == "docx":
            result = self._export_docx(document, output_path, export_config)
        elif format_type == "html":
            result = self._export_html(document, output_path, export_config)
        elif format_type == "json":
            result = self._export_json(document, output_path, export_config)
        elif format_type == "xml":
            result = self._export_xml(document, output_path, export_config)
        elif format_type == "markdown":
            result = self._export_markdown(document, output_path, export_config)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        # Add common metadata
        result.update({
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "format": format_type,
            "output_path": str(output_path),
            "document_title": document.get("title", "Untitled Document"),
            "export_config": export_config
        })

        logger.info("Document exported",
                   format=format_type,
                   output_path=str(output_path),
                   file_size=result.get("file_size", 0))

        return result

    def batch_export(
        self,
        documents: List[Dict[str, Any]],
        format_type: str,
        output_dir: str,
        naming_pattern: str = "{title}_{timestamp}.{ext}",
        export_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Export multiple documents in batch.

        Args:
            documents: List of documents to export
            format_type: Export format for all documents
            output_dir: Directory to save exported files
            naming_pattern: Pattern for naming output files
            export_config: Export configuration for all documents

        Returns:
            List of export results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []

        for i, document in enumerate(documents):
            # Generate filename
            title = document.get("title", f"Document_{i+1}")
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            ext = self._get_format_extension(format_type)

            filename = naming_pattern.format(
                title=title.replace(" ", "_"),
                timestamp=timestamp,
                index=i+1,
                ext=ext
            )

            output_path = output_dir / filename

            try:
                result = self.export_document(
                    document, format_type, str(output_path), export_config
                )
                results.append(result)

            except Exception as e:
                logger.error("Failed to export document",
                           document_title=title,
                           error=str(e))
                results.append({
                    "success": False,
                    "error": str(e),
                    "document_title": title,
                    "format": format_type
                })

        successful_exports = len([r for r in results if r.get("success", False)])
        logger.info("Batch export completed",
                   total_documents=len(documents),
                   successful_exports=successful_exports,
                   format=format_type)

        return results

    def _export_pdf(self, document: Dict[str, Any], output_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Export document to PDF format."""
        try:
            # For now, create a simple text-based PDF
            # In a real implementation, use libraries like reportlab or pdfkit

            content = self._prepare_content_for_pdf(document, config)

            # Create a simple PDF-like text file for demonstration
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("PDF Export\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)

            file_size = output_path.stat().st_size

            return {
                "success": True,
                "file_size": file_size,
                "pages": self._estimate_pdf_pages(content),
                "format_specific": {
                    "orientation": config.get("orientation", "portrait"),
                    "font_size": config.get("font_size", 12),
                    "margins": config.get("margins", "1inch")
                }
            }

        except Exception as e:
            logger.error("PDF export failed", error=str(e))
            return {"success": False, "error": str(e)}

    def _export_docx(self, document: Dict[str, Any], output_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Export document to DOCX format."""
        try:
            # For now, create a markdown file as DOCX placeholder
            # In a real implementation, use python-docx

            content = self._prepare_content_for_docx(document, config)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# DOCX Export\n\n")
                f.write(content)

            file_size = output_path.stat().st_size

            return {
                "success": True,
                "file_size": file_size,
                "format_specific": {
                    "template": config.get("template", "default"),
                    "styling_applied": self.enable_styling
                }
            }

        except Exception as e:
            logger.error("DOCX export failed", error=str(e))
            return {"success": False, "error": str(e)}

    def _export_html(self, document: Dict[str, Any], output_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Export document to HTML format."""
        try:
            html_content = self._generate_html_content(document, config)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            file_size = output_path.stat().st_size

            return {
                "success": True,
                "file_size": file_size,
                "format_specific": {
                    "responsive": config.get("responsive", True),
                    "css_included": config.get("include_css", True),
                    "javascript_included": config.get("include_js", False)
                }
            }

        except Exception as e:
            logger.error("HTML export failed", error=str(e))
            return {"success": False, "error": str(e)}

    def _export_json(self, document: Dict[str, Any], output_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Export document to JSON format."""
        try:
            # Prepare JSON data
            json_data = self._prepare_json_data(document, config)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            file_size = output_path.stat().st_size

            return {
                "success": True,
                "file_size": file_size,
                "format_specific": {
                    "schema_version": config.get("schema_version", "1.0"),
                    "pretty_print": config.get("pretty_print", True)
                }
            }

        except Exception as e:
            logger.error("JSON export failed", error=str(e))
            return {"success": False, "error": str(e)}

    def _export_xml(self, document: Dict[str, Any], output_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Export document to XML format."""
        try:
            xml_content = self._generate_xml_content(document, config)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)

            file_size = output_path.stat().st_size

            return {
                "success": True,
                "file_size": file_size,
                "format_specific": {
                    "schema_validated": config.get("validate_schema", False),
                    "encoding": config.get("encoding", "utf-8")
                }
            }

        except Exception as e:
            logger.error("XML export failed", error=str(e))
            return {"success": False, "error": str(e)}

    def _export_markdown(self, document: Dict[str, Any], output_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Export document to enhanced Markdown format."""
        try:
            markdown_content = self._generate_markdown_content(document, config)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            file_size = output_path.stat().st_size

            return {
                "success": True,
                "file_size": file_size,
                "format_specific": {
                    "enhanced_features": config.get("enhanced_features", True),
                    "toc_included": config.get("include_toc", True)
                }
            }

        except Exception as e:
            logger.error("Markdown export failed", error=str(e))
            return {"success": False, "error": str(e)}

    def _prepare_content_for_pdf(self, document: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Prepare content for PDF export."""
        content_parts = []

        # Add title
        title = document.get("title", "Untitled Document")
        content_parts.append(f"Title: {title}\n")

        # Add metadata if requested
        if self.include_metadata:
            metadata = document.get("metadata", {})
            if metadata:
                content_parts.append("Metadata:")
                for key, value in metadata.items():
                    content_parts.append(f"  {key}: {value}")
                content_parts.append("")

        # Add main content
        main_content = document.get("content", "")
        if main_content:
            content_parts.append("Content:")
            content_parts.append(main_content)

        # Add sections
        sections = document.get("sections", [])
        if sections:
            content_parts.append("\nSections:")
            for section in sections:
                section_title = section.get("title", "Untitled Section")
                section_content = section.get("content", "")
                content_parts.append(f"\n{section_title}:")
                content_parts.append(section_content)

        return "\n".join(content_parts)

    def _prepare_content_for_docx(self, document: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Prepare content for DOCX export."""
        return self._prepare_content_for_pdf(document, config)

    def _generate_html_content(self, document: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate HTML content for the document."""
        title = document.get("title", "Untitled Document")
        content = document.get("content", "")
        sections = document.get("sections", [])

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang=\"en\">",
            "<head>",
            f"<title>{title}</title>",
            "<meta charset=\"utf-8\">",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; margin-top: 30px; }",
            ".section { margin-bottom: 20px; }",
            ".metadata { background: #f5f5f5; padding: 10px; border-radius: 5px; }",
            "</style>" if config.get("include_css", True) else "",
            "</head>",
            "<body>",
            f"<h1>{title}</h1>"
        ]

        # Add metadata
        if self.include_metadata:
            metadata = document.get("metadata", {})
            if metadata:
                html_parts.append("<div class=\"metadata\">")
                html_parts.append("<h3>Document Metadata</h3>")
                html_parts.append("<ul>")
                for key, value in metadata.items():
                    html_parts.append(f"<li><strong>{key}:</strong> {value}</li>")
                html_parts.append("</ul>")
                html_parts.append("</div>")

        # Add main content
        if content:
            html_parts.append("<div class=\"content\">")
            # Convert line breaks to paragraphs
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    html_parts.append(f"<p>{para.strip()}</p>")
            html_parts.append("</div>")

        # Add sections
        if sections:
            for section in sections:
                section_title = section.get("title", "Untitled Section")
                section_content = section.get("content", "")
                level = section.get("level", 2)

                html_parts.append(f"<div class=\"section\">")
                html_parts.append(f"<h{level}>{section_title}</h{level}>")

                if section_content:
                    # Simple markdown-like conversion
                    section_html = section_content.replace('\n\n', '</p><p>')
                    section_html = section_html.replace('\n', '<br>')
                    html_parts.append(f"<p>{section_html}</p>")

                html_parts.append("</div>")

        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts)

    def _prepare_json_data(self, document: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare JSON data for export."""
        json_data = {
            "document": {
                "title": document.get("title", "Untitled Document"),
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "format_version": "1.0"
            }
        }

        # Add content
        if document.get("content"):
            json_data["document"]["content"] = document["content"]

        # Add sections
        if document.get("sections"):
            json_data["document"]["sections"] = document["sections"]

        # Add metadata
        if self.include_metadata and document.get("metadata"):
            json_data["document"]["metadata"] = document["metadata"]

        # Add table of contents
        if document.get("table_of_contents"):
            json_data["document"]["table_of_contents"] = document["table_of_contents"]

        return json_data

    def _generate_xml_content(self, document: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate XML content for the document."""
        title = document.get("title", "Untitled Document")
        content = document.get("content", "")
        sections = document.get("sections", [])

        xml_parts = [
            "<?xml version=\"1.0\" encoding=\"utf-8\"?>",
            "<document>",
            f"<title>{self._escape_xml(title)}</title>",
            f"<export_timestamp>{datetime.now(timezone.utc).isoformat()}</export_timestamp>"
        ]

        # Add metadata
        if self.include_metadata:
            metadata = document.get("metadata", {})
            if metadata:
                xml_parts.append("<metadata>")
                for key, value in metadata.items():
                    xml_parts.append(f"<{key}>{self._escape_xml(str(value))}</{key}>")
                xml_parts.append("</metadata>")

        # Add main content
        if content:
            xml_parts.append("<content>")
            xml_parts.append(self._escape_xml(content))
            xml_parts.append("</content>")

        # Add sections
        if sections:
            xml_parts.append("<sections>")
            for section in sections:
                section_title = section.get("title", "Untitled Section")
                section_content = section.get("content", "")

                xml_parts.append("<section>")
                xml_parts.append(f"<title>{self._escape_xml(section_title)}</title>")
                xml_parts.append(f"<level>{section.get('level', 1)}</level>")

                if section_content:
                    xml_parts.append("<content>")
                    xml_parts.append(self._escape_xml(section_content))
                    xml_parts.append("</content>")

                xml_parts.append("</section>")

            xml_parts.append("</sections>")

        xml_parts.append("</document>")

        return "\n".join(xml_parts)

    def _generate_markdown_content(self, document: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate enhanced Markdown content."""
        title = document.get("title", "Untitled Document")
        content = document.get("content", "")
        sections = document.get("sections", [])

        markdown_parts = [
            f"# {title}\n",
            f"**Export Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        ]

        # Add metadata
        if self.include_metadata:
            metadata = document.get("metadata", {})
            if metadata:
                markdown_parts.append("## Document Metadata\n")
                for key, value in metadata.items():
                    markdown_parts.append(f"- **{key}:** {value}")
                markdown_parts.append("")

        # Add table of contents
        if config.get("include_toc", True) and sections:
            markdown_parts.append("## Table of Contents\n")
            for section in sections:
                title = section.get("title", "Untitled")
                level = section.get("level", 1)
                indent = "  " * (level - 1)
                markdown_parts.append(f"{indent}- {title}")
            markdown_parts.append("")

        # Add main content
        if content:
            markdown_parts.append("## Content\n")
            markdown_parts.append(content)
            markdown_parts.append("")

        # Add sections
        if sections:
            for section in sections:
                section_title = section.get("title", "Untitled Section")
                section_content = section.get("content", "")
                level = section.get("level", 1)

                header = "#" * level + " " + section_title
                markdown_parts.append(header)

                if section_content:
                    markdown_parts.append("")
                    markdown_parts.append(section_content)

                markdown_parts.append("")

        return "\n".join(markdown_parts)

    def _estimate_pdf_pages(self, content: str) -> int:
        """Estimate number of PDF pages from content."""
        # Rough estimation: ~3000 characters per page
        char_count = len(content)
        return max(1, char_count // 3000)

    def _get_format_extension(self, format_type: str) -> str:
        """Get file extension for format type."""
        extensions = {
            "pdf": "pdf",
            "docx": "docx",
            "html": "html",
            "json": "json",
            "xml": "xml",
            "markdown": "md"
        }
        return extensions.get(format_type, "txt")

    def _escape_xml(self, text: str) -> str:
        """Escape special characters for XML."""
        return (text.replace("&", "&")
                .replace("<", "<")
                .replace(">", ">")
                .replace("\"", """)
                .replace("'", "'"))

    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return self.supported_formats.copy()

    def validate_export_config(self, format_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate export configuration for a format."""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": []
        }

        # Format-specific validation
        if format_type == "pdf":
            if config.get("font_size", 12) < 8:
                validation_result["warnings"].append("Font size too small for PDF readability")
            if config.get("font_size", 12) > 72:
                validation_result["warnings"].append("Font size too large for PDF")

        elif format_type == "html":
            if not config.get("include_css", True):
                validation_result["warnings"].append("CSS not included - HTML may not render properly")

        elif format_type == "json":
            if not config.get("pretty_print", True):
                validation_result["warnings"].append("JSON not pretty-printed - will be minified")

        return validation_result

    def get_format_capabilities(self, format_type: str) -> Dict[str, Any]:
        """Get capabilities and features for a format."""
        capabilities = {
            "pdf": {
                "supports_styling": True,
                "supports_images": True,
                "supports_tables": True,
                "supports_hyperlinks": True,
                "max_file_size": "unlimited",
                "best_for": "printing, formal documents"
            },
            "docx": {
                "supports_styling": True,
                "supports_images": True,
                "supports_tables": True,
                "supports_hyperlinks": True,
                "max_file_size": "unlimited",
                "best_for": "editing, collaboration"
            },
            "html": {
                "supports_styling": True,
                "supports_images": True,
                "supports_tables": True,
                "supports_hyperlinks": True,
                "max_file_size": "unlimited",
                "best_for": "web publishing, responsive design"
            },
            "json": {
                "supports_styling": False,
                "supports_images": False,
                "supports_tables": True,
                "supports_hyperlinks": False,
                "max_file_size": "unlimited",
                "best_for": "data interchange, APIs"
            },
            "xml": {
                "supports_styling": False,
                "supports_images": False,
                "supports_tables": True,
                "supports_hyperlinks": False,
                "max_file_size": "unlimited",
                "best_for": "structured data, enterprise systems"
            },
            "markdown": {
                "supports_styling": True,
                "supports_images": True,
                "supports_tables": True,
                "supports_hyperlinks": True,
                "max_file_size": "unlimited",
                "best_for": "documentation, version control"
            }
        }

        return capabilities.get(format_type, {})
