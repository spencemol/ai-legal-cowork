"""Jinja2 template loader (task 7.6).

Loads ``.j2`` templates from the ``agents/app/docgen/templates/`` directory
(or a custom directory) and exposes a simple :class:`TemplateLoader` API.
"""

from __future__ import annotations

import os

from jinja2 import Environment, FileSystemLoader, Template

# Default template directory relative to this file.
_DEFAULT_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


class TemplateLoader:
    """Load and list Jinja2 templates from a directory.

    Parameters
    ----------
    templates_dir:
        Path to the directory containing ``.j2`` template files.  Defaults
        to ``agents/app/docgen/templates/``.
    """

    def __init__(self, templates_dir: str | None = None) -> None:
        self.templates_dir = templates_dir or _DEFAULT_TEMPLATES_DIR
        self._env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=False,
            keep_trailing_newline=True,
        )

    def load(self, template_name: str) -> Template:
        """Load a template by name.

        Parameters
        ----------
        template_name:
            File name of the template (e.g. ``"nda.j2"``).

        Returns
        -------
        jinja2.Template
            A Jinja2 :class:`~jinja2.Template` object ready for rendering.

        Raises
        ------
        jinja2.TemplateNotFound
            If no template with the given name exists in the templates directory.
        """
        return self._env.get_template(template_name)

    def list_templates(self) -> list[str]:
        """Return the names of all ``.j2`` template files in the directory.

        Returns
        -------
        list[str]
            Sorted list of template file names (e.g. ``["nda.j2", ...]``).
        """
        try:
            files = os.listdir(self.templates_dir)
        except FileNotFoundError:
            return []
        return sorted(f for f in files if f.endswith(".j2"))
