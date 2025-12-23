"""Unit tests for gmuse msg --dry-run feature."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from gmuse.cli.main import _format_dry_run_output, app
from gmuse.commit import GenerationContext
from gmuse.git import StagedDiff


runner: CliRunner = CliRunner()


# -----------------------------------------------------------------------------
# Tests for _format_dry_run_output (T005)
# -----------------------------------------------------------------------------


class TestFormatDryRunOutput:
    """Tests for the _format_dry_run_output helper."""

    def test_basic_output_format(self) -> None:
        """Output contains MODEL, FORMAT, TRUNCATED header and prompt sections."""
        output: str = _format_dry_run_output(
            model="gpt-4",
            format="conventional",
            truncated=False,
            system_prompt="You are a helper.",
            user_prompt="Diff: ...",
        )

        assert "MODEL: gpt-4" in output
        assert "FORMAT: conventional" in output
        assert "TRUNCATED: false" in output
        assert "SYSTEM PROMPT:" in output
        assert "You are a helper." in output
        assert "USER PROMPT:" in output
        assert "Diff: ..." in output

    def test_none_model_renders_as_none(self) -> None:
        """If model is None, output should show 'none'."""
        output: str = _format_dry_run_output(
            model=None,
            format="freeform",
            truncated=False,
            system_prompt="sys",
            user_prompt="usr",
        )

        assert "MODEL: none" in output

    def test_truncated_true_renders_correctly(self) -> None:
        """TRUNCATED should render 'true' when truncated is True."""
        output: str = _format_dry_run_output(
            model="m",
            format="gitmoji",
            truncated=True,
            system_prompt="s",
            user_prompt="u",
        )

        assert "TRUNCATED: true" in output


# -----------------------------------------------------------------------------
# Tests asserting LLMClient.generate is NOT called (T007)
# -----------------------------------------------------------------------------


class TestDryRunDoesNotCallProvider:
    """Verify that --dry-run never invokes LLMClient.generate."""

    @patch("gmuse.cli.main.gather_context")
    @patch("gmuse.cli.main.build_prompt")
    @patch("gmuse.llm.LLMClient.generate")
    def test_dry_run_does_not_call_llm_generate(
        self,
        mock_generate: MagicMock,
        mock_build_prompt: MagicMock,
        mock_gather_context: MagicMock,
    ) -> None:
        """--dry-run must not call LLMClient.generate."""
        # Setup mocks
        mock_diff: StagedDiff = StagedDiff(
            raw_diff="diff --git a/f.py",
            files_changed=["f.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=100,
        )
        mock_context: GenerationContext = GenerationContext(
            diff=mock_diff,
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_gather_context.return_value = mock_context
        mock_build_prompt.return_value = ("sys prompt", "usr prompt")

        result = runner.invoke(app, ["msg", "--dry-run"])

        assert result.exit_code == 0
        mock_generate.assert_not_called()

    @patch("gmuse.cli.main.gather_context")
    @patch("gmuse.cli.main.build_prompt")
    @patch("gmuse.commit.generate_message")
    def test_dry_run_does_not_call_generate_message(
        self,
        mock_gen_msg: MagicMock,
        mock_build_prompt: MagicMock,
        mock_gather_context: MagicMock,
    ) -> None:
        """--dry-run should skip generate_message entirely."""
        mock_diff: StagedDiff = StagedDiff(
            raw_diff="diff",
            files_changed=["x.py"],
            lines_added=1,
            lines_removed=0,
            hash="h",
            size_bytes=50,
        )
        mock_context: GenerationContext = GenerationContext(
            diff=mock_diff,
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_gather_context.return_value = mock_context
        mock_build_prompt.return_value = ("sys", "usr")

        result = runner.invoke(app, ["msg", "--dry-run"])

        assert result.exit_code == 0
        mock_gen_msg.assert_not_called()


# -----------------------------------------------------------------------------
# Tests for flag combinations (T018, T019, T020)
# -----------------------------------------------------------------------------


class TestDryRunFlagCombinations:
    """Verify --dry-run works correctly with other flags."""

    @patch("gmuse.cli.main.gather_context")
    @patch("gmuse.cli.main.build_prompt")
    def test_hint_included_in_prompt(
        self,
        mock_build_prompt: MagicMock,
        mock_gather_context: MagicMock,
    ) -> None:
        """--hint should be passed to build_prompt."""
        mock_diff: StagedDiff = StagedDiff(
            raw_diff="d",
            files_changed=["a.py"],
            lines_added=1,
            lines_removed=0,
            hash="h",
            size_bytes=10,
        )
        mock_context: GenerationContext = GenerationContext(
            diff=mock_diff,
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_gather_context.return_value = mock_context
        mock_build_prompt.return_value = ("sys", "user with hint")

        result = runner.invoke(app, ["msg", "--dry-run", "--hint", "security fix"])

        assert result.exit_code == 0
        mock_build_prompt.assert_called_once()
        call_kwargs = mock_build_prompt.call_args.kwargs
        assert call_kwargs.get("user_hint") == "security fix"

    @patch.dict("os.environ", {"GMUSE_MAX_CHARS": "50"})
    def test_max_chars_passed_to_build_prompt(
        self,
        mock_build_prompt: MagicMock,
        mock_gather_context: MagicMock,
    ) -> None:
        """GMUSE_MAX_CHARS should be passed to build_prompt as max_chars."""
        mock_diff: StagedDiff = StagedDiff(
            raw_diff="d",
            files_changed=["a.py"],
            lines_added=1,
            lines_removed=0,
            hash="h",
            size_bytes=10,
        )
        mock_context: GenerationContext = GenerationContext(
            diff=mock_diff,
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_gather_context.return_value = mock_context
        mock_build_prompt.return_value = ("sys", "user")

        result = runner.invoke(app, ["msg", "--dry-run"])

        assert result.exit_code == 0
        mock_build_prompt.assert_called_once()
        call_kwargs = mock_build_prompt.call_args.kwargs
        assert call_kwargs.get("max_chars") == 50

    @patch("gmuse.cli.main.gather_context")
    @patch("gmuse.cli.main.build_prompt")
    def test_format_reflected_in_header(
        self,
        mock_build_prompt: MagicMock,
        mock_gather_context: MagicMock,
    ) -> None:
        """--format should appear in the FORMAT: header line."""
        mock_diff: StagedDiff = StagedDiff(
            raw_diff="d",
            files_changed=["b.py"],
            lines_added=1,
            lines_removed=0,
            hash="h",
            size_bytes=10,
        )
        mock_context: GenerationContext = GenerationContext(
            diff=mock_diff,
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_gather_context.return_value = mock_context
        mock_build_prompt.return_value = ("sys", "usr")

        result = runner.invoke(app, ["msg", "--dry-run", "--format", "conventional"])

        assert result.exit_code == 0
        assert "FORMAT: conventional" in result.output

    @patch("gmuse.cli.main.gather_context")
    @patch("gmuse.cli.main.build_prompt")
    @patch("gmuse.cli.main._copy_to_clipboard")
    def test_copy_does_not_copy_during_dry_run(
        self,
        mock_copy: MagicMock,
        mock_build_prompt: MagicMock,
        mock_gather_context: MagicMock,
    ) -> None:
        """--copy should NOT copy anything when --dry-run is used."""
        mock_diff: StagedDiff = StagedDiff(
            raw_diff="d",
            files_changed=["c.py"],
            lines_added=1,
            lines_removed=0,
            hash="h",
            size_bytes=10,
        )
        mock_context: GenerationContext = GenerationContext(
            diff=mock_diff,
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_gather_context.return_value = mock_context
        mock_build_prompt.return_value = ("sys", "usr")

        result = runner.invoke(app, ["msg", "--dry-run", "--copy"])

        assert result.exit_code == 0
        mock_copy.assert_not_called()

    @patch("gmuse.cli.main.gather_context")
    @patch("gmuse.cli.main.build_prompt")
    def test_truncated_true_in_header(
        self,
        mock_build_prompt: MagicMock,
        mock_gather_context: MagicMock,
    ) -> None:
        """TRUNCATED: true when context.diff_was_truncated is True."""
        mock_diff: StagedDiff = StagedDiff(
            raw_diff="d",
            files_changed=["d.py"],
            lines_added=1,
            lines_removed=0,
            hash="h",
            size_bytes=10,
        )
        mock_context: GenerationContext = GenerationContext(
            diff=mock_diff,
            history=None,
            repo_instructions=None,
            diff_was_truncated=True,
        )
        mock_gather_context.return_value = mock_context
        mock_build_prompt.return_value = ("sys", "usr")

        result = runner.invoke(app, ["msg", "--dry-run"])

        assert result.exit_code == 0
        assert "TRUNCATED: true" in result.output

    @patch("gmuse.cli.main.gather_context")
    @patch("gmuse.cli.main.build_prompt")
    def test_history_depth_passed_to_gather_context(
        self,
        mock_build_prompt: MagicMock,
        mock_gather_context: MagicMock,
    ) -> None:
        """--history-depth should be passed to gather_context."""
        mock_diff: StagedDiff = StagedDiff(
            raw_diff="d",
            files_changed=["e.py"],
            lines_added=1,
            lines_removed=0,
            hash="h",
            size_bytes=10,
        )
        mock_context: GenerationContext = GenerationContext(
            diff=mock_diff,
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_gather_context.return_value = mock_context
        mock_build_prompt.return_value = ("sys", "usr")

        result = runner.invoke(app, ["msg", "--dry-run", "--history-depth", "10"])

        assert result.exit_code == 0
        mock_gather_context.assert_called_once()
        call_kwargs = mock_gather_context.call_args.kwargs
        assert call_kwargs.get("history_depth") == 10

    @patch("gmuse.cli.main.gather_context")
    @patch("gmuse.cli.main.build_prompt")
    def test_model_shown_in_header(
        self,
        mock_build_prompt: MagicMock,
        mock_gather_context: MagicMock,
    ) -> None:
        """--model should appear in the MODEL: header line."""
        mock_diff: StagedDiff = StagedDiff(
            raw_diff="d",
            files_changed=["f.py"],
            lines_added=1,
            lines_removed=0,
            hash="h",
            size_bytes=10,
        )
        mock_context: GenerationContext = GenerationContext(
            diff=mock_diff,
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_gather_context.return_value = mock_context
        mock_build_prompt.return_value = ("sys", "usr")

        result = runner.invoke(app, ["msg", "--dry-run", "--model", "claude-3-opus"])

        assert result.exit_code == 0
        assert "MODEL: claude-3-opus" in result.output
