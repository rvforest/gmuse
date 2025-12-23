"""Template extraction utilities for documentation generation.

This module is used by Sphinx extensions and tests to keep documentation in sync
with the canonical prompt templates in gmuse.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

from gmuse.prompts import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    get_conventional_task,
    get_freeform_task,
    get_gitmoji_task,
)


@dataclass(frozen=True)
class ExtractedTemplate:
    """An extracted prompt template."""

    name: str
    content: str
    description: str


@dataclass(frozen=True)
class ContextInputInfo:
    """Information about a context input."""

    name: str
    description: str
    condition: str
    is_optional: bool


TemplateGetter = Callable[[], str]
TemplateSpec = tuple[str, TemplateGetter, str]


_TEMPLATE_SPECS: dict[str, TemplateSpec] = {
    "system": (
        "SYSTEM_PROMPT",
        lambda: SYSTEM_PROMPT,
        "Base system prompt used for all commit message generations.",
    ),
    "freeform": (
        "get_freeform_task()",
        get_freeform_task,
        "Formatting instructions for freeform commit messages.",
    ),
    "conventional": (
        "get_conventional_task()",
        get_conventional_task,
        "Formatting instructions for Conventional Commits messages.",
    ),
    "gitmoji": (
        "get_gitmoji_task()",
        get_gitmoji_task,
        "Formatting instructions for gitmoji-style commit messages.",
    ),
}


def get_prompt_version() -> str:
    """Return the current canonical prompt version.

    This is sourced directly from :data:`gmuse.prompts.PROMPT_VERSION`.
    """

    return PROMPT_VERSION


def _extract_template(name: str) -> ExtractedTemplate:
    try:
        source_name, getter, description = _TEMPLATE_SPECS[name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown template '{name}'. Known templates: {sorted(_TEMPLATE_SPECS.keys())}"
        ) from exc

    try:
        content = getter()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to extract template '{name}' from {source_name}: {exc}"
        ) from exc

    if not content or not content.strip():
        raise ValueError(f"Template '{name}' extracted from {source_name} is empty")

    return ExtractedTemplate(name=name, content=content, description=description)


def extract_system_prompt() -> ExtractedTemplate:
    """Extract the system prompt template."""

    return _extract_template("system")


def extract_format_task(format_name: str) -> ExtractedTemplate:
    """Extract the task prompt for a given output format.

    Args:
        format_name: One of ``freeform``, ``conventional``, or ``gitmoji``.

    Raises:
        ValueError: If ``format_name`` is unknown.
    """

    if format_name not in {"freeform", "conventional", "gitmoji"}:
        raise ValueError(
            f"Unknown format '{format_name}'. Expected one of: freeform, conventional, gitmoji"
        )
    return _extract_template(format_name)


def extract_all_templates() -> dict[str, ExtractedTemplate]:
    """Extract all canonical templates used in documentation."""

    return {name: _extract_template(name) for name in _TEMPLATE_SPECS}


def get_context_inputs() -> list[ContextInputInfo]:
    """Return the canonical list of context inputs used for documentation.

    This is intentionally a small, explicit list rather than trying to introspect
    runtime behavior. It should stay aligned with the context assembled by
    gmuse for suggestion requests.
    """

    return [
        ContextInputInfo(
            name="Staged Changes",
            description="A summary of staged changes (files changed, lines added/removed) and the staged diff.",
            condition="Always included",
            is_optional=False,
        ),
        ContextInputInfo(
            name="Commit History",
            description="Recent commit messages used as style reference.",
            condition="Included when commit history is available (depth configurable via history_depth)",
            is_optional=False,
        ),
        ContextInputInfo(
            name="Repository Instructions",
            description="Repository-level guidance loaded from a local .gmuse file.",
            condition="Included when a .gmuse file exists and contains content",
            is_optional=False,
        ),
        ContextInputInfo(
            name="Branch Context",
            description="Sanitized branch type/summary to provide extra intent context.",
            condition="Included only when --include-branch (or equivalent config) is enabled",
            is_optional=True,
        ),
        ContextInputInfo(
            name="User Hint",
            description="Additional user-provided context passed via the --hint flag.",
            condition="Included only when --hint is provided",
            is_optional=True,
        ),
        ContextInputInfo(
            name="Learning Examples",
            description="Prior (generated → edited) examples used to match your editing style.",
            condition="Included only when learning is enabled and examples exist",
            is_optional=True,
        ),
    ]


def validate_templates() -> None:
    """Validate that all required templates are extractable and non-empty.

    This is designed to be called during documentation builds; failures should be
    actionable and point at the missing or empty template.
    """

    # Check for forced failure flag used in integration tests to verify
    # that the documentation build properly fails when templates are invalid.
    if os.environ.get("GMUSE_DOCS_FORCE_TEMPLATE_VALIDATION_ERROR"):
        raise RuntimeError(
            "Prompt template validation failed: forced failure via GMUSE_DOCS_FORCE_TEMPLATE_VALIDATION_ERROR"
        )

    required = {"system", "freeform", "conventional", "gitmoji"}
    try:
        templates = extract_all_templates()
    except Exception as exc:
        raise RuntimeError(f"Prompt template validation failed: {exc}") from exc

    missing = required.difference(templates.keys())
    if missing:
        raise RuntimeError(
            "Prompt template validation failed: "
            f"missing required templates: {sorted(missing)}"
        )
