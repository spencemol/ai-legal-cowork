"""Tests for document exporter (tasks 7.10, 7.11, 7.12).

RED: These tests fail until app/docgen/exporter.py is implemented.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from app.docgen.exporter import DocumentExporter, ExportFormat


_SAMPLE_CONTENT = """MUTUAL NON-DISCLOSURE AGREEMENT

This Agreement is entered into as of March 1, 2026, between Acme Corporation
and Beta LLC.

1. Confidential Information
Each party agrees to keep the other party's confidential information secret.

2. Term
This Agreement shall remain in effect for 2 years.

3. Governing Law
This Agreement shall be governed by the laws of California.
"""


class TestExportFormat:
    def test_docx_format_exists(self):
        assert ExportFormat.DOCX == "docx"

    def test_pdf_format_exists(self):
        assert ExportFormat.PDF == "pdf"

    def test_markdown_format_exists(self):
        assert ExportFormat.MARKDOWN == "md"


class TestDocumentExporterInit:
    def test_instantiation(self):
        exporter = DocumentExporter()
        assert exporter is not None


class TestDocxExport:
    def test_export_docx_creates_file(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.docx")
        result = exporter.export_docx(_SAMPLE_CONTENT, output_path)
        assert os.path.isfile(output_path)

    def test_export_docx_returns_path(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.docx")
        result = exporter.export_docx(_SAMPLE_CONTENT, output_path)
        assert result == output_path

    def test_export_docx_file_nonempty(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.docx")
        exporter.export_docx(_SAMPLE_CONTENT, output_path)
        assert os.path.getsize(output_path) > 0

    def test_export_docx_valid_docx_format(self, tmp_path):
        """DOCX files are ZIP archives with a specific magic number."""
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.docx")
        exporter.export_docx(_SAMPLE_CONTENT, output_path)
        # DOCX (OOXML) files start with PK (ZIP magic number)
        with open(output_path, "rb") as f:
            magic = f.read(2)
        assert magic == b"PK"


class TestMarkdownExport:
    def test_export_markdown_creates_file(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.md")
        result = exporter.export_markdown(_SAMPLE_CONTENT, output_path)
        assert os.path.isfile(output_path)

    def test_export_markdown_returns_path(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.md")
        result = exporter.export_markdown(_SAMPLE_CONTENT, output_path)
        assert result == output_path

    def test_export_markdown_content_preserved(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.md")
        exporter.export_markdown(_SAMPLE_CONTENT, output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert "NON-DISCLOSURE AGREEMENT" in content

    def test_export_markdown_utf8_encoding(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.md")
        content_with_unicode = _SAMPLE_CONTENT + "\n\nSpecial chars: café, résumé"
        exporter.export_markdown(content_with_unicode, output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert "café" in content


class TestPdfExport:
    def test_export_pdf_creates_file(self, tmp_path):
        """PDF export should create a file (may be text fallback if weasyprint not available)."""
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.pdf")
        # Patch weasyprint to simulate unavailable
        with patch.dict("sys.modules", {"weasyprint": None}):
            result = exporter.export_pdf(_SAMPLE_CONTENT, output_path)
        assert os.path.isfile(output_path)

    def test_export_pdf_returns_path(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "test_doc.pdf")
        with patch.dict("sys.modules", {"weasyprint": None}):
            result = exporter.export_pdf(_SAMPLE_CONTENT, output_path)
        assert result == output_path

    def test_export_pdf_with_weasyprint_mocked(self, tmp_path):
        """When weasyprint is available, it should be used."""
        mock_weasyprint = MagicMock()
        mock_html = MagicMock()
        mock_weasyprint.HTML.return_value = mock_html
        mock_html.write_pdf = MagicMock()

        output_path = str(tmp_path / "test_doc.pdf")

        with patch.dict("sys.modules", {"weasyprint": mock_weasyprint}):
            exporter = DocumentExporter()
            result = exporter.export_pdf(_SAMPLE_CONTENT, output_path)

        # Should have attempted to use weasyprint
        assert result == output_path

    def test_export_pdf_graceful_degradation(self, tmp_path):
        """If weasyprint fails, should write text fallback file."""
        output_path = str(tmp_path / "test_fallback.pdf")
        with patch.dict("sys.modules", {"weasyprint": None}):
            exporter = DocumentExporter()
            result = exporter.export_pdf(_SAMPLE_CONTENT, output_path)
        # File should exist even in fallback mode
        assert os.path.isfile(output_path)
        assert result == output_path


class TestExportDispatch:
    def test_export_docx_via_dispatch(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "dispatch.docx")
        result = exporter.export(_SAMPLE_CONTENT, output_path, ExportFormat.DOCX)
        assert os.path.isfile(output_path)
        assert result == output_path

    def test_export_markdown_via_dispatch(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "dispatch.md")
        result = exporter.export(_SAMPLE_CONTENT, output_path, ExportFormat.MARKDOWN)
        assert os.path.isfile(output_path)

    def test_export_pdf_via_dispatch(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "dispatch.pdf")
        with patch.dict("sys.modules", {"weasyprint": None}):
            result = exporter.export(_SAMPLE_CONTENT, output_path, ExportFormat.PDF)
        assert os.path.isfile(output_path)

    def test_export_invalid_format_raises(self, tmp_path):
        exporter = DocumentExporter()
        output_path = str(tmp_path / "doc.xyz")
        with pytest.raises((ValueError, KeyError)):
            exporter.export(_SAMPLE_CONTENT, output_path, "xyz")  # type: ignore[arg-type]
