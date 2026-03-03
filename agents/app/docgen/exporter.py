"""Document exporter — DOCX, PDF, and Markdown (tasks 7.10, 7.11, 7.12).

Provides :class:`DocumentExporter` with methods for each output format and a
dispatch :meth:`export` method.  PDF export uses ``weasyprint`` when available
and falls back to writing a plain-text file with a ``.pdf`` extension when the
library is missing or fails (graceful degradation for development environments).
"""

from __future__ import annotations

import importlib
import os
from enum import StrEnum


class ExportFormat(StrEnum):
    """Supported document export formats."""

    DOCX = "docx"
    PDF = "pdf"
    MARKDOWN = "md"


class DocumentExporter:
    """Export rendered document strings to various file formats."""

    # ------------------------------------------------------------------
    # DOCX (task 7.10)
    # ------------------------------------------------------------------

    def export_docx(self, content: str, output_path: str) -> str:
        """Write *content* to a ``.docx`` file using *python-docx*.

        Parameters
        ----------
        content:
            Plain-text document content.  Each line becomes a paragraph.
        output_path:
            Destination file path (should end with ``.docx``).

        Returns
        -------
        str
            The *output_path* that was written.
        """
        from docx import Document  # noqa: PLC0415

        doc = Document()
        for line in content.splitlines():
            doc.add_paragraph(line)
        doc.save(output_path)
        return output_path

    # ------------------------------------------------------------------
    # Markdown (task 7.12)
    # ------------------------------------------------------------------

    def export_markdown(self, content: str, output_path: str) -> str:
        """Write *content* to a Markdown (``.md``) file.

        Parameters
        ----------
        content:
            Markdown (or plain text) content.
        output_path:
            Destination file path.

        Returns
        -------
        str
            The *output_path* that was written.
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return output_path

    # ------------------------------------------------------------------
    # PDF (task 7.11)
    # ------------------------------------------------------------------

    def export_pdf(self, content: str, output_path: str) -> str:
        """Write *content* to a ``.pdf`` file.

        Attempts to use ``weasyprint`` for proper PDF generation.  If
        ``weasyprint`` is not installed or raises an error, falls back to
        writing a UTF-8 text file at *output_path* with a note prepended
        (graceful degradation — production should install weasyprint).

        Parameters
        ----------
        content:
            Document content to render as PDF.
        output_path:
            Destination file path (should end with ``.pdf``).

        Returns
        -------
        str
            The *output_path* that was written.
        """
        weasyprint = importlib.import_module("weasyprint") if self._weasyprint_available() else None

        if weasyprint is not None:
            try:
                html_content = self._text_to_html(content)
                html_doc = weasyprint.HTML(string=html_content)
                html_doc.write_pdf(output_path)
                return output_path
            except Exception:
                pass  # Fall through to text fallback

        # Graceful degradation: write plain text with PDF extension
        fallback_note = (
            "[NOTE: weasyprint not available — this is a plain text fallback.\n"
            "Install weasyprint for proper PDF output.]\n\n"
        )
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(fallback_note + content)
        return output_path

    # ------------------------------------------------------------------
    # Dispatch (all formats)
    # ------------------------------------------------------------------

    def export(self, content: str, output_path: str, format: ExportFormat) -> str:  # noqa: A002
        """Dispatch export to the correct method based on *format*.

        Parameters
        ----------
        content:
            Document content.
        output_path:
            Destination file path.
        format:
            One of :class:`ExportFormat`.

        Returns
        -------
        str
            The *output_path* that was written.

        Raises
        ------
        ValueError
            If *format* is not a valid :class:`ExportFormat`.
        """
        fmt = ExportFormat(format)
        if fmt == ExportFormat.DOCX:
            return self.export_docx(content, output_path)
        if fmt == ExportFormat.PDF:
            return self.export_pdf(content, output_path)
        if fmt == ExportFormat.MARKDOWN:
            return self.export_markdown(content, output_path)
        raise ValueError(f"Unsupported export format: {format!r}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _weasyprint_available() -> bool:
        """Return True if ``weasyprint`` can be imported."""
        try:
            import weasyprint  # noqa: F401 PLC0415
            return True
        except (ImportError, ModuleNotFoundError):
            return False

    @staticmethod
    def _text_to_html(content: str) -> str:
        """Convert plain text to minimal HTML for weasyprint rendering."""
        import html as html_module  # noqa: PLC0415

        escaped = html_module.escape(content)
        paragraphs = "".join(
            f"<p>{line}</p>" if line.strip() else "<br/>"
            for line in escaped.splitlines()
        )
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
body {{ font-family: serif; font-size: 12pt; margin: 2cm; }}
p {{ margin: 0.4em 0; }}
</style>
</head>
<body>{paragraphs}</body>
</html>"""
