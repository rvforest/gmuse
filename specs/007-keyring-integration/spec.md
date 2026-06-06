# Feature Specification: Secure API Key Management

**Feature Branch**: `007-secure-auth`
**Created**: 2026-06-01
**Status**: Draft
**Input**: Design session exploring secure, UX-friendly API key management for interactive and non-interactive use

---

## Clarifications & Architecture Decisions

- **Auth command abstraction level**: Env var names (e.g., `OPENAI_API_KEY`), not provider names. This avoids reimplementing LiteLLM's provider registry and handles multi-var providers naturally.
- **Insecure keyring backend handling**: Block before prompting. Keyrings originating from the `keyrings.alt` module (plaintext) or `keyring.backends.null.Keyring` MUST be rejected. No escape hatches; env vars are the supported path for environments without a secure keyring.
- **Linux / `pass` support**: Supported transparently via `keyring`'s plugin system; gmuse has no `pass`-specific code.
- **Keyring namespace collisions**: Use `service_name="gmuse"` as the namespace.
- **Malicious package keyring access**: Not a gmuse-specific concern; identical risk profile to all secrets stored in the OS keychain.
- **Empty Environment Variables**: An environment variable set to an empty string or whitespace is considered "unresolved" and allows the resolution chain to fall through to the keyring.
- **State Tracking (The Index Method)**: Standard `keyring` lacks a cross-platform `list_keys()` method. `gmuse` will maintain a hidden index entry (`username="__gmuse_index__"`) containing a comma-separated list of managed variables to support offline/default `auth status` checks.
- **Provider Validation**: When a provider name is explicitly checked, `gmuse` will use the `<provider>/dummy` syntax with `litellm.validate_environment()` to leverage LiteLLM's internal validation without needing to hardcode provider requirements.

---

## User Scenarios & Testing

### User Story 1 — One-time interactive setup on a machine with a secure keyring (Priority: P1)

As a developer using gmuse interactively, I want to store my API key once in my OS keychain so that gmuse always has access to it without me exporting environment variables in every shell session.

**Independent Test**: Store a key via `gmuse auth set`, open a fresh shell with no related env vars exported, and run `gmuse msg`; the credential must resolve seamlessly.

**Acceptance Scenarios**:

1. **Given** a machine with a secure OS keyring backend, **When** the user runs `gmuse auth set OPENAI_API_KEY` and enters their key at the masked prompt, **Then** the key is stored under the `gmuse` service namespace, the `__gmuse_index__` is updated, and a success message is shown.
2. **Given** a key stored in the keyring, **When** the user opens a fresh shell with no related env vars set and runs `gmuse msg` for that provider's model, **Then** `gmuse` successfully resolves the key from the keyring and passes it to the generation engine without throwing a missing credential error.
3. **Given** a stored key, **When** `gmuse auth status` is run, **Then** the output lists the stored variable name, its storage source (keyring), and its masked value.

---

### User Story 2 — Linux/WSL without a secure keyring backend (Priority: P2)

As a developer on Linux or WSL2 without a secure keyring backend, I want a clear, actionable error when no secure keyring backend is available so I understand what gmuse supports and how to proceed.

**Independent Test**: Run `gmuse auth set` on a system with no backend installed (raising `NoKeyringError`) and a system where the only available backend is `PlaintextKeyring`; the command must exit with an error before prompting.

**Acceptance Scenarios**:

1. **Given** a system with no keyring backends installed (raising `keyring.errors.NoKeyringError`), **When** the user runs `gmuse auth set OPENAI_API_KEY`, **Then** the command catches the error, explains that no secure keychain is available, and directs the user to use env vars.
2. **Given** a system where the active backend is insecure (e.g., from `keyrings.alt`), **When** the user runs `gmuse auth set OPENAI_API_KEY`, **Then** the command intercepts it before prompting, explains why the plaintext backend was rejected, and directs the user to use env vars.

---

### User Story 3 — Removing stored credentials (Priority: P2)

As a developer, I want to remove one or more stored API keys from the keyring so I can rotate credentials or clean up after switching providers.

**Independent Test**: Store multiple keys, run `gmuse auth remove VAR1 VAR2`, then run `gmuse auth status`; the removed keys must no longer appear.

**Acceptance Scenarios**:

1. **Given** multiple keys stored, **When** the user runs `gmuse auth remove OPENAI_API_KEY ANTHROPIC_API_KEY`, **Then** the entries are deleted from the keyring, removed from `__gmuse_index__`, and a confirmation message is shown.
2. **Given** no entry stored for a variable, **When** the user runs `gmuse auth remove INVALID_KEY`, **Then** the command exits gracefully indicating no entry was found.

---

### User Story 4 — No auth configured anywhere (Priority: P1)

As a new user, I want a clear and actionable error when no API key is configured anywhere so I know exactly what to do next.

**Acceptance Scenarios**:

1. **Given** no env vars or keyring entries, **When** `gmuse msg` is run, **Then** the command exits with an error explaining the missing key, directing the user to `gmuse auth set` for interactive use and env vars for CI use.

---

### User Story 5 — Tab completions degrade gracefully (Priority: P3)

As a developer using zsh completions, I want the `git commit -m <TAB>` completion to degrade gracefully when credentials cannot be retrieved (e.g., OS GUI unlock prompt) so that my shell is never blocked.

**Acceptance Scenarios**:

1. **Given** a keyring backend that requires interactive prompting, **When** tab completion triggers gmuse, **Then** the retrieval times out at 200ms and exits cleanly with no suggestions, avoiding a shell hang.

---

## Edge Cases

- **Empty Env Vars**: If a user has `export OPENAI_API_KEY=""`, the resolution chain treats this as unresolved and falls through to the keyring.
- **Overwrites**: Running `gmuse auth set` for a variable that already exists requires a `[y/N]` confirmation. If run in a non-interactive shell, it aborts unless `--force` is passed.
- **Positional Arg Injection**: Attempting `gmuse auth set OPENAI_API_KEY sk-...` is rejected to prevent shell history exposure.
- **Multi-var Providers**: Azure requires `AZURE_API_KEY`, `AZURE_API_BASE`, etc. Each is stored and retrieved independently.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST resolve API key values in the following priority order: CLI flag → environment variable → keyring → actionable error. An environment variable set to an empty string or whitespace MUST be treated as unresolved, falling through to the keyring.
- **FR-002**: `gmuse auth set <VAR_NAME>` MUST prompt for the key value using masked input. Passing the value as a positional CLI argument MUST be rejected.
- **FR-003**: System MUST verify the availability of a secure keyring backend before prompting for a value. The command MUST elegantly catch `keyring.errors.NoKeyringError`. Furthermore, it MUST explicitly inspect the active backend and reject any backend originating from the `keyrings.alt` module or `keyring.backends.null.Keyring`. In both failure states, the command MUST exit with an error directing the user to use environment variables.
- **FR-004**: System MUST store keyring entries under service name `"gmuse"` with the env var name as the username.
- **FR-005**: `gmuse auth status` MUST default to displaying only the entries actively managed within the keyring. System MUST maintain an internal index of stored variable names (e.g., `username="__gmuse_index__"`). When invoked with no arguments, the command reads this index and displays the masked values without scanning the broader shell environment.
- **FR-006**: `gmuse auth remove <VAR_NAME> [VAR_NAME_2 ...]` MUST support variadic arguments to delete multiple entries simultaneously. It MUST remove the entries from both the keyring and the internal `__gmuse_index__`.
- **FR-007**: System MUST NOT provide any flag to bypass the insecure backend check.
- **FR-008**: System MUST NOT implement provider-specific auth logic internally. If `gmuse auth status <provider>` is explicitly invoked, `gmuse` MUST leverage LiteLLM's `validate_environment(model="<provider>/dummy")` to verify which required variables are present in the keyring or environment for that specific provider.
- **FR-009**: When no credentials are found via any path, System MUST exit with an error naming both setup paths.
- **FR-010**: The tab completions invocation path MUST enforce a strict **200ms timeout** on keyring retrieval. Any failure, interactive prompt blockage, or timeout MUST be treated as "no credentials available" and exit cleanly without emitting error output to the shell.
- **FR-011**: Valid environment variables MUST take precedence over keyring entries, preserving non-interactive compatibility.
- **FR-012**: Credential values MUST be masked in all UI output. If a credential is 12 characters or longer, it MUST be displayed as six asterisks followed by the last 4 characters (e.g., `******ABCD`). If a credential is shorter than 12 characters, every character MUST be replaced with an asterisk (e.g., `*******`).
- **FR-013**: Overwriting an existing keyring entry via `gmuse auth set` MUST require interactive `[y/N]` confirmation. In non-interactive environments, the overwrite MUST abort and exit with an error unless an explicit `--force` flag is provided.

---

## Constitution Check (Mandatory)

- **Security**: Keys never written to insecure backends (`keyrings.alt`, `null`); masked input enforced; strict key masking (last 4 chars) applied to all outputs; shell history injection blocked.
- **Code Quality**: Resolution chain is a single, isolated path. Keyring interactions abstracted to allow unit testing without daemon dependencies.
- **UX**: Strict 200ms timeout prevents shell hangs; multi-var teardown is painless via variadic args; `__gmuse_index__` ensures `status` is clean and scoped; empty env vars degrade smoothly.

---

## Success Criteria

- **SC-001**: A user with no related env vars exported can run `gmuse msg` successfully after a one-time `gmuse auth set` on a secure system.
- **SC-002**: A CI environment with only env vars experiences no change in behavior.
- **SC-003**: `gmuse auth set` on a system with no keyring backend (WSL2 default) or an insecure backend exits with a non-zero exit code before prompting for any key value, validated by automated tests mocking both `NoKeyringError` and a plaintext backend.
- **SC-004**: Tab completion exits with a zero exit code and no shell output if keyring retrieval exceeds 200ms.
- **SC-005**: All output accurately implements the standard masking rules defined in FR-012.
- **SC-006**: Multiple keys can be successfully removed in a single `auth remove` invocation, updating the internal index accurately.
