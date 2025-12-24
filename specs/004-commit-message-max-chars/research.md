````markdown
# Phase 0 Research: Commit Message Max Characters (`max_chars`)

## Context

This feature adds a new configuration parameter `max_chars` that, when set, is included in the LLM prompt and enforces a maximum commit message character count.

Important existing behavior:

- `gmuse` already enforces a maximum message length via `max_message_length` (config) and `gmuse.prompts.validate_message(max_length=...)`.
- The prompt for Conventional Commits currently includes a hard-coded “Keep total length under 100 characters”.

## Decisions

### Decision 1 — Introduce `max_chars` as an optional, prompt-visible limit

- Decision: Add a new config setting named `max_chars` with default `None` (disabled).
- Rationale:
  - Users explicitly asked for a prompt-visible character limit.
  - Keeping it optional avoids changing defaults and preserves current behavior.
- Alternatives considered:
  - Reuse existing `max_message_length` only.
    - Rejected because the user request explicitly needs the limit to be supplied to the prompt; `max_message_length` is currently validation-only.

### Decision 2 — Enforce by failing with an actionable error (no truncation, no retry)

- Decision: If the generated message exceeds the effective limit, fail with an `InvalidMessageError` that includes both the actual length and the configured limit.
- Rationale:
  - Truncation can produce malformed conventional commit lines or broken semantics.
  - Retries increase cost and latency, and can still fail.
- Alternatives considered:
  - Truncate to `max_chars`.
    - Rejected because it risks invalid formats and confusing output.
  - Retry once.
    - Rejected to keep behavior predictable and cost-bounded.

### Decision 3 — Character counting uses Unicode code points (`len(message)`)

- Decision: Define “character count” as `len(message)` (Unicode code points), including newline characters.
- Rationale:
  - Matches Python’s standard behavior and is consistent across platforms.
- Alternatives considered:
  - Grapheme cluster counting.
    - Rejected for complexity and added dependencies.
  - UTF-8 byte length.
    - Rejected because it does not match user expectations for “characters”.

### Decision 4 — Compatibility strategy with existing `max_message_length`

- Decision:
  - Keep existing `max_message_length` behavior unchanged.
  - If `max_chars` is set, it becomes the effective max-length used in both prompt context and validation.
  - If `max_chars` is not set, the system behaves as today (validation uses `max_message_length`).
- Rationale:
  - Avoids breaking existing config and tests.
  - Makes `max_chars` the single source of truth when explicitly configured.
- Alternatives considered:
  - Replace `max_message_length` with `max_chars`.
    - Rejected because it is a breaking configuration change.

### Decision 5 — Prompt inclusion is explicit and non-conflicting

- Decision:
  - When `max_chars` is set, the user prompt MUST include a clearly labeled rule such as: “Maximum length: {max_chars} characters.”
  - For Conventional Commits, the prompt MUST not contain conflicting length requirements when `max_chars` is set.
- Rationale:
  - Conflicting instructions reduce model compliance.
- Alternatives considered:
  - Add the rule without removing existing format guidance.
    - Rejected because it risks contradictory constraints.

## Notes / Best-practice reminders

- Keep the setting name consistent across config sources: TOML key `max_chars` and environment variable `GMUSE_MAX_CHARS`.
- Ensure errors are actionable and consistent with existing config validation errors.
- Add unit + integration tests to cover:
  - prompt inclusion
  - enforcement and error content
  - backwards compatibility

````
