# Implementation Plan: Backend and Transport Abstraction

**Branch**: `main` | **Date**: 2026-05-29 | **Spec**: ../007-backend-transport-abstraction/spec.md

**Input**: Feature specification from `specs/007-backend-transport-abstraction/spec.md`

## Summary

Separate backend resolution from model resolution while preserving today's simple direct-provider setup for the built-in direct backends. The implementation will introduce backend as a first-class configuration and diagnostic concept, apply a deterministic resolution order, and reserve a scoped extension point for future backend-specific options without shipping those options yet.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Typer (CLI), LiteLLM (model/provider parsing and request execution), tomllib/tomli (config loading), pytest (tests), Ruff (lint/format), pyrefly (type checking)

**Storage**: Filesystem config (`~/.config/gmuse/config.toml` by default), environment variables, in-memory resolution context, and git repository state for generation inputs

**Testing**: pytest (unit + integration)

**Target Platform**: Local CLI on Linux/macOS/Windows via Python

**Project Type**: Single Python package (`src/gmuse`) with Typer CLI entrypoint

**Performance Goals**: Add only negligible startup overhead versus the current direct-provider flow; perform no extra network calls or backend preflight requests during direct-backend resolution; preserve existing generation latency for single direct-backend users

**Constraints**: Preserve current behavior for users with one configured direct backend; initial implementation supports only the current built-in direct backends; configuration precedence remains CLI > environment > config file > defaults; errors and diagnostics must be actionable; do not advertise concrete backend-specific settings yet

**Scale/Scope**: Cross-cutting refactor of the LLM/config/CLI resolution path for five current built-in direct backends (`openai`, `anthropic`, `cohere`, `azure`, `gemini`) plus targeted docs and regression tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

All feature plans MUST validate against the `gmuse` Constitution. For this feature:

- **Code Quality Gate** — Yes. The change affects core resolution behavior, but remains localized to `src/gmuse/llm.py`, `src/gmuse/config.py`, `src/gmuse/cli/main.py`, and supporting tests/docs. The plan keeps the abstraction centered on small, typed helpers instead of spreading backend logic across call sites.
- **Testing Gate** — Yes. Add unit coverage for backend detection/resolution, config precedence, ambiguity handling, backend/model mismatch handling, and updated diagnostics; add integration coverage for single-backend preservation and explicit backend selection in multi-backend scenarios.
- **UX Gate** — Yes. CLI help, config reference, troubleshooting output, and `gmuse info` diagnostics will be updated to distinguish backend from model and to reserve provider wording for specific direct or routed provider cases only.
- **Performance Gate** — Yes. The design keeps resolution local and static for in-scope direct backends, avoiding network lookups or provider metadata preflight requests.

Checklist:

- Code Quality Gate: Yes — introduce a dedicated backend resolution layer instead of further coupling `detect_provider()` and `LLMClient` construction.
- Testing Gate: Yes — expand both unit and integration coverage across the existing direct-backend path and new ambiguity/error paths.
- UX Gate: Yes — update CLI/config/docs wording and diagnostics, with special attention to `gmuse info` and existing string-pinned tests.
- Performance Gate: Yes — resolution remains local, constant-sized, and bounded by static backend metadata.

## Project Structure

### Documentation (this feature)

```text
specs/007-backend-transport-abstraction/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── backend-selection.md
│   └── diagnostics.md
└── tasks.md
```

### Source Code (repository root)

```text
src/gmuse/
├── commit.py
├── config.py
├── exceptions.py
├── llm.py
└── cli/
    ├── config.py
    └── main.py

tests/
├── integration/
│   ├── test_cli.py
│   └── test_cli_config.py
└── unit/
    ├── test_cli_load_config_llm_overrides.py
    ├── test_cli_main.py
    ├── test_cli_main_additional.py
    ├── test_config.py
    └── test_llm.py

docs/source/
├── how_to/
│   ├── configuration.md
│   └── troubleshooting.md
└── reference/
    ├── cli.md
    ├── configuration.md
    └── default_models.md

README.md
```

**Structure Decision**: Single Python CLI package with centralized config and LLM resolution. This feature should preserve that shape and add a backend abstraction inside the existing modules rather than splitting the project into new packages.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 — Outline & Research (Output: `research.md`)

Research focus areas:

- Decouple today's provider-detection and model-resolution flow without breaking the current single direct-backend happy path.
- Define deterministic backend resolution rules for explicit backend selection, native backend hints, single compatible backend fallback, and ambiguous multi-backend cases.
- Standardize terminology so user-facing surfaces use `backend` as the umbrella term while reserving `provider` for more specific direct or routed provider meanings.
- Reserve a backend-specific settings mechanism without shipping concrete advanced options in the initial direct-backend implementation.
- Identify the docs, diagnostics, and tests that currently pin provider wording or behavior.

Output artifact:

- `specs/007-backend-transport-abstraction/research.md`

## Phase 1 — Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Resolution data model: `specs/007-backend-transport-abstraction/data-model.md`
- Backend selection contract: `specs/007-backend-transport-abstraction/contracts/backend-selection.md`
- Diagnostics contract: `specs/007-backend-transport-abstraction/contracts/diagnostics.md`
- User-facing adoption examples: `specs/007-backend-transport-abstraction/quickstart.md`

Phase 1 agent context update:

- Run `.specify/scripts/bash/update-agent-context.sh copilot` to keep agent context in sync with this plan.

Post-design constitution re-check:

- Code Quality: still localized to the current resolution modules; abstraction remains testable and typed.
- Testing: unit + integration coverage explicitly planned for new backend resolution rules and wording changes.
- UX: diagnostics, help text, and docs have concrete update targets and do not expose unused backend-specific controls.
- Performance: no extra network calls or dynamic provider discovery are required for the in-scope direct backends.

## Phase 2 — Implementation Planning (Tasks breakdown; `tasks.md` created by `/speckit.tasks`)

Planned implementation steps:

1. Introduce `backend` as a first-class config value with CLI, environment variable, config-file, merge, and validation support.
2. Extract backend resolution into a dedicated helper or set of helpers so `LLMClient` no longer owns the full provider-detection decision implicitly.
3. Represent the current built-in direct backends in one static backend registry that captures credential signals, default model, and compatibility checks.
4. Apply the documented resolution order: explicit backend, native backend hint, single configured compatible direct backend, otherwise actionable error.
5. Validate backend/model compatibility and missing-credential cases before request submission.
6. Update `gmuse info` and related diagnostics to surface resolved backend, resolved model, and resolution source while using `backend` as the umbrella term.
7. Update tests that currently pin provider wording or provider-only heuristics, plus add new coverage for ambiguity, mismatch, and explicit backend selection.
8. Update README and docs reference/how-to pages to document backend terminology, backend selection, and preserved direct-backend defaults.
