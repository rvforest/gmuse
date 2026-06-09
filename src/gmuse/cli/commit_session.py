"""Interactive commit session orchestration.

Provides a small review loop for generated commit drafts with actions:
- accept: create commit from draft
- edit: open user's editor with draft prefilled
- regenerate: request a fresh draft from the generation function
- abort: exit without committing

This module is intentionally minimal and testable: side effects (git commit /
editor invocation) are delegated to gmuse.git helpers so they can be mocked in
tests.
"""

import subprocess
import sys
from typing import Callable, NoReturn, Optional

import typer

from gmuse.commit import GenerationContext, GenerationResult
from gmuse.git import CommitOutcome, commit_with_message, open_editor_with_message


def _exit_after_git_failure(error: subprocess.CalledProcessError) -> NoReturn:
    """Preserve git's failure details without wrapping them in raw subprocess text."""
    output = (error.stderr or error.stdout or "").strip()
    if output:
        print(output, file=sys.stderr)
    else:
        print("Commit failed", file=sys.stderr)
    raise typer.Exit(code=1)


def run_commit_session(
    config: dict,
    hint: Optional[str],
    context: GenerationContext,
    generate_fn: Callable[[dict, Optional[str], GenerationContext], GenerationResult],
    non_interactive: bool = False,
    edit_first: bool = False,
) -> None:
    """Run the commit review session.

    Args:
        config: Resolved configuration dict.
        hint: Optional user hint passed to generator.
        context: Context object from gather_context.
        generate_fn: Callable returning a GenerationResult when called with
            ``(config, hint, context)``.
        non_interactive: If True, accept the generated message and commit immediately
        edit_first: If True, open the editor with the generated draft immediately.
    """
    # First generation
    result = generate_fn(config, hint, context)
    message = result.message

    if non_interactive:
        # Fast path: create commit and exit
        commit_with_message(message)
        return

    if edit_first:
        try:
            outcome = open_editor_with_message(message)
        except subprocess.CalledProcessError as e:
            _exit_after_git_failure(e)
        else:
            if outcome is CommitOutcome.ABORTED:
                print("Commit aborted")
                return
            print("Commit created")
            return

    # Interactive loop
    while True:
        # Show current draft
        print("\nDraft commit message\n")
        for line in message.splitlines():
            print(f"  {line}")
        print()

        print("Actions")
        print("  a  accept")
        print("  e  edit")
        print("  r  regenerate")
        print("  q  quit")
        print()

        while True:
            try:
                choice = input("Choose action: ").strip().lower()
            except EOFError:
                # Treat EOF as abort
                print("Input closed - aborting", file=sys.stderr)
                return

            if choice in ("a", "accept"):
                try:
                    commit_with_message(message)
                except subprocess.CalledProcessError as e:
                    _exit_after_git_failure(e)
                print("Commit created")
                return

            if choice in ("e", "edit"):
                try:
                    outcome = open_editor_with_message(message)
                except subprocess.CalledProcessError as e:
                    _exit_after_git_failure(e)
                else:
                    if outcome is CommitOutcome.ABORTED:
                        print("Commit aborted")
                        return
                    print("Commit created")
                    return

            if choice in ("r", "regenerate"):
                print("Regenerating commit message...")
                result = generate_fn(config, hint, context)
                message = result.message
                break

            if choice in ("q", "quit"):
                print("Commit aborted")
                return

            print("Invalid choice. Use a, e, r, or q.")
