# Runtime Contract: completion and raw generation

**Feature**: 008-commit-ux-redesign
**Date**: 2026-06-06

## Overview

This contract preserves `gmuse git-completions-run` as a dedicated runtime helper for shell completion while the main CLI shifts to `gmuse commit` and `gmuse generate`.

The key invariant is unchanged:

- shell completion uses a raw-generation path;
- shell completion never enters the interactive commit-session flow.

## Shared generation boundary

Completion-time suggestion generation must continue to reuse the same underlying raw generation primitive as `gmuse generate`.

That primitive must:

1. gather staged diff and other generation context;
2. call `gmuse.commit.generate_message()` or an extracted equivalent helper;
3. return a generated message without commit/editor/clipboard side effects.

`gmuse commit` orchestration must live above this boundary and must not be imported into completion-time control flow.

## Command contract: `gmuse git-completions-run`

### Signature

```text
gmuse git-completions-run --shell zsh --for "git commit -m" [--timeout FLOAT]
```

### Input validation

1. `--shell` currently accepts only `zsh`.
2. `--for` must describe a `git commit` command.
3. Invalid inputs return structured JSON with `status = "error"`.

### Success contract

On success, stdout must contain JSON only:

```json
{"suggestion":"feat: add branch-aware commit flow","status":"ok","metadata":{"elapsed_ms":420,"truncated":false}}
```

The helper must never print prompts, menus, editor notices, clipboard notices, or plain-text migration warnings to stdout.

## Status mapping

| Condition | `status` | `suggestion` | Notes |
|-----------|----------|--------------|-------|
| Suggestion generated successfully | `ok` | generated message | Includes `elapsed_ms`; may include `truncated` |
| Credential lookup timeout / provider timeout | `timeout` | empty | Preserve existing timeout semantics |
| Missing auth or offline-safe credential failure | `offline` | empty | No shell-visible prompt |
| No staged changes | `no_staged_changes` | empty | Structured JSON only |
| Invalid shell / invalid `--for` / unexpected runtime error | `error` | empty | Structured JSON only |

## Non-interactive safety contract

Completion runtime must never:

- invoke `gmuse commit`;
- enter the review loop;
- prompt for accept/edit/regenerate/abort;
- launch `git commit`;
- launch an editor;
- read from stdin interactively;
- perform clipboard work.

This remains true even if:

- `GMUSE_COPY` is set;
- `copy_to_clipboard = true` exists in config;
- the main CLI defaults to `gmuse commit`.

## Logging and output isolation

- JSON output must remain machine-parseable.
- Existing debug-log suppression for completion invocations must remain in place unless logging is redirected to a file.
- User-facing migration warnings for deprecated clipboard inputs must not be emitted on the completion path.

## Timeout and performance contract

- Completion must continue honoring `--timeout` and `GMUSE_COMPLETIONS_TIMEOUT`.
- Completion-specific timeout handling stays local to `src/gmuse/cli/completions.py`.
- Refactors for the new `generate` command must not add extra LLM calls or commit-session overhead to completion requests.

## Regression requirements

Phase 2 implementation must preserve these observable properties:

1. `gmuse git-completions-run` still returns JSON only.
2. Completion requests still use raw generation rather than interactive commit logic.
3. Clipboard retirement does not change completion output shape.
4. Existing timeout/offline/no-staged-changes status behavior remains intact.
