# Implementation Plan: Prompt Template Documentation Reference

**Branch**: `001-prompt-template-docs` | **Date**: 2025-12-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-prompt-template-docs/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a unified documentation reference page that displays the exact prompt templates and context inputs used by gmuse for AI suggestion requests. The reference must be automatically synchronized with the canonical template sources in `src/gmuse/prompts.py` via the documentation build process (`uv run nox -s docs`), preventing drift and maintaining a single source of truth. The build must fail if templates cannot be extracted.

## Technical Context

**Language/Version**: Python 3.10+ (project minimum)
**Primary Dependencies**: Sphinx, myst-parser, autodoc2, sphinx-copybutton, sphinx-design (existing docs stack)
**Storage**: N/A (documentation generation only)
**Testing**: pytest, pytest-cov (existing test infrastructure)
**Target Platform**: Documentation website (ReadTheDocs), local builds via nox
**Project Type**: Single project (existing structure: `src/gmuse/`, `tests/`, `docs/`)
**Performance Goals**: Documentation build time <30s additional overhead; no runtime impact
**Constraints**: Must integrate with existing Sphinx configuration; must not require manual template duplication
**Scale/Scope**: Single documentation page; 3 prompt templates (freeform, conventional, gitmoji); 4 context input types

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

All feature plans MUST validate against the `gmuse` Constitution. At minimum, the following checks MUST be documented and verified:

### Code Quality Gate ✅

- **Public API Changes**: No new public APIs exposed to end users; internal module `gmuse.docs` or `gmuse._docs_generator` may be added for Sphinx integration
- **Affected Modules**: `docs/source/conf.py` (Sphinx config), new `docs/_ext/` or `src/gmuse/_docs/` module for template extraction
- **Linting/Typing**: Standard Ruff/pyrefly rules apply; new extraction code must be fully typed
- **Conformance**: YES — no special linting rules required; follows existing patterns

### Testing Gate ✅

- **Unit Tests**: `tests/unit/test_prompt_template_extraction.py` — tests for template extraction logic, readability validation, error handling
- **Integration Tests**: `tests/integration/test_prompt_template_docs_sync.py` — verifies built documentation matches canonical templates; verifies docs build fails when templates missing/invalid
- **Coverage Target**: 85% for new template extraction modules
- **Drift Detection**: Tests MUST verify build failure on template mismatch
- **Conformance**: YES — test plan defined; coverage target set

### UX Gate ✅

- **CLI Changes**: None (documentation-only feature)
- **Documentation Updates**: New reference page at `docs/source/reference/prompt-templates.md`
- **Navigation**: Page linked from `docs/source/reference/index.md` and `docs/source/explanation/privacy.md`
- **Help Text**: N/A (no CLI changes)
- **Conformance**: YES — documentation structure defined

### Performance Gate ✅

- **Build Time**: Template extraction adds <2s to docs build (file I/O + regex parsing only)
- **Runtime Impact**: None (generation-time only)
- **Memory**: Negligible (<10MB additional during build)
- **Token Usage**: N/A (documentation feature, not LLM calls)
- **Conformance**: YES — no heavy operations; bounded and predictable

### Constitution Conformance Summary

| Gate | Status | Notes |
|------|--------|-------|
| Code Quality | ✅ PASS | Internal module, standard patterns |
| Testing | ✅ PASS | Unit + integration tests defined |
| UX | ✅ PASS | Documentation-only, navigation planned |
| Performance | ✅ PASS | <2s build overhead |

## Project Structure

### Documentation (this feature)

```text
specs/001-prompt-template-docs/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── template-extraction.md  # Template extraction interface contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── gmuse/
│   ├── prompts.py          # Canonical template source (EXISTING)
│   └── _docs/              # NEW: Documentation generation utilities
│       ├── __init__.py
│       └── template_extractor.py  # Extract templates from prompts.py

tests/
├── unit/
│   └── test_prompt_template_extraction.py  # NEW: Unit tests for extraction
└── integration/
    └── test_prompt_template_docs_sync.py   # NEW: Integration tests for sync

docs/
├── source/
│   ├── conf.py             # MODIFIED: Add template extraction hook
│   ├── reference/
│   │   ├── index.md        # MODIFIED: Add prompt-templates link
│   │   └── prompt-templates.md  # NEW: Generated reference page
│   └── explanation/
│       └── privacy.md      # MODIFIED: Link to prompt-templates reference
└── _ext/                   # ALTERNATIVE: Sphinx extension approach
    └── prompt_template_directive.py
```

**Structure Decision**: Single project structure (Option 1). The template extraction logic will be placed in `src/gmuse/_docs/` as a private module (prefixed with `_` to indicate internal use). This keeps extraction logic alongside source code and allows easy testing via the standard pytest setup.

## Complexity Tracking

> No Constitution Check violations requiring justification.

---

## Post-Design Constitution Re-evaluation

*Completed after Phase 1 design (2025-12-23)*

### Re-evaluation Summary

After completing research and design phases, all Constitution gates remain **PASSED**:

| Gate | Pre-Design | Post-Design | Changes |
|------|------------|-------------|---------|
| Code Quality | ✅ PASS | ✅ PASS | Confirmed: `gmuse._docs` module with typed functions |
| Testing | ✅ PASS | ✅ PASS | Confirmed: Test files and coverage targets defined |
| UX | ✅ PASS | ✅ PASS | Confirmed: Page structure and navigation documented |
| Performance | ✅ PASS | ✅ PASS | Confirmed: Direct import approach, <2s overhead |

### Design Decisions Validated

1. **Template Extraction**: Direct Python import (no AST parsing needed) — simplest approach, aligns with Code Quality principle of "well-structured and modular"
2. **Sphinx Integration**: Custom directive with `env-check-consistency` validation — ensures build failure on drift, aligns with Testing Standards
3. **Documentation Structure**: Single unified page with clear sections — meets UX Consistency principle
4. **No Public API Changes**: All new code is internal (`_docs` prefix) — no versioning/deprecation concerns

### Artifacts Generated

| Artifact | Path | Purpose |
|----------|------|---------|
| Research | [research.md](research.md) | Technical decisions and rationale |
| Data Model | [data-model.md](data-model.md) | Entity definitions and relationships |
| Contracts | [contracts/template-extraction.md](contracts/template-extraction.md) | Interface specifications |
| Quickstart | [quickstart.md](quickstart.md) | Implementation guide |

### Ready for Phase 2

This plan is ready for task breakdown (`/speckit.tasks` command). All Constitution gates pass, no violations require justification, and the design is complete.
