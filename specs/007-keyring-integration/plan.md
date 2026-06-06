# Implementation Plan: Secure API Key Management

**Branch**: `007-keyring-integration` | **Date**: 2026-06-02 | **Spec**: ../007-keyring-integration/spec.md
**Input**: Feature specification from `specs/007-keyring-integration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add secure OS-keyring-backed credential management to `gmuse` with a new `gmuse auth` command group, an env-var-first resolution chain that falls back to keyring storage, masked credential status/removal UX, and a completion-safe 200ms timeout so shell completions never hang on keychain prompts.

The implementation should isolate keyring access behind a small credential store abstraction, keep environment variables as the highest non-CLI credential source for CI compatibility, and reuse LiteLLM only for explicit provider validation instead of introducing gmuse-specific provider registries.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Typer CLI, LiteLLM, `keyring`, standard library (`getpass`, `os`, `concurrent.futures` or `threading`), pytest, Ruff, pyrefly

**Storage**: Environment variables plus OS keyring entries under service name `gmuse`, including hidden index entry `__gmuse_index__`; existing user config file remains unchanged

**Testing**: pytest unit and integration tests with backend/keyring mocking

**Target Platform**: Local Python CLI on Linux, macOS, and Windows, including Linux/WSL environments without a secure keyring backend

**Project Type**: Single Python package (`src/gmuse`) with Typer-based CLI entrypoint

**Performance Goals**: Normal `gmuse msg` resolution adds negligible overhead; completion-time credential access must stay within the feature's strict 200ms limit and fail closed without shell-visible noise

**Constraints**: Reject insecure backends (`keyrings.alt`, `keyring.backends.null`), treat empty env vars as unset, preserve env-var precedence for CI, mask all displayed secrets, avoid provider-specific credential rules except explicit LiteLLM validation, and keep logs/error output secret-safe

**Scale/Scope**: Focused but cross-cutting CLI/auth feature touching credential resolution, completion runtime, command surface, docs, and test coverage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. The change can stay modular by introducing a dedicated credential/keyring abstraction plus a separate CLI sub-app for auth commands, keeping import-time side effects out of existing modules.
- **Testing Gate**: Pass. The plan includes unit tests for backend validation, masking, index maintenance, resolution order, and overwrite confirmation, plus integration tests for auth CLI flows and completion fallback behavior.
- **UX Gate**: Pass. New commands, errors, help text, and docs are all user-facing and can remain actionable: secure keyring success paths, insecure backend failures, and missing-credential guidance all include next steps.
- **Performance Gate**: Pass. The only new latency-sensitive path is completion-time credential lookup, which is explicitly bounded to 200ms and degrades to “no credentials available” rather than blocking.
- **Security/Privacy Gate**: Pass. The design rejects insecure backends, stores secrets only in OS keyrings or env vars, masks all outputs, and prevents shell-history leakage from positional arguments.

Checklist:

- Code Quality Gate: Yes — add a narrow credential store module and keep command wiring in Typer subcommands.
- Testing Gate: Yes — cover unit, integration, and completion timeout scenarios with mocked keyring behavior.
- UX Gate: Yes — commands and error messages remain explicit and actionable; docs update required.
- Performance Gate: Yes — completion path uses a hard timeout and silent fallback.
- Security/Privacy Gate: Yes — secure backend enforcement and masking rules are part of the core design.

## Project Structure

### Documentation (this feature)

```text
specs/007-keyring-integration/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── auth-cli.md
│   └── credential-resolution.md
└── tasks.md
```

### Source Code (repository root)

```text
src/gmuse/
├── cli/
│   ├── auth.py              # new auth command group
│   ├── completions.py       # completion-safe credential fallback
│   └── main.py              # register auth subcommands and missing-credential UX
├── commit.py                # generation path may consume resolved credentials indirectly
├── config.py                # env loading semantics remain env-first, empty-string-aware
├── credentials.py           # new secure keyring abstraction and resolution helpers
├── exceptions.py            # auth/keyring-specific user-facing exceptions
└── llm.py                   # provider detection and credential resolution integration

tests/
├── integration/
│   ├── test_cli.py
│   ├── test_completions_run.py
│   └── test_keyring_auth_integration.py
└── unit/
    ├── test_cli_auth.py
    ├── test_cli_completions.py
    ├── test_credentials.py
    ├── test_llm.py
    └── test_main_env.py

docs/source/
├── explanation/
│   └── privacy.md
├── how_to/
│   ├── completions.md
│   ├── configuration.md
│   └── troubleshooting.md
└── reference/
    ├── cli.md
    └── configuration.md
```

**Structure Decision**: Keep the existing single-package CLI structure. Introduce one new library module for credential/keyring behavior and one new Typer subcommand module for `gmuse auth`; update existing CLI, completion, LLM, docs, and tests around those abstractions.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 — Outline & Research (Output: `research.md`)

Research focus areas:

- Define the secure keyring abstraction boundary so auth commands and runtime resolution share one code path.
- Confirm how to distinguish secure vs insecure/unavailable backends before prompting.
- Decide how env-var fallthrough, keyring indexing, and masking rules interact in `status` and `msg` flows.
- Define completion-time timeout behavior so keychain prompts cannot block shells.
- Confirm provider-specific validation strategy without recreating LiteLLM provider metadata in gmuse.

Output artifact:

- `specs/007-keyring-integration/research.md`

## Phase 1 — Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Credential entities and state transitions: `specs/007-keyring-integration/data-model.md`
- CLI interface contract: `specs/007-keyring-integration/contracts/auth-cli.md`
- Runtime credential resolution contract: `specs/007-keyring-integration/contracts/credential-resolution.md`
- User/operator walkthrough: `specs/007-keyring-integration/quickstart.md`

Phase 1 agent context update:

- Update `.github/copilot-instructions.md` so the Speckit plan reference points at `specs/007-keyring-integration/plan.md`.

Post-design constitution re-check:

- Code Quality: remains modular if keyring logic stays isolated from Typer wiring and LLM orchestration.
- Testing: still requires unit coverage for the store abstraction and integration coverage for CLI/completions.
- UX: docs and help text must reflect secure keyring vs env-var guidance.
- Performance: completion path still bounded to 200ms and degrades silently.
- Security/Privacy: all displayed values remain masked; insecure backend bypass is not introduced.

## Phase 2 — Implementation Planning (Tasks breakdown; `tasks.md` created by `/speckit.tasks`)

Planned implementation steps:

1. Add a credential/keyring module that validates the active backend, stores entries under service `gmuse`, and maintains the `__gmuse_index__` entry.
2. Add masking, overwrite detection, and remove/index-update helpers so all auth commands and status output share the same formatting rules.
3. Add a Typer `auth` command group with `set`, `status`, and `remove` commands centered on env var names, including masked prompt input and overwrite confirmation.
4. Integrate runtime resolution into the existing message-generation path so credential lookup order becomes CLI flag → environment variable → keyring → actionable error.
5. Treat empty or whitespace env vars as unresolved and allow keyring fallback instead of treating them as valid credentials.
6. Add explicit provider validation for `gmuse auth status <provider>` using LiteLLM `validate_environment(model="<provider>/dummy")` rather than gmuse-owned provider metadata.
7. Bound completion-time keyring lookup to 200ms and treat timeout, prompt blockage, or backend failure as an offline/no-suggestion outcome.
8. Update missing-credential and insecure-backend error messages so they direct interactive users to `gmuse auth set` and CI users to environment variables.
9. Add unit tests for backend qualification, index maintenance, masking, empty-env fallthrough, overwrite confirmation, and provider validation wiring.
10. Add integration tests for `gmuse auth` set/status/remove flows, `gmuse msg` keyring fallback, insecure backend rejection, and completion timeout degradation.
11. Update CLI/reference/privacy/completions documentation to explain secure keyring support, supported fallback behavior, and CI guidance.
