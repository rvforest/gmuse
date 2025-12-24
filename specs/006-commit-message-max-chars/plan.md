# Implementation Plan: Commit Message Max Characters (`max_chars`)

**Branch**: `006-commit-message-max-chars` | **Date**: 2025-12-23 | **Spec**: ../006-commit-message-max-chars/spec.md
**Input**: Feature specification from `specs/006-commit-message-max-chars/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add an optional configuration setting `max_chars` that, when set, is included in the prompt context and enforces a maximum character limit for generated commit messages.

When `max_chars` is unset (default), behavior remains unchanged.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.10+
**Primary Dependencies**: Typer (CLI), LiteLLM (provider calls), TOML loader (tomllib/tomli), pytest (tests), Ruff (lint/format), pyrefly (type-check)
**Storage**: Filesystem config (`~/.config/gmuse/config.toml` by default) + git repository state (staged diff)
**Testing**: pytest (unit + integration)
**Target Platform**: Local CLI (Linux/macOS/Windows via Python)
**Project Type**: Single Python package (`src/gmuse`) with Typer CLI entrypoint
**Performance Goals**: Negligible overhead vs baseline message generation; no extra provider calls
**Constraints**: Must keep config validation consistent; prompt must not include conflicting constraints; error messages must be actionable
**Scale/Scope**: Small, focused config + prompt behavior change with tests and docs updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

All feature plans MUST validate against the `gmuse` Constitution. At minimum, the following checks MUST be documented and verified:

- **Code Quality Gate** — The plan MUST identify whether the change introduces public API surface changes, the affected modules, and whether new linting or typing rules are required.
- **Testing Gate** — The plan MUST list tests to be added: unit tests for public APIs, integration tests for cross-component behavior, and any acceptance tests for CLI/UX flows. Coverage targets should be stated.
- **UX Gate** — For CLI or user-facing changes, the plan MUST include intended command changes, help text, error messages, and documentation updates.
- **Performance Gate** — The plan MUST outline expected performance characteristics (latency, memory, token usage) and proposed mitigations for heavy operations (summarization, streaming, batching).

The plan MUST include a short checklist showing conformance (Yes/No) and any mitigation steps for items answered No.

Checklist:

- Code Quality Gate: Yes — localized changes in config parsing/validation and prompt assembly; keep type hints and small helpers.
- Testing Gate: Yes — add unit tests for config + prompt inclusion + validation behavior; add integration test exercising the CLI flow.
- UX Gate: Yes — update configuration docs and CLI help/reference where config options are listed; ensure error message includes actual vs limit.
- Performance Gate: Yes — no extra provider calls; prompt adds only a small constant-size rule.

## Project Structure

### Documentation (this feature)

```text
specs/006-commit-message-max-chars/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/gmuse/
├── commit.py
├── config.py
├── prompts.py
└── cli/
  └── main.py

tests/
├── integration/
│   └── test_cli_msg_max_chars.py
└── unit/
  ├── test_config_max_chars.py
  └── test_prompts_max_chars.py

docs/source/
└── reference/
  └── configuration.md
```

**Structure Decision**: Single Python project (existing `src/gmuse` + `tests/`). This feature touches config validation (`config.py`), prompt assembly (`prompts.py`), and end-to-end generation flow (`commit.py` and/or CLI tests) with documentation updates.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

No constitution violations are expected for this feature.

## Phase 0 — Outline & Research (Output: `research.md`)

Research focus areas:

- Identify existing length-limit behavior (`max_message_length` + `validate_message`) and integrate `max_chars` without breaking compatibility.
- Decide enforcement strategy (fail vs truncate vs retry) and ensure errors remain actionable.
- Define character counting method and avoid adding new dependencies.

Output artifact:

- `specs/006-commit-message-max-chars/research.md`

## Phase 1 — Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Data model for `max_chars` and its interaction with `max_message_length`: `specs/006-commit-message-max-chars/data-model.md`
- Configuration contract: `specs/006-commit-message-max-chars/contracts/config.md`
- Prompt context contract: `specs/006-commit-message-max-chars/contracts/prompt-context.md`
- Quickstart examples: `specs/006-commit-message-max-chars/quickstart.md`

Phase 1 agent context update:

- Run `.specify/scripts/bash/update-agent-context.sh copilot` to keep agent context in sync.

Post-design constitution re-check:

- Code Quality: still localized; avoid expanding public APIs unless required.
- Testing: add unit + integration coverage for config validation and prompt inclusion.
- UX: document config key and environment variable; ensure errors include actual vs limit.
- Performance: prompt change is constant-size; no additional LLM calls.

## Phase 2 — Implementation Planning (Tasks breakdown; `tasks.md` created by `/speckit.tasks`)

Planned implementation steps:

1. Add new config key `max_chars` to defaults (default `None`) and merge/validation pipeline.
2. Add env var mapping `GMUSE_MAX_CHARS` → `max_chars` and validate range 1–500.
3. Thread `max_chars` into prompt assembly so the prompt includes an explicit maximum character instruction when configured.
4. Ensure conventional-commit prompt does not contain conflicting length constraints when `max_chars` is set.
5. Use `max_chars` as the effective `max_length` for `validate_message` when configured; otherwise use existing `max_message_length`.
6. Add unit tests:
  - config validation + env var parsing for `max_chars`
  - prompt inclusion behavior
  - validation failure contains “actual length” and “max”
7. Add integration test running `gmuse msg` with `GMUSE_MAX_CHARS` set and asserting failure when output exceeds limit (mocking provider output as needed).
8. Update docs to describe `max_chars` and how it interacts with `max_message_length`.
