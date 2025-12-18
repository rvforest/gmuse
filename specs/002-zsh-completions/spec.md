# Feature Specification: zsh completions for gmuse

**Feature Branch**: `002-zsh-completions`
**Created**: 2025-12-16
**Status**: Draft
**Input**: User description: "zsh completions for gmuse (emit + runtime helper, XDG-compliant)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Emit zsh completion script (Priority: P1)

As a user, I want to generate the zsh completion script so that I can install it in my shell.

**Why this priority**: Essential for the feature to work. Without the script, there is no completion.

**Independent Test**: Run `gmuse completions zsh` and verify output contains valid zsh code.

**Acceptance Scenarios**:

1. **Given** gmuse is installed on PATH, **When** the user runs `gmuse completions zsh`, **Then** the command prints a zsh completion script to stdout.
2. **Given** the user adds `eval "$(gmuse completions zsh)"` to their `~/.zshrc` and restarts the shell, **When** they type `git commit -m ` and press TAB, **Then** zsh has the completion function available.

---

### User Story 2 - Generate suggestion when -m has no user-provided text (Priority: P1)

As a user, I want to get an AI-generated commit message when I press TAB on an empty message argument.

**Why this priority**: Core value proposition of the feature.

**Independent Test**: Mock the runtime helper and verify zsh inserts the suggestion.

**Acceptance Scenarios**:

1. **Given** there are staged changes and GMUSE_COMPLETIONS_ENABLED=true, **When** the user types `git commit -m ` and presses TAB, **Then** the completion invokes `gmuse completions-run` and the returned suggestion is auto-inserted as the -m argument within GMUSE_COMPLETIONS_TIMEOUT seconds.
2. **Given** there are no staged changes, **When** the user types `git commit -m ` and presses TAB, **Then** the runtime helper returns status `no_staged_changes` and the completion shows a non-intrusive warning without inserting any text.

---

### User Story 3 - Timeout and fallback behavior (Priority: P2)

As a user, I want the completion to fail gracefully if it takes too long or is offline.

**Why this priority**: Critical for UX; blocking the shell is unacceptable.

**Independent Test**: Simulate slow runtime helper and verify zsh aborts.

**Acceptance Scenarios**:

1. **Given** GMUSE_COMPLETIONS_TIMEOUT=3 and the runtime helper does not return within 3s, **When** the user presses TAB, **Then** the completion aborts the request and returns fallback within 100ms of timeout detection.
2. **Given** the machine is offline or provider credentials are missing, **When** the user presses TAB, **Then** the completion falls back immediately and does not print provider credentials or secrets.

---

### User Story 5 - User opt-out and configuration (Priority: P3)

As a user, I want to configure or disable the feature via environment variables.

**Why this priority**: Important for user control and environment management.

**Independent Test**: Set env vars and verify behavior changes.

**Acceptance Scenarios**:

1. **Given** GMUSE_COMPLETIONS_ENABLED=false, **When** the completion script is loaded, **Then** pressing TAB after `git commit -m` does not invoke gmuse completions-run.
2. **Given** GMUSE_COMPLETIONS_TIMEOUT=1.5, **When** the user presses TAB, **Then** the runtime helper invocation is limited to ≈1.5s before aborting.

### Edge Cases

- No staged changes -> do not call remote provider; display a non-intrusive warning (do not insert text), e.g., a `zle` message or stderr warning. Do not insert the string "No staged changes" into the `-m` argument.
- Very large diffs -> Python layer truncates deterministically; runtime metadata.truncated=true.
- Quoting/escaping -> inserted suggestion must be safe to paste into the command line; when in doubt, do not insert.
- Long delays / slow provider -> completion must timeout at GMUSE_COMPLETIONS_TIMEOUT and fallback without blocking shell.
- Rapid repeated TABs -> enforce rate-limiting and return cached result where possible.
- Provider errors -> runtime returns status=error; completion must not print stack traces or provider credentials.

## Constitution Check (Mandatory)

- **Code Quality**: This spec introduces new CLI commands (`completions`, `completions-run`). All new Python code must be type-hinted and pass `ruff` checks. The zsh script is external but should be clean and commented. The zsh script is stored as a package resource at `src/gmuse/templates/zsh_completion.zsh` and loaded via `importlib.resources` so it can be packaged and tested independently.
- **Testing**:
    - Unit tests added for `gmuse.cli.completions` module.
    - Integration tests for `gmuse completions-run` output format.
    - Manual testing required for zsh integration (or shell harness if possible).
    - Coverage target: 85% for new Python modules.
- **UX**:
    - `gmuse completions --help` must explain usage.
    - Documentation must be updated with installation instructions for zsh/WSL.
    - Error messages in `completions-run` should be JSON-formatted for the shell script to handle, not printed to stderr/stdout directly if it breaks completion.
- **Performance**:
    - Latency target: < 4s for generation, < 200ms for cache hit.
    - Memory: Minimal overhead for runtime helper.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-002**: System MUST provide a CLI command `gmuse completions zsh` that emits a valid zsh completion script.
- **FR-002**: System MUST provide a runtime helper command `gmuse completions-run` that returns JSON-formatted suggestions.
- **FR-003**: The completion script MUST support auto-inserting the generated message into the `-m` argument.
- **FR-005**: The system MUST respect `GMUSE_COMPLETIONS_TIMEOUT` and abort if generation exceeds the limit.
- **FR-006**: The system MUST implement a short-lived cache (default 30s) to avoid redundant API calls.
- **FR-007**: The system MUST implement client-side rate limiting (default 1 req/2s).
- **FR-008**: The system MUST handle quoting and escaping correctly for zsh insertion.
- **FR-009**: The system MUST NOT print API keys or secrets to the terminal or logs.

### Key Entities *(include if feature involves data)*

- **CompletionRequest**: Represents the context for generation (staged diff, config).
- **CompletionResponse**: JSON structure containing the suggestion, status, and metadata.
- **CacheEntry**: Stored suggestion with timestamp for caching.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-002**: Installation: >=95% of test users can install using `gmuse completions zsh > $XDG_DATA_HOME/zsh/site-functions/_gmuse` and enable completions per docs.
- **SC-002**: Latency: >=95% of generation responses complete within 4s; cache hits within 200ms.
- **SC-003**: Timeout behavior: 100% of timed-out requests return fallback within 100ms of timeout detection.
- **SC-004**: Reliability: >=99% of runtime invocations return JSON status within configured timeout in supported environments.
- **SC-005**: False-trigger rate: <=1% of invocations when user is not targeting -m.

## Clarifications

### Session 2025-12-16

- Q: How should the completion behave when there are no staged changes? → A: Display a non-intrusive warning and do not insert any text into the `-m` argument (no automatic insertion of "No staged changes").

## Assumptions

- A1: Target OS v1 is WSL2 Ubuntu with zsh 5.9.
- A2: Users run zsh with compinit enabled and can write user-level completion files to $XDG_DATA_HOME (fallback $HOME/.local/share).
- A3: gmuse CLI is non-interactive and the Python layer supplies staged diffs and truncation logic.
- A4: Auto-insert of a single suggestion is the desired UX and preview-as-comment is omitted for v1.
- A5: Env var names GMUSE_COMPLETIONS_ENABLED, GMUSE_COMPLETIONS_TIMEOUT, GMUSE_COMPLETIONS_CACHE_TTL are acceptable.
- A6: No telemetry is collected in v1; future telemetry will be opt-in.

## Dependencies

- zsh (compinit) on WSL2 Ubuntu (zsh 5.9)
- gmuse CLI and Python layer installed and on PATH
- LLM provider credentials (user-managed) where remote generation is used
- Optional filesystem/tmpdir for short-lived cache

## Risks

- Secret leakage by sending staged diffs to external providers (document and provide opt-out).
- Latency causing poor UX if timeouts or caching are insufficient.
- Quoting/escaping bugs producing malformed git commands.
- Accidental commits of AI-generated text without review.
- Interactions with zsh frameworks (oh-my-zsh) causing unexpected behavior.
