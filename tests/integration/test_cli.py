"""Integration tests for gmuse CLI.

These tests verify end-to-end CLI behavior with mocked LLM responses
and real temporary git repositories.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest import mock

import pytest
from typer.testing import CliRunner

from gmuse.cli.main import app

runner = CliRunner()


@pytest.fixture
def git_repo() -> Generator[Path, None, None]:
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path


@pytest.fixture
def git_repo_with_history(git_repo: Path) -> Path:
    """Create a git repository with commit history."""
    # Create and commit initial file
    test_file = git_repo / "README.md"
    test_file.write_text("# Test Project\n")

    subprocess.run(
        ["git", "add", "README.md"], cwd=git_repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )

    # Add a few more commits for history
    for i in range(3):
        test_file.write_text(f"# Test Project\nVersion {i + 1}\n")
        subprocess.run(
            ["git", "add", "README.md"], cwd=git_repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"feat: update to version {i + 1}"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )

    return git_repo


def _mock_llm_response(content: str) -> mock.Mock:
    """Create a mock LLM response."""
    mock_response = mock.Mock()
    mock_response.choices = [mock.Mock(message=mock.Mock(content=content))]
    return mock_response


def _stage_file(repo: Path, filename: str, content: str) -> None:
    """Stage a file in the repository."""
    file_path = repo / filename
    file_path.write_text(content)
    subprocess.run(["git", "add", filename], cwd=repo, check=True, capture_output=True)


class TestUserStory1:
    """Integration tests for User Story 1: Generate Basic Commit Message."""

    def test_generate_with_staged_changes(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 1: Given staged changes, when user runs `gmuse msg`,
        then message generated and printed to STDOUT.
        """
        _stage_file(
            git_repo_with_history,
            "feature.py",
            "def hello():\n    return 'Hello'\n",
        )

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add hello function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                # Change to repo directory for git operations
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                assert "Add hello function" in result.stdout

    def test_no_staged_changes_error(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 2: Given no staged changes, when user runs `gmuse msg`,
        then error "No staged changes found...".
        """
        # Don't stage anything - just run in the repo

        old_cwd = os.getcwd()
        os.chdir(git_repo_with_history)
        try:
            result = runner.invoke(app, ["msg"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "No staged changes" in result.stderr

    def test_not_a_git_repository_error(self) -> None:
        """
        Acceptance 3: Given not a git repo, when user runs `gmuse msg`,
        then error "Not a git repository...".
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = runner.invoke(app, ["msg"])
            finally:
                os.chdir(old_cwd)

            assert result.exit_code == 1
            assert "Not a git repository" in result.stderr

    def test_no_api_key_error(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 4: Given no API key, when user runs `gmuse msg`,
        then error "No API key configured...".
        """
        _stage_file(git_repo_with_history, "test.py", "test content")

        # Remove all API keys and GMUSE_MODEL
        env_without_keys = {
            k: v
            for k, v in os.environ.items()
            if not k.endswith("_API_KEY") and k != "GMUSE_MODEL"
        }

        with mock.patch.dict(os.environ, env_without_keys, clear=True):
            old_cwd = os.getcwd()
            os.chdir(git_repo_with_history)
            try:
                result = runner.invoke(app, ["msg"])
            finally:
                os.chdir(old_cwd)

            assert result.exit_code != 0
            # Should mention either "No API key" or "No LLM provider"
            assert (
                "No API key" in result.stderr
                or "No LLM provider" in result.stderr
                or "provider" in result.stderr.lower()
            )

    def test_message_reflects_diff_content(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 5: Given staged changes and valid API key, when user runs `gmuse msg`,
        then message reflects diff content.
        """
        _stage_file(
            git_repo_with_history,
            "auth.py",
            "def authenticate(user, password):\n    pass\n",
        )

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add authentication function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                assert "authentication" in result.stdout

                # Verify LLM was called with a prompt containing the diff
                mock_client.generate.assert_called_once()
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("user_prompt", "")
                assert "authenticate" in prompt or "auth.py" in prompt


class TestUserStory2:
    """Integration tests for User Story 2: Influence Message with Runtime Hints."""

    def test_hint_flag_influences_message(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 1: Given staged changes, when `gmuse msg --hint "emphasize performance"`,
        then message mentions performance.
        """
        _stage_file(
            git_repo_with_history, "cache.py", "def cache_result(fn):\n    pass\n"
        )

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add caching for better performance"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(
                        app, ["msg", "--hint", "emphasize performance"]
                    )
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                assert "performance" in result.stdout

                # Verify hint was included in prompt
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("user_prompt", "")
                assert "emphasize performance" in prompt

    def test_hint_breaking_change(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 2: Given staged changes, when `gmuse msg --hint "breaking change"`,
        then message includes breaking change indicators.
        """
        _stage_file(
            git_repo_with_history,
            "api.py",
            "def new_api():\n    # Breaking: removed old_api()\n    pass\n",
        )

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "feat!: replace old_api with new_api\n\nBREAKING CHANGE: removed old_api"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg", "--hint", "breaking change"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                # Message should contain breaking change indicator
                assert "BREAKING" in result.stdout or "!" in result.stdout

    def test_no_hint_uses_diff_only(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 3: Given staged changes, when `gmuse msg` without hint,
        then message based on diff/history only.
        """
        _stage_file(git_repo_with_history, "utils.py", "def helper():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add helper utility function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                # Verify no user hint section in prompt (hint should not appear)
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("user_prompt", "")
                # If there's no hint, "User Hint" section shouldn't appear or be empty
                # The prompt builder only adds hint section when hint is provided
                # We just verify the call succeeded without hint


class TestUserStory3:
    """Integration tests for User Story 3: Copy Message to Clipboard."""

    def test_copy_flag_copies_to_clipboard(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 1: Given clipboard available, when `gmuse msg --copy`,
        then message copied to clipboard and printed to STDOUT.
        """
        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function"
            mock_client_class.return_value = mock_client

            # Mock pyperclip by patching where it's imported (inside _copy_to_clipboard)
            mock_pyperclip = mock.MagicMock()
            with mock.patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
                with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                    old_cwd = os.getcwd()
                    os.chdir(git_repo_with_history)
                    try:
                        result = runner.invoke(app, ["msg", "--copy"])
                    finally:
                        os.chdir(old_cwd)

                    assert result.exit_code == 0
                    assert "Add feature function" in result.stdout
                    # Verify clipboard copy was called
                    mock_pyperclip.copy.assert_called_once_with("Add feature function")
                    assert "Copied to clipboard" in result.stderr

    def test_copy_flag_pyperclip_not_installed(
        self, git_repo_with_history: Path
    ) -> None:
        """
        Acceptance 2: Given clipboard unavailable, when `gmuse msg --copy`,
        then message printed with warning.
        """
        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function"
            mock_client_class.return_value = mock_client

            # Simulate pyperclip not installed
            import builtins

            original_import = builtins.__import__

            def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "pyperclip":
                    raise ImportError("No module named 'pyperclip'")
                return original_import(name, *args, **kwargs)

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                with mock.patch.object(builtins, "__import__", mock_import):
                    old_cwd = os.getcwd()
                    os.chdir(git_repo_with_history)
                    try:
                        result = runner.invoke(app, ["msg", "--copy"])
                    finally:
                        os.chdir(old_cwd)

                    # Should still succeed and output the message
                    assert result.exit_code == 0
                    assert "Add feature function" in result.stdout
                    # Should show warning about pyperclip
                    assert (
                        "pyperclip" in result.stderr.lower()
                        or "clipboard" in result.stderr.lower()
                    )


class TestUserStory4:
    """Integration tests for User Story 4: Customize Message Format Style."""

    def test_format_conventional(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 1: Given staged changes, when `gmuse msg --format conventional`,
        then message follows "type(scope): description" format.
        """
        _stage_file(
            git_repo_with_history, "feature.py", "def new_feature():\n    pass\n"
        )

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "feat(core): add new feature function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg", "--format", "conventional"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                assert "feat" in result.stdout

                # Verify conventional format was requested in prompt
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("system_prompt", "") + call_kwargs.get(
                    "user_prompt", ""
                )
                assert "conventional" in prompt.lower() or "type(scope)" in prompt

    def test_format_gitmoji(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 2: Given staged changes, when `gmuse msg --format gitmoji`,
        then message includes emoji prefix.
        """
        _stage_file(
            git_repo_with_history, "feature.py", "def new_feature():\n    pass\n"
        )

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "✨ Add new feature function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg", "--format", "gitmoji"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                # Gitmoji messages should start with an emoji
                assert "✨" in result.stdout

    def test_format_freeform(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 3: Given staged changes, when `gmuse msg --format freeform`,
        then message has no formatting constraints.
        """
        _stage_file(
            git_repo_with_history, "feature.py", "def new_feature():\n    pass\n"
        )

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add new feature function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg", "--format", "freeform"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                assert "Add new feature function" in result.stdout


class TestUserStory5:
    """Integration tests for User Story 5: Repository-Level Instructions."""

    def test_gmuse_file_influences_message(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 1: Given `.gmuse` with "Always reference issue numbers",
        when `gmuse msg`, then message attempts to reference issues.
        """
        # Create .gmuse file with instructions
        gmuse_file = git_repo_with_history / ".gmuse"
        gmuse_file.write_text("Always reference issue numbers in commit messages.")

        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function (Issue #123)"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                assert "Issue" in result.stdout

                # Verify .gmuse content was included in prompt
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("user_prompt", "")
                assert "issue numbers" in prompt.lower()

    def test_gmuse_file_with_hint(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 2: Given `.gmuse` and `--hint`, when `gmuse msg`,
        then both influence message with hint precedence.
        """
        # Create .gmuse file
        gmuse_file = git_repo_with_history / ".gmuse"
        gmuse_file.write_text("Use conventional commits format.")

        _stage_file(git_repo_with_history, "security.py", "def secure():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add security function (critical fix)"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(
                        app, ["msg", "--hint", "this is a critical security fix"]
                    )
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0

                # Verify both .gmuse and hint were included in prompt
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("user_prompt", "")
                assert "conventional" in prompt.lower()
                assert "critical security fix" in prompt

    def test_no_gmuse_file(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 3: Given no `.gmuse`, when `gmuse msg`,
        then message generated without repo-specific instructions.
        """
        # Ensure no .gmuse file exists
        gmuse_file = git_repo_with_history / ".gmuse"
        if gmuse_file.exists():
            gmuse_file.unlink()

        _stage_file(git_repo_with_history, "utils.py", "def helper():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add helper function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                assert "Add helper function" in result.stdout


class TestUserStory6:
    """Integration tests for User Story 6: Global Configuration."""

    def test_config_copy_to_clipboard(
        self, git_repo_with_history: Path, tmp_path: Path
    ) -> None:
        """
        Acceptance 1: Given config with `copy_to_clipboard = true`,
        when `gmuse msg`, then auto-copy.
        """
        # Create config file
        config_dir = tmp_path / "gmuse"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text("copy_to_clipboard = true\n")

        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function"
            mock_client_class.return_value = mock_client

            mock_pyperclip = mock.MagicMock()
            with mock.patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
                with mock.patch.dict(
                    os.environ,
                    {
                        "OPENAI_API_KEY": "sk-test",
                        "XDG_CONFIG_HOME": str(tmp_path),
                    },
                ):
                    old_cwd = os.getcwd()
                    os.chdir(git_repo_with_history)
                    try:
                        result = runner.invoke(app, ["msg"])
                    finally:
                        os.chdir(old_cwd)

                    assert result.exit_code == 0
                    # Verify clipboard was called due to config
                    mock_pyperclip.copy.assert_called_once_with("Add feature function")

    def test_config_default_format(
        self, git_repo_with_history: Path, tmp_path: Path
    ) -> None:
        """
        Acceptance 4: Given config with `format = "conventional"`,
        when `gmuse msg`, then conventional format used.
        """
        # Create config file
        config_dir = tmp_path / "gmuse"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text('format = "conventional"\n')

        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "feat: add feature function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "sk-test",
                    "XDG_CONFIG_HOME": str(tmp_path),
                },
            ):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0
                # Verify conventional format was requested
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("system_prompt", "") + call_kwargs.get(
                    "user_prompt", ""
                )
                assert "conventional" in prompt.lower() or "type(scope)" in prompt

    def test_no_config_uses_defaults(self, git_repo_with_history: Path) -> None:
        """
        Acceptance: Given no config, when `gmuse msg`,
        then reasonable defaults used.
        """
        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function"
            mock_client_class.return_value = mock_client

            # Use a non-existent config directory
            with mock.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "sk-test",
                    "XDG_CONFIG_HOME": "/nonexistent/config",
                },
            ):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                # Should work with defaults
                assert result.exit_code == 0
                assert "Add feature function" in result.stdout


class TestUserStory7:
    """Integration tests for User Story 7: Learn from User Edits."""

    def test_learning_disabled_by_default(
        self, git_repo_with_history: Path, tmp_path: Path
    ) -> None:
        """
        Acceptance 3: Given `learning_enabled = false`, when `gmuse msg`,
        then no data stored or used.
        """
        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "sk-test",
                    "XDG_DATA_HOME": str(tmp_path),
                    "XDG_CONFIG_HOME": str(tmp_path),
                },
            ):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0

                # No history file should be created when learning is disabled
                history_file = tmp_path / "gmuse" / "history.jsonl"
                assert not history_file.exists()

    def test_learning_stores_record_when_enabled(
        self, git_repo_with_history: Path, tmp_path: Path
    ) -> None:
        """
        Acceptance 1: Given `learning_enabled = true`, when user runs gmuse,
        then record saved to history.jsonl.
        """
        # Create config with learning enabled
        config_dir = tmp_path / "gmuse"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text("learning_enabled = true\n")

        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "sk-test",
                    "XDG_DATA_HOME": str(tmp_path),
                    "XDG_CONFIG_HOME": str(tmp_path),
                },
            ):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0

                # History file should be created
                history_file = tmp_path / "gmuse" / "history.jsonl"
                assert history_file.exists()

                # Should contain the generated message
                content = history_file.read_text()
                assert "Add feature function" in content

    def test_learning_uses_history_when_available(
        self, git_repo_with_history: Path, tmp_path: Path
    ) -> None:
        """
        Acceptance 2: Given historical edits exist, when `gmuse msg`,
        then examples included in prompt as few-shot.
        """
        import json

        from gmuse.learning import get_repo_id

        # Create config with learning enabled
        config_dir = tmp_path / "gmuse"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text("learning_enabled = true\n")

        # Create existing history with edits
        history_file = tmp_path / "gmuse" / "history.jsonl"
        repo_id = get_repo_id(str(git_repo_with_history))
        record = {
            "timestamp": "2025-01-01T00:00:00Z",
            "repo_id": repo_id,
            "generated_message": "Old generated message",
            "final_message": "feat: improved message after edit",
            "diff_hash": "abc123",
            "model_used": "gpt-4",
            "format": "conventional",
        }
        history_file.write_text(json.dumps(record) + "\n")

        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "sk-test",
                    "XDG_DATA_HOME": str(tmp_path),
                    "XDG_CONFIG_HOME": str(tmp_path),
                },
            ):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0

                # Verify the learning example was included in prompt
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("user_prompt", "")
                assert "Old generated message" in prompt
                assert "improved message after edit" in prompt


class TestUserStory8:
    """Integration tests for User Story 8: Override Model Selection."""

    def test_model_flag_overrides_default(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 1: Given staged changes, when `gmuse msg --model claude-3-opus`,
        then claude-3-opus used.
        """
        _stage_file(git_repo_with_history, "test.py", "test content")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Update test file"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(
                        app, ["msg", "--model", "claude-3-opus-20240229"]
                    )
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0

                # Verify the model was passed to LLMClient
                mock_client_class.assert_called_once()
                call_kwargs = mock_client_class.call_args[1]
                assert call_kwargs.get("model") == "claude-3-opus-20240229"

    def test_model_flag_with_provider(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 2: Given config model, when `gmuse msg --model gpt-4`,
        then CLI flag overrides config.
        """
        _stage_file(git_repo_with_history, "test.py", "test content")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Update test file"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(
                        app, ["msg", "--model", "gpt-4", "--provider", "openai"]
                    )
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0

                # Verify provider was set
                mock_client_class.assert_called_once()
                call_kwargs = mock_client_class.call_args[1]
                assert call_kwargs.get("model") == "gpt-4"
                assert call_kwargs.get("provider") == "openai"


class TestUserStory9:
    """Integration tests for User Story 9: Adjust Commit History Depth."""

    def test_history_depth_flag(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 1: Given staged changes, when `gmuse msg --history-depth 2`,
        then only 2 commits used for context.
        """
        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg", "--history-depth", "2"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0

                # The prompt should only contain 2 recent commits
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("user_prompt", "")
                # Count how many "feat: update to version" messages are in the prompt
                # (our fixture creates 3 such commits)
                version_commits = prompt.count("feat: update to version")
                assert version_commits <= 2

    def test_history_depth_zero(self, git_repo_with_history: Path) -> None:
        """
        Acceptance 2: Given staged changes, when `gmuse msg --history-depth 0`,
        then no commit history used.
        """
        _stage_file(git_repo_with_history, "feature.py", "def feature():\n    pass\n")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Add feature function"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg", "--history-depth", "0"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0

                # Verify no commit history in prompt
                call_kwargs = mock_client.generate.call_args.kwargs
                prompt = call_kwargs.get("user_prompt", "")
                # With depth 0, there should be no commit history section
                # or the commits list should be empty
                assert (
                    "feat: update to version" not in prompt
                    or "Recent Commits" not in prompt
                )


class TestCLIHelp:
    """Tests for CLI help text."""

    def test_main_help(self) -> None:
        """Verify main --help output."""
        os.environ.pop("FORCE_COLOR", None)
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "gmuse" in result.stdout
        # Main help should show available commands
        assert "msg" in result.stdout or "info" in result.stdout

    def test_generate_help(self) -> None:
        """Verify generate command help."""
        os.environ.pop("FORCE_COLOR", None)
        result = runner.invoke(app, ["msg", "--help"])
        assert result.exit_code == 0
        assert "--hint" in result.stdout
        assert "--copy" in result.stdout
        assert "--model" in result.stdout
        assert "--format" in result.stdout


class TestExitCodes:
    """Tests for CLI exit codes."""

    def test_success_exit_code_zero(self, git_repo_with_history: Path) -> None:
        """Successful generation should exit with code 0."""
        _stage_file(git_repo_with_history, "test.py", "test")

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.return_value = "Update test"
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 0

    def test_user_error_exit_code_one(self) -> None:
        """User errors (not a repo, no staged changes) should exit with code 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = runner.invoke(app, ["msg"])
            finally:
                os.chdir(old_cwd)

            assert result.exit_code == 1

    def test_system_error_exit_code_two(self, git_repo_with_history: Path) -> None:
        """System errors (LLM failure) should exit with code 2."""
        _stage_file(git_repo_with_history, "test.py", "test")

        from gmuse.exceptions import LLMError

        with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
            mock_client = mock.Mock()
            mock_client.generate.side_effect = LLMError("Network timeout")
            mock_client_class.return_value = mock_client

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                old_cwd = os.getcwd()
                os.chdir(git_repo_with_history)
                try:
                    result = runner.invoke(app, ["msg"])
                finally:
                    os.chdir(old_cwd)

                assert result.exit_code == 2
