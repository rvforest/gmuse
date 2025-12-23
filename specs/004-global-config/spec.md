# Feature Specification: Global Config CLI

**Feature Branch**: `004-global-config`
**Created**: 2025-12-23
**Status**: Draft
**Input**: User description: "I'd like to be able to set and view global config from the gmuse cli."

## Clarifications

### Session 2025-12-23

- Q: Which file/location should the new “global-config view/set” commands read/write? → A: Use the existing global config file resolved by `gmuse.config` (XDG path, typically `~/.config/gmuse/config.toml`).
- Q: For `global-config set`, how strict should key validation be? → A: Reject unknown keys (only allow known config keys).
- Q: Should `global-config view` display persisted file contents, merged overrides, or both? → A: Display the file contents first, followed by a merged summary noting overrides from env/defaults.
- Q: Should `global-config view` warn when a higher precedence source overrides a stored value? → A: Yes, highlight overrides in the merged summary so users see conflicts immediately.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - View Global Config (Priority: P1)

A developer wants to view their **global gmuse configuration** from the command line so they can understand what defaults will apply across repositories.

**Why this priority**: Being able to see current settings is the fastest way to debug behavior (model choice, format, history depth, branch context) without editing files manually.

**Independent Test**: Can be fully tested by running a single CLI command that prints the current global config values and the config file location, delivering immediate visibility into persistent settings.

**Acceptance Scenarios**:

1. **Given** the user has a global config file with one or more settings, **When** they run the global-config view command, **Then** the CLI prints the configured keys and values in a human-readable format.
2. **Given** the user does not have a global config file yet, **When** they run the global-config view command, **Then** the CLI clearly indicates no global config is currently set and shows where it would be stored.
3. **Given** the global config file exists but cannot be read, **When** the user runs the global-config view command, **Then** the CLI prints a clear error message and exits with a non-zero status.

---

### User Story 2 - Set Global Config Values (Priority: P2)

A developer wants to set global gmuse configuration values via the CLI so they can persist preferences (e.g., message format or enabling branch context) without manually editing a configuration file.

**Why this priority**: Editing config by hand is error-prone and slows onboarding. A CLI setter enables quick, consistent, and validated configuration.

**Independent Test**: Can be fully tested by running a CLI command that sets a key/value, then running the view command to confirm the value persists.

**Acceptance Scenarios**:

1. **Given** the user provides a supported configuration key and a valid value, **When** they run the global-config set command, **Then** the setting is persisted and the CLI confirms success.
2. **Given** the user provides an unknown configuration key, **When** they run the set command, **Then** the CLI rejects the change with a clear error message and a non-zero status.
3. **Given** the user provides a known key but an invalid value (e.g., out of allowed range), **When** they run the set command, **Then** the CLI rejects the change with a clear validation error and a non-zero status.
4. **Given** the global config storage location does not exist, **When** the user sets a value, **Then** the necessary parent directories and config file are created automatically.
5. **Given** the config file exists but cannot be written, **When** the user sets a value, **Then** the CLI prints a clear error message and exits with a non-zero status.

---

### Edge Cases

- Running the view command when the global config file is empty.
- Running the view command when the global config file contains invalid syntax.
- Setting a value that includes spaces or special characters.
- Setting a value for a boolean or numeric option using common user inputs (e.g., true/false/1/0).
- Attempting to set a value that would overwrite an existing value (should be deterministic and clearly communicated).
- Concurrent edits: the config file changes between read and write (the CLI should avoid corrupting the file).
- Keys that are intentionally not supported for persistence (e.g., secrets/credentials).

## Constitution Check (Mandatory)

Every specification MUST explicitly address the following constitution-oriented questions and include evidence or steps:

- **Code Quality**: Does this spec change public APIs, require new libraries, or introduce patterns that need additional linting/type checks? Describe how you'll keep code readable and testable.
- **Testing**: What unit and integration tests will be added? Are there required coverage targets or new test types (contract, performance, security) that must be in CI?
- **UX**: If the spec introduces CLI or user-visible changes, include help text, error messages, and docs that will need updates.
- **Performance**: Document expected ranges for latency, memory, or token consumption, and any strategies for keeping those within acceptable bounds.

Address each item with short acceptance criteria.

- **Code Quality**: CLI surface expanded with a dedicated global-config command group; changes keep configuration behavior consistent with existing precedence rules. Public behavior is documented and error messages are deterministic.
- **Testing**: Unit tests cover read/write/validation behaviors and error cases (missing file, invalid key/value, permission errors). Integration tests cover end-to-end “set then view” in a temporary home/config directory.
- **UX**: CLI help text includes examples for viewing and setting global config. Docs are updated to describe the new commands and clarify that credentials remain environment-based.
- **Performance**: View and set operations complete quickly (local file I/O only). No network calls are required for these commands.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
-->

### Functional Requirements

- **FR-001**: System MUST provide a CLI command to view the user’s global gmuse configuration.
- **FR-002**: The view command MUST indicate whether a global config exists, where it is stored, show the file contents, and then present a merged summary highlighting overrides from environment variables or defaults.
- **FR-003**: System MUST provide a CLI command to set a global configuration key to a value.
- **FR-004**: The set command MUST validate configuration keys against the documented configuration options.
- **FR-005**: The set command MUST validate values according to the documented constraints (e.g., allowed ranges and allowed enumerations).
- **FR-006**: The set command MUST persist the updated configuration without removing unrelated existing settings.
- **FR-007**: The set command MUST be safe by default and MUST NOT store credentials or API keys in global config.
- **FR-008**: On read/write failures, the CLI MUST provide clear, actionable errors and exit with a non-zero status.
- **FR-009**: The set command MUST create the global config storage location if it does not exist.
- **FR-010**: The view command MUST NOT make any network calls.
- **FR-011**: The view/set global-config commands MUST read/write the existing XDG global config file resolved by `gmuse.config` (typically `~/.config/gmuse/config.toml`).
- **FR-012**: The set command MUST reject unknown configuration keys and only accept keys already defined by gmuse (enforced via the documented allowlist).
- **FR-013**: The view command MUST clearly highlight when a higher-precedence source (e.g., environment variable) overrides a value in the global config file so the user understands the conflict.

### Key Entities *(include if feature involves data)*

- **GlobalConfig**: A persistent set of user preferences for gmuse (key/value pairs) applied across repositories.
- **ConfigKey**: A named option (e.g., model, format, history depth, include-branch) with defined validation rules.
- **ConfigValue**: A user-provided value for a given key, validated and stored in a type-appropriate form.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: A user can view their current global config in under 5 seconds using a single CLI command.
- **SC-002**: A user can set a global config value and verify it persists (by re-running the view command) in under 30 seconds.
- **SC-003**: For invalid keys or invalid values, the CLI provides an actionable error message (what was wrong and how to fix it) in 100% of tested cases.
- **SC-004**: The feature does not increase the time-to-first-output for unrelated commands (e.g., commit message generation) in a measurable way.
