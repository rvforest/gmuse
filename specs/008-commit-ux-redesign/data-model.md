# Data Model: commit UX redesign

## Entity: `GenerationRequest`

Represents the shared non-interactive inputs used by `gmuse generate`, deprecated `gmuse msg`, `gmuse commit`, and `gmuse git-completions-run`.

**Fields**:

- `hint: str | None`
  - Optional user guidance to bias generation.
- `model: str | None`
  - Optional explicit model override.
- `format: Literal["freeform", "conventional", "gitmoji"]`
  - Message-shaping format.
- `history_depth: int`
  - Recent commit count used for style context.
- `temperature: float | None`
  - Optional model sampling override.
- `max_tokens: int | None`
  - Optional model response cap.
- `max_diff_bytes: int | None`
  - Diff truncation threshold.
- `include_branch: bool`
  - Whether sanitized branch context is included.
- `dry_run: bool`
  - Prompt-inspection mode for the raw path only.

**Rules**:

- This entity reuses the existing config-resolution and `gmuse.commit` generation path.
- `dry_run = true` is valid for the raw generation path and invalid for `gmuse commit`.
- Clipboard-oriented inputs are not part of this entity after the redesign.

## Entity: `GeneratedDraft`

Represents one AI-produced commit message draft.

**Fields**:

- `message: str`
  - Full generated commit message, including optional body.
- `generation_index: int`
  - Monotonic counter within one commit session, starting at `1`.
- `context_truncated: bool`
  - Whether the staged diff was truncated before generation.
- `source_command: Literal["generate", "msg", "commit", "git-completions-run"]`
  - Which command surface requested the draft.

**Validation Rules**:

- `message` must already satisfy existing `validate_message()` rules.
- Multi-line messages must preserve subject/body structure end-to-end.
- A later regenerated draft replaces the current draft for commit purposes but does not mutate prior session history.

## Entity: `ReviewAction`

Represents a user decision in the interactive `gmuse commit` review loop.

**Allowed values**:

- `accept`
- `edit`
- `regenerate`
- `abort`

**Rules**:

- Only available when stdin and stdout are interactive and `--yes` is not set.
- `regenerate` is the only action that requests another LLM call.
- `abort` never creates a git commit.

## Entity: `CommitSession`

Represents one invocation of `gmuse commit`.

**Fields**:

- `request: GenerationRequest`
  - Shared generation inputs for the session.
- `drafts: list[GeneratedDraft]`
  - Ordered draft history for the current session.
- `current_draft_index: int`
  - Index of the active draft in `drafts`.
- `interactive: bool`
  - `True` when both stdin and stdout are TTYs and `--yes` is not set.
- `fast_path: bool`
  - `True` when `--yes` bypasses the review loop.
- `selected_action: ReviewAction | None`
  - Most recent interactive action.
- `outcome: CommitOutcome | None`
  - Final session result once execution ends.

**State Transitions**:

1. Session starts with one generated draft.
2. If `fast_path = true`, the session attempts direct commit immediately.
3. If `interactive = true`, the session enters review:
   - `accept` -> direct commit attempt
   - `edit` -> editor handoff commit attempt
   - `regenerate` -> append new draft and return to review
   - `abort` -> terminal non-commit outcome
4. Any git/editor failure ends the session with a failed outcome and no false-success message.

## Entity: `CommitOutcome`

Represents the terminal result of a commit session.

**Fields**:

- `status: Literal["committed", "aborted", "failed"]`
- `method: Literal["accept", "edit", "yes", "none"]`
  - `none` is used for aborts and preflight failures before a commit attempt.
- `commit_created: bool`
- `head_changed: bool`
  - Whether `HEAD` advanced during the command.
- `message_used: str | None`
  - Final committed message when a commit succeeds.
- `error_kind: Literal["non_interactive", "git_rejected", "editor_failed", "validation", "prerequisite", "none"]`
- `error_message: str | None`

**Rules**:

- `status = "committed"` requires `commit_created = true`, `head_changed = true`, and a non-empty `message_used`.
- `status = "aborted"` requires `commit_created = false`.
- `status = "failed"` requires a non-`none` `error_kind`.
- Editor exits that do not create a commit are modeled as `aborted` or `failed` based on the observed git result, not guessed from prompt text alone.

## Entity: `RawGenerationOutput`

Represents the success contract for `gmuse generate`, deprecated `gmuse msg`, and completion-time raw generation.

**Fields**:

- `message: str`
  - Exact generated commit message content.
- `stdout_only: bool`
  - Indicates that success output is limited to the message payload for CLI raw generation.
- `side_effects: Literal["none"]`

**Rules**:

- On successful `gmuse generate`, stdout contains only `message`.
- No clipboard, editor, prompt, or `git commit` side effect is allowed on this path.
- Completion runtime wraps the message in JSON but still relies on the same raw-generation primitive.

## Entity: `MigrationNotice`

Represents user-facing guidance for renamed or removed CLI surfaces.

**Fields**:

- `trigger: Literal["msg_alias", "msg_copy", "gmuse_copy_env", "copy_to_clipboard_config"]`
- `severity: Literal["deprecation", "error"]`
- `replacement_raw_command: str`
  - Always `gmuse generate`.
- `replacement_commit_command: str`
  - Always `gmuse commit`.
- `details: str`

**Rules**:

- `msg_alias` emits a deprecation notice to stderr while preserving stdout compatibility.
- `msg_copy` is a hard error with explicit migration guidance.
- Passive legacy clipboard config/env inputs may trigger warnings or deprecation tracking, but must not violate the stdout-only success contract of `gmuse generate`.

## Relationships

- A `CommitSession` owns one or more `GeneratedDraft` records.
- A `CommitSession` ends in exactly one `CommitOutcome`.
- A `MigrationNotice` may be emitted by `gmuse msg`, `gmuse commit`, or `gmuse generate`, but does not alter raw generation semantics on success.
- `RawGenerationOutput.message` should equal the active `GeneratedDraft.message` when both arise from the same shared generation helper.
