"""Tests for Jinja2 template loader (tasks 7.6, 7.7).

RED: These tests fail until app/docgen/template_loader.py and templates are implemented.
"""

from __future__ import annotations

import os

import pytest
from jinja2 import TemplateNotFound

from app.docgen.template_loader import TemplateLoader


class TestTemplateLoaderInit:
    def test_instantiation_default(self):
        loader = TemplateLoader()
        assert loader is not None

    def test_instantiation_with_custom_dir(self, tmp_path):
        loader = TemplateLoader(templates_dir=str(tmp_path))
        assert loader is not None

    def test_default_templates_dir_exists(self):
        loader = TemplateLoader()
        assert os.path.isdir(loader.templates_dir)


class TestTemplateLoaderLoad:
    def test_load_engagement_letter(self):
        loader = TemplateLoader()
        template = loader.load("engagement_letter.j2")
        assert template is not None

    def test_load_nda(self):
        loader = TemplateLoader()
        template = loader.load("nda.j2")
        assert template is not None

    def test_load_motion(self):
        loader = TemplateLoader()
        template = loader.load("motion.j2")
        assert template is not None

    def test_load_missing_raises_template_not_found(self):
        loader = TemplateLoader()
        with pytest.raises(TemplateNotFound):
            loader.load("nonexistent_template.j2")

    def test_loaded_template_is_renderable(self, engagement_letter_context):
        loader = TemplateLoader()
        template = loader.load("engagement_letter.j2")
        rendered = template.render(**engagement_letter_context)
        assert isinstance(rendered, str)
        assert len(rendered) > 0


class TestTemplateLoaderListTemplates:
    def test_list_returns_list(self):
        loader = TemplateLoader()
        templates = loader.list_templates()
        assert isinstance(templates, list)

    def test_list_contains_j2_files(self):
        loader = TemplateLoader()
        templates = loader.list_templates()
        assert all(t.endswith(".j2") for t in templates)

    def test_list_contains_three_default_templates(self):
        loader = TemplateLoader()
        templates = loader.list_templates()
        assert len(templates) >= 3

    def test_list_contains_engagement_letter(self):
        loader = TemplateLoader()
        templates = loader.list_templates()
        assert "engagement_letter.j2" in templates

    def test_list_contains_nda(self):
        loader = TemplateLoader()
        templates = loader.list_templates()
        assert "nda.j2" in templates

    def test_list_contains_motion(self):
        loader = TemplateLoader()
        templates = loader.list_templates()
        assert "motion.j2" in templates


class TestTemplateVariables:
    """Task 7.7: Templates must have correct placeholder variables."""

    def test_engagement_letter_contains_client_name_var(self, engagement_letter_context):
        loader = TemplateLoader()
        template = loader.load("engagement_letter.j2")
        rendered = template.render(**engagement_letter_context)
        assert engagement_letter_context["client_name"] in rendered

    def test_engagement_letter_contains_attorney_name_var(self, engagement_letter_context):
        loader = TemplateLoader()
        template = loader.load("engagement_letter.j2")
        rendered = template.render(**engagement_letter_context)
        assert engagement_letter_context["attorney_name"] in rendered

    def test_engagement_letter_contains_firm_name_var(self, engagement_letter_context):
        loader = TemplateLoader()
        template = loader.load("engagement_letter.j2")
        rendered = template.render(**engagement_letter_context)
        assert engagement_letter_context["firm_name"] in rendered

    def test_nda_contains_party_a_var(self, nda_context):
        loader = TemplateLoader()
        template = loader.load("nda.j2")
        rendered = template.render(**nda_context)
        assert nda_context["party_a"] in rendered

    def test_nda_contains_party_b_var(self, nda_context):
        loader = TemplateLoader()
        template = loader.load("nda.j2")
        rendered = template.render(**nda_context)
        assert nda_context["party_b"] in rendered

    def test_nda_contains_governing_law_var(self, nda_context):
        loader = TemplateLoader()
        template = loader.load("nda.j2")
        rendered = template.render(**nda_context)
        assert nda_context["governing_law"] in rendered

    def test_motion_contains_case_number_var(self, motion_context):
        loader = TemplateLoader()
        template = loader.load("motion.j2")
        rendered = template.render(**motion_context)
        assert motion_context["case_number"] in rendered

    def test_motion_contains_court_name_var(self, motion_context):
        loader = TemplateLoader()
        template = loader.load("motion.j2")
        rendered = template.render(**motion_context)
        assert motion_context["court_name"] in rendered

    def test_motion_contains_motion_type_var(self, motion_context):
        loader = TemplateLoader()
        template = loader.load("motion.j2")
        rendered = template.render(**motion_context)
        assert motion_context["motion_type"] in rendered
