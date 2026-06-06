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

import sys
from typing import Callable, Optional

from gmuse.commit import GenerationContext, GenerationResult
from gmuse.git import commit_with_message, open_editor_with_message


def run_commit_session(
    config: dict,
    hint: Optional[str],
    context: GenerationContext,
    generate_fn: Callable[[dict, Optional[str], GenerationContext], GenerationResult],
    non_interactive: bool = False,
) -> None:
    """Run the commit review session.

    Args:
        config: Resolved configuration dict.
        hint: Optional user hint passed to generator.
        context: Context object from gather_context.
        generate_fn: Callable returning a GenerationResult when called with
            ``(config, hint, context)``.
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
            commit_with_message(message)
            print("Commit created")
            return

        elif choice in ("e", "edit"):
            open_editor_with_message(message)
            print("Editor exited — commit may have been created or aborted by git")
            return

        elif choice in ("r", "regenerate"):
            result = generate_fn(config, hint, context)
            message = result.message
            continue

        elif choice in ("q", "quit", "abort"):
            print("Aborted — no commit created", file=sys.stderr)
            return

        else:
            print("Unrecognized action. Choose one of: a, e, r, q")
            continue
