"""Interactive commit session orchestration.

Provides a small review loop for generated commit drafts with actions:
- accept: create commit from draft
- edit: open user's editor with draft prefilled
- regenerate: request a fresh draft from the generation function
- abort: exit without committing

This module is intentionally minimal and testable: side effects (git commit / editor
invocation) are delegated to gmuse.git helpers so they can be mocked in tests.
"""
from typing import Callable, Optional
import tempfile
import sys

from gmuse.git import commit_with_message, open_editor_with_message
from gmuse.commit import MessageResult


def run_commit_session(
    config: dict,
    hint: Optional[str],
    context,
    generate_fn: Callable[[dict, Optional[str], object], MessageResult],
    non_interactive: bool = False,
) -> None:
    """Run the commit review session.

    Args:
        config: Resolved configuration dict
        hint: Optional user hint passed to generator
        context: Context object from gather_context
        generate_fn: Callable that returns MessageResult when called as generate_fn(config, hint, context)
        non_interactive: If True, accept the generated message and commit immediately
    """
    # First generation
    result = generate_fn(config, hint, context)
    message = result.message

    if non_interactive:
        # Fast path: create commit and exit
        commit_with_message(message)
        return

    # Interactive loop
    while True:
        # Show current draft
        print("\n----- DRAFT COMMIT MESSAGE -----\n")
        print(message)
        print("\n--------------------------------\n")

        print("Actions: [a]ccept, [e]dit, [r]egenerate, [q]uit")
        try:
            choice = input("Choose action: ").strip().lower()
        except EOFError:
            # Treat EOF as abort
            print("Input closed — aborting", file=sys.stderr)
            return

        if choice in ("a", "accept"):
            try:
                commit_with_message(message)
                print("Commit created")
                return
            except Exception as e:
                print(f"Failed to create commit: {e}", file=sys.stderr)
                return

        elif choice in ("e", "edit"):
            try:
                open_editor_with_message(message)
                print("Editor exited — commit may have been created or aborted by git")
                return
            except Exception as e:
                print(f"Failed to open editor: {e}", file=sys.stderr)
                return

        elif choice in ("r", "regenerate"):
            try:
                result = generate_fn(config, hint, context)
                message = result.message
                continue
            except Exception as e:
                print(f"Regeneration failed: {e}", file=sys.stderr)
                return

        elif choice in ("q", "quit", "abort"):
            print("Aborted — no commit created", file=sys.stderr)
            return

        else:
            print("Unrecognized action. Choose one of: a, e, r, q")
            continue
