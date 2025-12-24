# Feature Specification: Commit Message Max Characters

**Feature Branch**: `006-commit-message-max-chars`
**Created**: 2025-12-23
**Status**: Draft
**Input**: User description: "Create a config param for the number of characters in a commit message which will be provided in the prompt"

## Clarifications

### Session 2025-12-23
- Q: Configuration Parameter Name → A: `max_chars`
- Q: Enforcement Strategy → A: Fail with an error
- Q: Character Counting Method → A: Unicode code points (Python `len()`)
- Q: Default Value → A: No default (disabled)
- Q: Error Message Content → A: Actual length vs. configured limit

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Limit commit message size (Priority: P1)

As a user, I want to configure a maximum commit message character limit so generated commit messages fit team or tooling constraints.

**Why this priority**: Prevents generated messages from being rejected by tooling, cut off in UIs, or violating team guidelines.

**Independent Test**: Set the max character limit and generate a message; the returned message must not exceed the configured limit.

**Acceptance Scenarios**:

1. **Given** a configured maximum character limit, **When** the user generates a commit message, **Then** the resulting message length is at or below the configured limit.
2. **Given** a configured maximum character limit, **When** the user generates a commit message, **Then** the limit value is included in the prompt context used for generation.

---

### User Story 2 - Default behavior remains usable (Priority: P2)

As a user, I want message generation to work without configuring any new setting.

**Why this priority**: Ensures backwards-compatible behavior for existing users.

**Independent Test**: Run message generation with no max character configuration; generation completes successfully.

**Acceptance Scenarios**:

1. **Given** no configured maximum character limit, **When** the user generates a commit message, **Then** message generation succeeds and does not require any new configuration.

---

### User Story 3 - Clear validation errors for invalid values (Priority: P3)

As a user, I want clear feedback when the configured maximum character limit is invalid.

**Why this priority**: Prevents confusing failures and makes configuration mistakes easy to correct.

**Independent Test**: Provide an invalid maximum character limit; the system rejects it with a clear, actionable error.

**Acceptance Scenarios**:

1. **Given** an invalid maximum character limit (non-integer, zero, or negative), **When** the user runs message generation, **Then** the system fails fast with a clear error explaining the valid format.
2. **Given** an out-of-range maximum character limit, **When** the user runs message generation, **Then** the system fails fast with a clear error stating the supported range.

### Edge Cases

- Very small limit values (e.g., a limit too small to express a meaningful message)
- Very large limit values (should not create disproportionately long prompts or slowdowns)
- Multi-line messages (character counting applies to the entire message, including newline characters)
- Non-ASCII characters (character counting uses user-visible characters, not bytes)
- The model returns a message exceeding the limit

## Constitution Check (Mandatory)

- **Code Quality**: Adds a new user-facing configuration parameter. Acceptance: existing configuration patterns remain consistent; public interfaces remain documented.
- **Testing**: Add unit tests for config parsing/validation and prompt inclusion; add at least one integration test covering end-to-end enforcement of the limit.
- **UX**: Expose the setting through the same configuration mechanisms as other settings and document it in user-facing configuration/reference docs; errors are actionable.
- **Performance**: Including the limit in the prompt adds negligible overhead; with the limit enabled, end-to-end message generation time remains within 10% of the baseline for the same inputs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a configurable setting named `max_chars` that represents the maximum number of characters permitted in a generated commit message.
- **FR-002**: System MUST validate that the configured `max_chars` limit is a positive integer within the supported range of 1–500 characters.
- **FR-003**: System MUST include the configured `max_chars` limit as explicit context in the prompt used to generate commit messages.
- **FR-004**: When `max_chars` is configured, System MUST return a commit message whose total character count is less than or equal to that limit.
- **FR-005**: If the LLM returns a message exceeding `max_chars`, System MUST fail with an actionable error that includes both the actual length and the configured limit.
- **FR-006**: When no `max_chars` limit is configured, System MUST preserve existing behavior (generation continues without requiring the setting).
- **FR-007**: The default value for `max_chars` MUST be `None` (disabled).
- **FR-008**: System MUST use Unicode code points (Python `len()`) for character counting to ensure consistency across environments.

### Key Entities *(include if feature involves data)*

- **max_chars**: A user-configurable numeric setting that constrains the length of the generated commit message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With the limit enabled, 100% of generated commit messages in automated tests are at or under the configured character limit.
- **SC-002**: Invalid limit values are rejected with a clear, actionable error message (validated by automated tests).
- **SC-003**: The configured limit is present in the generation prompt context whenever the feature is enabled (validated by automated tests).
- **SC-004**: Users can successfully generate a commit message without setting the limit (backwards compatibility validated by automated tests).

## Assumptions

- The product already supports user configuration via existing mechanisms; this feature adds one additional setting.
- Supported range for the maximum character limit is 1–500 characters.
