"""Sphinx extension for prompt template documentation.

This extension renders canonical prompt template text and context-input metadata
directly from code, ensuring documentation stays in sync with gmuse.
"""

from __future__ import annotations

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.errors import SphinxError
from sphinx.util.docutils import SphinxDirective

from gmuse._docs.template_extractor import (
    extract_all_templates,
    get_context_inputs,
    validate_templates,
)


class PromptTemplateDirective(SphinxDirective):
    """Render a prompt template as a literal code block."""

    required_arguments = 1
    has_content = False

    # Sphinx's SphinxDirective.run() expects list[nodes.Node] but the base
    # Directive class (from docutils) has a more general sequence type.
    # The type ignore is needed to satisfy both type checkers.
    def run(self) -> list[nodes.Node]:  # type: ignore[bad-override] # noqa: D102
        template_name = self.arguments[0]
        templates = extract_all_templates()

        if template_name not in templates:
            raise self.error(
                f"Unknown template '{template_name}'. Expected one of: {', '.join(sorted(templates.keys()))}"
            )

        template = templates[template_name]
        block = nodes.literal_block(template.content, template.content)
        block["language"] = "text"
        return [block]


class ContextInputsTableDirective(SphinxDirective):
    """Render a table describing possible context inputs."""

    has_content = False

    # Sphinx's SphinxDirective.run() expects list[nodes.Node] but the base
    # Directive class (from docutils) has a more general sequence type.
    # The type ignore is needed to satisfy both type checkers.
    def run(self) -> list[nodes.Node]:  # type: ignore[bad-override] # noqa: D102
        inputs = get_context_inputs()

        table = nodes.table()
        tgroup = nodes.tgroup(cols=4)
        table += tgroup

        for _ in range(4):
            tgroup += nodes.colspec(colwidth=1)

        thead = nodes.thead()
        tgroup += thead

        header_row = nodes.row()
        for text in ("Input", "Description", "Included When", "Optional"):
            entry = nodes.entry()
            entry += nodes.paragraph(text=text)
            header_row += entry
        thead += header_row

        tbody = nodes.tbody()
        tgroup += tbody

        for info in inputs:
            row = nodes.row()
            for text in (
                info.name,
                info.description,
                info.condition,
                "Yes" if info.is_optional else "No",
            ):
                entry = nodes.entry()
                entry += nodes.paragraph(text=text)
                row += entry
            tbody += row

        return [table]


def setup(app: Sphinx):
    """Register directives for prompt template documentation."""

    app.add_directive("prompt-template", PromptTemplateDirective)
    app.add_directive("context-inputs-table", ContextInputsTableDirective)

    def _validate_on_build(app: Sphinx) -> None:
        try:
            validate_templates()
        except Exception as exc:  # pragma: no cover
            raise SphinxError(str(exc)) from exc

    app.connect("builder-inited", _validate_on_build)
    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
