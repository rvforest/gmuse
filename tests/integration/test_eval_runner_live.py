from __future__ import annotations

from typer.testing import CliRunner
import pytest

from tools.evals.gmuse_evals.cli import app


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


def test_live_cancellation_does_not_create_logs(tmp_path) -> None:
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
        input="n\n",
    )
    assert result.exit_code == 0
    assert "cancelled" in result.stdout.lower()
    assert not (tmp_path / "inspect").exists()
