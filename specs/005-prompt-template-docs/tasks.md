---

description: "Task list for implementing prompt template documentation reference"
---

# Tasks: Prompt Template Documentation Reference

**Input**: Design documents from `/specs/005-prompt-template-docs/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Included (explicitly requested in `spec.md`).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm existing code + docs build constraints and create the minimal directories needed.

- [X] T001 [P] Review canonical prompt definitions in src/gmuse/prompts.py (SYSTEM_PROMPT, get_*_task())
- [X] T002 [P] Review Sphinx build entrypoints in noxfile.py and docs/source/conf.py (confirm where to hook build-time validation)
- [X] T003 Create internal docs module package directory in src/gmuse/_docs/__init__.py
- [X] T004 Create Sphinx extension directory in docs/_ext/prompt_templates.py (file placeholder; real implementation in later phases)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Make `gmuse` importable during Sphinx builds and establish the shared extraction + directive scaffolding.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Update import paths for Sphinx builds in docs/source/conf.py (add `src/` and `docs/_ext/` to `sys.path`)
- [X] T006 Implement extractor scaffolding types in src/gmuse/_docs/template_extractor.py (define `ExtractedTemplate`, `ContextInputInfo` dataclasses)
- [X] T007 Implement Sphinx extension scaffolding in docs/_ext/prompt_templates.py (register directives: `prompt-template`, `context-inputs-table`)
- [X] T008 Run docs build to confirm extension loads: `uv run nox -s docs` (validates docs/source/conf.py and docs/_ext/prompt_templates.py)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Understand What Gets Sent (Priority: P1) 🎯 MVP

**Goal**: Provide a documentation page that lists every possible context input in a suggestion request and clearly states inclusion rules.

**Independent Test**: Build docs and open the reference page; verify the page lists all context inputs and clearly indicates which are optional and when they are included.

### Implementation for User Story 1

- [X] T009 [P] [US1] Define canonical context inputs list in src/gmuse/_docs/template_extractor.py (`get_context_inputs()` matches `build_context()` inputs)
- [X] T010 [P] [US1] Implement `{context-inputs-table}` directive rendering a 4-column table in docs/_ext/prompt_templates.py (Input, Description, Included When, Optional)
- [X] T011 [US1] Create the reference page shell in docs/source/reference/prompt-templates.md (overview + context inputs section using `{context-inputs-table}`)
- [X] T012 [P] [US1] Add the page to Reference navigation in docs/source/reference/index.md
- [X] T013 [P] [US1] Add a cross-link from Privacy page to the reference page in docs/source/explanation/privacy.md
- [X] T014 [US1] Build docs via `uv run nox -s docs` (verify docs/build/html/reference/prompt-templates.html renders the context inputs table)

**Checkpoint**: US1 complete — users can see all possible request inputs + inclusion rules.

---

## Phase 4: User Story 2 - See the Exact Template Text (Priority: P2)

**Goal**: Show the exact canonical prompt template text used for suggestion requests, without manual copying.

**Independent Test**: Build docs and confirm the rendered template text matches src/gmuse/prompts.py (byte-for-byte, ignoring HTML wrappers) and is copyable.

### Tests for User Story 2 (write first; ensure they FAIL before implementation)

- [X] T015 [P] [US2] Add unit tests for template extraction success paths in tests/unit/test_prompt_template_extraction.py
- [X] T016 [P] [US2] Add unit tests for error cases (unknown format, empty template) in tests/unit/test_prompt_template_extraction.py

### Implementation for User Story 2

- [X] T017 [P] [US2] Implement template extraction functions in src/gmuse/_docs/template_extractor.py (`get_prompt_version()`, `extract_system_prompt()`, `extract_format_task()`, `extract_all_templates()`)
- [X] T018 [P] [US2] Implement `{prompt-template}` directive in docs/_ext/prompt_templates.py (renders requested template as a copyable literal/code block)
- [X] T019 [US2] Extend docs/source/reference/prompt-templates.md with sections for system + freeform/conventional/gitmoji templates using `{prompt-template}`
- [X] T020 [US2] Add stability/versioning section to docs/source/reference/prompt-templates.md (state “stable public contract within major versions” and link to CHANGELOG if present)
- [X] T021 [US2] Run focused unit tests via `uv run nox -s test -- tests/unit/test_prompt_template_extraction.py`
- [X] T022 [US2] Build docs via `uv run nox -s docs` (verify the templates render and are copyable on docs/build/html/reference/prompt-templates.html)

**Checkpoint**: US2 complete — exact template text is visible in docs and sourced from code.

---

## Phase 5: User Story 3 - Maintain Single Source of Truth (Priority: P3)

**Goal**: Prevent drift by automatically synchronizing docs to canonical templates and failing docs builds when templates cannot be extracted.

**Independent Test**: Intentionally break template extraction (e.g., rename a canonical function) and confirm `uv run nox -s docs` fails with a clear, actionable error. Change template content in src/gmuse/prompts.py and confirm docs output changes without editing docs text.

### Tests for User Story 3 (write first; ensure they FAIL before implementation)

- [X] T023 [P] [US3] Add integration test asserting docs build succeeds and output contains expected prompt snippets in tests/integration/test_prompt_template_docs_sync.py
- [X] T024 [P] [US3] Add integration test asserting docs build fails on template extraction failure in tests/integration/test_prompt_template_docs_sync.py
- [X] T025 [P] [US3] Add unit test for build-validation error messaging in tests/unit/test_prompt_template_extraction.py (assert `validate_templates()` raises `RuntimeError` with actionable message)

### Implementation for User Story 3

- [X] T026 [US3] Implement `validate_templates()` in src/gmuse/_docs/template_extractor.py (non-empty templates; known set present; actionable errors)
- [X] T027 [US3] Wire build-time validation into docs/_ext/prompt_templates.py (hook Sphinx validation early and abort build on validation failure)
- [X] T028 [US3] Ensure docs build failure messages are clear and identify the missing/empty template in docs/_ext/prompt_templates.py
- [X] T029 [US3] Run focused integration tests via `uv run nox -s test -- tests/integration/test_prompt_template_docs_sync.py`

**Checkpoint**: US3 complete — docs are always in sync and drift cannot silently ship.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Keep quality gates green and ensure privacy expectations are met.

- [X] T030 [P] Confirm the reference page uses only synthetic placeholders (no real repo content) in docs/source/reference/prompt-templates.md
- [X] T031 [P] Run repo quality gates via `uv run nox -s check` (lint/format/types)
- [X] T032 [P] Run full test suite via `uv run nox -s test` (ensure no regressions)
- [X] T033 [P] Run docs build one final time via `uv run nox -s docs` (verify navigation + rendering)

---

## Dependencies & Execution Order

### User Story Dependencies (graph)

- US1 → US2 → US3

Interpretation: US1 establishes the discoverable reference page + context inputs; US2 adds exact template rendering; US3 adds build-failing drift prevention and sync tests.

### Phase Dependencies

- Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1)
- Phase 3 (US1) → Phase 4 (US2)
- Phase 4 (US2) → Phase 5 (US3)
- Phase 6 (Polish) after all desired stories

---

## Parallel Execution Examples

### User Story 1

- In parallel:
  - T009 (src/gmuse/_docs/template_extractor.py)
  - T010 (docs/_ext/prompt_templates.py)
  - T012 (docs/source/reference/index.md)
  - T013 (docs/source/explanation/privacy.md)

### User Story 2

- In parallel:
  - T015–T016 (tests/unit/test_prompt_template_extraction.py)
  - T017 (src/gmuse/_docs/template_extractor.py)
  - T018 (docs/_ext/prompt_templates.py)

### User Story 3

- In parallel:
  - T023–T024 (tests/integration/test_prompt_template_docs_sync.py)
  - T025 (tests/unit/test_prompt_template_extraction.py)

---

## Implementation Strategy

### Suggested MVP Scope

Implement **Phase 1–3 (US1)** first: deliver the discoverable reference page and context inputs table.

### Incremental Delivery

1. Setup + Foundational
2. US1 (context inputs + navigation)
3. US2 (exact template rendering + unit tests)
4. US3 (drift prevention + integration tests)
5. Polish gates
