# Phase 0 Research: Secure API Key Management

## Context

This feature adds secure API key management for `gmuse` by introducing OS keyring storage and a new `gmuse auth` command group. The design must preserve the existing environment-variable-first behavior for non-interactive environments while giving interactive users a one-time secure setup path.

The existing codebase already has three important anchors:

- `gmuse.llm.detect_provider()` currently only checks environment variables and raises a missing-credential error when no provider key is present.
- `gmuse.cli.main.msg()` already funnels user-visible generation failures through actionable `LLMError` handling.
- `gmuse.cli.completions.completions_run_command()` already distinguishes timeout/offline/error completion outcomes, so keyring retrieval needs to plug into that path without introducing shell hangs.

## Decisions

### Decision 1 — Introduce a dedicated credential store abstraction

- Decision: Add a small `gmuse.credentials` module that owns all keyring reads, writes, deletes, backend checks, masking, and env-var fallback logic.
- Rationale:
  - The feature crosses CLI commands, message generation, and completions, so keyring behavior needs one shared implementation.
  - A single abstraction makes backend mocking straightforward for unit tests and keeps Typer/LLM modules free of keyring-specific branching.
- Alternatives considered:
  - Inline keyring access directly inside CLI commands and `llm.py`.
    - Rejected because it would duplicate backend checks, masking rules, and index maintenance across multiple call sites.

### Decision 2 — Enforce secure backend qualification before any prompt or write

- Decision: Validate backend availability and security before prompting in `gmuse auth set`, and reject `keyring.errors.NoKeyringError`, any backend from the `keyrings.alt` module, and `keyring.backends.null.Keyring`.
- Rationale:
  - This matches the spec's security requirement and prevents the user from entering secrets that would be written insecurely or discarded.
  - Failing early keeps the UX explicit and deterministic.
- Alternatives considered:
  - Attempt the write and inspect failures afterward.
    - Rejected because it prompts for a secret before knowing whether storage is safe.
  - Provide a `--allow-insecure` escape hatch.
    - Rejected by FR-007.

### Decision 3 — Keep env vars as the primary non-CLI source, with empty values treated as missing

- Decision: Credential resolution order remains CLI flag → environment variable → keyring → actionable error, but env vars containing only empty or whitespace content are treated as unresolved and allow keyring fallback.
- Rationale:
  - Preserves CI behavior while fixing the common “exported but blank” edge case.
  - Keeps existing precedence semantics simple and explicit.
- Alternatives considered:
  - Treat any present env var as authoritative, even if blank.
    - Rejected because it blocks fallback and creates a confusing failure mode.
  - Prefer keyring over env vars.
    - Rejected because it would surprise CI users and break established override semantics.

### Decision 4 — Use an internal managed-key index for default `auth status`

- Decision: Store a comma-separated managed-variable index under service `gmuse`, username `__gmuse_index__`, and use it for offline/default `gmuse auth status` output.
- Rationale:
  - Standard `keyring` does not offer a portable key enumeration API.
  - The index lets `status` remain scoped to gmuse-managed secrets without scanning the user's environment or OS keychain.
- Alternatives considered:
  - Attempt backend-specific key enumeration.
    - Rejected because it would break portability and complicate tests.
  - Show only variables passed explicitly to `status`.
    - Rejected because the default status command would become nearly useless.

### Decision 5 — Keep auth command inputs env-var-centric; use LiteLLM only for explicit provider validation

- Decision: `gmuse auth set/remove` operate on env var names like `OPENAI_API_KEY`; only `gmuse auth status <provider>` invokes `litellm.validate_environment(model="<provider>/dummy")` to interpret provider requirements.
- Rationale:
  - Avoids reimplementing LiteLLM's provider registry and supports providers that require multiple environment variables.
  - Keeps the command surface stable even when LiteLLM adds or changes providers.
- Alternatives considered:
  - Model the command surface around provider names only.
    - Rejected because multi-variable providers would need gmuse-owned mapping logic.

### Decision 6 — Bound completion-time keyring access to 200ms and fail closed

- Decision: Completion-time keyring retrieval runs through a bounded call path with a strict 200ms budget; timeout, interactive unlock prompts, and other keyring failures are treated as “credentials unavailable” and return no suggestion without shell-visible error output.
- Rationale:
  - Completion responsiveness is a hard UX requirement and already has offline/timeout handling in the completion runtime.
  - Silent degradation is safer than attempting to surface auth diagnostics during shell completion.
- Alternatives considered:
  - Reuse the normal `msg` credential path with no timeout.
    - Rejected because GUI unlock prompts or blocking backends can freeze the shell.
  - Disable keyring lookup entirely for completions.
    - Rejected because it would make completion quality worse for users who rely on keyring-backed auth.

### Decision 7 — Standardize masked output and overwrite confirmation behavior

- Decision: All displayed credential values use one masking helper: values with length 8 or more show only the last 4 characters; shorter values are fully masked. Overwrites require interactive `[y/N]` confirmation unless `--force` is supplied.
- Rationale:
  - Shared formatting avoids inconsistent UI and accidental leaks.
  - Explicit confirmation protects users from unintentionally replacing existing secrets.
- Alternatives considered:
  - Show partially masked short values.
    - Rejected by the spec's masking rule.
  - Overwrite silently.
    - Rejected because it removes an important safety check.
