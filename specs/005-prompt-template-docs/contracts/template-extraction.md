# Contract: Template Extraction Interface

**Feature**: 001-prompt-template-docs
**Date**: 2025-12-23
**Version**: 1.0.0

## Overview

This document defines the interface contracts for extracting prompt templates from the canonical source (`src/gmuse/prompts.py`) and rendering them in documentation.

---

## Module: `gmuse._docs.template_extractor`

### Purpose

Provides functions to extract prompt templates from the `gmuse.prompts` module for use in documentation generation.

### Public Interface

```python
"""Template extraction utilities for documentation generation.

This module extracts prompt templates from gmuse.prompts for inclusion
in documentation. It is intended for use by Sphinx extensions and tests only.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ExtractedTemplate:
    """An extracted prompt template."""

    name: str
    """Template identifier (e.g., 'system', 'freeform')."""

    content: str
    """The template text content."""

    description: str
    """Human-readable description of the template."""


@dataclass(frozen=True)
class ContextInputInfo:
    """Information about a context input."""

    name: str
    """Human-readable name."""

    description: str
    """What this input contains."""

    condition: str
    """When this input is included."""

    is_optional: bool
    """Whether this is an opt-in input."""


def get_prompt_version() -> str:
    """Get the current prompt template version.

    Returns:
        Version string (e.g., '1.0.0')

    Raises:
        ImportError: If gmuse.prompts cannot be imported.
        AttributeError: If PROMPT_VERSION is not defined.

    Example:
        >>> version = get_prompt_version()
        >>> print(version)
        '1.0.0'
    """
    ...


def extract_system_prompt() -> ExtractedTemplate:
    """Extract the base system prompt.

    Returns:
        ExtractedTemplate with system prompt content.

    Raises:
        ImportError: If gmuse.prompts cannot be imported.
        AttributeError: If SYSTEM_PROMPT is not defined.
        ValueError: If the extracted content is empty.

    Example:
        >>> template = extract_system_prompt()
        >>> print(template.name)
        'system'
    """
    ...


def extract_format_task(format_name: str) -> ExtractedTemplate:
    """Extract a format-specific task prompt.

    Args:
        format_name: One of 'freeform', 'conventional', 'gitmoji'.

    Returns:
        ExtractedTemplate with task prompt content.

    Raises:
        ImportError: If gmuse.prompts cannot be imported.
        ValueError: If format_name is not recognized.
        ValueError: If the extracted content is empty.

    Example:
        >>> template = extract_format_task('conventional')
        >>> print(template.name)
        'conventional'
        >>> 'Conventional Commits' in template.content
        True
    """
    ...


def extract_all_templates() -> Dict[str, ExtractedTemplate]:
    """Extract all prompt templates.

    Returns:
        Dict mapping template name to ExtractedTemplate.
        Keys: 'system', 'freeform', 'conventional', 'gitmoji'

    Raises:
        ImportError: If gmuse.prompts cannot be imported.
        ValueError: If any template is empty or missing.

    Example:
        >>> templates = extract_all_templates()
        >>> list(templates.keys())
        ['system', 'freeform', 'conventional', 'gitmoji']
    """
    ...


def get_context_inputs() -> List[ContextInputInfo]:
    """Get information about all context inputs.

    Returns:
        List of ContextInputInfo for each possible input.

    Example:
        >>> inputs = get_context_inputs()
        >>> [i.name for i in inputs]
        ['Staged Diff', 'Commit History', 'Repository Instructions',
         'Branch Context', 'User Hint', 'Learning Examples']
    """
    ...


def validate_templates() -> None:
    """Validate all templates are extractable and non-empty.

    Raises:
        RuntimeError: If any template cannot be extracted or is empty.
            Error message includes which template failed and why.

    Example:
        >>> validate_templates()  # No error if valid
        >>> # Raises RuntimeError if templates invalid
    """
    ...
```

---

## Sphinx Extension: `docs/_ext/prompt_templates.py`

### Purpose

Sphinx extension that provides directives for including prompt templates in documentation.

### Directives

#### `{prompt-template}`

Includes a prompt template's content as a code block.

**Usage**:
```markdown
```{prompt-template} system
```

```{prompt-template} freeform
```
```

**Arguments**:
- `template_name` (required): One of `system`, `freeform`, `conventional`, `gitmoji`

**Output**: A fenced code block containing the template text.

#### `{context-inputs-table}`

Renders a table of all context inputs with their descriptions and conditions.

**Usage**:
```markdown
```{context-inputs-table}
```
```

**Arguments**: None

**Output**: A Markdown table with columns: Name, Description, Included When, Optional

---

### Extension Setup

```python
def setup(app: Sphinx) -> Dict[str, Any]:
    """Set up the prompt templates extension.

    Registers:
        - prompt-template directive
        - context-inputs-table directive
        - env-check-consistency event handler for validation

    Returns:
        Extension metadata dict.
    """
    app.add_directive("prompt-template", PromptTemplateDirective)
    app.add_directive("context-inputs-table", ContextInputsTableDirective)
    app.connect("env-check-consistency", _validate_templates_on_build)

    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
```

---

## Error Messages

All errors MUST be actionable. Required error messages:

| Scenario | Error Message |
|----------|---------------|
| Import failure | `"Failed to import gmuse.prompts: {exception}. Ensure the package is installed."` |
| Missing template | `"Template '{name}' not found in gmuse.prompts. Expected function 'get_{name}_task' or constant '{NAME}'."` |
| Empty template | `"Template '{name}' is empty. Check the source in src/gmuse/prompts.py."` |
| Unknown format | `"Unknown template format '{name}'. Valid formats: system, freeform, conventional, gitmoji"` |
| Build validation | `"Prompt template validation failed: {details}. Documentation build aborted."` |

---

## Integration Points

### 1. Documentation Build (`nox -s docs`)

```
nox -s docs
    │
    ├── sphinx-build invoked
    │       │
    │       ├── Extension loaded (docs/_ext/prompt_templates.py)
    │       │
    │       ├── env-check-consistency event
    │       │       └── validate_templates() called
    │       │           └── FAIL: RuntimeError → build aborts
    │       │           └── PASS: continue build
    │       │
    │       ├── Process prompt-templates.md
    │       │       ├── {prompt-template} directives
    │       │       │       └── extract_format_task() or extract_system_prompt()
    │       │       │
    │       │       └── {context-inputs-table} directive
    │       │               └── get_context_inputs()
    │       │
    │       └── Generate HTML output
    │
    └── Build complete (exit 0) or failed (exit 1)
```

### 2. Test Integration

```python
# tests/unit/test_prompt_template_extraction.py

def test_extract_system_prompt():
    """System prompt is extractable and non-empty."""
    template = extract_system_prompt()
    assert template.name == "system"
    assert len(template.content) > 100

def test_extract_all_formats():
    """All format templates are extractable."""
    templates = extract_all_templates()
    assert set(templates.keys()) == {"system", "freeform", "conventional", "gitmoji"}

def test_validate_templates_succeeds():
    """Validation passes for valid templates."""
    validate_templates()  # Should not raise

def test_context_inputs_complete():
    """All context inputs are documented."""
    inputs = get_context_inputs()
    names = {i.name for i in inputs}
    assert "Staged Diff" in names
    assert "Branch Context" in names
```

```python
# tests/integration/test_prompt_template_docs_sync.py

def test_docs_build_includes_templates():
    """Built documentation contains template content."""
    result = subprocess.run(["uv", "run", "nox", "-s", "docs"], capture_output=True)
    assert result.returncode == 0

    html_path = Path("docs/build/html/reference/prompt-templates.html")
    content = html_path.read_text()
    assert "You are an expert commit message generator" in content

def test_docs_build_fails_on_broken_import(monkeypatch):
    """Build fails if templates cannot be imported."""
    # Patch to simulate import failure
    ...
    result = subprocess.run(["uv", "run", "nox", "-s", "docs"], capture_output=True)
    assert result.returncode != 0
    assert "Failed to import" in result.stderr.decode()
```

---

## Version Compatibility

- **Minimum Python**: 3.10 (matches project requirement)
- **Sphinx Version**: Compatible with Sphinx 7.x (current docs stack)
- **MyST Parser**: Compatible with myst-parser 3.x

---

## Changelog

### 1.0.0 (2025-12-23)
- Initial contract definition
- Core extraction functions defined
- Sphinx directives specified
- Validation and error handling contracts established
