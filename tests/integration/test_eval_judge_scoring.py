"""Exercise guarded judge scoring and resumed attempts using a fake provider."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from inspect_ai.log import read_eval_log
from typer.testing import CliRunner

from tools.evals.gmuse_evals import cli, judge
from tools.evals.gmuse_evals.calibration import CalibrationExample, run_calibration
from tools.evals.gmuse_evals.cli import app
from tools.evals.gmuse_evals.inspect_runner import run_inspect_plan
from tools.evals.gmuse_evals.inspect_scorers import (
    InspectScoringError,
    prepare_inspect_judge_plan,
)
from tools.evals.gmuse_evals.run_plan import Guardrails, build_run_plan
from tools.evals.gmuse_evals.scoring_evidence import recover_scoring_evidence
from tools.evals.gmuse_evals.validate import validate_suite

ASSETS = Path(__file__).resolve().parents[2] / "evals"


@pytest.fixture(scope="module")
def candidate_log(tmp_path_factory: pytest.TempPathFactory) -> Path:
    plan = build_run_plan(validate_suite(ASSETS, "smoke"), mode="check")

    def candidate(**kwargs: object) -> str:
        prompt = str(kwargs["user_prompt"])
        if "Synthetic safety fixture" in prompt:
            return "x" * 1001
        # Freeform accepts a conventional-looking subject as well.
        return "docs: update documentation"

    run = run_inspect_plan(
        plan,
        log_dir=tmp_path_factory.mktemp("judge-source"),
        response_generator=candidate,
    )
    return Path(run.logs[0].location)


def _args(source: Path, output: Path, limit: int = 2) -> list[str]:
    return [
        "score",
        "--log",
        str(source),
        "--output",
        str(output),
        "--evals-dir",
        str(ASSETS),
        "--judge-model",
        "openai/gpt-4o-mini",
        "--limit-samples",
        str(limit),
    ]


def _records(output: Path) -> list[dict[str, Any]]:
    with output.open("rb") as stream:
        log = read_eval_log(stream)
    assert log.samples is not None
    records = []
    for sample in log.samples:
        assert sample.scores is not None
        metadata = sample.scores["gmuse_judge"].metadata
        assert metadata is not None
        records.append(metadata)
    return records


def _response(prompt: judge.JudgePrompt, *, gate: bool = False) -> str:
    style = prompt.style_context_applicable
    return json.dumps(
        {
            "judge_output_schema_version": 1,
            "scores": {
                "accuracy": 4,
                "message_quality": 3,
                "style_context_fit": 4 if style else None,
            },
            "usability": "usable",
            "hard_failure_findings": ["privacy_leak"] if gate else [],
            "quality_errors": [],
            "rationales": {
                "accuracy": "Describes the documentation change.",
                "message_quality": "Clear subject.",
                "style_context_fit": "Fits the previous subjects." if style else None,
                "usability": "Useful description.",
            },
        }
    )


def test_live_plan_budget_confirmation_and_hard_gate_skip(
    candidate_log: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[judge.JudgePrompt] = []

    def provider(
        _configuration: judge.JudgeConfiguration, prompt: judge.JudgePrompt
    ) -> str:
        seen.append(prompt)
        return _response(prompt, gate=True)

    monkeypatch.setattr(judge, "default_judge_provider", provider)
    output = tmp_path / "scored.eval"
    runner = CliRunner()
    denied = runner.invoke(app, [*_args(candidate_log, output, 1), "--yes"])
    assert denied.exit_code == 2, denied.output
    without_confirmation = runner.invoke(app, _args(candidate_log, output))
    assert without_confirmation.exit_code == 2, without_confirmation.output
    planned = runner.invoke(app, [*_args(candidate_log, output), "--plan"])
    assert planned.exit_code == 0, planned.output
    assert "Planned judge calls: 2" in planned.output

    with monkeypatch.context() as terminal:
        stdin = SimpleNamespace(isatty=lambda: True)
        terminal.setattr(cli, "sys", SimpleNamespace(stdin=stdin))
        declined = runner.invoke(app, _args(candidate_log, output), input="n\n")
    assert declined.exit_code == 0, declined.output
    assert declined.output.index("Planned judge calls: 2") < declined.output.index(
        "Proceed with live judge scoring?"
    )
    assert "Judge scoring cancelled. Provider calls: 0" in declined.output
    assert len(seen) == 0
    assert not output.exists()

    scored = runner.invoke(app, [*_args(candidate_log, output), "--yes"])
    assert scored.exit_code == 0, scored.output
    assert len(seen) == 2
    records = _records(output)
    assert len(records) == 5
    judged = [record for record in records if record["judge_result"]]
    assert len(judged) == 2
    assert all(
        record["effective_ratings"]["usability"] == "unusable" for record in records
    )
    assert all(record["effective_ratings"]["accuracy"] == 4 for record in judged)
    assert all(record["assessment_evidence_ref"] for record in judged)
    assert all(
        record["judge_input_controls"]["candidate_identity_hidden"] for record in judged
    )
    assert all(
        record["judge_result"]["raw_response_metadata"]["sha256"] for record in judged
    )


@pytest.mark.parametrize(
    ("guardrails", "args", "guidance"),
    [
        (Guardrails(), [], "explicit positive --limit-samples"),
        (
            Guardrails(max_samples=2, max_tokens=100),
            ["--limit-samples", "2", "--limit-tokens", "100"],
            "Use --limit-samples, --max-tokens, and --timeout.",
        ),
        (
            Guardrails(max_samples=1),
            ["--limit-samples", "1"],
            "Planned judge calls 2 exceed --limit-samples 1.",
        ),
    ],
)
def test_judge_limit_errors_get_flag_guidance_at_the_cli(
    candidate_log: Path,
    tmp_path: Path,
    guardrails: Guardrails,
    args: list[str],
    guidance: str,
) -> None:
    output = tmp_path / "scored.eval"
    with pytest.raises(InspectScoringError) as error:
        prepare_inspect_judge_plan(
            candidate_log,
            output,
            configuration=judge.JudgeConfiguration(
                judge_provider="openai", judge_model="openai/gpt-4o-mini"
            ),
            guardrails=guardrails,
            evals_dir=ASSETS,
        )
    assert "--" not in str(error.value)

    result = CliRunner().invoke(
        app, [*_args(candidate_log, output)[:-2], *args, "--plan"]
    )
    assert result.exit_code == 2, result.output
    assert guidance in result.output
    assert not output.exists()


@pytest.mark.parametrize(
    ("failure", "category"),
    [
        (PermissionError("unauthorized"), "auth_error"),
        (RuntimeError("rate limit"), "rate_limit"),
        (TimeoutError(), "timeout"),
        (ConnectionError("DNS"), "network_error"),
        (ValueError("context length"), "context_length"),
        ("", "empty_response"),
        ("{", "judge_parse_error"),
    ],
)
def test_judge_operational_failure_has_no_quality_rating(
    candidate_log: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception | str,
    category: str,
) -> None:
    def provider(
        _configuration: judge.JudgeConfiguration, _prompt: judge.JudgePrompt
    ) -> str:
        if isinstance(failure, Exception):
            raise failure
        return failure

    monkeypatch.setattr(judge, "default_judge_provider", provider)
    output = tmp_path / "scored.eval"
    run = CliRunner().invoke(app, [*_args(candidate_log, output), "--yes"])
    assert run.exit_code == 0, run.output
    failed = [
        record for record in _records(output) if record["judge_operational_error"]
    ]
    assert len(failed) == 2
    for record in failed:
        assert record["judge_operational_error"]["category"] == category
        assert record["operational_errors"] == [category]
        assert record["scoring_status"] == "unscored"
        assert record["quality_errors"] == []
        assert record["effective_ratings"]["accuracy"] is None


def test_resume_skips_completed_calls_and_rejects_incompatible_configuration(
    candidate_log: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def provider(
        _configuration: judge.JudgeConfiguration, prompt: judge.JudgePrompt
    ) -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            raise KeyboardInterrupt
        return _response(prompt)

    monkeypatch.setattr(judge, "default_judge_provider", provider)
    first, output = tmp_path / "first.eval", tmp_path / "resumed.eval"
    runner = CliRunner()
    attempt = runner.invoke(app, [*_args(candidate_log, first), "--yes"])
    assert attempt.exit_code == 130, attempt.output
    assert first.exists()
    assert sum(bool(record["judge_result"]) for record in _records(first)) == 1
    original = first.read_bytes()

    args = [*_args(candidate_log, output, 1), "--resume", str(first), "--yes"]
    invalid = runner.invoke(app, [*args, "--temperature", "0.5"])
    assert invalid.exit_code == 2, invalid.output
    assert attempts == 2
    assert not output.exists()

    resumed = runner.invoke(app, args)
    assert resumed.exit_code == 0, resumed.output
    assert attempts == 3
    assert first.read_bytes() == original
    judged = [item for item in _records(output) if item["judge_result"]]
    assert len(judged) == 2
    assert sum(bool(item.get("reused_from_scoring_run_id")) for item in judged) == 1


def test_missing_evidence_skips_judging(
    candidate_log: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_call(*args: object) -> str:
        pytest.fail("missing evidence must prevent provider calls")

    monkeypatch.setattr(judge, "default_judge_provider", unexpected_call)
    moved = tmp_path / "candidate.eval"
    moved.write_bytes(candidate_log.read_bytes())
    output = tmp_path / "scored.eval"
    result = CliRunner().invoke(app, [*_args(moved, output), "--yes"])
    assert result.exit_code == 0, result.output
    assert "Provider calls: 0" in result.output
    assert (
        sum(
            record["unscored_reason"] == "missing_assessment_evidence"
            for record in _records(output)
        )
        == 2
    )


def test_judge_response_keeps_echoed_evidence_in_private_store(
    candidate_log: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def provider(
        _configuration: judge.JudgeConfiguration, prompt: judge.JudgePrompt
    ) -> str:
        result = json.loads(_response(prompt))
        result["rationales"]["accuracy"] = json.loads(prompt.user_prompt)["staged_diff"]
        return json.dumps(result)

    monkeypatch.setattr(judge, "default_judge_provider", provider)
    output = tmp_path / "scored.eval"
    result = CliRunner().invoke(app, [*_args(candidate_log, output), "--yes"])
    assert result.exit_code == 0, result.output
    for item in _records(output):
        if judged := item["judge_result"]:
            assert judged["rationales_redacted"] is True
            assert judged["rationales"]["accuracy"] == "[private evidence]"
            raw = candidate_log.parent / judged["raw_response_metadata"]["locator"]
            assert "diff --git" in json.loads(raw.read_text())["rationales"]["accuracy"]


def test_calibration_report_is_linked_to_compatible_judgments(
    candidate_log: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def provider(
        _configuration: judge.JudgeConfiguration, prompt: judge.JudgePrompt
    ) -> str:
        return _response(prompt)

    with candidate_log.open("rb") as stream:
        log = read_eval_log(stream)
    case = next(
        item
        for item in validate_suite(ASSETS, "smoke").resolved_cases
        if item.case.id == "docs-history"
    )
    assert log.samples is not None
    sample = next(
        item for item in log.samples if item.metadata["case_id"] == case.case.id
    )
    evidence = recover_scoring_evidence(
        candidate_log, sample.metadata, log.metadata, case
    )
    example = CalibrationExample(
        example_id="docs-review",
        resolved_case=case,
        staged_diff=evidence.staged_diff,
        context=evidence.context,
        generated_message=sample.metadata["generated_message"],
        format_name=sample.metadata["format"],
        max_chars=sample.metadata["max_chars"],
        expected_usability="usable",
    )
    report = run_calibration(
        [example],
        judge.JudgeConfiguration(
            judge_model="openai/gpt-4o-mini", judge_provider="openai"
        ),
        expected_label_version="docs-labels-1",
        provider_call=provider,
    )
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(judge, "default_judge_provider", provider)
    output = tmp_path / "scored.eval"
    result = CliRunner().invoke(
        app,
        [
            *_args(candidate_log, output),
            "--calibration-report",
            str(report_path),
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Judge samples without matching calibration" not in result.output
    judged = [record for record in _records(output) if record["judge_result"]]
    assert len(judged) == 2
    assert all(
        record["calibration_report_id"] == report["calibration_report_id"]
        for record in judged
    )
