from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from tools.evals.gmuse_evals import cli
from tools.evals.gmuse_evals.cli import app
from tools.evals.gmuse_evals.inspect_runner import run_inspect_plan


def _mock_terminal(monkeypatch, *, interactive: bool) -> None:
    terminal = SimpleNamespace(isatty=lambda: interactive)
    monkeypatch.setattr(cli, "sys", SimpleNamespace(stdin=terminal, stdout=terminal))


@pytest.mark.parametrize(
    ("option", "value"),
    [
        ("--limit-tokens", "1000"),
        ("--limit-cost", "1"),
        ("--limit-time", "30"),
        ("--concurrency", "2"),
        ("--concurrency", "0"),
    ],
)
def test_unsupported_limits_fail_before_execution(tmp_path, monkeypatch, option, value):
    def unexpected_execution(*args, **kwargs):
        pytest.fail("unsupported limits must fail before execution")

    monkeypatch.setattr(
        "tools.evals.gmuse_evals.cli.run_inspect_plan", unexpected_execution
    )
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "live",
            "--suite",
            "smoke",
            "--model",
            "test/model",
            "--limit-samples",
            "5",
            option,
            value,
            "--yes",
            "--log-dir",
            str(tmp_path / "inspect"),
        ],
    )
    assert result.exit_code == 2
    assert not (tmp_path / "inspect").exists()


def test_concurrency_alone_is_not_a_spend_guardrail():
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "live",
            "--suite",
            "smoke",
            "--model",
            "test/model",
            "--concurrency",
            "1",
            "--yes",
        ],
    )
    assert result.exit_code == 2
    assert "--limit-samples" in result.stdout


def test_live_preflight_requires_model_and_guardrail() -> None:
    runner = CliRunner()
    missing_model = runner.invoke(app, ["run", "--mode", "live", "--suite", "smoke"])
    assert missing_model.exit_code != 0
    assert "model" in missing_model.stdout

    missing_limit = runner.invoke(
        app, ["run", "--mode", "live", "--suite", "smoke", "--model", "test/model"]
    )
    assert missing_limit.exit_code != 0
    assert "guardrail" in missing_limit.stdout


def test_invalid_live_suite_fails_before_inspect_execution(tmp_path, monkeypatch):
    def unexpected_execution(*args, **kwargs):
        pytest.fail("invalid suites must fail before Inspect execution")

    monkeypatch.setattr(cli, "run_inspect_plan", unexpected_execution)
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "live",
            "--suite",
            "missing-suite",
            "--evals-dir",
            str(tmp_path),
            "--model",
            "test/model",
            "--limit-samples",
            "5",
            "--yes",
            "--log-dir",
            str(tmp_path / "inspect"),
        ],
    )
    assert result.exit_code == 2
    assert "Error:" in result.stdout
    assert not (tmp_path / "inspect").exists()


def test_live_empty_selection_fails_before_inspect_execution(tmp_path, monkeypatch):
    empty = replace(cli.validate_suite(Path("evals"), "smoke"), resolved_cases=())
    monkeypatch.setattr(cli, "validate_suite", lambda *args, **kwargs: empty)

    def unexpected_execution(*args, **kwargs):
        pytest.fail("an empty selection must fail before Inspect execution")

    monkeypatch.setattr(cli, "run_inspect_plan", unexpected_execution)
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "live",
            "--model",
            "test/model",
            "--limit-samples",
            "5",
            "--yes",
            "--log-dir",
            str(tmp_path / "inspect"),
        ],
    )
    assert result.exit_code == 2
    assert "no matching cases were selected" in result.stdout
    assert not (tmp_path / "inspect").exists()


def test_live_limit_overflow_fails_before_confirmation(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "live",
            "--suite",
            "smoke",
            "--model",
            "test/model",
            "--limit-samples",
            "1",
            "--log-dir",
            str(tmp_path / "inspect"),
        ],
    )
    assert result.exit_code != 0
    assert "No provider calls" in result.stdout
    assert not (tmp_path / "inspect").exists()


@pytest.mark.parametrize("show_config", [False, True])
def test_live_cancellation_does_not_create_logs(
    tmp_path, monkeypatch, show_config: bool
) -> None:
    _mock_terminal(monkeypatch, interactive=True)
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "live",
            "--suite",
            "smoke",
            "--model",
            "test/model",
            "--limit-samples",
            "5",
            "--log-dir",
            str(tmp_path / "inspect"),
            *(["--show-config"] if show_config else []),
        ],
        input="n\n",
    )
    assert result.exit_code == 0
    assert "Planned entries: 5" in result.stdout
    assert "Models: test/model" in result.stdout
    assert "Sample limit: 5" in result.stdout
    assert "'history_depth':" in result.stdout
    assert "cancelled" in result.stdout.lower()
    assert not (tmp_path / "inspect").exists()


@pytest.mark.parametrize("limit", [None, "0", "-1", "1"])
def test_yes_does_not_bypass_live_sample_guardrails(tmp_path, monkeypatch, limit):
    def unexpected_execution(*args, **kwargs):
        pytest.fail("invalid live limits must fail before Inspect execution")

    monkeypatch.setattr(cli, "run_inspect_plan", unexpected_execution)
    args = [
        "run",
        "--mode",
        "live",
        "--suite",
        "smoke",
        "--model",
        "test/model",
        "--yes",
        "--log-dir",
        str(tmp_path / "inspect"),
    ]
    if limit is not None:
        args.extend(["--limit-samples", limit])

    result = CliRunner().invoke(app, args)

    assert result.exit_code == 2
    assert (
        "provider calls" in result.stdout.lower()
        or "guardrail" in result.stdout.lower()
    )
    assert not (tmp_path / "inspect").exists()


def test_noninteractive_live_run_without_yes_fails_with_guidance(tmp_path, monkeypatch):
    calls: list[object] = []
    monkeypatch.setattr(
        cli,
        "run_inspect_plan",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    _mock_terminal(monkeypatch, interactive=False)

    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "live",
            "--suite",
            "smoke",
            "--model",
            "test/model",
            "--limit-samples",
            "5",
            "--log-dir",
            str(tmp_path / "inspect"),
        ],
    )

    assert result.exit_code == 2
    assert "--yes" in result.stdout
    assert calls == []
    assert not (tmp_path / "inspect").exists()


def test_existing_inspect_run_identity_fails_before_confirmation(tmp_path, monkeypatch):
    log_dir = tmp_path / "inspect"
    log_dir.mkdir()
    (log_dir / "prior.eval").touch()
    calls: list[object] = []
    monkeypatch.setattr(
        cli,
        "run_inspect_plan",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "live",
            "--suite",
            "smoke",
            "--model",
            "test/model",
            "--limit-samples",
            "5",
            "--log-dir",
            str(log_dir),
        ],
    )

    assert result.exit_code == 2
    assert "conflicting run identity" in result.stdout
    assert "Proceed with live provider calls?" not in result.stdout
    assert calls == []


@pytest.mark.parametrize("yes", [False, True])
def test_live_plan_is_displayed_before_inspect_execution(tmp_path, monkeypatch, yes):
    events: list[str] = []
    original_echo = cli.typer.echo

    def tracked_echo(message=None, *args, **kwargs):
        if isinstance(message, str) and message.startswith("Planned entries:"):
            events.append("plan")
        return original_echo(message, *args, **kwargs)

    def mocked_execution(*args, **kwargs):
        events.append("inspect")
        return SimpleNamespace(results=(), logs=(), log_dir=tmp_path / "inspect")

    monkeypatch.setattr(cli.typer, "echo", tracked_echo)
    monkeypatch.setattr(cli, "run_inspect_plan", mocked_execution)
    _mock_terminal(monkeypatch, interactive=not yes)
    args = [
        "run",
        "--mode",
        "live",
        "--suite",
        "smoke",
        "--model",
        "test/model",
        "--limit-samples",
        "5",
        "--log-dir",
        str(tmp_path / "inspect"),
    ]
    invocation_args = [*args]
    if yes:
        invocation_args.append("--yes")
    result = CliRunner().invoke(app, invocation_args, input="y\n")

    assert result.exit_code == 0, result.stdout
    assert events.index("plan") < events.index("inspect")
    assert ("Confirmation: --yes" in result.stdout) is yes
    assert "Confirmation: interactive" in result.stdout or yes


def test_fresh_rerun_requires_limits_and_confirmation(tmp_path, monkeypatch):
    calls = []

    def response(**kwargs):
        calls.append(kwargs)
        return "docs: update documentation"

    def execute(plan, **kwargs):
        return run_inspect_plan(plan, response_generator=response, **kwargs)

    monkeypatch.setattr(cli, "run_inspect_plan", execute)
    _mock_terminal(monkeypatch, interactive=False)
    runner = CliRunner()
    args = ["run", "--mode", "live", "--model", "test/model"]
    original_dir = tmp_path / "original"
    original = runner.invoke(
        app, [*args, "--limit-samples", "5", "--yes", "--log-dir", str(original_dir)]
    )
    assert original.exit_code == 0, original.output
    assert len(calls) == 5
    (original_log,) = original_dir.glob("*.eval")
    prior_evidence = original_log.read_bytes()

    rerun_dir = tmp_path / "rerun"
    args.extend(["--log-dir", str(rerun_dir)])
    for guardrails, error in [
        (["--yes"], "explicit --limit-samples"),
        (["--limit-samples", "1", "--yes"], "exceed --limit-samples"),
        (["--limit-samples", "5"], "require --yes"),
    ]:
        rerun = runner.invoke(app, [*args, *guardrails])
        assert rerun.exit_code == 2, rerun.output
        assert error in rerun.stdout
        assert len(calls) == 5
        assert not rerun_dir.exists()
    assert original_log.read_bytes() == prior_evidence
