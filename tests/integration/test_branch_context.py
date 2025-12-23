"""Integration tests for branch context feature."""

import subprocess
from unittest import mock

from gmuse.commit import gather_context
from gmuse.config import merge_config


class TestBranchContextIntegration:
    """Integration tests for branch context in commit message generation."""

    def test_gather_context_with_branch_enabled(self) -> None:
        """Test that gather_context includes branch info when enabled."""
        # Mock git operations
        mock_diff = """diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
+new line
 existing line
"""
        
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                # Configure mock to return different values for different commands
                def run_side_effect(*args, **kwargs):
                    cmd = args[0]
                    if "diff" in cmd and "--cached" in cmd:
                        if "--name-only" in cmd:
                            return mock.Mock(returncode=0, stdout="file.py\n", stderr="")
                        return mock.Mock(returncode=0, stdout=mock_diff, stderr="")
                    elif "log" in cmd:
                        return mock.Mock(returncode=0, stdout="", stderr="")
                    elif "rev-parse" in cmd:
                        if "--abbrev-ref" in cmd:
                            return mock.Mock(returncode=0, stdout="feature/add-auth\n", stderr="")
                        return mock.Mock(returncode=0, stdout="/repo\n", stderr="")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                
                mock_run.side_effect = run_side_effect
                
                # Gather context with branch enabled
                context = gather_context(
                    history_depth=5,
                    include_branch=True,
                    branch_max_length=60,
                )
                
                # Verify branch info is included
                assert context.branch_info is not None
                assert context.branch_info.raw_name == "feature/add-auth"
                assert context.branch_info.branch_type == "feature"
                assert context.branch_info.branch_summary == "add/auth"

    def test_gather_context_with_branch_disabled(self) -> None:
        """Test that gather_context excludes branch info when disabled."""
        mock_diff = "diff --git a/file.py b/file.py\n+new line\n"
        
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                def run_side_effect(*args, **kwargs):
                    cmd = args[0]
                    if "diff" in cmd and "--cached" in cmd:
                        if "--name-only" in cmd:
                            return mock.Mock(returncode=0, stdout="file.py\n", stderr="")
                        return mock.Mock(returncode=0, stdout=mock_diff, stderr="")
                    elif "log" in cmd:
                        return mock.Mock(returncode=0, stdout="", stderr="")
                    elif "rev-parse" in cmd and "--show-toplevel" in cmd:
                        return mock.Mock(returncode=0, stdout="/repo\n", stderr="")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                
                mock_run.side_effect = run_side_effect
                
                # Gather context with branch disabled
                context = gather_context(
                    history_depth=5,
                    include_branch=False,
                )
                
                # Verify branch info is not included
                assert context.branch_info is None

    def test_gather_context_skips_default_branch(self) -> None:
        """Test that default branches (main/master) are skipped."""
        mock_diff = "diff --git a/file.py b/file.py\n+new line\n"
        
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                def run_side_effect(*args, **kwargs):
                    cmd = args[0]
                    if "diff" in cmd and "--cached" in cmd:
                        if "--name-only" in cmd:
                            return mock.Mock(returncode=0, stdout="file.py\n", stderr="")
                        return mock.Mock(returncode=0, stdout=mock_diff, stderr="")
                    elif "log" in cmd:
                        return mock.Mock(returncode=0, stdout="", stderr="")
                    elif "rev-parse" in cmd:
                        if "--abbrev-ref" in cmd:
                            return mock.Mock(returncode=0, stdout="main\n", stderr="")
                        return mock.Mock(returncode=0, stdout="/repo\n", stderr="")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                
                mock_run.side_effect = run_side_effect
                
                # Gather context with branch enabled
                context = gather_context(
                    history_depth=5,
                    include_branch=True,
                )
                
                # Verify default branch is skipped (None)
                assert context.branch_info is None

    def test_config_merge_with_cli_flag(self) -> None:
        """Test that CLI flag for include_branch is merged correctly."""
        cli_args = {"include_branch": True}
        config = merge_config(cli_args=cli_args)
        
        assert config["include_branch"] is True

    def test_config_merge_precedence(self) -> None:
        """Test that CLI flag overrides config file and env vars."""
        cli_args = {"include_branch": True}
        config_file = {"include_branch": False}
        env_vars = {"include_branch": False}
        
        config = merge_config(
            cli_args=cli_args,
            config_file=config_file,
            env_vars=env_vars,
        )
        
        # CLI should have highest precedence
        assert config["include_branch"] is True

    def test_branch_sanitization_in_context(self) -> None:
        """Test that branch names are properly sanitized in gathered context."""
        mock_diff = "diff --git a/file.py b/file.py\n+new line\n"
        
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                def run_side_effect(*args, **kwargs):
                    cmd = args[0]
                    if "diff" in cmd and "--cached" in cmd:
                        if "--name-only" in cmd:
                            return mock.Mock(returncode=0, stdout="file.py\n", stderr="")
                        return mock.Mock(returncode=0, stdout=mock_diff, stderr="")
                    elif "log" in cmd:
                        return mock.Mock(returncode=0, stdout="", stderr="")
                    elif "rev-parse" in cmd:
                        if "--abbrev-ref" in cmd:
                            # Return branch with ticket ID that should be masked
                            return mock.Mock(returncode=0, stdout="fix/PROJ-123-bug-in-api\n", stderr="")
                        return mock.Mock(returncode=0, stdout="/repo\n", stderr="")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                
                mock_run.side_effect = run_side_effect
                
                context = gather_context(
                    history_depth=5,
                    include_branch=True,
                )
                
                # Verify ticket ID is masked in summary
                assert context.branch_info is not None
                assert context.branch_info.branch_type == "fix"
                assert "ticket-xxx" in context.branch_info.branch_summary.lower()
                assert "PROJ-123" not in context.branch_info.branch_summary

    def test_branch_max_length_applied(self) -> None:
        """Test that branch_max_length config is applied correctly."""
        mock_diff = "diff --git a/file.py b/file.py\n+new line\n"
        long_branch = "feature/" + "x" * 100
        
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                def run_side_effect(*args, **kwargs):
                    cmd = args[0]
                    if "diff" in cmd and "--cached" in cmd:
                        if "--name-only" in cmd:
                            return mock.Mock(returncode=0, stdout="file.py\n", stderr="")
                        return mock.Mock(returncode=0, stdout=mock_diff, stderr="")
                    elif "log" in cmd:
                        return mock.Mock(returncode=0, stdout="", stderr="")
                    elif "rev-parse" in cmd:
                        if "--abbrev-ref" in cmd:
                            return mock.Mock(returncode=0, stdout=f"{long_branch}\n", stderr="")
                        return mock.Mock(returncode=0, stdout="/repo\n", stderr="")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                
                mock_run.side_effect = run_side_effect
                
                context = gather_context(
                    history_depth=5,
                    include_branch=True,
                    branch_max_length=30,
                )
                
                # Verify summary is truncated
                assert context.branch_info is not None
                assert context.branch_info.branch_summary is not None
                assert len(context.branch_info.branch_summary) <= 30
