# Feature Specification: Dry-run for `gmuse msg` (print prompt without calling LLM)

**Feature Branch**: `003-msg-dry-run`
**Created**: 2025-12-19
**Status**: Draft
**Input**: User description: "Add a `--dry-run` flag to `gmuse msg` that doesn't send anything to the llm provider but returns what the prompt would have been."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview prompt (Priority: P1)

As a developer or reviewer, I want to see the exact prompt `gmuse` would send to the LLM so I can inspect or audit it without consuming tokens or contacting any provider.

**Why this priority**: This delivers immediate value for debugging, auditing, and creating reproducible prompts without incurring cost or side effects.

**Independent Test**: Run `gmuse msg --dry-run` in a repository with staged changes and assert that the CLI prints the assembled prompt to stdout, exits with code 0, and does not call any LLM provider client methods.

**Acceptance Scenarios**:

1. **Given** a git repository with staged changes, **When** the user runs `gmuse msg --dry-run`, **Then** the command prints the full assembled prompt to stdout and exits with code 0, and no network requests or LLM client `generate()` calls are performed.
2. **Given** a requested message format (e.g., `--format conventional`), **When** `gmuse msg --dry-run` is run, **Then** the printed prompt reflects that format's prompt template.
3. **Given** there are errors (e.g., not a git repo, or no staged changes), **When** `gmuse msg --dry-run` is run, **Then** the command returns the same error exit codes and messages as the normal `gmuse msg` flow.

---

### User Story 2 - CLI discoverability and docs (Priority: P2)

As a user, I want the `--dry-run` flag to be visible in `gmuse msg --help` and documented so I can learn and use it without reading source code.

**Why this priority**: Usability and discoverability are important for adoption and avoiding confusion.

**Independent Test**: Run `gmuse msg --help` and assert the help text includes `--dry-run` with a short description; update docs and ensure documentation build includes the new flag.

**Acceptance Scenarios**:

1. **Given** the CLI is installed, **When** the user runs `gmuse msg --help`, **Then** `--dry-run` appears with a brief description (e.g., "Print the assembled prompt without calling the LLM provider").
2. **Given** the docs are built, **When** the docs are viewed, **Then** they include an example showing `gmuse msg --dry-run` and describe the behavior.

---

### User Story 3 - Safe integration with other options (Priority: P3)

As a user, I expect `--dry-run` to play nicely with other options (e.g., `--hint`, `--format`, `--model`), but to never invoke the provider.

**Why this priority**: Ensures this feature is predictable when combined with other CLI flags.

**Independent Test**: Combination tests that run `gmuse msg --dry-run --hint 'x' --format conventional` and assert output matches prompt that would have been sent if provider was invoked.

**Acceptance Scenarios**:

1. **Given** multiple flags, **When** `gmuse msg --dry-run` is run, **Then** the assembled prompt includes the effects of those flags and still avoids provider calls.

---

### Edge Cases

- Empty or very small diffs: Ensure the prompt still assembles correctly and clearly indicates missing context if applicable.
- Large diffs that would have been truncated: The dry-run output should indicate truncation in the same way the regular path does.
- Streaming or provider-specific flags (if present): `--dry-run` must be dominant and prevent any streaming or network activity.
- Piped input and CI environments: Behavior should be deterministic when running non-interactively.

---

## Constitution Check (Mandatory)

- **Code Quality**: Changes are limited to CLI parsing and the generation flow (`generate_message`). Introduce a typed `dry_run: bool = False` parameter to `generate_message` (or equivalent CLI-level early-exit that calls `build_prompt`). Keep changes small and covered by unit tests; add type hints and docstrings for the new parameter.
  - Acceptance: All new functions are type-hinted and pass pyrefly/ruff checks.

- **Testing**: Add unit tests and integration tests:
  - Unit tests: `tests/unit/test_commit_dry_run.py` verifying prompt assembly and that `LLMClient.generate()` is not called when `dry_run=True`.
  - Integration tests: `tests/integration/test_cli_msg_dry_run.py` invoking the CLI and asserting stdout contains the prompt and no network calls are attempted (monkeypatch/mocking of `LLMClient` or network layer).
  - Acceptance: Tests added and CI passes; coverage for modified modules remains >= existing baseline.

- **UX**: Update `gmuse msg --help` to include `--dry-run` and add an example in the docs (getting_started/quickstart.md or CLI reference). Add one-line explanation in docs about why and when to use it.
  - Acceptance: Help text contains `--dry-run` entry; docs include example usage.

- **Performance**: No production performance impact since no provider calls or heavy compute are added. The only added cost is building the prompt (already done in normal path).
  - Acceptance: No performance regression tests necessary beyond existing tests.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI `gmuse msg` MUST accept a boolean flag `--dry-run` that is documented in the help text.
- **FR-002**: When `--dry-run` is provided, the command MUST assemble the exact `system_prompt` and `user_prompt` that would be sent to the LLM and output them to stdout as labeled plain text (see Assumptions section for exact layout).
- **FR-003**: When `--dry-run` is provided, the system MUST NOT call into the LLM provider client (no `LLMClient.generate()` or network requests must be made).
- **FR-004**: When `--dry-run` is provided and the normal run would return an error (e.g., not a git repo, no staged changes), the command MUST return the same error messages and non-zero exit codes as the normal `gmuse msg` path.
- **FR-005**: `--dry-run` MUST respect other flags that affect prompt construction (e.g., `--hint`, `--format`) so the printed prompt matches what would have been sent if the provider were invoked.
- **FR-006**: Add unit and integration tests that explicitly assert no provider calls and that printed prompt equals the assembled prompt (file paths documented below).
- **FR-007**: Update CLI help text and project documentation to include `--dry-run` usage and examples.
- **FR-008**: Implementation MUST be covered by tests and pass existing linting/type checks.
- **FR-009**: Output format: For the MVP, `--dry-run` MUST print labeled plain text with `SYSTEM PROMPT` and `USER PROMPT` sections. Machine-readable output (e.g., JSON) may be added in a follow-up feature if requested.

### Key Entities *(include if feature involves data)*

- **Prompt**: The assembled text that would be sent to the LLM. Attributes: `system_prompt` (string), `user_prompt` (string). The dry-run output MUST present both parts.
- **CLI Flag**: `--dry-run` boolean controlling dry-run behavior.
- **LLMClient**: The abstraction responsible for interacting with LLM providers; MUST not be invoked in dry-run tests.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Unit tests assert that `generate_message(..., dry_run=True)` (or CLI `--dry-run`) prints the assembled prompt exactly and that `LLMClient.generate()` is not called (test coverage: one or more assertions per code path).
- **SC-002**: Integration test `tests/integration/test_cli_msg_dry_run.py` runs `gmuse msg --dry-run` on a repository with staged changes and passes (stdout contains prompt and exit code is 0).
- **SC-003**: CLI help (`gmuse msg --help`) contains `--dry-run` and the docs include an example (doc build includes the example without errors).
- **SC-004**: All tests and linting/type checks pass in CI with no regressions; the change is small and limited to the message generation flow.

---

## Assumptions

- Default output for the MVP is **plain text** that labels the two prompt sections like:

```
SYSTEM PROMPT:
<system_prompt>

USER PROMPT:
<user_prompt>
```

- If the user requests machine-readable output (e.g., JSON), that will be a follow-up enhancement unless the reviewer requests otherwise (see **FR-009** clarification).
- The dry-run is only required for `gmuse msg` and not for other CLI commands at this time.
- The generator will not perform any hidden telemetry or token usage in dry-run mode.

---

## Implementation Notes (non-normative)

- Option A: Add a small, testable API hook that allows assembling the prompt and returning it to the caller for inspection in non-production or testing paths. Keep the hook internal if possible to avoid expanding the public surface.
- Option B: Implement the dry-run in the CLI layer by calling `gather_context()` and `build_prompt()` directly and printing the prompt; this keeps the public generation API unchanged and minimizes surface area.

Both approaches are acceptable; Option B reduces public API impact and is likely easier to review and test.

---

## Test Plan (files & quick summary)

- **Unit**: `tests/unit/test_commit_dry_run.py`
  - Test that `build_prompt()` returns the expected prompts for sample diffs and that `generate_message(..., dry_run=True)` or CLI-level dry-run prints expected output.
  - Mock `LLMClient.generate` and assert it is NOT called when dry-run is used.

- **Integration**: `tests/integration/test_cli_msg_dry_run.py`
  - Create a git repo fixture with staged changes, run `gmuse msg --dry-run` and assert output and exit status.

- **Docs**: Update `docs/source/getting_started/quickstart.md` with an example using `--dry-run`.

---

## Open Questions / Clarifications

Q1: Output format chosen — Plain text only for MVP (Option A). The spec has been updated accordingly; JSON output may be added in a follow-up if needed.



**End of spec
