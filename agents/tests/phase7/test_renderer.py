"""Tests for template renderer (task 7.8).

RED: These tests fail until app/docgen/renderer.py is implemented.
"""

from __future__ import annotations

import pytest

from app.docgen.renderer import DocumentRenderer


class TestDocumentRendererInit:
    def test_instantiation(self):
        renderer = DocumentRenderer()
        assert renderer is not None


class TestDocumentRendererRender:
    def test_render_engagement_letter(self, engagement_letter_context):
        renderer = DocumentRenderer()
        result = renderer.render("engagement_letter.j2", engagement_letter_context)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_nda(self, nda_context):
        renderer = DocumentRenderer()
        result = renderer.render("nda.j2", nda_context)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_motion(self, motion_context):
        renderer = DocumentRenderer()
        result = renderer.render("motion.j2", motion_context)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_fills_placeholders(self, nda_context):
        renderer = DocumentRenderer()
        result = renderer.render("nda.j2", nda_context)
        assert nda_context["party_a"] in result
        assert nda_context["party_b"] in result
        assert nda_context["governing_law"] in result

    def test_render_engagement_letter_fills_placeholders(self, engagement_letter_context):
        renderer = DocumentRenderer()
        result = renderer.render("engagement_letter.j2", engagement_letter_context)
        assert engagement_letter_context["client_name"] in result
        assert engagement_letter_context["firm_name"] in result
        assert engagement_letter_context["attorney_name"] in result

    def test_render_motion_fills_placeholders(self, motion_context):
        renderer = DocumentRenderer()
        result = renderer.render("motion.j2", motion_context)
        assert motion_context["case_number"] in result
        assert motion_context["court_name"] in result

    def test_render_raises_for_missing_template(self):
        from jinja2 import TemplateNotFound

        renderer = DocumentRenderer()
        with pytest.raises(TemplateNotFound):
            renderer.render("nonexistent.j2", {})


class TestDocumentRendererRenderTemplate:
    def test_render_template_with_jinja2_object(self, nda_context):
        from app.docgen.template_loader import TemplateLoader

        loader = TemplateLoader()
        template = loader.load("nda.j2")

        renderer = DocumentRenderer()
        result = renderer.render_template(template, nda_context)
        assert isinstance(result, str)
        assert nda_context["party_a"] in result

    def test_render_template_returns_string(self, engagement_letter_context):
        from app.docgen.template_loader import TemplateLoader

        loader = TemplateLoader()
        template = loader.load("engagement_letter.j2")

        renderer = DocumentRenderer()
        result = renderer.render_template(template, engagement_letter_context)
        assert isinstance(result, str)
