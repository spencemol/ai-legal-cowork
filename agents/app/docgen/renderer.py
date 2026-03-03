"""Template renderer (task 7.8).

Provides :class:`DocumentRenderer` which renders Jinja2 templates
(identified by name or loaded as objects) into document strings.
"""

from __future__ import annotations

from jinja2 import Template

from app.docgen.template_loader import TemplateLoader


class DocumentRenderer:
    """Render Jinja2 templates with a context dictionary.

    Parameters
    ----------
    template_loader:
        Optional :class:`~app.docgen.template_loader.TemplateLoader`.
        A default instance is created if not provided.
    """

    def __init__(self, template_loader: TemplateLoader | None = None) -> None:
        self._loader = template_loader or TemplateLoader()

    def render(self, template_name: str, context: dict) -> str:
        """Load a template by name and render it with *context*.

        Parameters
        ----------
        template_name:
            File name of the ``.j2`` template (e.g. ``"nda.j2"``).
        context:
            Dictionary of variable names to values.

        Returns
        -------
        str
            Rendered document as a plain string.

        Raises
        ------
        jinja2.TemplateNotFound
            Propagated from the loader when the template is not found.
        """
        template = self._loader.load(template_name)
        return self.render_template(template, context)

    def render_template(self, template: Template, context: dict) -> str:
        """Render a pre-loaded Jinja2 template object with *context*.

        Parameters
        ----------
        template:
            A :class:`jinja2.Template` object.
        context:
            Dictionary of variable names to values.

        Returns
        -------
        str
            Rendered document as a plain string.
        """
        return template.render(**context)
