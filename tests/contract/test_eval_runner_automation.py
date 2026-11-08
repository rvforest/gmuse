from __future__ import annotations

from pathlib import Path


def test_inspect_is_not_a_runtime_dependency_and_workflows_have_no_live_eval() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    runtime = pyproject.split("[project.optional-dependencies]", 1)[0]
    assert "inspect-ai" not in runtime
    workflows = Path(".github/workflows")
    if workflows.exists():
        assert "--mode live" not in "\n".join(
            path.read_text(encoding="utf-8") for path in workflows.glob("*.yml")
        )
