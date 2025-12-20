# Implementation Plan: `gmuse msg --dry-run` (print prompt without calling LLM)

**Branch**: `003-msg-dry-run` | **Date**: 2025-12-19 | **Spec**: ../003-msg-dry-run/spec.md
**Input**: Feature specification from `specs/003-msg-dry-run/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add a `--dry-run` flag to `gmuse msg` that assembles the exact prompts that would be sent to the LLM, but prints them to stdout instead of making any provider calls.

Dry-run output is plain text and MUST include a short metadata header (`MODEL`, `FORMAT`, `TRUNCATED`) followed by the labeled `SYSTEM PROMPT` and `USER PROMPT` sections.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.10+
**Primary Dependencies**: Typer (CLI), pytest (tests), Ruff (lint/format), pyrefly (type-check), LiteLLM (provider calls; must be avoided in dry-run)
**Storage**: Filesystem + git repository state (staged diff, optional `.gmuse` file); N/A for new persistent storage
**Testing**: pytest (unit + integration)
**Target Platform**: Local CLI (Linux/macOS/Windows via Python)
**Project Type**: Single Python package (`src/gmuse`) with CLI entrypoints
**Performance Goals**: Dry-run should be near-instant (prompt assembly only); no network activity
**Constraints**: Must not call provider code paths; must preserve existing error handling and exit codes
**Scale/Scope**: Small, focused CLI behavior change with new tests and docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

All feature plans MUST validate against the `gmuse` Constitution. At minimum, the following checks MUST be documented and verified:

- **Code Quality Gate** — The plan MUST identify whether the change introduces public API surface changes, the affected modules, and whether new linting or typing rules are required.
- **Testing Gate** — The plan MUST list tests to be added: unit tests for public APIs, integration tests for cross-component behavior, and any acceptance tests for CLI/UX flows. Coverage targets should be stated.
- **UX Gate** — For CLI or user-facing changes, the plan MUST include intended command changes, help text, error messages, and documentation updates.
- **Performance Gate** — The plan MUST outline expected performance characteristics (latency, memory, token usage) and proposed mitigations for heavy operations (summarization, streaming, batching).

The plan MUST include a short checklist showing conformance (Yes/No) and any mitigation steps for items answered No.

Checklist:

- Code Quality Gate: Yes — changes are localized to CLI flow and prompt assembly; keep type hints and small helpers.
- Testing Gate: Yes — add unit tests and integration tests for `--dry-run` and “no provider calls”.
- UX Gate: Yes — add help text for `--dry-run` and update docs examples.
- Performance Gate: Yes — dry-run removes provider latency; prompt assembly is bounded by existing diff truncation.

## Project Structure

### Documentation (this feature)

```text
specs/003-msg-dry-run/
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
├── cli/
│   └── main.py
├── commit.py
├── prompts.py
└── llm.py

tests/
├── integration/
│   └── test_cli_msg_dry_run.py
└── unit/
  └── test_commit_dry_run.py

docs/source/
├── getting_started/
│   └── quickstart.md
└── reference/
  └── cli.md
```

**Structure Decision**: Single Python project (existing `src/gmuse` + `tests/`). Dry-run is implemented as a small CLI behavior extension with prompt assembly via existing `gmuse.prompts.build_prompt`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

No constitution violations are expected for this feature.

## Phase 0 — Outline & Research (Output: `research.md`)

Research focus areas:

- Implementing dry-run without triggering provider initialization (avoid `gmuse.llm.LLMClient` and its provider detection)
- Producing deterministic, labeled plain-text output for prompts + metadata header
- Testing strategy to assert “no provider call” at both unit and CLI integration levels

Output artifact:

- `specs/003-msg-dry-run/research.md`

## Phase 1 — Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Data model describing prompt output payload (non-persistent): `specs/003-msg-dry-run/data-model.md`
- CLI contract specifying exact output layout and flags: `specs/003-msg-dry-run/contracts/cli.md`
- Quickstart instructions and examples: `specs/003-msg-dry-run/quickstart.md`

Post-design constitution re-check:

- Code Quality: still localized; avoid expanding public API where possible.
- Testing: ensure unit + integration tests cover dry-run output and no-provider-call invariant.
- UX: help text and docs updated.
- Performance: no network; prompt build remains bounded by diff truncation.

## Phase 2 — Implementation Planning (Tasks breakdown; `tasks.md` created by `/speckit.tasks`)

Planned implementation steps:

1. Add `--dry-run` flag to `gmuse msg` command in `src/gmuse/cli/main.py`.
2. In dry-run mode:
  - Load config as usual (to resolve `MODEL`/`FORMAT`).
  - Gather context as usual (to preserve errors and truncation warnings).
  - Build prompts via `gmuse.prompts.build_prompt`.
  - Print metadata header and labeled prompts.
  - Exit 0 without calling any provider.
3. Add unit tests ensuring no provider calls occur.
4. Add integration tests invoking CLI and asserting header + prompt sections.
5. Update docs to mention `--dry-run` in CLI reference and quickstart.
