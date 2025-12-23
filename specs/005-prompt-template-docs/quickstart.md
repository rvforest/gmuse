# Quickstart: Prompt Template Documentation Reference

**Feature**: 005-prompt-template-docs
**Date**: 2025-12-23

## Overview

This guide provides a minimal path to implementing the prompt template documentation reference feature. Follow these steps in order.

---

## Prerequisites

- Python 3.10+
- `uv` package manager installed
- Repository cloned and dependencies synced (`uv sync`)

---

## Implementation Order

### Step 1: Create Template Extractor Module

Create the internal module for extracting templates:

```bash
mkdir -p src/gmuse/_docs
touch src/gmuse/_docs/__init__.py
```

Create `src/gmuse/_docs/template_extractor.py`:

```python
"""Template extraction utilities for documentation generation."""

from dataclasses import dataclass
from typing import Dict, List

from gmuse.prompts import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    get_conventional_task,
    get_freeform_task,
    get_gitmoji_task,
)


@dataclass(frozen=True)
class ExtractedTemplate:
    """An extracted prompt template."""
    name: str
    content: str
    description: str


@dataclass(frozen=True)
class ContextInputInfo:
    """Information about a context input."""
    name: str
    description: str
    condition: str
    is_optional: bool


# Template definitions
_TEMPLATES = {
    "system": ("SYSTEM_PROMPT", lambda: SYSTEM_PROMPT, "Base system prompt"),
    "freeform": ("get_freeform_task", get_freeform_task, "Freeform format task"),
    "conventional": ("get_conventional_task", get_conventional_task, "Conventional commits task"),
    "gitmoji": ("get_gitmoji_task", get_gitmoji_task, "Gitmoji format task"),
}

# Context input definitions
_CONTEXT_INPUTS = [
    ContextInputInfo("Staged Diff", "Code changes added to git index", "Always included", False),
    ContextInputInfo("Commit History", "Recent commit messages for style", "Always (if available)", False),
    ContextInputInfo("Repository Instructions", "Content from .gmuse file", "If .gmuse exists", False),
    ContextInputInfo("Branch Context", "Sanitized branch name info", "--include-branch flag", True),
    ContextInputInfo("User Hint", "User-provided context", "--hint flag provided", True),
    ContextInputInfo("Learning Examples", "Previous edit history", "Learning enabled", True),
]


def get_prompt_version() -> str:
    """Get the current prompt template version."""
    return PROMPT_VERSION


def extract_all_templates() -> Dict[str, ExtractedTemplate]:
    """Extract all prompt templates."""
    result = {}
    for name, (source_name, getter, desc) in _TEMPLATES.items():
        content = getter() if callable(getter) else getter
        if not content or not content.strip():
            raise ValueError(f"Template '{name}' is empty")
        result[name] = ExtractedTemplate(name=name, content=content, description=desc)
    return result


def get_context_inputs() -> List[ContextInputInfo]:
    """Get information about all context inputs."""
    return list(_CONTEXT_INPUTS)


def validate_templates() -> None:
    """Validate all templates are extractable and non-empty."""
    try:
        templates = extract_all_templates()
        if len(templates) != 4:
            raise ValueError(f"Expected 4 templates, got {len(templates)}")
    except Exception as e:
        raise RuntimeError(f"Prompt template validation failed: {e}") from e
```

---

### Step 2: Create Sphinx Extension

Create `docs/_ext/prompt_templates.py`:

```python
"""Sphinx extension for prompt template documentation."""

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

from gmuse._docs.template_extractor import (
    extract_all_templates,
    get_context_inputs,
    validate_templates,
)


class PromptTemplateDirective(SphinxDirective):
    """Include a prompt template as a code block."""

    required_arguments = 1
    has_content = False

    def run(self):
        template_name = self.arguments[0]
        templates = extract_all_templates()

        if template_name not in templates:
            raise self.error(f"Unknown template: {template_name}")

        template = templates[template_name]
        code = nodes.literal_block(template.content, template.content)
        code["language"] = "text"
        return [code]


class ContextInputsTableDirective(SphinxDirective):
    """Render context inputs as a table."""

    has_content = False

    def run(self):
        inputs = get_context_inputs()

        # Build table structure
        table = nodes.table()
        tgroup = nodes.tgroup(cols=4)
        table += tgroup

        # Column specs
        for _ in range(4):
            tgroup += nodes.colspec(colwidth=1)

        # Header
        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for text in ["Input", "Description", "Included When", "Optional"]:
            entry = nodes.entry()
            entry += nodes.paragraph(text=text)
            header_row += entry
        thead += header_row

        # Body
        tbody = nodes.tbody()
        tgroup += tbody
        for inp in inputs:
            row = nodes.row()
            for text in [inp.name, inp.description, inp.condition, "Yes" if inp.is_optional else "No"]:
                entry = nodes.entry()
                entry += nodes.paragraph(text=text)
                row += entry
            tbody += row

        return [table]


def _validate_on_build(app, env):
    """Validate templates during build."""
    validate_templates()


def setup(app: Sphinx):
    """Set up the extension."""
    app.add_directive("prompt-template", PromptTemplateDirective)
    app.add_directive("context-inputs-table", ContextInputsTableDirective)
    app.connect("env-check-consistency", _validate_on_build)

    return {"version": "1.0.0", "parallel_read_safe": True}
```

---

### Step 3: Update Sphinx Configuration

Edit `docs/source/conf.py`:

```python
# Add extension path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "_ext"))

# Add to extensions list
extensions = [
    # ... existing extensions ...
    "prompt_templates",  # Add this
]
```

---

### Step 4: Create Documentation Page

Create `docs/source/reference/prompt-templates.md`:

````markdown
# Prompt Template Reference

This page documents the exact prompts and context inputs that gmuse sends to
LLM providers when generating commit messages.

## Overview

When you run `gmuse msg`, the tool builds a prompt from several sources and
sends it to your configured LLM provider. This reference shows exactly what
is included so you can make informed privacy and accuracy decisions.

**Template Version**: See [PROMPT_VERSION](../../src/gmuse/prompts.py) in source.

## Context Inputs

The following information may be included in requests:

```{context-inputs-table}
```

## System Prompt

The base system prompt is always included:

```{prompt-template} system
```

## Output Format Templates

Depending on the `--format` flag, one of these task prompts is appended:

### Freeform (default)

```{prompt-template} freeform
```

### Conventional Commits

```{prompt-template} conventional
```

### Gitmoji

```{prompt-template} gitmoji
```

## Stability

These templates are treated as a **stable public contract** within major versions.
Changes will only occur in major releases with documented migration notes in the
[CHANGELOG](https://github.com/rvforest/gmuse/blob/main/CHANGELOG.md).
````

---

### Step 5: Update Navigation

Edit `docs/source/reference/index.md`:

```markdown
# Reference

Technical reference for APIs and configuration.

```{toctree}
:maxdepth: 1

cli
configuration
prompt-templates
validation
default_models
../apidocs/index
```
```

---

### Step 6: Add Tests

Create `tests/unit/test_prompt_template_extraction.py`:

```python
"""Tests for prompt template extraction."""

import pytest

from gmuse._docs.template_extractor import (
    extract_all_templates,
    get_context_inputs,
    get_prompt_version,
    validate_templates,
)


def test_get_prompt_version():
    """Version string is returned."""
    version = get_prompt_version()
    assert isinstance(version, str)
    assert version  # Non-empty


def test_extract_all_templates():
    """All templates are extracted."""
    templates = extract_all_templates()
    assert set(templates.keys()) == {"system", "freeform", "conventional", "gitmoji"}
    for name, template in templates.items():
        assert template.name == name
        assert len(template.content) > 50


def test_get_context_inputs():
    """Context inputs are returned."""
    inputs = get_context_inputs()
    assert len(inputs) == 6
    names = {i.name for i in inputs}
    assert "Staged Diff" in names
    assert "Branch Context" in names


def test_validate_templates_succeeds():
    """Validation passes for valid templates."""
    validate_templates()  # Should not raise
```

Create `tests/integration/test_prompt_template_docs_sync.py`:

```python
"""Integration tests for prompt template documentation sync."""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.slow
def test_docs_build_succeeds():
    """Documentation builds successfully with templates."""
    result = subprocess.run(
        ["uv", "run", "nox", "-s", "docs"],
        capture_output=True,
        cwd=Path(__file__).parent.parent.parent,
    )
    assert result.returncode == 0, f"Docs build failed: {result.stderr.decode()}"


@pytest.mark.slow
def test_docs_contain_template_content():
    """Built docs contain template content."""
    # First build docs
    subprocess.run(["uv", "run", "nox", "-s", "docs"], capture_output=True)

    html_path = Path("docs/build/html/reference/prompt-templates.html")
    if html_path.exists():
        content = html_path.read_text()
        assert "expert commit message generator" in content.lower()
```

---

### Step 7: Verify

Run the full verification:

```bash
# Run unit tests
uv run pytest tests/unit/test_prompt_template_extraction.py -v

# Build docs
uv run nox -s docs

# Open and verify
open docs/build/html/reference/prompt-templates.html
```

---

## Success Criteria Checklist

- [ ] Template extractor module created and tested
- [ ] Sphinx extension registered and functional
- [ ] Documentation page renders with template content
- [ ] Navigation updated (reference index, privacy page link)
- [ ] Docs build fails if templates are invalid (test manually)
- [ ] All unit tests pass
- [ ] Integration tests pass

---

## Troubleshooting

### Import Error in Sphinx Build

```
ImportError: No module named 'gmuse._docs'
```

**Fix**: Ensure `src/gmuse/_docs/__init__.py` exists and the package is installed in editable mode.

### Template Not Found

```
Unknown template: freeform
```

**Fix**: Verify `_TEMPLATES` dict in `template_extractor.py` includes all template names.

### Build Doesn't Fail on Error

**Fix**: Ensure `env-check-consistency` event is connected in `setup()` function.
