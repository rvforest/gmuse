"""Tests for judge evidence controls, structured output, and failures."""

import hashlib
import json
from typing import Any

import pytest

from tools.evals.gmuse_evals import judge
from tools.evals.gmuse_evals.results import ResolvedCase
from tools.evals.gmuse_evals.validate import validate_suite


@pytest.fixture
def payload() -> dict[str, Any]:
    return {
        "judge_output_schema_version": 1,
        "scores": {"accuracy": 4, "message_quality": 3, "style_context_fit": None},
        "usability": "minor_edit",
        "hard_failure_findings": [],
        "quality_errors": ["vague"],
        "rationales": {
            "accuracy": "Correctly identifies the change.",
            "message_quality": "Could name the changed behavior.",
            "style_context_fit": None,
            "usability": "Needs a small wording change.",
        },
    }


@pytest.fixture
def resolved_case() -> ResolvedCase:
    return validate_suite("evals", "smoke").resolved_cases[0]


@pytest.fixture
def configuration() -> judge.JudgeConfiguration:
    return judge.JudgeConfiguration(judge_provider="openai", judge_model="gpt-4o")


def test_valid_payload_preserves_raw_response_without_serializing_it(
    payload: dict[str, Any],
) -> None:
    raw = "\n" + json.dumps(payload, indent=2) + "\n"
    result = judge.parse_judge_response(raw, style_context_applicable=False)

    assert result.scores.accuracy == 4
    assert result.scores.style_context_fit is None
    assert result.usability == "minor_edit"
    assert result.raw_response == raw
    assert (
        result.raw_response_metadata.sha256 == hashlib.sha256(raw.encode()).hexdigest()
    )
    assert result.raw_response_metadata.byte_count == len(raw.encode())
    assert "raw_response" not in result.model_dump(mode="json")
    assert raw not in repr(result)


@pytest.mark.parametrize(
    ("section", "field", "invalid"),
    [
        ("scores", "accuracy", 0),
        ("scores", "accuracy", 5),
        ("scores", "accuracy", "3"),
        ("scores", "accuracy", True),
        ("scores", "accuracy", 3.0),
        ("scores", "accuracy", None),
        ("scores", "style_context_fit", 3),
        ("scores", "aggregate", 3),
        ("rationales", "usability", " \n "),
        ("rationales", "accuracy", None),
        ("rationales", "style_context_fit", "This context fits."),
        (None, "judge_output_schema_version", True),
        (None, "judge_output_schema_version", 2),
        (None, "usability", "pass"),
        (None, "hard_failure_findings", ["other"]),
        (None, "quality_errors", ["rate_limit"]),
        (None, "extra", None),
    ],
)
def test_rejects_invalid_contract_fields(
    payload: dict[str, Any], section: str | None, field: str, invalid: object
) -> None:
    target = payload[section] if section else payload
    target[field] = invalid
    with pytest.raises(judge.JudgeResponseError) as caught:
        judge.parse_judge_response(json.dumps(payload), style_context_applicable=False)
    assert caught.value.category == "judge_parse_error"


@pytest.mark.parametrize(
    ("score", "rationale"),
    [(None, None), (None, "It fits."), (3, None)],
)
def test_applicable_style_requires_both_score_and_rationale(
    payload: dict[str, Any], score: int | None, rationale: str | None
) -> None:
    payload["scores"]["style_context_fit"] = score
    payload["rationales"]["style_context_fit"] = rationale
    with pytest.raises(judge.JudgeResponseError):
        judge.parse_judge_response(json.dumps(payload), style_context_applicable=True)


def test_accepts_applicable_style_score_and_rationale(payload: dict[str, Any]) -> None:
    payload["scores"]["style_context_fit"] = 3
    payload["rationales"]["style_context_fit"] = "Mostly follows style guidance."
    result = judge.parse_judge_response(
        json.dumps(payload), style_context_applicable=True
    )
    assert result.scores.style_context_fit == 3
    assert result.rationales.style_context_fit == "Mostly follows style guidance."


def test_missing_duplicate_and_non_json_fields_rejected(
    payload: dict[str, Any],
) -> None:
    del payload["rationales"]["accuracy"]
    bad_responses = (
        json.dumps(payload),
        '{"usability":"usable","usability":"minor_edit"}',
        "```json\n{}\n```",
    )
    for raw in bad_responses:
        with pytest.raises(judge.JudgeResponseError) as caught:
            judge.parse_judge_response(raw, style_context_applicable=False)
        assert caught.value.category == "judge_parse_error"


def test_prompt_supplies_evidence_and_hides_candidate_identity(
    resolved_case: ResolvedCase,
) -> None:
    raw_diff = 'diff --git a/f b/f\n+example "text"\n'
    context = {"history": ["docs: explain fixture"], "candidate_model": "private-model"}
    prompt = judge.build_judge_prompt(
        staged_diff=raw_diff,
        context=context,
        resolved_case=resolved_case,
        generated_message="docs: update fixture",
        format_name="conventional",
        max_chars=72,
        candidate_provider="private-provider",
        candidate_model="private-model",
    )
    evidence = json.loads(prompt.user_prompt)
    assert evidence["staged_diff"] == raw_diff
    assert evidence["generated_message"] == "docs: update fixture"
    assert evidence["constraints"] == {"format": "conventional", "max_chars": 72}
    assert evidence["context"] == {"history": ["docs: explain fixture"]}
    assert evidence["case_rubric"] == resolved_case.rubric.model_dump(mode="json")
    assert evidence["scoring_profile"] == resolved_case.scoring_profile.model_dump(
        mode="json"
    )
    assert prompt.style_context_applicable
    assert prompt.input_controls.candidate_identity_hidden
    assert prompt.input_controls.candidate_identity_inclusion_reason is None
    assert "private-provider" not in prompt.user_prompt
    assert "private-model" not in prompt.user_prompt
    assert "Judge prompt revision 1" in prompt.system_prompt


def test_diagnostic_prompt_records_reason_and_candidate_identity(
    resolved_case: ResolvedCase,
) -> None:
    prompt = judge.build_judge_prompt(
        staged_diff="diff",
        context={},
        resolved_case=resolved_case,
        generated_message="Update fixture",
        format_name="freeform",
        max_chars=None,
        candidate_provider="openai",
        candidate_model="gpt-4o",
        identity_inclusion_reason="Measure identity bias",
    )
    assert not prompt.style_context_applicable
    assert not prompt.input_controls.candidate_identity_hidden
    assert (
        prompt.input_controls.candidate_identity_inclusion_reason
        == "Measure identity bias"
    )
    assert json.loads(prompt.user_prompt)["candidate_identity"] == {
        "provider": "openai",
        "model": "gpt-4o",
    }


def test_self_judge_and_model_family_are_independent(
    configuration: judge.JudgeConfiguration,
) -> None:
    assert judge.judge_identity_flags(
        configuration, candidate_provider=None, candidate_model="openai/GPT-4o"
    ) == judge.JudgeIdentityFlags(self_judged=True, same_model_family=True)
    assert judge.judge_identity_flags(
        configuration, candidate_provider="openai", candidate_model="gpt-4o-2024-08-06"
    ) == judge.JudgeIdentityFlags(self_judged=False, same_model_family=True)
    assert judge.judge_identity_flags(
        configuration,
        candidate_provider="azure",
        candidate_model="deployment",
        equivalent_models=(("azure", "deployment"),),
    ) == judge.JudgeIdentityFlags(self_judged=True, same_model_family=False)


@pytest.mark.parametrize(
    ("error", "category"),
    [
        (RuntimeError("No API credential is configured"), "auth_error"),
        (RuntimeError("429"), "rate_limit"),
        (TimeoutError(), "timeout"),
        (ConnectionError(), "network_error"),
        (RuntimeError("maximum context"), "context_length"),
        (RuntimeError("empty completion"), "empty_response"),
        (RuntimeError("sensitive transport details"), "unknown_error"),
    ],
)
def test_provider_exceptions_are_safe_operational_errors(
    configuration: judge.JudgeConfiguration, error: Exception, category: str
) -> None:
    prompt = judge.JudgePrompt(
        "", "", False, judge.JudgeInputControls(candidate_identity_hidden=True)
    )

    def fail(_: judge.JudgeConfiguration, __: judge.JudgePrompt) -> str:
        raise error

    result = judge.run_judge(configuration, prompt, provider_call=fail)
    assert isinstance(result, judge.JudgeOperationalError)
    assert result.category == category
    assert result.raw_response_metadata is None
    assert "sensitive transport details" not in result.model_dump_json()


@pytest.mark.parametrize(
    ("raw", "category"), [("   ", "empty_response"), ("bad", "judge_parse_error")]
)
def test_invalid_response_is_preserved_but_not_published(
    configuration: judge.JudgeConfiguration, raw: str, category: str
) -> None:
    prompt = judge.JudgePrompt(
        "", "", False, judge.JudgeInputControls(candidate_identity_hidden=True)
    )
    result = judge.run_judge(configuration, prompt, provider_call=lambda *_: raw)
    assert isinstance(result, judge.JudgeOperationalError)
    assert result.category == category
    assert result.raw_response == raw
    assert result.raw_response_metadata is not None
    assert "raw_response" not in result.model_dump(mode="json")


def test_default_provider_preserves_model_case_and_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace
    from unittest.mock import Mock

    from gmuse import llm

    client = Mock(return_value=SimpleNamespace(provider="huggingface", api_key=None))
    completion = Mock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="  {}\n"))]
        )
    )
    monkeypatch.setattr(llm, "LLMClient", client)
    monkeypatch.setattr(llm.litellm, "completion", completion)

    configuration = judge.JudgeConfiguration(
        judge_provider="huggingface", judge_model="Org/Model", timeout=12
    )
    prompt = judge.JudgePrompt(
        "rules",
        "evidence",
        False,
        judge.JudgeInputControls(candidate_identity_hidden=True),
    )

    assert judge.default_judge_provider(configuration, prompt) == "  {}\n"
    client.assert_called_once_with(
        model="huggingface/Org/Model", timeout=12, credential_lookup_timeout=12
    )
    completion.assert_called_once_with(
        model="huggingface/Org/Model",
        messages=[
            {"role": "system", "content": "rules"},
            {"role": "user", "content": "evidence"},
        ],
        temperature=0.0,
        max_tokens=1000,
        timeout=12,
        api_key=None,
        num_retries=0,
    )
