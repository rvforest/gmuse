"""Unit tests for gmuse._docs.template_extractor.

These tests ensure documentation extraction stays aligned with the canonical
prompt templates in gmuse.prompts.
"""

from __future__ import annotations

import pytest

from gmuse._docs import template_extractor
from gmuse.prompts import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    get_conventional_task,
    get_freeform_task,
    get_gitmoji_task,
)


class TestTemplateExtraction:
    """Tests for template extraction helpers."""

    def test_get_prompt_version(self) -> None:
        """Returns the canonical PROMPT_VERSION."""
        assert template_extractor.get_prompt_version() == PROMPT_VERSION

    def test_extract_system_prompt(self) -> None:
        """Extracts SYSTEM_PROMPT byte-for-byte."""
        extracted = template_extractor.extract_system_prompt()
        assert extracted.name == "system"
        assert extracted.content == SYSTEM_PROMPT
        assert extracted.content.strip()

    @pytest.mark.parametrize(
        ("format_name", "expected"),
        [
            ("freeform", get_freeform_task()),
            ("conventional", get_conventional_task()),
            ("gitmoji", get_gitmoji_task()),
        ],
    )
    def test_extract_format_task(self, format_name: str, expected: str) -> None:
        """Extracts format task prompts byte-for-byte."""
        extracted = template_extractor.extract_format_task(format_name)
        assert extracted.name == format_name
        assert extracted.content == expected
        assert extracted.content.strip()

    def test_extract_format_task_unknown_raises(self) -> None:
        """Unknown formats raise a ValueError with a helpful message."""
        with pytest.raises(ValueError, match=r"Unknown format"):
            template_extractor.extract_format_task("unknown")

    def test_extract_all_templates(self) -> None:
        """Extracts all required templates."""
        templates = template_extractor.extract_all_templates()
        assert set(templates.keys()) == {"system", "freeform", "conventional", "gitmoji"}
        assert templates["system"].content == SYSTEM_PROMPT

    def test_validate_templates_success(self) -> None:
        """Validation passes for canonical templates."""
        template_extractor.validate_templates()

    def test_validate_templates_empty_template_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Validation fails with an actionable message when a template is empty."""

        def _empty() -> str:
            return "   "

        monkeypatch.setitem(
            template_extractor._TEMPLATE_SPECS,  # type: ignore[attr-defined]
            "system",
            ("SYSTEM_PROMPT", _empty, "Base system prompt used for all generations"),
        )

        with pytest.raises(RuntimeError, match=r"system"):
            template_extractor.validate_templates()
