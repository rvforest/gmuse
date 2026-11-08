from __future__ import annotations

from typer.testing import CliRunner

from tools.evals.gmuse_evals.cli import app


def test_check_smoke_writes_one_inspect_result_per_entry(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "check",
            "--suite",
            "smoke",
            "--log-dir",
            str(tmp_path / "inspect"),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "Provider calls: 0" in result.stdout
    assert "Completed entries: 5" in result.stdout
    assert len(list((tmp_path / "inspect").glob("*.eval"))) == 1


def test_check_rejects_model_before_execution(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--mode",
            "check",
            "--suite",
            "smoke",
            "--model",
            "provider/model",
            "--log-dir",
            str(tmp_path / "inspect"),
        ],
    )

    assert result.exit_code != 0
    assert "only valid" in result.stdout
    assert not (tmp_path / "inspect").exists()
