from __future__ import annotations

from typer.testing import CliRunner
import pytest

from tools.evals.gmuse_evals import cli
from tools.evals.gmuse_evals.cli import app


def test_live_plan_displays_preflight_without_prompt_or_execution(
    tmp_path, monkeypatch
):
    log_dir = tmp_path / "new-inspect-logs"
    calls: list[object] = []

    def unexpected_execution(*args, **kwargs):
        calls.append((args, kwargs))
        pytest.fail("a plan-only invocation must not call Inspect")

    monkeypatch.setattr(cli, "run_inspect_plan", unexpected_execution)
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
            "--plan",
            "--log-dir",
            str(log_dir),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "Suite: smoke" in result.stdout
    assert "Suite revision: 1" in result.stdout
    assert "Cases: 2" in result.stdout
    assert "Models: test/model" in result.stdout
    assert "Planned entries: 5" in result.stdout
    assert "Sample limit: 5" in result.stdout
    assert f"Inspect log directory: {log_dir}" in result.stdout
    assert "Confirmation: plan_only" in result.stdout
    assert "history_depth" in result.stdout
    assert "Proceed with live provider calls?" not in result.stdout
    assert "Completed entries:" not in result.stdout
    assert calls == []
    assert not log_dir.exists()
