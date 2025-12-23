# Data Model: Prompt Template Documentation Reference

**Feature**: 005-prompt-template-docs
**Date**: 2025-12-23
**Status**: Complete

## Overview

This document defines the data structures used for extracting, representing, and rendering prompt template documentation. Since this is a documentation-generation feature, the "data model" describes internal structures used during the build process rather than persisted entities.

---

## Entities

### 1. PromptTemplate

Represents a single prompt template extracted from source code.

```python
@dataclass
class PromptTemplate:
    """A prompt template extracted from the canonical source."""

    name: str
    """Unique identifier for the template (e.g., 'system', 'freeform')."""

    content: str
    """The raw template text content."""

    template_type: Literal["constant", "function"]
    """Whether the template is a module constant or returned by a function."""

    source_location: str
    """File path and location where the template is defined."""

    description: Optional[str] = None
    """Optional description extracted from docstring or comments."""
```

**Validation Rules**:
- `name` must be non-empty and lowercase alphanumeric with hyphens
- `content` must be non-empty after stripping whitespace
- `template_type` must be either "constant" or "function"
- `source_location` must point to an existing file

---

### 2. ContextInput

Represents a piece of context that may be included in a prompt.

```python
@dataclass
class ContextInput:
    """A context input that may be included in LLM requests."""

    name: str
    """Human-readable name (e.g., 'Staged Diff', 'Branch Context')."""

    identifier: str
    """Code identifier (e.g., 'staged_diff', 'branch_info')."""

    description: str
    """Description of what this input contains."""

    inclusion_condition: str
    """When this input is included (e.g., 'Always', 'When --include-branch flag set')."""

    is_required: bool
    """Whether this input is always required for a valid request."""

    is_optional: bool
    """Whether this input is opt-in via configuration."""

    privacy_notes: Optional[str] = None
    """Privacy-relevant notes (e.g., sanitization applied)."""
```

**Known Context Inputs**:

| Identifier | Name | Required | Optional | Condition |
|------------|------|----------|----------|-----------|
| `staged_diff` | Staged Diff | ✅ | ❌ | Always included |
| `commit_history` | Commit History | ❌ | ❌ | Included if available |
| `repo_instructions` | Repository Instructions | ❌ | ❌ | Included if `.gmuse` exists |
| `branch_info` | Branch Context | ❌ | ✅ | `--include-branch` flag |
| `user_hint` | User Hint | ❌ | ✅ | `--hint` flag provided |
| `learning_examples` | Learning Examples | ❌ | ✅ | Learning enabled |

---

### 3. TemplateRegistry

Collection of all templates with metadata.

```python
@dataclass
class TemplateRegistry:
    """Registry of all prompt templates."""

    version: str
    """Version of the prompt template format (from PROMPT_VERSION)."""

    templates: Dict[str, PromptTemplate]
    """Map of template name to template."""

    context_inputs: List[ContextInput]
    """All possible context inputs."""

    extracted_at: datetime
    """Timestamp when templates were extracted."""

    source_module: str
    """Python module path for canonical source."""

    def get_template(self, name: str) -> PromptTemplate:
        """Get a template by name, raising KeyError if not found."""
        ...

    def validate(self) -> None:
        """Validate all templates are present and valid."""
        ...
```

**Required Templates**:
- `system` — Base system prompt
- `freeform` — Freeform format task
- `conventional` — Conventional commits format task
- `gitmoji` — Gitmoji format task

---

### 4. DocumentationPage

Represents the generated documentation output.

```python
@dataclass
class DocumentationPage:
    """Generated documentation page content."""

    title: str
    """Page title."""

    sections: List[DocumentationSection]
    """Ordered list of sections."""

    def render_markdown(self) -> str:
        """Render the page as Markdown."""
        ...


@dataclass
class DocumentationSection:
    """A section within the documentation page."""

    heading: str
    """Section heading."""

    level: int
    """Heading level (1-6)."""

    content: str
    """Section content (Markdown)."""

    template_name: Optional[str] = None
    """If this section displays a template, its name."""
```

---

## Relationships

```
TemplateRegistry
    │
    ├── 1:N ──► PromptTemplate
    │               - system
    │               - freeform
    │               - conventional
    │               - gitmoji
    │
    └── 1:N ──► ContextInput
                    - staged_diff
                    - commit_history
                    - repo_instructions
                    - branch_info
                    - user_hint
                    - learning_examples


DocumentationPage
    │
    └── 1:N ──► DocumentationSection
                    - overview
                    - context_inputs_table
                    - system_prompt
                    - freeform_section
                    - conventional_section
                    - gitmoji_section
                    - versioning_notes
```

---

## State Transitions

This feature has no runtime state transitions. All operations occur at documentation build time:

```
[Source Code] ──extract──► [TemplateRegistry] ──render──► [DocumentationPage] ──write──► [HTML]
     │                           │                              │
     │                           ▼                              │
     │                    [Validation]                          │
     │                      (pass/fail)                         │
     │                           │                              │
     ▼                           ▼                              ▼
prompts.py             Build continues              prompt-templates.html
                       or fails with error
```

---

## Validation Rules Summary

| Entity | Rule | Error Message |
|--------|------|---------------|
| PromptTemplate | `content` non-empty | "Template '{name}' is empty" |
| PromptTemplate | `source_location` exists | "Source file not found: {path}" |
| TemplateRegistry | All required templates present | "Missing required template: {name}" |
| TemplateRegistry | Version matches PROMPT_VERSION | "Version mismatch: expected {expected}, got {actual}" |
| ContextInput | `identifier` matches code | "Unknown context input: {identifier}" |

---

## Example: Extracted Registry

```python
registry = TemplateRegistry(
    version="1.0.0",
    templates={
        "system": PromptTemplate(
            name="system",
            content="You are an expert commit message generator...",
            template_type="constant",
            source_location="src/gmuse/prompts.py:L35-L42",
            description="Base system prompt used for all generations",
        ),
        "freeform": PromptTemplate(
            name="freeform",
            content="Generate a commit message in natural language...",
            template_type="function",
            source_location="src/gmuse/prompts.py:L57-L71",
            description="Task prompt for freeform commit messages",
        ),
        # ... conventional, gitmoji
    },
    context_inputs=[
        ContextInput(
            name="Staged Diff",
            identifier="staged_diff",
            description="The literal code changes added to git index",
            inclusion_condition="Always included",
            is_required=True,
            is_optional=False,
            privacy_notes="Contains actual code changes",
        ),
        # ... other inputs
    ],
    extracted_at=datetime(2025, 12, 23, 12, 0, 0),
    source_module="gmuse.prompts",
)
```
