"""Exercise the maintainer score command on a saved candidate run."""

from pathlib import Path

from inspect_ai.log import read_eval_log
from typer.testing import CliRunner

from tools.evals.gmuse_evals.cli import app


def test_score_saved_check_run(tmp_path: Path) -> None:
    runner = CliRunner()
    log_dir = tmp_path / "source"
    run = runner.invoke(app, ["run", "--mode", "check", "--log-dir", str(log_dir)])
    assert run.exit_code == 0, run.output
    (source,) = log_dir.glob("*.eval")
    original = source.read_bytes()
    output = tmp_path / "scored.eval"

    args = ["score", "--log", str(source), "--output", str(output)]
    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output
    assert "Deterministically scored: 5" in result.output
    assert "Provider calls: 0" in result.output
    assert source.read_bytes() == original
    with output.open("rb") as stream:
        scored = read_eval_log(stream)
    assert scored.samples is not None
    assert len(scored.samples) == 5
    for sample in scored.samples:
        assert sample.scores is not None
        metadata = sample.scores["gmuse_deterministic"].metadata
        assert metadata is not None
        assert metadata["scoring_status"] == "scored"

    saved = output.read_bytes()
    repeated = runner.invoke(app, args)
    assert repeated.exit_code == 2
    assert output.read_bytes() == saved


def test_score_reports_invalid_log(tmp_path: Path) -> None:
    source = tmp_path / "invalid.eval"
    source.write_bytes(b"not an Inspect log")
    output = tmp_path / "scored.eval"
    result = CliRunner().invoke(
        app, ["score", "--log", str(source), "--output", str(output)]
    )
    assert result.exit_code == 2, result.output
    assert "Error:" in result.output
    assert not output.exists()
