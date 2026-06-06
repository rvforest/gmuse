# Runtime Contract: Credential Resolution

**Feature**: 007-keyring-integration
**Date**: 2026-06-02

## Overview

This contract defines how `gmuse` resolves credentials for normal message generation and for shell completion helpers.

## Resolution Order

For a required credential variable `VAR_NAME`, runtime resolution MUST follow this order:

1. Explicit CLI-provided value, where a command path supports one.
2. Environment variable `VAR_NAME`.
3. Keyring entry stored under service `gmuse`, username `VAR_NAME`.
4. Actionable user-facing error.

### Empty Environment Variables

- If `VAR_NAME` is present in the environment but its value is empty or whitespace-only, it MUST be treated as unresolved.
- Resolution MUST then continue to the keyring lookup step.

## Normal `gmuse msg` Behavior

### Success path

1. Determine provider/model as usual.
2. Resolve required credentials via env/keyring.
3. Pass resolved values to the generation path without printing them.

### Missing credential error

If no credential resolves, `gmuse msg` MUST exit non-zero with guidance for both supported setup modes.

**Error shape**:

```text
Error: No API credential is configured for the selected provider.

For interactive use, run:
  gmuse auth set OPENAI_API_KEY

For non-interactive environments, use environment variables:
  export OPENAI_API_KEY='sk-...'
```

## `gmuse git-completions-run` Behavior

### Completion-time timeout contract

- Any keyring-backed credential lookup triggered during completion must complete within 200ms.
- Timeouts, GUI unlock prompts, backend failures, and auth errors are treated as “credentials unavailable”.
- The completion helper MUST not print raw error text to the shell for these cases.

### Completion result mapping

| Condition | Completion Status | Suggestion | Shell-visible error |
|-----------|-------------------|------------|---------------------|
| Credential resolved and generation succeeds | `ok` | Generated suggestion | No |
| Credential lookup times out | `timeout` or offline-safe status | Empty | No |
| Keyring prompts/blocks/fails auth | `offline` | Empty | No |
| Other unexpected internal error | `error` | Empty | Structured JSON only |

## Masking Contract

- Runtime status/debug output may show whether a credential source exists but MUST never print unmasked secret values.
- Values shown in `auth status` or related diagnostics use the shared masking rule:
  - length >= 12: display `******` followed by the last 4 characters
  - length < 12: mask all characters

## Secure Backend Contract

- Writes MUST be blocked when the active backend is unavailable or insecure.
- Reads SHOULD use the same backend qualification rules, surfacing user-facing errors for command paths and silent fallback for completion paths.
