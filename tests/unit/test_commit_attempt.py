from __future__ import annotations

import pytest

from gmuse.commit import (
    GenerationContext,
    GenerationPromptMetadata,
    ValidationOutcome,
    generate_message,
    generate_message_attempt,
)
from gmuse.exceptions import InvalidMessageError, LLMError
from gmuse.git import StagedDiff


def _context() -> GenerationContext:
    return GenerationContext(
        diff=StagedDiff("diff", ["README.md"], 1, 0, "a" * 64, 4),
        history=None,
        repo_instructions=None,
    )


def test_attempt_records_prompt_metadata_and_validates_injected_response() -> None:
    result = generate_message_attempt(
        {"format": "freeform", "max_message_length": 1000},
        context=_context(),
        response_generator=lambda **_: "Add documentation",
    )

    assert result.message == "Add documentation"
    assert result.validation.valid is True
    assert isinstance(result.prompt, GenerationPromptMetadata)
    assert result.prompt.prompt_hash
    assert result.prompt.prompt_size_bytes > 0
    assert result.prompt.estimated_input_tokens > 0
    assert result.prompt.prompt_version == "1.0.0"


def test_attempt_preserves_invalid_output_without_raising() -> None:
    result = generate_message_attempt(
        {"format": "conventional", "max_message_length": 1000},
        context=_context(),
        response_generator=lambda **_: "not conventional",
    )

    assert result.message == "not conventional"
    assert result.validation == ValidationOutcome(
        valid=False,
        category="validation",
        message=result.validation.message,
    )


def test_attempt_records_operational_failure() -> None:
    def fail(**_: object) -> str:
        raise LLMError("provider unavailable")

    result = generate_message_attempt(
        {"format": "freeform"}, context=_context(), response_generator=fail
    )

    assert result.message is None
    assert result.operational_error is not None
    assert result.operational_error.category == "unknown"


def test_generate_message_keeps_raising_for_invalid_injected_response() -> None:
    with pytest.raises(InvalidMessageError):
        generate_message(
            {"format": "conventional", "max_message_length": 1000},
            context=_context(),
            response_generator=lambda **_: "invalid",
        )
