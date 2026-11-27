from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import Mock

from noxfile import evals_check


def test_inspect_is_not_a_runtime_dependency() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    runtime = pyproject.split("[project.optional-dependencies]", 1)[0]
    assert "inspect-ai" not in runtime


def test_workflows_have_no_live_eval() -> None:
    workflows = Path(".github/workflows")
    workflow_files = sorted((*workflows.glob("*.yml"), *workflows.glob("*.yaml")))
    assert workflow_files
    for path in workflow_files:
        assert not re.search(
            r"""--mode[\s=]+['"]?live\b""", path.read_text(encoding="utf-8")
        ), path


def test_evals_check_runs_offline_without_provider_credentials() -> None:
    session = Mock()

    evals_check.func(session)

    (run,) = session.run.call_args_list
    assert run.args[:8] == (
        "python",
        "-m",
        "tools.evals.gmuse_evals",
        "run",
        "--mode",
        "check",
        "--suite",
        "smoke",
    )
    env = run.kwargs["env"]
    assert env["LITELLM_LOCAL_MODEL_COST_MAP"] == "True"
    for variable in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "COHERE_API_KEY",
        "GEMINI_API_KEY",
    ):
        assert env[variable] == ""
