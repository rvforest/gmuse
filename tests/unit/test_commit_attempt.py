from __future__ import annotations

import pytest

from gmuse.commit import (
    GenerationAttemptResult,
    GenerationContext,
    GenerationOperationalError,
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


def test_validation_and_attempt_aliases_expose_contract_names() -> None:
    passed = ValidationOutcome(valid=True)
    failed = ValidationOutcome(valid=False, category="validation", message="bad")

    assert passed.status == "passed"
    assert passed.error_category is None
    assert failed.status == "failed"
    assert failed.error_category == "validation"

    result = generate_message_attempt(
        {"format": "freeform", "max_message_length": 1000},
        context=_context(),
        response_generator=lambda **_: "Add documentation",
    )
    assert result.raw_message == result.message
    assert result.prompt_metadata is result.prompt
    assert result.validation_outcome is result.validation
    assert result.prompt.prompt_sha256 == result.prompt.prompt_hash


def test_generate_message_restores_llm_error_without_original_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_attempt(*_args: object, **_kwargs: object) -> GenerationAttemptResult:
        return GenerationAttemptResult(
            message=None,
            context=_context(),
            prompt=GenerationPromptMetadata.from_prompts("system", "user"),
            validation=ValidationOutcome(valid=False),
            operational_error=GenerationOperationalError(
                category="unknown",
                message="provider unavailable",
                exception_type="LLMError",
                exception=None,
            ),
        )

    monkeypatch.setattr("gmuse.commit.generate_message_attempt", fake_attempt)
    with pytest.raises(LLMError, match="provider unavailable"):
        generate_message({"format": "freeform"}, context=_context())


def test_response_generator_without_inspectable_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def uninspectable(**_: object) -> str:
        return "Add documentation"

    def raise_no_signature(_fn: object) -> object:
        raise TypeError("no signature")

    monkeypatch.setattr("inspect.signature", raise_no_signature)
    result = generate_message_attempt(
        {"format": "freeform", "max_message_length": 1000},
        context=_context(),
        response_generator=uninspectable,
    )
    assert result.message == "Add documentation"
    assert result.validation.valid is True


def test_response_generator_accepts_named_and_positional_seams() -> None:
    def named_only(*, system_prompt: str) -> str:
        assert system_prompt
        return "Add documentation"

    named = generate_message_attempt(
        {"format": "freeform", "max_message_length": 1000},
        context=_context(),
        response_generator=named_only,
    )
    assert named.message == "Add documentation"
    assert named.validation.valid is True

    def positional_only(system_prompt: str, user_prompt: str, /) -> str:
        assert system_prompt
        assert user_prompt
        return "Add documentation"

    positional = generate_message_attempt(
        {"format": "freeform", "max_message_length": 1000},
        context=_context(),
        response_generator=positional_only,
    )
    assert positional.message == "Add documentation"
    assert positional.validation.valid is True
