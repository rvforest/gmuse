# Research: Prompt Template Documentation Reference

**Feature**: 001-prompt-template-docs
**Date**: 2025-12-23
**Status**: Complete

## Research Questions

Based on the Technical Context in [plan.md](plan.md), the following areas required clarification:

1. How to extract prompt templates from Python source (`prompts.py`) reliably?
2. What Sphinx integration patterns best support auto-generated content?
3. How to implement drift detection that fails the build on mismatch?
4. What is the best approach for including templates in documentation?

---

## 1. Template Extraction Approach

### Decision: Direct Python Import with AST Fallback

**Rationale**: The canonical templates are defined as:
- Module-level constants: `SYSTEM_PROMPT`, `PROMPT_VERSION`
- Functions returning strings: `get_freeform_task()`, `get_conventional_task()`, `get_gitmoji_task()`

Direct Python import is the most reliable approach since `prompts.py` has no side effects at import time (verified in codebase review).

**Implementation**:
```python
# Primary approach: Direct import
from gmuse.prompts import (
    SYSTEM_PROMPT,
    PROMPT_VERSION,
    get_freeform_task,
    get_conventional_task,
    get_gitmoji_task,
)

templates = {
    "system": SYSTEM_PROMPT,
    "freeform": get_freeform_task(),
    "conventional": get_conventional_task(),
    "gitmoji": get_gitmoji_task(),
}
```

**Alternatives Considered**:
- **AST parsing**: More complex, unnecessary since module is side-effect-free
- **Regex extraction**: Fragile, breaks with formatting changes
- **Separate template files**: Requires refactoring existing code, out of scope

---

## 2. Sphinx Integration Patterns

### Decision: Sphinx Extension with Custom Directive

**Rationale**: Sphinx extensions provide the cleanest integration with the existing docs build. A custom directive allows:
- Template content to be injected at build time
- Build failure if extraction fails
- No manual file generation step

**Implementation Approach**:
```python
# docs/_ext/prompt_templates.py
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

class PromptTemplateDirective(SphinxDirective):
    """Include prompt template content in documentation."""

    required_arguments = 1  # template name

    def run(self):
        template_name = self.arguments[0]
        content = extract_template(template_name)
        # Return code block node with template content
        ...
```

**Usage in Markdown/RST**:
```markdown
## System Prompt

```{prompt-template} system
```

## Freeform Format

```{prompt-template} freeform
```
```

**Alternatives Considered**:
- **Pre-generation script**: Adds build step complexity; requires watching for changes
- **Jinja templates**: Sphinx already uses Jinja, but custom directive is cleaner
- **Include directive with generated file**: Requires generation step, defeats single-source goal

---

## 3. Drift Detection Strategy

### Decision: Build-Time Validation with Hash Comparison

**Rationale**: The build must fail if:
1. Templates cannot be imported (import error, module not found)
2. Template structure has changed unexpectedly (new templates added, old ones removed)

**Implementation**:
```python
# In Sphinx extension setup
def validate_templates(app, env):
    """Validate all expected templates are extractable."""
    REQUIRED_TEMPLATES = ["system", "freeform", "conventional", "gitmoji"]

    for name in REQUIRED_TEMPLATES:
        try:
            content = extract_template(name)
            if not content or not content.strip():
                raise ValueError(f"Template '{name}' is empty")
        except Exception as e:
            raise RuntimeError(
                f"Failed to extract prompt template '{name}': {e}\n"
                f"Ensure src/gmuse/prompts.py is valid and contains the template."
            ) from e

def setup(app: Sphinx):
    app.connect("env-check-consistency", validate_templates)
```

**Build Failure Scenario**:
```console
$ uv run nox -s docs
...
ERROR: Failed to extract prompt template 'gitmoji': Template function not found
Ensure src/gmuse/prompts.py is valid and contains the template.
```

**Alternatives Considered**:
- **Hash file comparison**: Overkill for this use case; import errors are sufficient
- **CI-only check**: Misses local builds; developers should see failures immediately
- **Warning-only**: Violates FR-005 (MUST fail, not warn)

---

## 4. Context Inputs Documentation

### Decision: Structured Table with Conditional Indicators

**Rationale**: The spec requires documenting all context inputs with their inclusion conditions. A structured table provides clarity.

**Context Inputs Identified** (from `build_context()` in `prompts.py`):

| Input | Description | Included When | Source |
|-------|-------------|---------------|--------|
| **Branch Context** | Branch type and summary | `--include-branch` flag enabled | `BranchInfo` dataclass |
| **Commit History** | Recent commit messages (up to 5) | Always (if available) | `CommitHistory` dataclass |
| **Repository Instructions** | Content from `.gmuse` file | `.gmuse` file exists | `RepositoryInstructions` dataclass |
| **User Hint** | User-provided context | `--hint` flag provided | CLI argument |
| **Learning Examples** | Previous generated/edited pairs | Learning enabled & history exists | Learning store |
| **Staged Diff** | Raw diff of staged changes | Always required | `StagedDiff` dataclass |

**Staged Diff Metadata** (always included):
- Files changed count
- Lines added count
- Lines removed count
- Truncation indicator (if diff exceeds limits)

---

## 5. Documentation Page Structure

### Decision: Single Unified Page with Clear Sections

**Rationale**: Per spec clarification, a single page with section dividers is preferred over multiple pages.

**Proposed Structure**:
```markdown
# Prompt Template Reference

## Overview
Brief explanation of what this page documents and why.

## What Gets Sent to the LLM

### Context Inputs
Table of all inputs with conditions.

### System Prompt
The base system prompt (always included).

## Output Formats

### Freeform Format
Task prompt for freeform messages.

### Conventional Commits Format
Task prompt for conventional commits.

### Gitmoji Format
Task prompt for gitmoji messages.

## Stability & Versioning
Template versioning policy (stable within major versions).
```

---

## 6. Testing Strategy

### Decision: Unit + Integration Tests with Build Validation

**Unit Tests** (`tests/unit/test_prompt_template_extraction.py`):
- `test_extract_system_prompt` — verifies SYSTEM_PROMPT extraction
- `test_extract_format_tasks` — verifies all format task functions
- `test_extract_handles_import_error` — verifies graceful error handling
- `test_template_content_non_empty` — verifies templates have content

**Integration Tests** (`tests/integration/test_prompt_template_docs_sync.py`):
- `test_docs_build_succeeds` — runs `nox -s docs` and verifies exit code 0
- `test_docs_build_fails_on_missing_template` — patches import to fail, verifies build fails
- `test_generated_page_contains_templates` — reads built HTML, verifies template content present

**Coverage Target**: 85% for new extraction modules

---

## Summary of Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| Extraction | Direct Python import | Side-effect-free module; simplest approach |
| Sphinx Integration | Custom directive | Clean integration; build-time generation |
| Drift Detection | Build-time validation | Immediate feedback; meets FR-005 |
| Documentation | Single page, sectioned | Per spec clarification; user-friendly |
| Testing | Unit + integration | Coverage for extraction + build validation |

---

## References

- [Sphinx Extension Tutorial](https://www.sphinx-doc.org/en/master/development/tutorials/helloworld.html)
- [MyST Markdown Directives](https://myst-parser.readthedocs.io/en/latest/syntax/roles-and-directives.html)
- [gmuse prompts.py](../../src/gmuse/prompts.py) — Canonical template source
