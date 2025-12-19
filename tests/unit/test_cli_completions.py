"""Unit tests for gmuse.cli.completions module."""

from unittest import mock

import pytest
import typer

from gmuse.cli.completions import (
    CompletionRequest,
    CompletionResponse,
    CompletionStatus,
    _load_zsh_template,
    completions_run_command,
    completions_zsh,
)


class TestDataStructures:
    """Tests for CompletionRequest and CompletionResponse data classes."""

    def test_completion_request_minimal(self) -> None:
        """CompletionRequest should work with only staged_diff."""
        request = CompletionRequest(staged_diff="diff content")

        assert request.staged_diff == "diff content"
        assert request.timeout == 3.0

    def test_completion_response_to_json_ok(self) -> None:
        """CompletionResponse.to_json should serialize correctly for ok status."""
        response = CompletionResponse(
            suggestion="feat: add login",
            status=CompletionStatus.OK,
            metadata={"elapsed_ms": 1200, "truncated": False},
        )

        import json

        parsed = json.loads(response.to_json())

        assert parsed["suggestion"] == "feat: add login"
        assert parsed["status"] == "ok"
        assert parsed["metadata"]["elapsed_ms"] == 1200
        assert parsed["metadata"]["truncated"] is False

    def test_completion_response_to_json_error(self) -> None:
        """CompletionResponse.to_json should serialize correctly for error status."""
        response = CompletionResponse(
            suggestion="",
            status=CompletionStatus.NO_STAGED_CHANGES,
            metadata={"elapsed_ms": 50},
        )

        import json

        parsed = json.loads(response.to_json())

        assert parsed["suggestion"] == ""
        assert parsed["status"] == "no_staged_changes"
        assert parsed["metadata"]["elapsed_ms"] == 50


class TestCompletionsZsh:
    """Tests for the 'gmuse git-completions zsh' command."""

    def test_completions_zsh_outputs_template(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """gmuse git-completions zsh should print the zsh completion template."""
        completions_zsh()

        captured = capsys.readouterr()

        # Check for key elements of the zsh template
        assert "#compdef git" in captured.out
        assert "_gmuse_cache_policy" in captured.out
        assert "_gmuse_git_commit_message" in captured.out
        assert "gmuse git-completions-run" in captured.out

    def test_zsh_template_contains_installation_instructions(self) -> None:
        """Zsh template should contain installation instructions."""
        template = _load_zsh_template()
        assert "Installation:" in template
        assert 'eval "$(gmuse git-completions zsh)"' in template
        assert "exec zsh" in template
        # Template should try multiple invocation strategies for the runtime helper
        assert "command -v gmuse" in template
        assert "python3 -m gmuse git-completions-run" in template

    def test_zsh_template_contains_env_var_checks(self) -> None:
        """Zsh template should check for configuration environment variables."""
        template = _load_zsh_template()
        assert "GMUSE_COMPLETIONS_ENABLED" in template
        assert "GMUSE_COMPLETIONS_TIMEOUT" in template
        assert "GMUSE_COMPLETIONS_CACHE_TTL" in template

    def test_zsh_template_resource_file_exists_and_matches(self) -> None:
        """The zsh template should be stored as a package resource and match the exported constant."""
        import importlib.resources as resources

        file_text = (
            resources.files("gmuse")
            .joinpath("templates", "zsh_completion.zsh")
            .read_text(encoding="utf-8")
        )

        assert file_text == _load_zsh_template()
        # Ensure we included multiple invocation strategies in the template
        assert "command -v gmuse" in file_text
        assert "python3 -m gmuse git-completions-run" in file_text

    def test_completions_zsh_missing_template_should_exit(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """If the template cannot be loaded, the command should exit non-zero with an error."""

        def raise_runtime() -> str:
            raise RuntimeError("missing template")

        monkeypatch.setattr("gmuse.cli.completions._load_zsh_template", raise_runtime)

        with pytest.raises(typer.Exit) as excinfo:
            completions_zsh()

        captured = capsys.readouterr()
        assert "missing template" in captured.err
        # Ensure exit code is non-zero
        assert (
            getattr(excinfo.value, "exit_code", getattr(excinfo.value, "code", 1)) != 0
        )


class TestCompletionsRun:
    """Tests for the 'gmuse git-completions-run' runtime helper command."""

    def _create_mock_diff(self) -> mock.Mock:
        """Create a mock StagedDiff object."""
        return mock.Mock(
            raw_diff="diff --git a/file.py b/file.py\n+print('hello')",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc123",
            size_bytes=50,
            truncated=False,
        )

    def test_completions_run_no_staged_changes(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """git-completions-run should return no_staged_changes status when no changes."""
        from gmuse.exceptions import NoStagedChangesError

        def mock_get_staged_diff() -> None:
            raise NoStagedChangesError("No staged changes")

        monkeypatch.setattr(
            "gmuse.cli.completions.get_staged_diff",
            mock_get_staged_diff,
        )

        completions_run_command(
            shell="zsh",
            for_command="git commit -m",
            timeout=3.0,
        )

        captured = capsys.readouterr()
        import json

        result = json.loads(captured.out)

        assert result["status"] == "no_staged_changes"
        assert result["suggestion"] == ""
        assert "elapsed_ms" in result["metadata"]

    def test_completions_run_success(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """git-completions-run should return ok status with suggestion on success."""
        from gmuse.commit import GenerationContext, GenerationResult

        mock_diff = self._create_mock_diff()

        monkeypatch.setattr(
            "gmuse.cli.completions.get_staged_diff",
            lambda: mock_diff,
        )

        # Mock git functions for commit history and instructions
        from gmuse.git import CommitHistory, RepositoryInstructions
        from unittest import mock

        monkeypatch.setattr(
            "gmuse.cli.completions.get_commit_history",
            lambda depth: CommitHistory(
                commits=[], depth=depth, repository_path="/test"
            ),
        )
        monkeypatch.setattr(
            "gmuse.cli.completions.load_repository_instructions",
            lambda: RepositoryInstructions(content="", file_path="", exists=False),
        )

        # Mock config loading
        monkeypatch.setattr(
            "gmuse.cli.completions.load_config",
            lambda: {},
        )
        monkeypatch.setattr(
            "gmuse.cli.completions.get_env_config",
            lambda: {},
        )
        monkeypatch.setattr(
            "gmuse.cli.completions.merge_config",
            lambda **kwargs: {"timeout": 3.0, "history_depth": 5},
        )

        # Mock generate_message
        def mock_generate_message(**kwargs: object) -> GenerationResult:
            context = kwargs.get("context")
            return GenerationResult(
                message="feat: add hello world",
                context=context,  # type: ignore
            )

        monkeypatch.setattr(
            "gmuse.cli.completions.generate_message",
            mock_generate_message,
        )

        completions_run_command(
            shell="zsh",
            for_command="git commit -m",
            timeout=3.0,
        )

        captured = capsys.readouterr()
        import json

        result = json.loads(captured.out)

        assert result["status"] == "ok"
        assert result["suggestion"] == "feat: add hello world"
        assert "elapsed_ms" in result["metadata"]

    def test_completions_run_llm_error_auth(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """git-completions-run should return offline status for auth errors."""
        from gmuse.exceptions import LLMError

        mock_diff = self._create_mock_diff()

        monkeypatch.setattr(
            "gmuse.cli.completions.get_staged_diff",
            lambda: mock_diff,
        )

        # Mock git functions for commit history and instructions
        from gmuse.git import CommitHistory, RepositoryInstructions

        monkeypatch.setattr(
            "gmuse.cli.completions.get_commit_history",
            lambda depth: CommitHistory(
                commits=[], depth=depth, repository_path="/test"
            ),
        )
        monkeypatch.setattr(
            "gmuse.cli.completions.load_repository_instructions",
            lambda: RepositoryInstructions(content="", file_path="", exists=False),
        )

        monkeypatch.setattr(
            "gmuse.cli.completions.load_config",
            lambda: {},
        )
        monkeypatch.setattr(
            "gmuse.cli.completions.get_env_config",
            lambda: {},
        )
        monkeypatch.setattr(
            "gmuse.cli.completions.merge_config",
            lambda **kwargs: {"timeout": 3.0, "history_depth": 5},
        )

        def mock_generate_message(**kwargs: object) -> None:
            raise LLMError("API key not configured")

        monkeypatch.setattr(
            "gmuse.cli.completions.generate_message",
            mock_generate_message,
        )

        completions_run_command(
            shell="zsh",
            for_command="git commit -m",
            timeout=3.0,
        )

        captured = capsys.readouterr()
        import json

        result = json.loads(captured.out)

        assert result["status"] == "offline"
        assert "api key" in result["metadata"]["error"].lower()

    def test_completions_run_timeout_from_env(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """git-completions-run should respect GMUSE_COMPLETIONS_TIMEOUT env var."""
        from gmuse.exceptions import NoStagedChangesError

        monkeypatch.setenv("GMUSE_COMPLETIONS_TIMEOUT", "5.0")

        def mock_get_staged_diff() -> None:
            raise NoStagedChangesError("No staged changes")

        monkeypatch.setattr(
            "gmuse.cli.completions.get_staged_diff",
            mock_get_staged_diff,
        )

        # Just verify it doesn't crash with env var set
        completions_run_command(
            shell="zsh",
            for_command="git commit -m",
            timeout=3.0,  # CLI default, should be overridden by env
        )

        captured = capsys.readouterr()
        import json

        result = json.loads(captured.out)
        assert result["status"] == "no_staged_changes"

    def test_completions_run_invalid_shell(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """git-completions-run should return error status for unsupported shell."""
        completions_run_command(
            shell="bash",
            for_command="git commit -m",
            timeout=3.0,
        )

        captured = capsys.readouterr()
        import json

        result = json.loads(captured.out)

        assert result["status"] == "error"
        assert result["suggestion"] == ""
        assert "Unsupported shell: bash" in result["metadata"]["error"]
        assert "elapsed_ms" in result["metadata"]

    def test_completions_run_invalid_command(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """git-completions-run should return error status for invalid command."""
        completions_run_command(
            shell="zsh",
            for_command="svn commit",
            timeout=3.0,
        )

        captured = capsys.readouterr()
        import json

        result = json.loads(captured.out)

        assert result["status"] == "error"
        assert result["suggestion"] == ""
        assert "Invalid command: svn commit" in result["metadata"]["error"]
        assert "git commit" in result["metadata"]["error"]
        assert "elapsed_ms" in result["metadata"]


class TestCompletionStatus:
    """Tests for CompletionStatus enum."""

    def test_status_values(self) -> None:
        """CompletionStatus should have expected string values."""
        assert CompletionStatus.OK.value == "ok"
        assert CompletionStatus.TIMEOUT.value == "timeout"
        assert CompletionStatus.OFFLINE.value == "offline"
        assert CompletionStatus.NO_STAGED_CHANGES.value == "no_staged_changes"
        assert CompletionStatus.ERROR.value == "error"
